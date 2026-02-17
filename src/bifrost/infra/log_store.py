from __future__ import annotations

import json
import subprocess
from dataclasses import asdict
from pathlib import Path

from bifrost.infra.ssh import run_remote
from bifrost.shared import LogCopyError, RunMetadata, SetupConfig


class LogStore:
    """Handles storing and retrieving logs from remote runs."""

    def __init__(self, local_project_root: Path | None = None) -> None:
        self._project_root = local_project_root or Path.cwd()

    def store_run_metadata(self, setup: SetupConfig, metadata: RunMetadata) -> None:
        remote_run_dir = f"{setup.logs.remote_log_dir}/{metadata.run_id}"
        run_remote(setup, ["mkdir", "-p", remote_run_dir])

        metadata_json = json.dumps(asdict(metadata), indent=2)
        run_remote(
            setup,
            [
                "bash",
                "-c",
                f"cat > {remote_run_dir}/run.json << 'BIFROST_EOF'\n"
                f"{metadata_json}\nBIFROST_EOF",
            ],
        )

    def copy_logs(self, setup: SetupConfig, run_id: str) -> list[str]:
        remote_run_dir = f"{setup.logs.remote_log_dir}/{run_id}"
        local_run_dir = self._project_root / setup.logs.local_log_dir / run_id

        local_run_dir.mkdir(parents=True, exist_ok=True)

        ssh_target = f"{setup.user}@{setup.host}"
        remote_path = f"{ssh_target}:{remote_run_dir}/"
        local_path = str(local_run_dir) + "/"

        try:
            result = subprocess.run(
                ["rsync", "-az", "--timeout=30", remote_path, local_path],
                capture_output=True,
                text=True,
                timeout=120,
            )
        except (subprocess.TimeoutExpired, OSError) as e:
            raise LogCopyError(f"rsync failed for {setup.name}: {e}") from e

        if result.returncode != 0:
            raise LogCopyError(
                f"rsync failed for {setup.name}: {result.stderr.strip()}"
            )

        return [
            str(p.relative_to(self._project_root))
            for p in local_run_dir.rglob("*")
            if p.is_file()
        ]
