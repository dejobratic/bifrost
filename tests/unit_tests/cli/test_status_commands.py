"""Tests for the 'status' and 'setups' commands parameter parsing."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from bifrost.cli.app import app
from bifrost.shared import BifrostConfig, LogConfig, SetupConfig

runner = CliRunner()


@patch("bifrost.commands.status.command.create_pipeline_gate")
@patch("bifrost.commands.status.command.check_reachable")
@patch("bifrost.cli.app.create_container")
def test_status_with_specific_setup_long_option(
    mock_create_container: MagicMock,
    mock_check_reachable: MagicMock,
    mock_create_pipeline_gate: MagicMock,
) -> None:
    setup_config = SetupConfig(
        name="prod",
        host="prod.example.com",
        user="admin",
        runner=None,
        logs=LogConfig(remote_log_dir=".logs", local_log_dir=".logs"),
    )

    mock_container = MagicMock()
    mock_container.get_config.return_value = BifrostConfig(
        setups={"prod": setup_config}, default_setup=None
    )
    mock_create_container.return_value = mock_container
    mock_check_reachable.return_value = True

    mock_pipeline_gate = MagicMock()
    mock_pipeline_gate.is_busy.return_value = False
    mock_create_pipeline_gate.return_value = mock_pipeline_gate

    result = runner.invoke(app, ["status", "--setup", "prod"])

    assert result.exit_code == 0
    mock_check_reachable.assert_called_once_with(setup_config)
    mock_pipeline_gate.is_busy.assert_called_once_with("prod")


@patch("bifrost.commands.status.command.create_pipeline_gate")
@patch("bifrost.commands.status.command.check_reachable")
@patch("bifrost.cli.app.create_container")
def test_status_with_specific_setup_short_option(
    mock_create_container: MagicMock,
    mock_check_reachable: MagicMock,
    mock_create_pipeline_gate: MagicMock,
) -> None:
    setup_config = SetupConfig(
        name="staging",
        host="staging.example.com",
        user="deployer",
        runner=None,
        logs=LogConfig(remote_log_dir=".logs", local_log_dir=".logs"),
    )

    mock_container = MagicMock()
    mock_container.get_config.return_value = BifrostConfig(
        setups={"staging": setup_config}, default_setup=None
    )
    mock_create_container.return_value = mock_container
    mock_check_reachable.return_value = False

    mock_pipeline_gate = MagicMock()
    mock_pipeline_gate.is_busy.return_value = True
    mock_create_pipeline_gate.return_value = mock_pipeline_gate

    result = runner.invoke(app, ["status", "-s", "staging"])

    assert result.exit_code == 0
    mock_check_reachable.assert_called_once_with(setup_config)
    mock_pipeline_gate.is_busy.assert_called_once_with("staging")


@patch("bifrost.commands.status.command.create_pipeline_gate")
@patch("bifrost.commands.status.command.check_reachable")
@patch("bifrost.cli.app.create_container")
def test_status_without_setup_checks_all_setups(
    mock_create_container: MagicMock,
    mock_check_reachable: MagicMock,
    mock_create_pipeline_gate: MagicMock,
) -> None:
    setups = {
        "prod": SetupConfig(
            name="prod",
            host="prod.local",
            user="admin",
            runner=None,
            logs=LogConfig(remote_log_dir=".logs", local_log_dir=".logs"),
        ),
        "dev": SetupConfig(
            name="dev",
            host="dev.local",
            user="developer",
            runner=None,
            logs=LogConfig(remote_log_dir=".logs", local_log_dir=".logs"),
        ),
    }

    mock_container = MagicMock()
    mock_container.get_config.return_value = BifrostConfig(
        setups=setups, default_setup=None
    )
    mock_create_container.return_value = mock_container
    mock_check_reachable.return_value = True

    mock_pipeline_gate = MagicMock()
    mock_pipeline_gate.is_busy.return_value = False
    mock_create_pipeline_gate.return_value = mock_pipeline_gate

    result = runner.invoke(app, ["status"])

    assert result.exit_code == 0
    assert mock_check_reachable.call_count == 2
    assert mock_pipeline_gate.is_busy.call_count == 2


@patch("bifrost.cli.app.create_container")
def test_setups_lists_all_configured_setups(mock_create_container: MagicMock) -> None:
    setups = {
        "prod": SetupConfig(
            name="prod",
            host="prod.example.com",
            user="admin",
            runner="pytest",
            logs=LogConfig(remote_log_dir=".logs", local_log_dir=".logs"),
        ),
        "dev": SetupConfig(
            name="dev",
            host="dev.example.com",
            user="developer",
            runner=None,
            logs=LogConfig(remote_log_dir=".logs", local_log_dir=".logs"),
        ),
    }

    mock_container = MagicMock()
    mock_container.get_config.return_value = BifrostConfig(
        setups=setups, default_setup="prod"
    )
    mock_create_container.return_value = mock_container

    result = runner.invoke(app, ["setups"])

    assert result.exit_code == 0
    assert "prod" in result.stdout
    assert "dev" in result.stdout
    assert "prod.example.com" in result.stdout
    assert "dev.example.com" in result.stdout
