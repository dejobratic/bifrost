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
            "office-a": SetupConfig(name="office-a", host="10.0.0.1", user="ci"),
            "office-b": SetupConfig(name="office-b", host="10.1.0.1", user="admin"),
        }
    )
    container.get_config_manager.return_value = config_manager
    container.get_config.return_value = config
    return container


class TestSetDefault:
    def test_sets_default_setup(self, mock_container: MagicMock) -> None:
        result = runner.invoke(
            config_app, ["set-default", "office-b"], obj=mock_container
        )

        assert result.exit_code == 0
        assert "Default setup set" in result.stdout
        mock_container.get_config_manager.return_value.write_config.assert_called_once()

    def test_rejects_unknown_setup(self, mock_container: MagicMock) -> None:
        result = runner.invoke(
            config_app, ["set-default", "nonexistent"], obj=mock_container
        )

        assert result.exit_code == 3
