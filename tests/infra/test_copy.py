import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from bifrost.core.errors import ArtifactCopyError
from bifrost.core.models import ArtifactsConfig, RunMetadata, SetupConfig
from bifrost.infra.copy import ArtifactCopier


@pytest.fixture
def setup() -> SetupConfig:
    return SetupConfig(
        name="lab-a",
        host="10.0.0.5",
        user="ci",
        artifacts=ArtifactsConfig(remote_dir=".bifrost", local_dir=".bifrost/lab-a"),
    )


@pytest.fixture
def metadata() -> RunMetadata:
    return RunMetadata(
        run_id="abc123",
        setup="lab-a",
        ref="main",
        command=["pytest"],
        timestamp="2026-01-01T00:00:00",
    )


class TestStoreRunMetadata:
    def test_creates_remote_dir_and_writes_json(
        self, setup: SetupConfig, metadata: RunMetadata, tmp_path: Path
    ) -> None:
        # Arrange
        copier = ArtifactCopier(local_project_root=tmp_path)

        with patch("bifrost.infra.copy.run_remote") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="", stderr=""
            )

            # Act
            copier.store_run_metadata(setup, metadata)

            # Assert
            assert mock_run.call_count == 2
            mkdir_call = mock_run.call_args_list[0]
            assert "mkdir" in mkdir_call[0][1]
            assert ".bifrost/abc123" in " ".join(mkdir_call[0][1])


class TestCopyArtifacts:
    def test_runs_rsync_and_returns_paths(
        self, setup: SetupConfig, tmp_path: Path
    ) -> None:
        # Arrange
        copier = ArtifactCopier(local_project_root=tmp_path)

        with patch("bifrost.infra.copy.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="", stderr=""
            )

            # Create a fake local file to simulate rsync having copied it
            local_dir = tmp_path / ".bifrost" / "lab-a" / "abc123"
            local_dir.mkdir(parents=True)
            (local_dir / "run.json").write_text("{}")

            # Act
            paths = copier.copy_artifacts(setup, "abc123")

            # Assert
            assert len(paths) == 1
            assert "run.json" in paths[0]
            mock_run.assert_called_once()
            rsync_args = mock_run.call_args[0][0]
            assert rsync_args[0] == "rsync"

    def test_raises_on_rsync_failure(self, setup: SetupConfig, tmp_path: Path) -> None:
        # Arrange
        copier = ArtifactCopier(local_project_root=tmp_path)

        with patch("bifrost.infra.copy.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=1, stdout="", stderr="connection refused"
            )

            # Act / Assert
            with pytest.raises(ArtifactCopyError, match="rsync failed"):
                copier.copy_artifacts(setup, "abc123")

    def test_raises_on_timeout(self, setup: SetupConfig, tmp_path: Path) -> None:
        # Arrange
        copier = ArtifactCopier(local_project_root=tmp_path)

        with (
            patch(
                "bifrost.infra.copy.subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd="rsync", timeout=120),
            ),
            pytest.raises(ArtifactCopyError, match="rsync failed"),
        ):
            copier.copy_artifacts(setup, "abc123")
