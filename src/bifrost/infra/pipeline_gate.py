from __future__ import annotations

import os
from typing import Protocol

import httpx

from bifrost.shared import ConfigError, GitLabConfig


class PipelineGate(Protocol):
    """Protocol for checking if pipeline is busy."""

    def is_busy(self, setup_name: str) -> bool: ...


class NonePipelineGate:
    """No-op gate when no CI is configured."""

    def is_busy(self, setup_name: str) -> bool:
        return False


class GitLabPipelineGate:
    """GitLab CI pipeline gate."""

    RUNNING_STATUSES = frozenset({"running", "pending"})

    def __init__(self, gitlab_config: GitLabConfig) -> None:
        self._config = gitlab_config
        self._token = os.environ.get(gitlab_config.token_env, "")
        if not self._token:
            raise ConfigError(
                f"GitLab token not found in environment variable "
                f"'{gitlab_config.token_env}'"
            )

    def is_busy(self, setup_name: str) -> bool:
        url = f"{self._config.url}/api/v4/projects/{self._config.project_id}/pipelines"
        headers = {"PRIVATE-TOKEN": self._token}
        params: dict[str, str | int] = {"status": "running", "per_page": 1}

        response = httpx.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()

        if response.json():
            return True

        params["status"] = "pending"
        response = httpx.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()

        return bool(response.json())


def create_pipeline_gate(gitlab_config: GitLabConfig | None) -> PipelineGate:
    if gitlab_config is None:
        return NonePipelineGate()
    return GitLabPipelineGate(gitlab_config)
