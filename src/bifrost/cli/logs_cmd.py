from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

from bifrost.cli.app import app
from bifrost.core.config import find_config_file, load_config
from bifrost.core.errors import ConfigError

console = Console()


@app.command()
def logs(
    run_id: str = typer.Argument(
        "last", help="Run ID or 'last' for the most recent run"
    ),
    setup: str | None = typer.Option(
        None, "--setup", "-s", help="Setup to look for logs"
    ),
) -> None:
    """Show or fetch run logs."""
    config_path = find_config_file()
    config = load_config(config_path)

    setup_name = setup or config.default_setup
    if not setup_name:
        raise ConfigError("No setup specified and no default configured")

    if setup_name not in config.setups:
        raise ConfigError(f"Setup '{setup_name}' not found")

    setup_config = config.setups[setup_name]
    local_base = Path(setup_config.artifacts.local_dir)

    if run_id == "last":
        run_dir = _find_latest_run(local_base)
    else:
        run_dir = local_base / run_id
        if not run_dir.exists():
            raise ConfigError(f"Run '{run_id}' not found in {local_base}")

    _display_run(run_dir)


def _find_latest_run(base_dir: Path) -> Path:
    if not base_dir.exists():
        raise ConfigError(f"No runs found in {base_dir}")

    run_dirs = sorted(
        [d for d in base_dir.iterdir() if d.is_dir()],
        key=lambda d: d.stat().st_mtime,
        reverse=True,
    )
    if not run_dirs:
        raise ConfigError(f"No runs found in {base_dir}")
    return run_dirs[0]


def _display_run(run_dir: Path) -> None:
    metadata_file = run_dir / "run.json"
    if metadata_file.exists():
        metadata = json.loads(metadata_file.read_text())
        console.print(f"[bold]Run:[/bold] {metadata.get('run_id', run_dir.name)}")
        console.print(f"  Setup:     {metadata.get('setup')}")
        console.print(f"  Command:   {' '.join(metadata.get('command', []))}")
        console.print(f"  Ref:       {metadata.get('ref', 'n/a')}")
        console.print(f"  Exit code: {metadata.get('exit_code')}")
        console.print(f"  Timestamp: {metadata.get('timestamp')}")
    else:
        console.print(f"[bold]Run:[/bold] {run_dir.name}")

    log_file = run_dir / "run.log"
    if log_file.exists():
        console.print("\n[bold]Log output:[/bold]")
        console.print(log_file.read_text())

    files = [
        p
        for p in run_dir.rglob("*")
        if p.is_file() and p.name not in ("run.json", "run.log")
    ]
    if files:
        console.print(f"\n[bold]Artifacts:[/bold] {len(files)} file(s)")
        for f in files:
            console.print(f"  {f.relative_to(run_dir)}")
