import typer
from rich.console import Console

from bifrost.di import create_container
from bifrost.shared import BifrostError

app = typer.Typer(
    name="bf",
    help="Bifrost — bridge between local dev and remote test setups.",
    no_args_is_help=True,
)

LOGO = """[bold magenta]
██████╗ ██╗███████╗██████╗  ██████╗ ███████╗████████╗
██╔══██╗██║██╔════╝██╔══██╗██╔═══██╗██╔════╝╚══██╔══╝
██████╔╝██║█████╗  ██████╔╝██║   ██║███████╗   ██║
██╔══██╗██║██╔══╝  ██╔══██╗██║   ██║╚════██║   ██║
██████╔╝██║██║     ██║  ██║╚██████╔╝███████║   ██║
╚═════╝ ╚═╝╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝
[/bold magenta]"""


def version_callback(value: bool) -> None:
    if value:
        from importlib.metadata import version as get_version

        console = Console()
        console.print(LOGO)
        console.print(f"\nBifrost version {get_version('bifrost')}")
        raise typer.Exit()


@app.callback()
def callback(
    ctx: typer.Context,
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """Initialize dependency injection container."""
    ctx.obj = create_container()


def main() -> None:
    import bifrost.commands.run.command
    import bifrost.commands.ssh.command
    import bifrost.commands.status.command  # noqa: F401
    from bifrost.commands.config import config_app

    app.add_typer(config_app)

    try:
        app()
    except BifrostError as e:
        Console(stderr=True).print(f"[red]Error:[/red] {e.message}")
        raise typer.Exit(code=e.exit_code) from None
