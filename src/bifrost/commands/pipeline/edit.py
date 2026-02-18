"""Edit an existing pipeline configuration."""

from __future__ import annotations

import typer
from rich.console import Console

from bifrost.commands.pipeline.command import pipeline_app
from bifrost.di import Container
from bifrost.shared import BifrostConfig, PipelineConfig

console = Console()
err_console = Console(stderr=True)


@pipeline_app.command("edit")
def edit_pipeline(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Pipeline name to edit"),
    url: str | None = typer.Option(None, "--url", help="New GitLab instance URL"),
    project_id: int | None = typer.Option(
        None, "--project-id", help="New GitLab project ID"
    ),
    token_env: str | None = typer.Option(
        None,
        "--token-env",
        help="New environment variable name containing GitLab token",
    ),
) -> None:
    """Edit an existing pipeline configuration."""
    container: Container = ctx.obj
    config_manager = container.get_config_manager()
    config = container.get_config()

    raise_if(name, config)

    pipeline = config.pipelines[name]

    new_pipeline = PipelineConfig(
        url=url or pipeline.url,
        project_id=project_id if project_id is not None else pipeline.project_id,
        token_env=token_env or pipeline.token_env,
    )

    new_pipelines = {**config.pipelines, name: new_pipeline}
    new_config = BifrostConfig(
        setups=config.setups,
        default_setup=config.default_setup,
        pipelines=new_pipelines,
    )

    config_manager.write_config(new_config)
    console.print(f"[green]Pipeline '{name}' updated successfully[/green]")


def raise_if(name: str, config: BifrostConfig) -> None:
    if name not in config.pipelines:
        available = list(config.pipelines.keys())
        err_console.print(
            f"[red]Error:[/red] Pipeline '{name}' not found. Available: {available}"
        )
        raise typer.Exit(code=3)
