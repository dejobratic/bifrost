"""Remove a setup configuration."""

from __future__ import annotations

import typer
from rich.console import Console

from bifrost.commands.config.command import config_app
from bifrost.di import Container
from bifrost.shared import BifrostConfig

console = Console()
err_console = Console(stderr=True)


@config_app.command("remove")
def remove_setup(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Setup name to remove"),
) -> None:
    """Remove a setup configuration."""
    container: Container = ctx.obj
    config_manager = container.get_config_manager()
    config = container.get_config()

    if name not in config.setups:
        available = list(config.setups.keys())
        err_console.print(
            f"[red]Error:[/red] Setup '{name}' not found. Available: {available}"
        )
        raise typer.Exit(code=3)

    new_setups = {k: v for k, v in config.setups.items() if k != name}
    new_default = None if config.default_setup == name else config.default_setup

    new_config = BifrostConfig(
        setups=new_setups,
        default_setup=new_default,
    )

    config_manager.write_config(new_config)
    console.print(f"[yellow]Setup '{name}' removed[/yellow]")
    if config.default_setup == name:
        console.print("  [yellow]Default setup was cleared[/yellow]")
