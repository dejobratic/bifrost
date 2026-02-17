"""List all setup configurations."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from bifrost.commands.config.command import config_app
from bifrost.di import Container

console = Console()


@config_app.command("list")
def list_setups(ctx: typer.Context) -> None:
    """List all setup configurations."""
    container: Container = ctx.obj
    config = container.get_config()

    table = Table(title="Configured Setups")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Host", style="yellow")
    table.add_column("User", style="green")
    table.add_column("Runner", style="magenta")
    table.add_column("Default", style="bold")

    for name, setup in config.setups.items():
        is_default = "✓" if name == config.default_setup else ""
        runner_display = setup.runner or "-"
        table.add_row(name, setup.host, setup.user, runner_display, is_default)

    console.print(table)
