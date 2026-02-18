from unittest.mock import MagicMock, patch

import pytest

from bifrost.infra.pipeline_gate import (
    GitLabPipelineGate,
    NonePipelineGate,
    create_pipeline_gate,
)
from bifrost.shared import ConfigError, PipelineConfig

GITLAB_CONFIG = PipelineConfig(
    url="https://gitlab.example.com",
    project_id=12345,
    token_env="GITLAB_TOKEN",
)


class TestNonePipelineGate:
    def test_never_busy(self) -> None:
        gate = NonePipelineGate()

        assert gate.is_busy("any-setup") is False


class TestGitLabPipelineGate:
    def test_raises_when_token_missing(self) -> None:
        with (
            patch.dict("os.environ", {}, clear=True),
            pytest.raises(ConfigError, match="token not found"),
        ):
            GitLabPipelineGate(GITLAB_CONFIG)

    def test_returns_true_when_pipeline_running(self) -> None:
        with patch.dict("os.environ", {"GITLAB_TOKEN": "test-token"}):
            gate = GitLabPipelineGate(GITLAB_CONFIG)

        mock_response = MagicMock()
        mock_response.json.return_value = [{"id": 1, "status": "running"}]
        mock_response.raise_for_status = MagicMock()

        with patch("bifrost.infra.pipeline_gate.httpx.get", return_value=mock_response):
            result = gate.is_busy("office-a")

            assert result is True

    def test_returns_false_when_no_pipelines(self) -> None:
        with patch.dict("os.environ", {"GITLAB_TOKEN": "test-token"}):
            gate = GitLabPipelineGate(GITLAB_CONFIG)

        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()

        with patch("bifrost.infra.pipeline_gate.httpx.get", return_value=mock_response):
            result = gate.is_busy("office-a")

            assert result is False

    def test_checks_pending_when_no_running(self) -> None:
        with patch.dict("os.environ", {"GITLAB_TOKEN": "test-token"}):
            gate = GitLabPipelineGate(GITLAB_CONFIG)

        responses = [
            MagicMock(json=MagicMock(return_value=[]), raise_for_status=MagicMock()),
            MagicMock(
                json=MagicMock(return_value=[{"id": 2}]),
                raise_for_status=MagicMock(),
            ),
        ]

        with patch("bifrost.infra.pipeline_gate.httpx.get", side_effect=responses):
            result = gate.is_busy("office-a")

            assert result is True


class TestCreatePipelineGate:
    def test_returns_none_gate_without_config(self) -> None:
        gate = create_pipeline_gate(None)

        assert isinstance(gate, NonePipelineGate)

    def test_returns_gitlab_gate_with_config(self) -> None:
        with patch.dict("os.environ", {"GITLAB_TOKEN": "test-token"}):
            gate = create_pipeline_gate(GITLAB_CONFIG)

        assert isinstance(gate, GitLabPipelineGate)
