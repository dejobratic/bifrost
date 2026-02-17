from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from bifrost.infra.utils import as_mapping, require_int, require_str
from bifrost.shared.errors import ConfigError


@dataclass(frozen=True, slots=True)
class LogConfig:
    remote_log_dir: str = ".bifrost/logs"
    local_log_dir: str = ".bifrost"

    @classmethod
    def from_mapping(
        cls, raw: Any, *, default_local_log_dir: str = ".bifrost"
    ) -> LogConfig:
        data = as_mapping(raw, what="Setup logs")

        # Support old 'artifacts' key for backward compatibility
        remote_key = "remote_log_dir" if "remote_log_dir" in data else "remote_dir"
        local_key = "local_log_dir" if "local_log_dir" in data else "local_dir"

        return cls(
            remote_log_dir=str(data.get(remote_key, ".bifrost/logs")),
            local_log_dir=str(data.get(local_key, default_local_log_dir)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "remote_log_dir": self.remote_log_dir,
            "local_log_dir": self.local_log_dir,
        }


@dataclass(frozen=True, slots=True)
class SetupConfig:
    name: str
    host: str
    user: str
    runner: str | None = None
    logs: LogConfig = field(default_factory=LogConfig)

    @classmethod
    def from_mapping(cls, name: str, raw: Any) -> SetupConfig:
        data = as_mapping(raw, what=f"Setup '{name}'")
        host = require_str(data, "host", what=f"Setup '{name}'")
        user = require_str(data, "user", what=f"Setup '{name}'")

        # Support both 'logs' and old 'artifacts' key for backward compatibility
        logs_data = data.get("logs") if "logs" in data else data.get("artifacts")
        logs = LogConfig.from_mapping(
            logs_data,
            default_local_log_dir=f".bifrost/{name}",
        )

        runner = data.get("runner")
        if runner is not None and not isinstance(runner, str):
            raise ConfigError(f"Setup '{name}' runner must be a string")

        return cls(name=name, host=host, user=user, runner=runner, logs=logs)

    def default_logs(self) -> LogConfig:
        return LogConfig(local_log_dir=f".bifrost/{self.name}")

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"host": self.host, "user": self.user}
        if self.runner is not None:
            data["runner"] = self.runner

        if self.logs != self.default_logs():
            data["logs"] = self.logs.to_dict()

        return data


@dataclass(frozen=True, slots=True)
class GitLabConfig:
    url: str
    project_id: int
    token_env: str

    @classmethod
    def from_mapping(cls, raw: Any) -> GitLabConfig:
        data = as_mapping(raw, what="GitLab config")
        url = require_str(data, "url", what="GitLab config")
        token_env = require_str(data, "token_env", what="GitLab config")
        project_id = require_int(data, "project_id", what="GitLab config")
        return cls(url=url, project_id=project_id, token_env=token_env)

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "project_id": self.project_id,
            "token_env": self.token_env,
        }


@dataclass(frozen=True, slots=True)
class BifrostConfig:
    setups: dict[str, SetupConfig]
    default_setup: str | None = None
    gitlab: GitLabConfig | None = None

    @classmethod
    def from_mapping(cls, raw: Any) -> BifrostConfig:
        data = as_mapping(raw, what="Bifrost config")

        version = data.get("version")
        if version != 1:
            raise ConfigError(f"Unsupported config version: {version} (expected 1)")

        raw_setups = data.get("setups")
        setups_map = as_mapping(raw_setups, what="setups")
        if not setups_map:
            raise ConfigError("No setups defined")

        setups = {
            name: SetupConfig.from_mapping(name, setup_raw)
            for name, setup_raw in setups_map.items()
        }

        defaults = as_mapping(data.get("defaults"), what="defaults")
        default_setup = defaults.get("setup")
        if default_setup is not None and not isinstance(default_setup, str):
            raise ConfigError("defaults.setup must be a string")

        gitlab_raw = data.get("gitlab")
        gitlab = (
            GitLabConfig.from_mapping(gitlab_raw) if gitlab_raw is not None else None
        )

        cfg = cls(setups=setups, default_setup=default_setup, gitlab=gitlab)
        cfg._validate()
        return cfg

    def _validate(self) -> None:
        if self.default_setup is not None and self.default_setup not in self.setups:
            setup_list = list(self.setups.keys())
            raise ConfigError(
                f"Default setup '{self.default_setup}' "
                f"not found in setups: {setup_list}"
            )

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "version": 1,
            "setups": {name: setup.to_dict() for name, setup in self.setups.items()},
        }
        if self.default_setup is not None:
            result["defaults"] = {"setup": self.default_setup}
        if self.gitlab is not None:
            result["gitlab"] = self.gitlab.to_dict()
        return result


@dataclass(frozen=True, slots=True)
class RunMetadata:
    run_id: str
    setup: str
    ref: str | None
    command: list[str]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    exit_code: int = 0
    log_paths: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "setup": self.setup,
            "ref": self.ref,
            "command": self.command,
            "timestamp": self.timestamp.isoformat(),
            "exit_code": self.exit_code,
            "log_paths": self.log_paths,
        }
