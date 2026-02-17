import subprocess
from unittest.mock import patch

import pytest

from bifrost.infra.ssh import check_reachable, run_remote
from bifrost.shared import SetupConfig, SshError


@pytest.fixture
def setup() -> SetupConfig:
    return SetupConfig(name="lab-a", host="10.0.0.5", user="ci")


class TestRunRemote:
    def test_builds_correct_ssh_command(self, setup: SetupConfig) -> None:
        # Arrange
        with patch("bifrost.infra.ssh.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="ok", stderr=""
            )

            # Act
            run_remote(setup, ["pytest", "-m", "smoke"])

            # Assert
            mock_run.assert_called_once_with(
                ["ssh", "-o", "BatchMode=yes", "ci@10.0.0.5", "pytest -m smoke"],
                capture_output=True,
                text=True,
                timeout=600,
            )

    def test_raises_ssh_error_on_timeout(self, setup: SetupConfig) -> None:
        with (
            patch(
                "bifrost.infra.ssh.subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd="ssh", timeout=600),
            ),
            pytest.raises(SshError, match="timed out"),
        ):
            run_remote(setup, ["pytest"])

    def test_raises_ssh_error_on_os_error(self, setup: SetupConfig) -> None:
        with (
            patch("bifrost.infra.ssh.subprocess.run", side_effect=OSError("no ssh")),
            pytest.raises(SshError, match="Failed to execute SSH"),
        ):
            run_remote(setup, ["pytest"])


class TestCheckReachable:
    def test_returns_true_when_ssh_succeeds(self, setup: SetupConfig) -> None:
        # Arrange
        with patch("bifrost.infra.ssh.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="", stderr=""
            )

            # Act
            result = check_reachable(setup)

            # Assert
            assert result is True

    def test_returns_false_when_ssh_fails(self, setup: SetupConfig) -> None:
        # Arrange
        with patch("bifrost.infra.ssh.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=255, stdout="", stderr=""
            )

            # Act
            result = check_reachable(setup)

            # Assert
            assert result is False

    def test_returns_false_on_timeout(self, setup: SetupConfig) -> None:
        # Arrange
        with patch(
            "bifrost.infra.ssh.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="ssh", timeout=5),
        ):
            # Act
            result = check_reachable(setup)

            # Assert
            assert result is False
