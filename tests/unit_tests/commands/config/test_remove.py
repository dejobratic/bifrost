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
        },
        default_setup="office-a",
    )
    container.get_config_manager.return_value = config_manager
    container.get_config.return_value = config
    return container


class TestRemoveSetup:
    def test_removes_setup(self, mock_container: MagicMock) -> None:
        result = runner.invoke(config_app, ["remove", "office-b"], obj=mock_container)

        assert result.exit_code == 0
        assert "removed" in result.stdout
        mock_container.get_config_manager.return_value.write_config.assert_called_once()

    def test_rejects_removing_last_setup(self) -> None:
        container = MagicMock(spec=Container)
        config = BifrostConfig(
            setups={"only-one": SetupConfig(name="only-one", host="1.1.1.1", user="ci")}
        )
        container.get_config.return_value = config

        result = runner.invoke(config_app, ["remove", "only-one"], obj=container)

        assert result.exit_code == 3

    def test_rejects_unknown_setup(self, mock_container: MagicMock) -> None:
        result = runner.invoke(
            config_app, ["remove", "nonexistent"], obj=mock_container
        )

        assert result.exit_code == 3
