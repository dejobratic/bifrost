"""List all pipeline configurations."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from bifrost.commands.pipeline.command import pipeline_app
from bifrost.di import Container

console = Console()


@pipeline_app.command("list")
def list_pipelines(ctx: typer.Context) -> None:
    """List all pipeline configurations."""
    container: Container = ctx.obj
    config = container.get_config()

    if not config.pipelines:
        console.print("[yellow]No pipelines configured[/yellow]")
        console.print("  Use 'bf pipeline add' to add a pipeline configuration")
        return

    table = Table(title="Pipeline Configurations")
    table.add_column("Name", style="bold")
    table.add_column("URL")
    table.add_column("Project ID")
    table.add_column("Token Env")
    table.add_column("Used By", style="dim")

    used_by: dict[str, list[str]] = {}
    for setup_name, setup in config.setups.items():
        if setup.pipeline:
            if setup.pipeline not in used_by:
                used_by[setup.pipeline] = []
            used_by[setup.pipeline].append(setup_name)

    for name, pipeline in config.pipelines.items():
        setups = used_by.get(name, [])
        table.add_row(
            name,
            pipeline.url,
            str(pipeline.project_id),
            pipeline.token_env,
            ", ".join(setups) if setups else "-",
        )

    console.print(table)
