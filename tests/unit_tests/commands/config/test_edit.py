from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

from bifrost.commands.config import config_app
from bifrost.di import Container
from bifrost.shared import BifrostConfig, SetupConfig

runner = CliRunner()


@pytest.fixture
def mock_container() -> MagicMock:
    container = MagicMock(spec=Container)
    config_manager = MagicMock()
    config = BifrostConfig(
        setups={
            "test-rig": SetupConfig(
                name="test-rig", host="10.0.0.1", user="ci", runner="pytest"
            )
        }
    )
    container.get_config_manager.return_value = config_manager
    container.get_config.return_value = config
    return container


class TestEditSetup:
    def test_edits_existing_setup(self, mock_container: MagicMock) -> None:
        result = runner.invoke(
            config_app,
            ["edit", "test-rig", "--host", "10.0.0.2"],
            obj=mock_container,
        )

        assert result.exit_code == 0
        assert "updated successfully" in result.stdout
        mock_container.get_config_manager.return_value.write_config.assert_called_once()

    def test_rejects_unknown_setup(self, mock_container: MagicMock) -> None:
        result = runner.invoke(
            config_app,
            ["edit", "nonexistent", "--host", "10.0.0.2"],
            obj=mock_container,
        )

        assert result.exit_code == 3

    def test_edits_port(self, mock_container: MagicMock) -> None:
        result = runner.invoke(
            config_app,
            ["edit", "test-rig", "--port", "2222"],
            obj=mock_container,
        )

        assert result.exit_code == 0
        assert "updated successfully" in result.stdout
        config_manager = mock_container.get_config_manager.return_value
        config_manager.write_config.assert_called_once()
        written_config = config_manager.write_config.call_args[0][0]
        assert written_config.setups["test-rig"].port == 2222
