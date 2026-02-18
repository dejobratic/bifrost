"""Pipeline command group for managing CI/CD pipeline integration."""

import typer

pipeline_app = typer.Typer(
    name="pipeline",
    help="Manage CI/CD pipeline integration",
    no_args_is_help=True,
)

from bifrost.commands.pipeline import add, edit, list, remove  # noqa: E402, F401
