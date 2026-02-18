"""Add a new setup configuration."""

from __future__ import annotations

import typer
from rich.console import Console

from bifrost.commands.config.command import config_app
from bifrost.di import Container
from bifrost.shared import (
    BifrostConfig,
    ConfigError,
    LogConfig,
    SetupConfig,
)

console = Console()
err_console = Console(stderr=True)


@config_app.command("add")
def add_setup(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Setup name"),
    host: str = typer.Option(..., "--host", help="SSH hostname or IP"),
    user: str = typer.Option(..., "--user", help="SSH username"),
    port: int | None = typer.Option(None, "--port", help="SSH port"),
    runner: str | None = typer.Option(None, "--runner", help="Default command"),
    remote_log_dir: str = typer.Option(
        ".bifrost/logs", "--remote-log-dir", help="Remote log directory"
    ),
    local_log_dir: str | None = typer.Option(
        None, "--local-log-dir", help="Local log directory"
    ),
    pipeline: str | None = typer.Option(
        None, "--pipeline", help="Pipeline configuration name"
    ),
) -> None:
    """Add a new setup configuration."""
    container: Container = ctx.obj
    config_manager = container.get_config_manager()

    try:
        config = container.get_config()
        if name in config.setups:
            err_console.print(
                f"[red]Error:[/red] Setup '{name}' already exists. "
                "Use 'config edit' to modify it."
            )
            raise typer.Exit(code=3)
    except ConfigError:
        config = None

    if pipeline is not None and config is not None and pipeline not in config.pipelines:
        available = list(config.pipelines.keys())
        err_console.print(
            f"[red]Error:[/red] Pipeline '{pipeline}' not found. Available: {available}"
        )
        err_console.print("  Use 'bf pipeline add' to create a pipeline first")
        raise typer.Exit(code=3)

    logs = LogConfig(
        remote_log_dir=remote_log_dir,
        local_log_dir=local_log_dir or f".bifrost/{name}",
    )

    setup = SetupConfig(
        name=name,
        host=host,
        user=user,
        port=port,
        runner=runner,
        logs=logs,
        pipeline=pipeline,
    )

    if config is None:
        config = BifrostConfig(
            setups={name: setup},
            default_setup=None,
            pipelines={},
        )
    else:
        new_setups = {**config.setups, name: setup}

        config = BifrostConfig(
            setups=new_setups,
            default_setup=config.default_setup,
            pipelines=config.pipelines,
        )

    config_manager.write_config(config)
    console.print(f"[green]Setup '{name}' added successfully[/green]")
    if pipeline:
        console.print(f"  Pipeline: {pipeline}")
