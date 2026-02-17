from unittest.mock import MagicMock

from typer.testing import CliRunner

from bifrost.commands.config import config_app
from bifrost.di import Container
from bifrost.shared import BifrostConfig, SetupConfig

runner = CliRunner()


def test_lists_all_setups() -> None:
    container = MagicMock(spec=Container)
    config = BifrostConfig(
        setups={
            "office-a": SetupConfig(
                name="office-a", host="10.0.0.1", user="ci", runner="pytest"
            ),
            "office-b": SetupConfig(name="office-b", host="10.1.0.1", user="admin"),
        },
        default_setup="office-a",
    )
    container.get_config.return_value = config

    result = runner.invoke(config_app, ["list"], obj=container)

    assert result.exit_code == 0
    assert "office-a" in result.stdout
    assert "office-b" in result.stdout
    assert "10.0.0.1" in result.stdout
    assert "pytest" in result.stdout
