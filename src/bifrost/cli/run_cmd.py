from __future__ import annotations

import subprocess

import typer
from rich.console import Console

from bifrost.cli.app import app
from bifrost.core.config import find_config_file, load_config
from bifrost.core.models import SetupConfig
from bifrost.core.runner import Runner
from bifrost.infra.ci_gate import create_ci_gate
from bifrost.infra.copy import ArtifactCopier
from bifrost.infra.git_remote import fetch_and_checkout
from bifrost.infra.ssh import run_remote

console = Console()


class _RemoteExecutor:
    def run_remote(
        self, setup: SetupConfig, command: list[str], capture: bool = True
    ) -> subprocess.CompletedProcess[str]:
        return run_remote(setup, command, capture=capture)


class _GitOps:
    def fetch_and_checkout(
        self, setup: SetupConfig, ref: str, latest: bool = False
    ) -> None:
        fetch_and_checkout(setup, ref, latest=latest)


@app.command()
def run(
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
    config_path = find_config_file()
    config = load_config(config_path)

    ci_gate = create_ci_gate(config.gitlab)
    copier = ArtifactCopier()

    runner = Runner(
        config=config,
        ci_gate=ci_gate,
        executor=_RemoteExecutor(),
        git_ops=_GitOps(),
        copier=copier,
    )

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
    if metadata.artifact_paths:
        console.print(f"  Artifacts: {len(metadata.artifact_paths)} file(s) copied")
