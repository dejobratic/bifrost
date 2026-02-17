from __future__ import annotations

from pathlib import Path

import yaml

from bifrost.shared.errors import ConfigError
from bifrost.shared.models import BifrostConfig

CONFIG_FILENAMES = [".bifrost.yml", ".bifrost.yaml"]
USER_CONFIG_DIR = Path.home() / ".config" / "bifrost" / "config.yml"


class ConfigManager:
    def read_config(self, path: Path | None = None) -> BifrostConfig:
        config_file_path = self._find_config_file(path)
        try:
            raw = yaml.safe_load(config_file_path.read_text())
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in {config_file_path}: {e}") from e
        except OSError as e:
            raise ConfigError(f"Cannot read config file {config_file_path}: {e}") from e

        if not isinstance(raw, dict):
            raise ConfigError(f"Config file {config_file_path} must be a YAML mapping")

        return BifrostConfig.from_mapping(raw)

    def write_config(self, config: BifrostConfig, path: Path | None = None) -> Path:
        config_file_path = path or USER_CONFIG_DIR
        config_file_path.parent.mkdir(parents=True, exist_ok=True)
        data = config.to_dict()
        config_file_path.write_text(
            yaml.dump(data, sort_keys=False, default_flow_style=False)
        )
        return config_file_path

    def _find_config_file(self, start_dir: Path | None = None) -> Path:
        if start_dir is not None:
            if start_dir.is_file():
                return start_dir
            if start_dir.name in CONFIG_FILENAMES and not start_dir.is_dir():
                return start_dir

        if start_dir is None:
            search_dir = Path.cwd()
        elif start_dir.is_dir():
            search_dir = start_dir
        else:
            search_dir = start_dir.parent

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
