from __future__ import annotations

import uuid

from bifrost.commands.run.errors import CiBusyError, RemoteCommandError
from bifrost.infra.git_ops import fetch_and_checkout
from bifrost.infra.log_store import LogStore
from bifrost.infra.pipeline_gate import PipelineGate
from bifrost.infra.ssh import run_remote
from bifrost.shared import BifrostConfig, ConfigError, RunMetadata, SetupConfig


class Runner:
    """Orchestrates running commands on remote setups."""

    def __init__(
        self, config: BifrostConfig, pipeline_gate: PipelineGate, log_store: LogStore
    ) -> None:
        self._config = config
        self._pipeline_gate = pipeline_gate
        self._log_store = log_store

    def resolve_setup(self, setup_name: str | None) -> SetupConfig:
        name = setup_name or self._config.default_setup
        if not name:
            raise ConfigError("No setup specified and no default configured")
        if name not in self._config.setups:
            available = list(self._config.setups.keys())
            raise ConfigError(f"Setup '{name}' not found. Available: {available}")
        return self._config.setups[name]

    def run(
        self,
        setup_name: str | None = None,
        command: list[str] | None = None,
        ref: str | None = None,
        latest: bool = False,
        force: bool = False,
        dry_run: bool = False,
    ) -> RunMetadata:
        setup = self.resolve_setup(setup_name)
        resolved_command = command or ([setup.runner] if setup.runner else None)
        if not resolved_command:
            raise ConfigError(
                f"No command provided and no default runner for setup '{setup.name}'"
            )

        if not force and self._pipeline_gate.is_busy(setup.name):
            raise CiBusyError(
                f"CI pipeline is busy on setup '{setup.name}'. Use --force to override."
            )

        run_id = uuid.uuid4().hex[:12]

        if dry_run:
            return RunMetadata(
                run_id=run_id,
                setup=setup.name,
                ref=ref,
                command=resolved_command,
            )

        if ref:
            fetch_and_checkout(setup, ref, latest=latest)

        result = run_remote(setup, resolved_command)

        metadata = RunMetadata(
            run_id=run_id,
            setup=setup.name,
            ref=ref,
            command=resolved_command,
            exit_code=result.returncode,
        )

        self._log_store.store_run_metadata(setup, metadata)

        if result.returncode != 0:
            log_paths = self._log_store.copy_logs(setup, run_id)
            metadata = RunMetadata(
                run_id=metadata.run_id,
                setup=metadata.setup,
                ref=metadata.ref,
                command=metadata.command,
                timestamp=metadata.timestamp,
                exit_code=metadata.exit_code,
                log_paths=log_paths,
            )
            raise RemoteCommandError(
                f"Command failed on '{setup.name}' (exit {result.returncode})",
                remote_exit_code=result.returncode,
            )

        metadata = RunMetadata(
            run_id=metadata.run_id,
            setup=metadata.setup,
            ref=metadata.ref,
            command=metadata.command,
            timestamp=metadata.timestamp,
            exit_code=metadata.exit_code,
            log_paths=self._log_store.copy_logs(setup, run_id),
        )

        return metadata
