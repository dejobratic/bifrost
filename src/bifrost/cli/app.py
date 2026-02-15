import typer

from bifrost.core.errors import BifrostError

app = typer.Typer(
    name="bf",
    help="Bifrost — bridge between local dev and remote test setups.",
    no_args_is_help=True,
)


@app.callback()
def _callback() -> None:
    pass


def main() -> None:
    import bifrost.cli.configure_cmd
    import bifrost.cli.logs_cmd
    import bifrost.cli.run_cmd
    import bifrost.cli.ssh_cmd
    import bifrost.cli.status_cmd  # noqa: F401

    try:
        app()
    except BifrostError as e:
        from rich.console import Console

        Console(stderr=True).print(f"[red]Error:[/red] {e.message}")
        raise typer.Exit(code=e.exit_code) from None
