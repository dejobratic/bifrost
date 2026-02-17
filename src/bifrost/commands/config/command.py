"""Config command group for managing setup configurations."""

import typer

config_app = typer.Typer(
    name="config",
    help="Manage setup configurations",
    no_args_is_help=True,
)
