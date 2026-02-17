import subprocess
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from bifrost.infra.log_store import LogStore
from bifrost.shared import LogConfig, LogCopyError, RunMetadata, SetupConfig


@pytest.fixture
def setup() -> SetupConfig:
    return SetupConfig(
        name="lab-a",
        host="10.0.0.5",
        user="ci",
        logs=LogConfig(remote_log_dir=".bifrost/logs", local_log_dir=".bifrost/lab-a"),
    )


@pytest.fixture
def metadata() -> RunMetadata:
    return RunMetadata(
        run_id="abc123",
        setup="lab-a",
        ref="main",
        command=["pytest"],
        timestamp=datetime(2026, 1, 1, 0, 0, 0),
    )


class TestStoreRunMetadata:
    def test_creates_remote_dir_and_writes_json(
        self, setup: SetupConfig, metadata: RunMetadata, tmp_path: Path
    ) -> None:
        store = LogStore(local_project_root=tmp_path)

        with patch("bifrost.infra.log_store.run_remote") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="", stderr=""
            )

            store.store_run_metadata(setup, metadata)

            assert mock_run.call_count == 2
            mkdir_call = mock_run.call_args_list[0]
            assert "mkdir" in mkdir_call[0][1]
            assert ".bifrost/logs/abc123" in " ".join(mkdir_call[0][1])


class TestCopyLogs:
    def test_runs_rsync_and_returns_paths(
        self, setup: SetupConfig, tmp_path: Path
    ) -> None:
        store = LogStore(local_project_root=tmp_path)

        with patch("bifrost.infra.log_store.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="", stderr=""
            )

            local_dir = tmp_path / ".bifrost" / "lab-a" / "abc123"
            local_dir.mkdir(parents=True)
            (local_dir / "run.json").write_text("{}")

            paths = store.copy_logs(setup, "abc123")

            assert len(paths) == 1
            assert "run.json" in paths[0]
            mock_run.assert_called_once()
            rsync_args = mock_run.call_args[0][0]
            assert rsync_args[0] == "rsync"

    def test_raises_on_rsync_failure(self, setup: SetupConfig, tmp_path: Path) -> None:
        store = LogStore(local_project_root=tmp_path)

        with patch("bifrost.infra.log_store.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=1, stdout="", stderr="connection refused"
            )

            with pytest.raises(LogCopyError, match="rsync failed"):
                store.copy_logs(setup, "abc123")

    def test_raises_on_timeout(self, setup: SetupConfig, tmp_path: Path) -> None:
        store = LogStore(local_project_root=tmp_path)

        with (
            patch(
                "bifrost.infra.log_store.subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd="rsync", timeout=120),
            ),
            pytest.raises(LogCopyError, match="rsync failed"),
        ):
            store.copy_logs(setup, "abc123")
