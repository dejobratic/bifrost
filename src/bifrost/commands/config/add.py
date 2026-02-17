"""Add a new setup configuration."""

from __future__ import annotations

import typer
from rich.console import Console

from bifrost.commands.config.command import config_app
from bifrost.di import Container
from bifrost.shared import BifrostConfig, ConfigError, LogConfig, SetupConfig

console = Console()
err_console = Console(stderr=True)


@config_app.command("add")
def add_setup(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Setup name"),
    host: str = typer.Option(..., "--host", help="SSH hostname or IP"),
    user: str = typer.Option(..., "--user", help="SSH username"),
    runner: str | None = typer.Option(None, "--runner", help="Default command"),
    remote_log_dir: str = typer.Option(
        ".bifrost/logs", "--remote-log-dir", help="Remote log directory"
    ),
    local_log_dir: str | None = typer.Option(
        None, "--local-log-dir", help="Local log directory"
    ),
    set_default: bool = typer.Option(
        False, "--set-default", help="Make this the default setup"
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

    logs = LogConfig(
        remote_log_dir=remote_log_dir,
        local_log_dir=local_log_dir or f".bifrost/{name}",
    )

    setup = SetupConfig(
        name=name,
        host=host,
        user=user,
        runner=runner,
        logs=logs,
    )

    if config is None:
        config = BifrostConfig(
            setups={name: setup},
            default_setup=name if set_default else None,
        )
    else:
        new_setups = {**config.setups, name: setup}
        new_default = name if set_default else config.default_setup

        config = BifrostConfig(
            setups=new_setups,
            default_setup=new_default,
            gitlab=config.gitlab,
        )

    config_manager.write_config(config)
    console.print(f"[green]Setup '{name}' added successfully[/green]")
    if set_default:
        console.print("  Set as default setup")
