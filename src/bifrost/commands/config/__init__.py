"""Config command group and subcommands."""

from bifrost.commands.config.add import add_setup
from bifrost.commands.config.command import config_app
from bifrost.commands.config.edit import edit_setup
from bifrost.commands.config.list import list_setups
from bifrost.commands.config.remove import remove_setup
from bifrost.commands.config.set_default import set_default_setup

__all__ = [
    "add_setup",
    "config_app",
    "edit_setup",
    "list_setups",
    "remove_setup",
    "set_default_setup",
]
