from pathlib import Path

import yaml

from bifrost.core.errors import ConfigError
from bifrost.core.models import (
    ArtifactsConfig,
    BifrostConfig,
    GitLabConfig,
    SetupConfig,
)

CONFIG_FILENAMES = [".bifrost.yml", ".bifrost.yaml"]
USER_CONFIG_DIR = Path.home() / ".config" / "bifrost" / "config.yml"


def find_config_file(start_dir: Path | None = None) -> Path:
    search_dir = start_dir or Path.cwd()
    for name in CONFIG_FILENAMES:
        candidate = search_dir / name
        if candidate.is_file():
            return candidate
    if USER_CONFIG_DIR.is_file():
        return USER_CONFIG_DIR
    raise ConfigError(
        f"No config file found. Expected {' or '.join(CONFIG_FILENAMES)} "
        f"in project root, or {USER_CONFIG_DIR}"
    )


def load_config(path: Path) -> BifrostConfig:
    try:
        raw = yaml.safe_load(path.read_text())
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in {path}: {e}") from e
    except OSError as e:
        raise ConfigError(f"Cannot read config file {path}: {e}") from e

    if not isinstance(raw, dict):
        raise ConfigError(f"Config file {path} must be a YAML mapping")

    return _parse_config(raw, path)


def _parse_config(raw: dict, path: Path) -> BifrostConfig:
    version = raw.get("version")
    if version != 1:
        raise ConfigError(f"Unsupported config version: {version} (expected 1)")

    setups = _parse_setups(raw.get("setups"), path)
    defaults = raw.get("defaults", {})
    default_setup = defaults.get("setup")

    if default_setup and default_setup not in setups:
        available = list(setups.keys())
        raise ConfigError(
            f"Default setup '{default_setup}' not found in setups: {available}"
        )

    gitlab = _parse_gitlab(raw.get("gitlab"))

    return BifrostConfig(
        setups=setups,
        default_setup=default_setup,
        gitlab=gitlab,
    )


def _parse_setups(raw_setups: dict | None, path: Path) -> dict[str, SetupConfig]:
    if not raw_setups:
        raise ConfigError(f"No setups defined in {path}")

    setups: dict[str, SetupConfig] = {}
    for name, raw_setup in raw_setups.items():
        if not isinstance(raw_setup, dict):
            raise ConfigError(f"Setup '{name}' must be a mapping")
        setups[name] = _parse_single_setup(name, raw_setup)
    return setups


def _parse_single_setup(name: str, raw: dict) -> SetupConfig:
    host = raw.get("host")
    user = raw.get("user")
    if not host or not user:
        raise ConfigError(f"Setup '{name}' must have 'host' and 'user'")

    artifacts_raw = raw.get("artifacts", {})
    artifacts = ArtifactsConfig(
        remote_dir=artifacts_raw.get("remote_dir", ".bifrost"),
        local_dir=artifacts_raw.get("local_dir", f".bifrost/{name}"),
    )

    return SetupConfig(
        name=name,
        host=host,
        user=user,
        runner=raw.get("runner"),
        artifacts=artifacts,
    )


def _parse_gitlab(raw: dict | None) -> GitLabConfig | None:
    if not raw:
        return None

    url = raw.get("url")
    project_id = raw.get("project_id")
    token_env = raw.get("token_env")

    if not url or not project_id or not token_env:
        raise ConfigError("GitLab config requires 'url', 'project_id', and 'token_env'")

    return GitLabConfig(url=url, project_id=int(project_id), token_env=token_env)
