from __future__ import annotations

import typer
from rich.console import Console

from bifrost.cli.app import app
from bifrost.core.config import find_config_file, load_config
from bifrost.core.errors import ConfigError
from bifrost.infra.ssh import open_interactive_session

console = Console()


@app.command()
def ssh(
    setup: str | None = typer.Option(None, "--setup", "-s", help="Setup to connect to"),
) -> None:
    """Open an interactive SSH session to a setup."""
    config_path = find_config_file()
    config = load_config(config_path)

    setup_name = setup or config.default_setup
    if not setup_name:
        raise ConfigError("No setup specified and no default configured")

    if setup_name not in config.setups:
        raise ConfigError(f"Setup '{setup_name}' not found")

    setup_config = config.setups[setup_name]
    target = f"{setup_config.user}@{setup_config.host}"
    console.print(f"Connecting to [bold]{setup_name}[/bold] ({target})...")

    exit_code = open_interactive_session(setup_config)
    raise typer.Exit(code=exit_code)
