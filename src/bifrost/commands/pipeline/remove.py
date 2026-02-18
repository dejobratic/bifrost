"""Remove a pipeline configuration."""

from __future__ import annotations

import typer
from rich.console import Console

from bifrost.commands.pipeline.command import pipeline_app
from bifrost.di import Container
from bifrost.shared import BifrostConfig

console = Console()
err_console = Console(stderr=True)


@pipeline_app.command("remove")
def remove_pipeline(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Pipeline name to remove"),
) -> None:
    """Remove a pipeline configuration."""
    container: Container = ctx.obj
    config_manager = container.get_config_manager()
    config = container.get_config()

    if name not in config.pipelines:
        available = list(config.pipelines.keys())
        err_console.print(
            f"[red]Error:[/red] Pipeline '{name}' not found. Available: {available}"
        )
        raise typer.Exit(code=3)

    used_by = [
        setup_name
        for setup_name, setup in config.setups.items()
        if setup.pipeline == name
    ]
    if used_by:
        err_console.print(
            f"[red]Error:[/red] Pipeline '{name}' is used by setups: {used_by}"
        )
        err_console.print("  Remove pipeline references from setups first")
        raise typer.Exit(code=3)

    new_pipelines = {k: v for k, v in config.pipelines.items() if k != name}
    new_config = BifrostConfig(
        setups=config.setups,
        default_setup=config.default_setup,
        pipelines=new_pipelines,
    )

    config_manager.write_config(new_config)
    console.print(f"[green]Pipeline '{name}' removed successfully[/green]")
