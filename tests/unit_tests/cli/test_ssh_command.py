"""Tests for the 'ssh' command parameter parsing."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from bifrost.cli.app import app
from bifrost.shared import BifrostConfig, LogConfig, SetupConfig

runner = CliRunner()


@patch("bifrost.commands.ssh.command.open_interactive_session")
@patch("bifrost.cli.app.create_container")
def test_ssh_with_long_option(
    mock_create_container: MagicMock, mock_open_session: MagicMock
) -> None:
    setup_config = SetupConfig(
        name="prod",
        host="192.168.1.100",
        user="admin",
        runner=None,
        logs=LogConfig(remote_log_dir=".logs", local_log_dir=".logs"),
    )

    mock_container = MagicMock()
    mock_container.get_config.return_value = BifrostConfig(
        setups={"prod": setup_config}, default_setup=None
    )
    mock_create_container.return_value = mock_container
    mock_open_session.return_value = 0

    result = runner.invoke(app, ["ssh", "--setup", "prod"])

    assert result.exit_code == 0
    mock_open_session.assert_called_once_with(setup_config)


@patch("bifrost.commands.ssh.command.open_interactive_session")
@patch("bifrost.cli.app.create_container")
def test_ssh_with_short_option(
    mock_create_container: MagicMock, mock_open_session: MagicMock
) -> None:
    setup_config = SetupConfig(
        name="dev",
        host="localhost",
        user="developer",
        runner=None,
        logs=LogConfig(remote_log_dir=".logs", local_log_dir=".logs"),
    )

    mock_container = MagicMock()
    mock_container.get_config.return_value = BifrostConfig(
        setups={"dev": setup_config}, default_setup=None
    )
    mock_create_container.return_value = mock_container
    mock_open_session.return_value = 0

    result = runner.invoke(app, ["ssh", "-s", "dev"])

    assert result.exit_code == 0
    mock_open_session.assert_called_once_with(setup_config)


@patch("bifrost.commands.ssh.command.open_interactive_session")
@patch("bifrost.cli.app.create_container")
def test_ssh_uses_default_setup_when_no_option(
    mock_create_container: MagicMock, mock_open_session: MagicMock
) -> None:
    setup_config = SetupConfig(
        name="default-setup",
        host="default.local",
        user="user",
        runner=None,
        logs=LogConfig(remote_log_dir=".logs", local_log_dir=".logs"),
    )

    mock_container = MagicMock()
    mock_container.get_config.return_value = BifrostConfig(
        setups={"default-setup": setup_config}, default_setup="default-setup"
    )
    mock_create_container.return_value = mock_container
    mock_open_session.return_value = 0

    result = runner.invoke(app, ["ssh"])

    assert result.exit_code == 0
    mock_open_session.assert_called_once_with(setup_config)
