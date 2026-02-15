from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

import yaml
from typer.testing import CliRunner

from bifrost.cli.app import app

runner = CliRunner()


def _read_written_config(tmp_path: Path) -> dict[str, Any]:
    target = tmp_path / "config.yml"
    result: dict[str, Any] = yaml.safe_load(target.read_text())
    return result


class TestNewConfigFlow:
    def test_creates_config_with_single_setup(self, tmp_path: Path) -> None:
        target = tmp_path / "config.yml"
        user_input = "\n".join(
            [
                "mylab",  # setup name
                "10.0.0.1",  # host
                "ci",  # user
                "",  # runner (empty)
                "n",  # customize artifacts? no
                "n",  # add another? no
                "n",  # gitlab? no
            ]
        )

        with (
            patch("bifrost.core.configure.USER_CONFIG_DIR", target),
            patch("bifrost.cli.configure_cmd.load_existing_config", return_value=None),
        ):
            result = runner.invoke(app, ["configure"], input=user_input)

        assert result.exit_code == 0, result.output
        data = _read_written_config(tmp_path)
        assert "mylab" in data["setups"]
        assert data["setups"]["mylab"]["host"] == "10.0.0.1"


class TestExistingConfigAddSetup:
    def test_adds_setup_to_existing(self, tmp_path: Path) -> None:
        from bifrost.core.models import BifrostConfig, SetupConfig

        existing = BifrostConfig(
            setups={"old": SetupConfig(name="old", host="1.1.1.1", user="u")}
        )
        target = tmp_path / "config.yml"

        user_input = "\n".join(
            [
                "add",  # action
                "newbox",  # setup name
                "2.2.2.2",  # host
                "admin",  # user
                "",  # runner (empty)
                "n",  # customize artifacts? no
                "done",  # action
            ]
        )

        with (
            patch("bifrost.core.configure.USER_CONFIG_DIR", target),
            patch(
                "bifrost.cli.configure_cmd.load_existing_config", return_value=existing
            ),
        ):
            result = runner.invoke(app, ["configure"], input=user_input)

        assert result.exit_code == 0, result.output
        data = _read_written_config(tmp_path)
        assert "old" in data["setups"]
        assert "newbox" in data["setups"]
        assert data["setups"]["newbox"]["host"] == "2.2.2.2"
