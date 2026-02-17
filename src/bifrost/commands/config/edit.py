"""Edit an existing setup configuration."""

from __future__ import annotations

import typer
from rich.console import Console

from bifrost.commands.config.command import config_app
from bifrost.di import Container
from bifrost.shared import BifrostConfig, LogConfig, SetupConfig

console = Console()
err_console = Console(stderr=True)


@config_app.command("edit")
def edit_setup(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Setup name to edit"),
    host: str | None = typer.Option(None, "--host", help="New SSH hostname or IP"),
    user: str | None = typer.Option(None, "--user", help="New SSH username"),
    runner: str | None = typer.Option(None, "--runner", help="New default command"),
    remote_log_dir: str | None = typer.Option(
        None, "--remote-log-dir", help="New remote log directory"
    ),
    local_log_dir: str | None = typer.Option(
        None, "--local-log-dir", help="New local log directory"
    ),
) -> None:
    """Edit an existing setup configuration."""
    container: Container = ctx.obj
    config_manager = container.get_config_manager()
    config = container.get_config()

    raise_if(name, config)

    setup = config.setups[name]

    new_logs = LogConfig(
        remote_log_dir=remote_log_dir or setup.logs.remote_log_dir,
        local_log_dir=local_log_dir or setup.logs.local_log_dir,
    )

    new_setup = SetupConfig(
        name=name,
        host=host or setup.host,
        user=user or setup.user,
        runner=runner if runner is not None else setup.runner,
        logs=new_logs,
    )

    new_setups = {**config.setups, name: new_setup}
    new_config = BifrostConfig(
        setups=new_setups,
        default_setup=config.default_setup,
        gitlab=config.gitlab,
    )

    config_manager.write_config(new_config)
    console.print(f"[green]Setup '{name}' updated successfully[/green]")


def raise_if(name: str, config: BifrostConfig) -> None:
    if name not in config.setups:
        available = list(config.setups.keys())
        err_console.print(
            f"[red]Error:[/red] Setup '{name}' not found. Available: {available}"
        )
        raise typer.Exit(code=3)
