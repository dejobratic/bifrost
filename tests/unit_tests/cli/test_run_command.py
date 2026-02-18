"""Tests for the 'run' command parameter parsing."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from bifrost.cli.app import app
from bifrost.shared import BifrostConfig

runner = CliRunner()


@patch("bifrost.cli.app.create_container")
def test_run_with_all_long_options(mock_create_container: MagicMock) -> None:
    mock_runner = MagicMock()
    mock_runner.run.return_value = MagicMock(
        setup="test-setup",
        ref="main",
        command=["pytest"],
        run_id="123",
        log_paths=[],
    )

    mock_container = MagicMock()
    mock_container.get_config.return_value = BifrostConfig(
        setups={}, default_setup=None
    )
    mock_container.get_pipeline_gate.return_value = MagicMock()
    mock_container.get_log_store.return_value = MagicMock()
    mock_create_container.return_value = mock_container

    with patch("bifrost.commands.run.command.Runner", return_value=mock_runner):
        result = runner.invoke(
            app,
            [
                "run",
                "--setup",
                "test-setup",
                "--ref",
                "main",
                "--latest",
                "--force",
                "--",
                "pytest",
            ],
        )

    assert result.exit_code == 0
    mock_runner.run.assert_called_once_with(
        setup_name="test-setup",
        command=["pytest"],
        ref="main",
        latest=True,
        force=True,
        dry_run=False,
    )


@patch("bifrost.cli.app.create_container")
def test_run_with_all_short_options(mock_create_container: MagicMock) -> None:
    mock_runner = MagicMock()
    mock_runner.run.return_value = MagicMock(
        setup="prod",
        ref="v1.0",
        command=["make", "test"],
        run_id="456",
        log_paths=[],
    )

    mock_container = MagicMock()
    mock_container.get_config.return_value = BifrostConfig(
        setups={}, default_setup=None
    )
    mock_container.get_pipeline_gate.return_value = MagicMock()
    mock_container.get_log_store.return_value = MagicMock()
    mock_create_container.return_value = mock_container

    with patch("bifrost.commands.run.command.Runner", return_value=mock_runner):
        result = runner.invoke(
            app,
            ["run", "-s", "prod", "-r", "v1.0", "-l", "-f", "--", "make", "test"],
        )

    assert result.exit_code == 0
    mock_runner.run.assert_called_once_with(
        setup_name="prod",
        command=["make", "test"],
        ref="v1.0",
        latest=True,
        force=True,
        dry_run=False,
    )


@patch("bifrost.cli.app.create_container")
def test_run_with_dry_run_flag(mock_create_container: MagicMock) -> None:
    mock_runner = MagicMock()
    mock_runner.run.return_value = MagicMock(
        setup="staging",
        ref=None,
        command=["npm", "test"],
        run_id="789",
        log_paths=[],
    )

    mock_container = MagicMock()
    mock_container.get_config.return_value = BifrostConfig(
        setups={}, default_setup=None
    )
    mock_container.get_pipeline_gate.return_value = MagicMock()
    mock_container.get_log_store.return_value = MagicMock()
    mock_create_container.return_value = mock_container

    with patch("bifrost.commands.run.command.Runner", return_value=mock_runner):
        result = runner.invoke(
            app,
            ["run", "--setup", "staging", "--dry-run", "--", "npm", "test"],
        )

    assert result.exit_code == 0
    mock_runner.run.assert_called_once_with(
        setup_name="staging",
        command=["npm", "test"],
        ref=None,
        latest=False,
        force=False,
        dry_run=True,
    )
    assert "Dry run" in result.stdout


@patch("bifrost.cli.app.create_container")
def test_run_without_optional_parameters(mock_create_container: MagicMock) -> None:
    mock_runner = MagicMock()
    mock_runner.run.return_value = MagicMock(
        setup="default",
        ref=None,
        command=None,
        run_id="111",
        log_paths=[],
    )

    mock_container = MagicMock()
    mock_container.get_config.return_value = BifrostConfig(
        setups={}, default_setup=None
    )
    mock_container.get_pipeline_gate.return_value = MagicMock()
    mock_container.get_log_store.return_value = MagicMock()
    mock_create_container.return_value = mock_container

    with patch("bifrost.commands.run.command.Runner", return_value=mock_runner):
        result = runner.invoke(app, ["run"])

    assert result.exit_code == 0
    mock_runner.run.assert_called_once_with(
        setup_name=None,
        command=None,
        ref=None,
        latest=False,
        force=False,
        dry_run=False,
    )


@patch("bifrost.cli.app.create_container")
def test_run_with_multi_word_command(mock_create_container: MagicMock) -> None:
    mock_runner = MagicMock()
    mock_runner.run.return_value = MagicMock(
        setup="test",
        ref=None,
        command=["docker", "run", "--rm", "test-image"],
        run_id="999",
        log_paths=[],
    )

    mock_container = MagicMock()
    mock_container.get_config.return_value = BifrostConfig(
        setups={}, default_setup=None
    )
    mock_container.get_pipeline_gate.return_value = MagicMock()
    mock_container.get_log_store.return_value = MagicMock()
    mock_create_container.return_value = mock_container

    with patch("bifrost.commands.run.command.Runner", return_value=mock_runner):
        result = runner.invoke(
            app,
            ["run", "-s", "test", "--", "docker", "run", "--rm", "test-image"],
        )

    assert result.exit_code == 0
    mock_runner.run.assert_called_once_with(
        setup_name="test",
        command=["docker", "run", "--rm", "test-image"],
        ref=None,
        latest=False,
        force=False,
        dry_run=False,
    )
