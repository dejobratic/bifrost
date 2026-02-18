"""Set the default setup."""

from __future__ import annotations

import typer
from rich.console import Console

from bifrost.commands.config.command import config_app
from bifrost.di import Container
from bifrost.shared import BifrostConfig

console = Console()
err_console = Console(stderr=True)


@config_app.command("set-default")
def set_default_setup(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Setup name to set as default"),
) -> None:
    """Set the default setup."""
    container: Container = ctx.obj
    config_manager = container.get_config_manager()
    config = container.get_config()

    if name not in config.setups:
        available = list(config.setups.keys())
        err_console.print(
            f"[red]Error:[/red] Setup '{name}' not found. Available: {available}"
        )
        raise typer.Exit(code=3)

    new_config = BifrostConfig(
        setups=config.setups,
        default_setup=name,
    )

    config_manager.write_config(new_config)
    console.print(f"[green]Default setup set to '{name}'[/green]")
