"""Dependency injection container for Bifrost CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from bifrost.infra.log_store import LogStore
from bifrost.shared import BifrostConfig, ConfigManager


class Container(Protocol):
    """Protocol for dependency injection container."""

    def get_config_manager(self) -> ConfigManager: ...
    def get_config(self, path: Path | None = None) -> BifrostConfig: ...
    def get_log_store(self) -> LogStore: ...


class DefaultContainer:
    """Default implementation of dependency container.

    Provides lazy initialization of dependencies and caches them
    for the lifetime of the container instance.
    """

    def __init__(self) -> None:
        self._config_manager: ConfigManager | None = None
        self._config: BifrostConfig | None = None
        self._log_store: LogStore | None = None

    def get_config_manager(self) -> ConfigManager:
        """Get the configuration manager instance."""
        if self._config_manager is None:
            self._config_manager = ConfigManager()
        return self._config_manager

    def get_config(self, path: Path | None = None) -> BifrostConfig:
        """Get the bifrost configuration.

        Args:
            path: Optional path to config file. If None, will search for config.

        Returns:
            The loaded BifrostConfig instance.
        """
        if self._config is None or path is not None:
            config_manager = self.get_config_manager()
            self._config = config_manager.read_config(path)
        return self._config

    def get_log_store(self) -> LogStore:
        """Get the log store instance."""
        if self._log_store is None:
            self._log_store = LogStore()
        return self._log_store


def create_container() -> Container:
    """Create a new dependency injection container.

    Returns:
        A new Container instance with default dependencies.
    """
    return DefaultContainer()
