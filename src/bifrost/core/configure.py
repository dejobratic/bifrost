from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from bifrost.core.config import USER_CONFIG_DIR, load_config
from bifrost.core.errors import ConfigError
from bifrost.core.models import (
    ArtifactsConfig,
    BifrostConfig,
    GitLabConfig,
    SetupConfig,
)


def load_existing_config() -> BifrostConfig | None:
    if not USER_CONFIG_DIR.is_file():
        return None
    return load_config(USER_CONFIG_DIR)


def config_to_dict(config: BifrostConfig) -> dict[str, Any]:
    result: dict[str, Any] = {"version": 1}

    setups: dict[str, Any] = {}
    for name, setup in config.setups.items():
        setup_dict: dict[str, Any] = {"host": setup.host, "user": setup.user}
        if setup.runner is not None:
            setup_dict["runner"] = setup.runner
        default_artifacts = ArtifactsConfig()
        if (
            setup.artifacts.remote_dir != default_artifacts.remote_dir
            or setup.artifacts.local_dir != default_artifacts.local_dir
        ):
            setup_dict["artifacts"] = {
                "remote_dir": setup.artifacts.remote_dir,
                "local_dir": setup.artifacts.local_dir,
            }
        setups[name] = setup_dict
    result["setups"] = setups

    if config.default_setup is not None:
        result["defaults"] = {"setup": config.default_setup}

    if config.gitlab is not None:
        result["gitlab"] = {
            "url": config.gitlab.url,
            "project_id": config.gitlab.project_id,
            "token_env": config.gitlab.token_env,
        }

    return result


def write_config(config: BifrostConfig, path: Path | None = None) -> Path:
    target = path or USER_CONFIG_DIR
    target.parent.mkdir(parents=True, exist_ok=True)
    data = config_to_dict(config)
    target.write_text(yaml.dump(data, sort_keys=False, default_flow_style=False))
    return target


def build_config(
    setups: dict[str, SetupConfig],
    default_setup: str | None = None,
    gitlab: GitLabConfig | None = None,
) -> BifrostConfig:
    if not setups:
        raise ConfigError("At least one setup is required")
    if default_setup is not None and default_setup not in setups:
        raise ConfigError(
            f"Default setup '{default_setup}' not found in setups: "
            f"{list(setups.keys())}"
        )
    return BifrostConfig(setups=setups, default_setup=default_setup, gitlab=gitlab)
