import subprocess
from unittest.mock import MagicMock

import pytest

from bifrost.core.errors import CiBusyError, ConfigError, RemoteCommandError
from bifrost.core.models import BifrostConfig, SetupConfig
from bifrost.core.runner import Runner


@pytest.fixture
def setup_a() -> SetupConfig:
    return SetupConfig(name="office-a", host="10.0.0.5", user="ci", runner="pytest")


@pytest.fixture
def setup_b() -> SetupConfig:
    return SetupConfig(name="office-b", host="10.1.0.7", user="ci")


@pytest.fixture
def config(setup_a: SetupConfig, setup_b: SetupConfig) -> BifrostConfig:
    return BifrostConfig(
        setups={"office-a": setup_a, "office-b": setup_b},
        default_setup="office-a",
    )


@pytest.fixture
def ci_gate() -> MagicMock:
    gate = MagicMock()
    gate.is_busy.return_value = False
    return gate


@pytest.fixture
def executor() -> MagicMock:
    ex = MagicMock()
    ex.run_remote.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="ok", stderr=""
    )
    return ex


@pytest.fixture
def git_ops() -> MagicMock:
    return MagicMock()


@pytest.fixture
def copier() -> MagicMock:
    c = MagicMock()
    c.copy_artifacts.return_value = []
    c.store_run_metadata.return_value = None
    return c


@pytest.fixture
def runner(
    config: BifrostConfig,
    ci_gate: MagicMock,
    executor: MagicMock,
    git_ops: MagicMock,
    copier: MagicMock,
) -> Runner:
    return Runner(config, ci_gate, executor, git_ops, copier)


class TestResolveSetup:
    def test_resolves_by_name(self, runner: Runner, setup_a: SetupConfig) -> None:
        # Act
        result = runner.resolve_setup("office-a")

        # Assert
        assert result == setup_a

    def test_falls_back_to_default(self, runner: Runner, setup_a: SetupConfig) -> None:
        # Act
        result = runner.resolve_setup(None)

        # Assert
        assert result == setup_a

    def test_raises_when_no_name_and_no_default(
        self,
        config: BifrostConfig,
        ci_gate: MagicMock,
        executor: MagicMock,
        git_ops: MagicMock,
        copier: MagicMock,
    ) -> None:
        # Arrange
        config_no_default = BifrostConfig(setups=config.setups)
        r = Runner(config_no_default, ci_gate, executor, git_ops, copier)

        # Act / Assert
        with pytest.raises(ConfigError, match="No setup specified"):
            r.resolve_setup(None)

    def test_raises_for_unknown_setup(self, runner: Runner) -> None:
        # Act / Assert
        with pytest.raises(ConfigError, match="not found"):
            runner.resolve_setup("nonexistent")


class TestRun:
    def test_successful_run_with_command(
        self, runner: Runner, executor: MagicMock, copier: MagicMock
    ) -> None:
        # Act
        meta = runner.run(setup_name="office-a", command=["pytest", "-m", "smoke"])

        # Assert
        assert meta.setup == "office-a"
        assert meta.command == ["pytest", "-m", "smoke"]
        assert meta.exit_code == 0
        executor.run_remote.assert_called_once()
        copier.copy_artifacts.assert_called_once()

    def test_uses_default_runner_when_no_command(
        self, runner: Runner, executor: MagicMock
    ) -> None:
        # Act
        meta = runner.run(setup_name="office-a")

        # Assert
        assert meta.command == ["pytest"]

    def test_raises_when_no_command_and_no_runner(self, runner: Runner) -> None:
        # Act / Assert
        with pytest.raises(ConfigError, match="No command provided"):
            runner.run(setup_name="office-b")

    def test_checks_ci_gate(self, runner: Runner, ci_gate: MagicMock) -> None:
        # Arrange
        ci_gate.is_busy.return_value = True

        # Act / Assert
        with pytest.raises(CiBusyError, match="busy"):
            runner.run(setup_name="office-a", command=["pytest"])

    def test_force_skips_ci_gate(
        self, runner: Runner, ci_gate: MagicMock, executor: MagicMock
    ) -> None:
        # Arrange
        ci_gate.is_busy.return_value = True

        # Act
        meta = runner.run(setup_name="office-a", command=["pytest"], force=True)

        # Assert
        assert meta.exit_code == 0
        ci_gate.is_busy.assert_not_called()

    def test_dry_run_does_not_execute(
        self,
        runner: Runner,
        executor: MagicMock,
        git_ops: MagicMock,
        copier: MagicMock,
    ) -> None:
        # Act
        meta = runner.run(
            setup_name="office-a", command=["pytest"], ref="main", dry_run=True
        )

        # Assert
        assert meta.setup == "office-a"
        assert meta.ref == "main"
        executor.run_remote.assert_not_called()
        git_ops.fetch_and_checkout.assert_not_called()
        copier.copy_artifacts.assert_not_called()

    def test_handles_ref_with_latest(self, runner: Runner, git_ops: MagicMock) -> None:
        # Act
        runner.run(setup_name="office-a", command=["pytest"], ref="main", latest=True)

        # Assert
        git_ops.fetch_and_checkout.assert_called_once()
        args = git_ops.fetch_and_checkout.call_args
        assert args[0][1] == "main"
        assert args[1]["latest"] is True

    def test_raises_on_remote_failure(
        self, runner: Runner, executor: MagicMock, copier: MagicMock
    ) -> None:
        # Arrange
        executor.run_remote.return_value = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="fail"
        )

        # Act / Assert
        with pytest.raises(RemoteCommandError, match="Command failed"):
            runner.run(setup_name="office-a", command=["pytest"])

        copier.store_run_metadata.assert_called_once()
        copier.copy_artifacts.assert_called_once()
