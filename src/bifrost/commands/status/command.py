from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from bifrost.cli.app import app
from bifrost.di import Container
from bifrost.infra.ssh import check_reachable

console = Console()


@app.command()
def status(
    ctx: typer.Context,
    setup: str | None = typer.Option(
        None, "--setup", "-s", help="Check a specific setup"
    ),
) -> None:
    """Show CI pipeline state and setup reachability."""
    container: Container = ctx.obj
    config = container.get_config()
    pipeline_gate = container.get_pipeline_gate()

    setups_to_check = {setup: config.setups[setup]} if setup else config.setups

    table = Table(title="Setup Status")
    table.add_column("Setup", style="bold")
    table.add_column("Host")
    table.add_column("Reachable")
    table.add_column("CI Busy")

    for name, setup_config in setups_to_check.items():
        reachable = check_reachable(setup_config)
        try:
            busy = pipeline_gate.is_busy(name)
        except Exception:
            busy = None

        table.add_row(
            name,
            f"{setup_config.user}@{setup_config.host}",
            "[green]yes[/green]" if reachable else "[red]no[/red]",
            "[yellow]yes[/yellow]"
            if busy
            else "[green]no[/green]"
            if busy is not None
            else "[dim]n/a[/dim]",
        )

    console.print(table)


@app.command()
def setups(ctx: typer.Context) -> None:
    """List all configured setups."""
    container: Container = ctx.obj
    config = container.get_config()

    table = Table(title="Configured Setups")
    table.add_column("Setup", style="bold")
    table.add_column("Host")
    table.add_column("User")
    table.add_column("Runner")
    table.add_column("Default", justify="center")

    for name, setup_config in config.setups.items():
        is_default = name == config.default_setup
        table.add_row(
            name,
            setup_config.host,
            setup_config.user,
            setup_config.runner or "[dim]-[/dim]",
            "[green]✓[/green]" if is_default else "",
        )

    console.print(table)
