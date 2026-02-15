from __future__ import annotations

import os
from typing import Protocol

import httpx

from bifrost.core.errors import ConfigError
from bifrost.core.models import GitLabConfig


class CiGate(Protocol):
    def is_busy(self, setup_name: str) -> bool: ...


class NoneCiGate:
    def is_busy(self, setup_name: str) -> bool:
        return False


class GitLabCiGate:
    RUNNING_STATUSES = frozenset({"running", "pending"})

    def __init__(self, gitlab_config: GitLabConfig) -> None:
        self._config = gitlab_config
        self._token = os.environ.get(gitlab_config.token_env, "")
        if not self._token:
            env_var = gitlab_config.token_env
            raise ConfigError(
                f"GitLab token not found in environment variable '{env_var}'"
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


def create_ci_gate(gitlab_config: GitLabConfig | None) -> CiGate:
    if gitlab_config is None:
        return NoneCiGate()
    return GitLabCiGate(gitlab_config)
