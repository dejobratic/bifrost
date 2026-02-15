from unittest.mock import MagicMock, patch

import pytest

from bifrost.core.errors import ConfigError
from bifrost.core.models import GitLabConfig
from bifrost.infra.ci_gate import GitLabCiGate, NoneCiGate, create_ci_gate

GITLAB_CONFIG = GitLabConfig(
    url="https://gitlab.example.com",
    project_id=12345,
    token_env="GITLAB_TOKEN",
)


class TestNoneCiGate:
    def test_never_busy(self) -> None:
        # Arrange
        gate = NoneCiGate()

        # Act / Assert
        assert gate.is_busy("any-setup") is False


class TestGitLabCiGate:
    def test_raises_when_token_missing(self) -> None:
        # Arrange / Act / Assert
        with (
            patch.dict("os.environ", {}, clear=True),
            pytest.raises(ConfigError, match="token not found"),
        ):
            GitLabCiGate(GITLAB_CONFIG)

    def test_returns_true_when_pipeline_running(self) -> None:
        # Arrange
        with patch.dict("os.environ", {"GITLAB_TOKEN": "test-token"}):
            gate = GitLabCiGate(GITLAB_CONFIG)

        mock_response = MagicMock()
        mock_response.json.return_value = [{"id": 1, "status": "running"}]
        mock_response.raise_for_status = MagicMock()

        with patch("bifrost.infra.ci_gate.httpx.get", return_value=mock_response):
            # Act
            result = gate.is_busy("office-a")

            # Assert
            assert result is True

    def test_returns_false_when_no_pipelines(self) -> None:
        # Arrange
        with patch.dict("os.environ", {"GITLAB_TOKEN": "test-token"}):
            gate = GitLabCiGate(GITLAB_CONFIG)

        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()

        with patch("bifrost.infra.ci_gate.httpx.get", return_value=mock_response):
            # Act
            result = gate.is_busy("office-a")

            # Assert
            assert result is False

    def test_checks_pending_when_no_running(self) -> None:
        # Arrange
        with patch.dict("os.environ", {"GITLAB_TOKEN": "test-token"}):
            gate = GitLabCiGate(GITLAB_CONFIG)

        responses = [
            MagicMock(json=MagicMock(return_value=[]), raise_for_status=MagicMock()),
            MagicMock(
                json=MagicMock(return_value=[{"id": 2}]),
                raise_for_status=MagicMock(),
            ),
        ]

        with patch("bifrost.infra.ci_gate.httpx.get", side_effect=responses):
            # Act
            result = gate.is_busy("office-a")

            # Assert
            assert result is True


class TestCreateCiGate:
    def test_returns_none_gate_without_config(self) -> None:
        # Act
        gate = create_ci_gate(None)

        # Assert
        assert isinstance(gate, NoneCiGate)

    def test_returns_gitlab_gate_with_config(self) -> None:
        # Arrange / Act
        with patch.dict("os.environ", {"GITLAB_TOKEN": "test-token"}):
            gate = create_ci_gate(GITLAB_CONFIG)

        # Assert
        assert isinstance(gate, GitLabCiGate)
