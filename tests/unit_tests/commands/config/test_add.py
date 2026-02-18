from pathlib import Path
from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

from bifrost.commands.config import config_app
from bifrost.di import Container
from bifrost.shared import BifrostConfig, ConfigError, SetupConfig

runner = CliRunner()


@pytest.fixture
def mock_container(tmp_path: Path) -> MagicMock:
    container = MagicMock(spec=Container)
    config_manager = MagicMock()
    container.get_config_manager.return_value = config_manager
    container.get_config.side_effect = ConfigError("No config")
    return container


@pytest.fixture
def mock_container_with_config(tmp_path: Path) -> MagicMock:
    container = MagicMock(spec=Container)
    config_manager = MagicMock()
    existing_config = BifrostConfig(
        setups={"existing": SetupConfig(name="existing", host="1.1.1.1", user="test")}
    )
    container.get_config_manager.return_value = config_manager
    container.get_config.return_value = existing_config
    return container


class TestAddSetup:
    def test_adds_new_setup(self, mock_container: MagicMock) -> None:
        result = runner.invoke(
            config_app,
            ["add", "test-rig", "--host", "10.0.0.1", "--user", "ci"],
            obj=mock_container,
        )

        assert result.exit_code == 0
        assert "added successfully" in result.stdout
        mock_container.get_config_manager.return_value.write_config.assert_called_once()

    def test_rejects_duplicate_setup(
        self, mock_container_with_config: MagicMock
    ) -> None:
        result = runner.invoke(
            config_app,
            ["add", "existing", "--host", "10.0.0.1", "--user", "ci"],
            obj=mock_container_with_config,
        )

        assert result.exit_code == 3
        assert "already exists" in result.stderr or "already exists" in str(
            result.output
        )

    def test_adds_setup_with_port(self, mock_container: MagicMock) -> None:
        result = runner.invoke(
            config_app,
            ["add", "test-rig", "--host", "10.0.0.1", "--user", "ci", "--port", "2222"],
            obj=mock_container,
        )

        assert result.exit_code == 0
        assert "added successfully" in result.stdout
        config_manager = mock_container.get_config_manager.return_value
        config_manager.write_config.assert_called_once()
        written_config = config_manager.write_config.call_args[0][0]
        assert written_config.setups["test-rig"].port == 2222
