from collections.abc import Callable
from pathlib import Path

import pytest
import typer


@pytest.fixture
def tmp_config(tmp_path: Path) -> Callable[[str], Path]:
    def _write(content: str) -> Path:
        config_file = tmp_path / ".bifrost.yml"
        config_file.write_text(content)
        return config_file

    return _write


@pytest.fixture
def cli_app() -> typer.Typer:
    """Return a properly initialized CLI app with all commands registered."""
    import bifrost.commands.run.command
    import bifrost.commands.ssh.command
    import bifrost.commands.status.command  # noqa: F401
    from bifrost.cli.app import app
    from bifrost.commands.config import config_app

    app.add_typer(config_app)
    return app
