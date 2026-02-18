"""Add a pipeline configuration."""

from __future__ import annotations

import typer
from rich.console import Console

from bifrost.commands.pipeline.command import pipeline_app
from bifrost.di import Container
from bifrost.shared import BifrostConfig, PipelineConfig

console = Console()
err_console = Console(stderr=True)


@pipeline_app.command("add")
def add_pipeline(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Pipeline name"),
    url: str = typer.Option(..., "--url", help="GitLab instance URL"),
    project_id: int = typer.Option(..., "--project-id", help="GitLab project ID"),
    token_env: str = typer.Option(
        ..., "--token-env", help="Environment variable name containing GitLab token"
    ),
) -> None:
    """Add a pipeline configuration."""
    container: Container = ctx.obj
    config_manager = container.get_config_manager()

    try:
        config = container.get_config()
        if name in config.pipelines:
            err_console.print(
                f"[red]Error:[/red] Pipeline '{name}' already exists. "
                "Use a different name."
            )
            raise typer.Exit(code=3)
    except Exception:
        config = BifrostConfig(setups={})

    pipeline_config = PipelineConfig(
        url=url, project_id=project_id, token_env=token_env
    )

    new_pipelines = {**config.pipelines, name: pipeline_config}
    new_config = BifrostConfig(
        setups=config.setups,
        default_setup=config.default_setup,
        pipelines=new_pipelines,
    )

    config_manager.write_config(new_config)
    console.print(f"[green]Pipeline '{name}' added successfully[/green]")
    console.print(f"  URL:        {url}")
    console.print(f"  Project ID: {project_id}")
    console.print(f"  Token env:  {token_env}")
