import subprocess
from unittest.mock import MagicMock

import pytest

from bifrost.commands.run import CiBusyError, RemoteCommandError, Runner
from bifrost.shared import BifrostConfig, ConfigError, SetupConfig


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
def pipeline_gate() -> MagicMock:
    gate = MagicMock()
    gate.is_busy.return_value = False
    return gate


@pytest.fixture
def log_store() -> MagicMock:
    store = MagicMock()
    store.copy_logs.return_value = []
    store.store_run_metadata.return_value = None
    return store


@pytest.fixture
def runner(
    config: BifrostConfig,
    log_store: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> Runner:
    run_remote_mock = MagicMock(
        return_value=subprocess.CompletedProcess(
            args=[], returncode=0, stdout="ok", stderr=""
        )
    )
    fetch_checkout_mock = MagicMock()
    pipeline_gate_mock = MagicMock(
        return_value=MagicMock(is_busy=MagicMock(return_value=False))
    )

    monkeypatch.setattr("bifrost.commands.run.runner.run_remote", run_remote_mock)
    monkeypatch.setattr(
        "bifrost.commands.run.runner.fetch_and_checkout", fetch_checkout_mock
    )
    monkeypatch.setattr(
        "bifrost.commands.run.runner.create_pipeline_gate", pipeline_gate_mock
    )

    return Runner(config, log_store)


class TestResolveSetup:
    def test_resolves_by_name(self, runner: Runner, setup_a: SetupConfig) -> None:
        result = runner.resolve_setup("office-a")
        assert result == setup_a

    def test_falls_back_to_default(self, runner: Runner, setup_a: SetupConfig) -> None:
        result = runner.resolve_setup(None)
        assert result == setup_a

    def test_raises_when_no_name_and_no_default(
        self, config: BifrostConfig, log_store: MagicMock
    ) -> None:
        config_no_default = BifrostConfig(setups=config.setups)
        r = Runner(config_no_default, log_store)

        with pytest.raises(ConfigError, match="No setup specified"):
            r.resolve_setup(None)

    def test_raises_for_unknown_setup(self, runner: Runner) -> None:
        with pytest.raises(ConfigError, match="not found"):
            runner.resolve_setup("nonexistent")


class TestRun:
    def test_successful_run_with_command(
        self, runner: Runner, log_store: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        run_remote_mock = MagicMock(
            return_value=subprocess.CompletedProcess(
                args=[], returncode=0, stdout="ok", stderr=""
            )
        )

        monkeypatch.setattr("bifrost.commands.run.runner.run_remote", run_remote_mock)

        meta = runner.run(setup_name="office-a", command=["pytest", "-m", "smoke"])

        assert meta.setup == "office-a"
        assert meta.command == ["pytest", "-m", "smoke"]
        assert meta.exit_code == 0
        run_remote_mock.assert_called_once()
        log_store.copy_logs.assert_called_once()

    def test_uses_default_runner_when_no_command(self, runner: Runner) -> None:
        meta = runner.run(setup_name="office-a")
        assert meta.command == ["pytest"]

    def test_raises_when_no_command_and_no_runner(self, runner: Runner) -> None:
        with pytest.raises(ConfigError, match="No command provided"):
            runner.run(setup_name="office-b")

    def test_checks_pipeline_gate(
        self, runner: Runner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        busy_gate = MagicMock(is_busy=MagicMock(return_value=True))
        monkeypatch.setattr(
            "bifrost.commands.run.runner.create_pipeline_gate",
            MagicMock(return_value=busy_gate),
        )

        with pytest.raises(CiBusyError, match="busy"):
            runner.run(setup_name="office-a", command=["pytest"])

    def test_force_skips_pipeline_gate(
        self, runner: Runner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        busy_gate = MagicMock(is_busy=MagicMock(return_value=True))
        create_gate_mock = MagicMock(return_value=busy_gate)
        monkeypatch.setattr(
            "bifrost.commands.run.runner.create_pipeline_gate", create_gate_mock
        )

        meta = runner.run(setup_name="office-a", command=["pytest"], force=True)

        assert meta.exit_code == 0
        busy_gate.is_busy.assert_not_called()

    def test_dry_run_does_not_execute(
        self, runner: Runner, log_store: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        run_remote_mock = MagicMock()
        fetch_checkout_mock = MagicMock()

        monkeypatch.setattr("bifrost.commands.run.runner.run_remote", run_remote_mock)
        monkeypatch.setattr(
            "bifrost.commands.run.runner.fetch_and_checkout", fetch_checkout_mock
        )

        meta = runner.run(
            setup_name="office-a", command=["pytest"], ref="main", dry_run=True
        )

        assert meta.setup == "office-a"
        assert meta.ref == "main"
        run_remote_mock.assert_not_called()
        fetch_checkout_mock.assert_not_called()
        log_store.copy_logs.assert_not_called()

    def test_handles_ref_with_latest(
        self, runner: Runner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        fetch_checkout_mock = MagicMock()
        monkeypatch.setattr(
            "bifrost.commands.run.runner.fetch_and_checkout", fetch_checkout_mock
        )

        runner.run(setup_name="office-a", command=["pytest"], ref="main", latest=True)

        fetch_checkout_mock.assert_called_once()
        args = fetch_checkout_mock.call_args
        assert args[0][1] == "main"
        assert args[1]["latest"] is True

    def test_raises_on_remote_failure(
        self, runner: Runner, log_store: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        run_remote_mock = MagicMock(
            return_value=subprocess.CompletedProcess(
                args=[], returncode=1, stdout="", stderr="fail"
            )
        )

        monkeypatch.setattr("bifrost.commands.run.runner.run_remote", run_remote_mock)

        with pytest.raises(RemoteCommandError, match="Command failed"):
            runner.run(setup_name="office-a", command=["pytest"])

        log_store.store_run_metadata.assert_called_once()
        log_store.copy_logs.assert_called_once()
