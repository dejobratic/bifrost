"""Tests for the 'config' subcommands parameter parsing."""

from unittest.mock import MagicMock, patch

import typer
from typer.testing import CliRunner

from bifrost.shared import BifrostConfig, LogConfig, SetupConfig

runner = CliRunner()


@patch("bifrost.cli.app.create_container")
def test_config_add_with_all_parameters(
    mock_create_container: MagicMock, cli_app: typer.Typer
) -> None:
    mock_config_manager = MagicMock()
    mock_container = MagicMock()
    mock_container.get_config_manager.return_value = mock_config_manager
    mock_container.get_config.return_value = BifrostConfig(
        setups={}, default_setup=None
    )
    mock_create_container.return_value = mock_container

    result = runner.invoke(
        cli_app,
        [
            "config",
            "add",
            "new-setup",
            "--host",
            "192.168.1.50",
            "--user",
            "testuser",
            "--runner",
            "make test",
            "--remote-log-dir",
            "/var/logs",
            "--local-log-dir",
            "./logs",
        ],
    )

    assert result.exit_code == 0
    mock_config_manager.write_config.assert_called_once()
    saved_config = mock_config_manager.write_config.call_args[0][0]
    assert "new-setup" in saved_config.setups
    assert saved_config.setups["new-setup"].host == "192.168.1.50"
    assert saved_config.setups["new-setup"].user == "testuser"
    assert saved_config.setups["new-setup"].runner == "make test"
    assert saved_config.setups["new-setup"].logs.remote_log_dir == "/var/logs"
    assert saved_config.setups["new-setup"].logs.local_log_dir == "./logs"
    assert saved_config.default_setup is None


@patch("bifrost.cli.app.create_container")
def test_config_add_with_minimal_parameters(
    mock_create_container: MagicMock, cli_app: typer.Typer
) -> None:
    mock_config_manager = MagicMock()
    mock_container = MagicMock()
    mock_container.get_config_manager.return_value = mock_config_manager
    mock_container.get_config.return_value = BifrostConfig(
        setups={}, default_setup=None
    )
    mock_create_container.return_value = mock_container

    result = runner.invoke(
        cli_app,
        [
            "config",
            "add",
            "minimal-setup",
            "--host",
            "10.0.0.1",
            "--user",
            "root",
        ],
    )

    assert result.exit_code == 0
    mock_config_manager.write_config.assert_called_once()
    saved_config = mock_config_manager.write_config.call_args[0][0]
    assert "minimal-setup" in saved_config.setups
    assert saved_config.setups["minimal-setup"].host == "10.0.0.1"
    assert saved_config.setups["minimal-setup"].user == "root"
    assert saved_config.setups["minimal-setup"].runner is None
    assert saved_config.setups["minimal-setup"].logs.remote_log_dir == ".bifrost/logs"
    assert (
        saved_config.setups["minimal-setup"].logs.local_log_dir
        == ".bifrost/minimal-setup"
    )
    assert saved_config.default_setup is None


@patch("bifrost.cli.app.create_container")
def test_config_edit_with_all_parameters(
    mock_create_container: MagicMock, cli_app: typer.Typer
) -> None:
    existing_setup = SetupConfig(
        name="existing",
        host="old.example.com",
        user="olduser",
        runner="old command",
        logs=LogConfig(remote_log_dir=".old", local_log_dir=".old"),
    )

    mock_config_manager = MagicMock()
    mock_container = MagicMock()
    mock_container.get_config_manager.return_value = mock_config_manager
    mock_container.get_config.return_value = BifrostConfig(
        setups={"existing": existing_setup}, default_setup=None
    )
    mock_create_container.return_value = mock_container

    result = runner.invoke(
        cli_app,
        [
            "config",
            "edit",
            "existing",
            "--host",
            "new.example.com",
            "--user",
            "newuser",
            "--runner",
            "new command",
            "--remote-log-dir",
            "/new/logs",
            "--local-log-dir",
            "./new/logs",
        ],
    )

    assert result.exit_code == 0
    mock_config_manager.write_config.assert_called_once()
    saved_config = mock_config_manager.write_config.call_args[0][0]
    assert saved_config.setups["existing"].host == "new.example.com"
    assert saved_config.setups["existing"].user == "newuser"
    assert saved_config.setups["existing"].runner == "new command"
    assert saved_config.setups["existing"].logs.remote_log_dir == "/new/logs"
    assert saved_config.setups["existing"].logs.local_log_dir == "./new/logs"


