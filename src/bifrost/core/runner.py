from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Protocol

from bifrost.core.errors import CiBusyError, ConfigError, RemoteCommandError
from bifrost.core.models import BifrostConfig, RunMetadata, SetupConfig

if TYPE_CHECKING:
    import subprocess


class CiGate(Protocol):
    def is_busy(self, setup_name: str) -> bool: ...


class RemoteExecutor(Protocol):
    def run_remote(self, setup: SetupConfig, command: list[str], capture: bool = True) -> subprocess.CompletedProcess[str]: ...


class GitOps(Protocol):
    def fetch_and_checkout(self, setup: SetupConfig, ref: str, latest: bool = False) -> None: ...


class ArtifactCopier(Protocol):
    def copy_artifacts(self, setup: SetupConfig, run_id: str) -> list[str]: ...
    def store_run_metadata(self, setup: SetupConfig, metadata: RunMetadata) -> None: ...


class Runner:
    def __init__(
        self,
        config: BifrostConfig,
        ci_gate: CiGate,
        executor: RemoteExecutor,
        git_ops: GitOps,
        copier: ArtifactCopier,
    ) -> None:
        self._config = config
        self._ci_gate = ci_gate
        self._executor = executor
        self._git_ops = git_ops
        self._copier = copier

    def resolve_setup(self, setup_name: str | None) -> SetupConfig:
        name = setup_name or self._config.default_setup
        if not name:
            raise ConfigError("No setup specified and no default configured")
        if name not in self._config.setups:
            raise ConfigError(f"Setup '{name}' not found. Available: {list(self._config.setups.keys())}")
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
            raise ConfigError(f"No command provided and no default runner for setup '{setup.name}'")

        if not force and self._ci_gate.is_busy(setup.name):
            raise CiBusyError(f"CI pipeline is busy on setup '{setup.name}'. Use --force to override.")

        run_id = uuid.uuid4().hex[:12]

        if dry_run:
            return RunMetadata(
                run_id=run_id,
                setup=setup.name,
                ref=ref,
                command=resolved_command,
            )

        if ref:
            self._git_ops.fetch_and_checkout(setup, ref, latest=latest)

        result = self._executor.run_remote(setup, resolved_command)

        metadata = RunMetadata(
            run_id=run_id,
            setup=setup.name,
            ref=ref,
            command=resolved_command,
            exit_code=result.returncode,
        )

        self._copier.store_run_metadata(setup, metadata)

        if result.returncode != 0:
            artifact_paths = self._copier.copy_artifacts(setup, run_id)
            metadata = RunMetadata(
                run_id=metadata.run_id,
                setup=metadata.setup,
                ref=metadata.ref,
                command=metadata.command,
                timestamp=metadata.timestamp,
                exit_code=metadata.exit_code,
                artifact_paths=artifact_paths,
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
            artifact_paths=self._copier.copy_artifacts(setup, run_id),
        )

        return metadata
