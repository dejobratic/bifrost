from __future__ import annotations

import typer
from rich.console import Console

from bifrost.cli.app import app
from bifrost.commands.run.runner import Runner
from bifrost.di import Container

console = Console()


@app.command()
def run(
    ctx: typer.Context,
    setup: str | None = typer.Option(None, "--setup", "-s", help="Target setup name"),
    ref: str | None = typer.Option(
        None, "--ref", "-r", help="Git ref (branch/tag/commit) to checkout"
    ),
    latest: bool = typer.Option(
        False, "--latest", "-l", help="Fetch latest changes before running"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Skip CI gate check"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be done without executing"
    ),
    command: list[str] | None = typer.Argument(  # noqa: B008
        None, help="Command to run remotely (after --)"
    ),
) -> None:
    """Run a command on a remote setup."""
    runner = _create_runner(ctx)

    metadata = runner.run(
        setup_name=setup,
        command=command or None,
        ref=ref,
        latest=latest,
        force=force,
        dry_run=dry_run,
    )

    if dry_run:
        console.print("[bold]Dry run[/bold] — no commands executed")
        console.print(f"  Setup:   {metadata.setup}")
        console.print(f"  Ref:     {metadata.ref or '(current)'}")
        console.print(f"  Command: {' '.join(metadata.command)}")
        return

    console.print(
        f"[green]Run completed[/green] on {metadata.setup} (run: {metadata.run_id})"
    )
    if metadata.log_paths:
        console.print(f"  Logs: {len(metadata.log_paths)} file(s) copied")


def _create_runner(ctx: typer.Context) -> Runner:
    container: Container = ctx.obj
    config = container.get_config()
    log_store = container.get_log_store()
    runner = Runner(config=config, log_store=log_store)
    return runner