@patch("bifrost.cli.app.create_container")
def test_config_edit_with_partial_parameters(
    mock_create_container: MagicMock, cli_app: typer.Typer
) -> None:
    existing_setup = SetupConfig(
        name="existing",
        host="old.example.com",
        user="olduser",
        runner="old command",
        logs=LogConfig(remote_log_dir=".old", local_log_dir=".old"),
    )

    mock_config_manager = MagicMock()
    mock_container = MagicMock()
    mock_container.get_config_manager.return_value = mock_config_manager
    mock_container.get_config.return_value = BifrostConfig(
        setups={"existing": existing_setup}, default_setup=None
    )
    mock_create_container.return_value = mock_container

    result = runner.invoke(
        cli_app,
        [
            "config",
            "edit",
            "existing",
            "--host",
            "updated.example.com",
        ],
    )

    assert result.exit_code == 0
    mock_config_manager.write_config.assert_called_once()
    saved_config = mock_config_manager.write_config.call_args[0][0]
    assert saved_config.setups["existing"].host == "updated.example.com"
    assert saved_config.setups["existing"].user == "olduser"
    assert saved_config.setups["existing"].runner == "old command"


@patch("bifrost.cli.app.create_container")
def test_config_list_displays_all_setups(
    mock_create_container: MagicMock, cli_app: typer.Typer
) -> None:
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

    result = runner.invoke(cli_app, ["config", "list"])

    assert result.exit_code == 0
    assert "prod" in result.stdout
    assert "dev" in result.stdout
    assert "prod.example.com" in result.stdout
    assert "dev.example.com" in result.stdout


@patch("bifrost.cli.app.create_container")
def test_config_remove_removes_setup(
    mock_create_container: MagicMock, cli_app: typer.Typer
) -> None:
    setups = {
        "prod": SetupConfig(
            name="prod",
            host="prod.example.com",
            user="admin",
            runner=None,
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

    mock_config_manager = MagicMock()
    mock_container = MagicMock()
    mock_container.get_config_manager.return_value = mock_config_manager
    mock_container.get_config.return_value = BifrostConfig(
        setups=setups, default_setup="prod"
    )
    mock_create_container.return_value = mock_container

    result = runner.invoke(cli_app, ["config", "remove", "dev"])

    assert result.exit_code == 0
    mock_config_manager.write_config.assert_called_once()
    saved_config = mock_config_manager.write_config.call_args[0][0]
    assert "dev" not in saved_config.setups
    assert "prod" in saved_config.setups
    assert saved_config.default_setup == "prod"


@patch("bifrost.cli.app.create_container")
def test_config_set_default_updates_default_setup(
    mock_create_container: MagicMock, cli_app: typer.Typer
) -> None:
    setups = {
        "prod": SetupConfig(
            name="prod",
            host="prod.example.com",
            user="admin",
            runner=None,
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

    mock_config_manager = MagicMock()
    mock_container = MagicMock()
    mock_container.get_config_manager.return_value = mock_config_manager
    mock_container.get_config.return_value = BifrostConfig(
        setups=setups, default_setup="prod"
    )
    mock_create_container.return_value = mock_container

    result = runner.invoke(cli_app, ["config", "set-default", "dev"])

    assert result.exit_code == 0
    mock_config_manager.write_config.assert_called_once()
    saved_config = mock_config_manager.write_config.call_args[0][0]
    assert saved_config.default_setup == "dev"
