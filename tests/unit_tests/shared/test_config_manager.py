from collections.abc import Callable
from pathlib import Path

import pytest

from bifrost.shared import (
    BifrostConfig,
    ConfigError,
    ConfigManager,
    LogConfig,
    PipelineConfig,
    SetupConfig,
)

VALID_CONFIG = """\
version: 1

defaults:
  setup: office-a

pipelines:
  main:
    url: "https://gitlab.example.com"
    project_id: 12345
    token_env: "GITLAB_TOKEN"

setups:
  office-a:
    host: "10.0.0.5"
    user: "ci"
    runner: "pytest"
    pipeline: main
    logs:
      remote_log_dir: ".bifrost/logs"
      local_log_dir: ".bifrost/office-a"

  office-b:
    host: "10.1.0.7"
    user: "ci"
"""

MINIMAL_CONFIG = """\
version: 1
setups:
  lab:
    host: "192.168.1.1"
    user: "tester"
"""


@pytest.fixture
def config_manager() -> ConfigManager:
    return ConfigManager()


def _minimal_setup(name: str = "lab") -> SetupConfig:
    return SetupConfig(
        name=name,
        host="10.0.0.1",
        user="ci",
        logs=LogConfig(local_log_dir=f".bifrost/{name}"),
    )


def _full_setup(name: str = "office") -> SetupConfig:
    return SetupConfig(
        name=name,
        host="10.0.0.5",
        user="ci",
        runner="pytest",
        logs=LogConfig(remote_log_dir="build/out", local_log_dir="local/out"),
    )


class TestConfigManagerRead:
    def test_loads_discovered_bifrost_yml_in_directory(
        self, tmp_path: Path, config_manager: ConfigManager
    ) -> None:
        config_file = tmp_path / ".bifrost.yml"
        config_file.write_text(
            """\
version: 1
setups:
  lab:
    host: "127.0.0.1"
    user: "ci"
"""
        )

        result = config_manager.read_config(tmp_path)

        assert "lab" in result.setups

    def test_raises_when_no_config_file_found(
        self, tmp_path: Path, config_manager: ConfigManager
    ) -> None:
        with pytest.raises(ConfigError, match="No config file found"):
            config_manager.read_config(tmp_path)

    def test_loads_valid_full_config(
        self, tmp_config: Callable[[str], Path], config_manager: ConfigManager
    ) -> None:
        path = tmp_config(VALID_CONFIG)

        config = config_manager.read_config(path)

        assert config.default_setup == "office-a"
        assert "office-a" in config.setups
        assert "office-b" in config.setups
        assert config.setups["office-a"].host == "10.0.0.5"
        assert config.setups["office-a"].user == "ci"
        assert config.setups["office-a"].runner == "pytest"
        assert config.setups["office-a"].pipeline == "main"
        assert config.setups["office-a"].logs.remote_log_dir == ".bifrost/logs"
        assert "main" in config.pipelines
        assert config.pipelines["main"].project_id == 12345
        assert config.pipelines["main"].token_env == "GITLAB_TOKEN"

    def test_loads_minimal_config(
        self, tmp_config: Callable[[str], Path], config_manager: ConfigManager
    ) -> None:
        path = tmp_config(MINIMAL_CONFIG)

        config = config_manager.read_config(path)

        assert config.default_setup is None
        assert config.pipelines == {}
        assert config.setups["lab"].host == "192.168.1.1"

    def test_defaults_log_local_dir_to_setup_name(
        self, tmp_config: Callable[[str], Path], config_manager: ConfigManager
    ) -> None:
        path = tmp_config(MINIMAL_CONFIG)

        config = config_manager.read_config(path)

        assert config.setups["lab"].logs.local_log_dir == ".bifrost/lab"

    def test_rejects_invalid_yaml(
        self, tmp_config: Callable[[str], Path], config_manager: ConfigManager
    ) -> None:
        path = tmp_config(": invalid: yaml: [")

        with pytest.raises(ConfigError, match="Invalid YAML"):
            config_manager.read_config(path)

    def test_rejects_wrong_version(
        self, tmp_config: Callable[[str], Path], config_manager: ConfigManager
    ) -> None:
        path = tmp_config("version: 99\nsetups:\n  x:\n    host: h\n    user: u")

        with pytest.raises(ConfigError, match="Unsupported config version"):
            config_manager.read_config(path)

    def test_allows_empty_setups(
        self, tmp_config: Callable[[str], Path], config_manager: ConfigManager
    ) -> None:
        path = tmp_config("version: 1\nsetups: {}")

        config = config_manager.read_config(path)
        assert config.setups == {}

    def test_rejects_setup_without_host(
        self, tmp_config: Callable[[str], Path], config_manager: ConfigManager
    ) -> None:
        path = tmp_config("version: 1\nsetups:\n  bad:\n    user: ci")

        with pytest.raises(ConfigError, match="must have 'host'"):
            config_manager.read_config(path)

    def test_rejects_invalid_default_setup(
        self, tmp_config: Callable[[str], Path], config_manager: ConfigManager
    ) -> None:
        config_text = """\
version: 1
defaults:
  setup: nonexistent
setups:
  lab:
    host: "1.2.3.4"
    user: "ci"
"""
        path = tmp_config(config_text)

        with pytest.raises(ConfigError, match="Default setup 'nonexistent' not found"):
            config_manager.read_config(path)

    def test_rejects_incomplete_pipeline(
        self, tmp_config: Callable[[str], Path], config_manager: ConfigManager
    ) -> None:
        config_text = """\
version: 1
pipelines:
  main:
    url: "https://gitlab.example.com"
setups:
  lab:
    host: "1.2.3.4"
    user: "ci"
"""
        path = tmp_config(config_text)

        with pytest.raises(ConfigError, match="must have"):
            config_manager.read_config(path)

    def test_loads_config_with_port(
        self, tmp_config: Callable[[str], Path], config_manager: ConfigManager
    ) -> None:
        config_text = """\
version: 1
setups:
  lab:
    host: "1.2.3.4"
    user: "ci"
    port: 2222
"""
        path = tmp_config(config_text)

        config = config_manager.read_config(path)

        assert config.setups["lab"].port == 2222


class TestConfigToDict:
    def test_minimal(self) -> None:
        config = BifrostConfig(setups={"lab": _minimal_setup()})

        result = config.to_dict()

        assert result["version"] == 1
        assert result["setups"]["lab"] == {"host": "10.0.0.1", "user": "ci"}
        assert "defaults" not in result
        assert "pipelines" not in result

    def test_full(self) -> None:
        config = BifrostConfig(
            setups={"office": _full_setup()},
            default_setup="office",
            pipelines={
                "main": PipelineConfig(
                    url="https://gitlab.example.com",
                    project_id=42,
                    token_env="GL_TOKEN",
                )
            },
        )

        result = config.to_dict()

        assert result["defaults"] == {"setup": "office"}
        assert result["pipelines"]["main"]["project_id"] == 42
        setup = result["setups"]["office"]
        assert setup["runner"] == "pytest"
        assert setup["logs"]["remote_log_dir"] == "build/out"

    def test_omits_default_logs(self) -> None:
        config = BifrostConfig(setups={"lab": _minimal_setup()})

        result = config.to_dict()

        assert "logs" not in result["setups"]["lab"]

    def test_omits_none_runner(self) -> None:
        config = BifrostConfig(setups={"lab": _minimal_setup()})

        result = config.to_dict()

        assert "runner" not in result["setups"]["lab"]

    def test_includes_port_when_set(self) -> None:
        setup = SetupConfig(name="lab", host="10.0.0.1", user="ci", port=2222)
        config = BifrostConfig(setups={"lab": setup})

        result = config.to_dict()

        assert result["setups"]["lab"]["port"] == 2222

    def test_omits_none_port(self) -> None:
        config = BifrostConfig(setups={"lab": _minimal_setup()})

        result = config.to_dict()

        assert "port" not in result["setups"]["lab"]


class TestWriteConfigRoundTrip:
    def test_round_trip(self, tmp_path: Path, config_manager: ConfigManager) -> None:
        original = BifrostConfig(
            setups={
                "a": SetupConfig(name="a", host="1.2.3.4", user="u", runner="make"),
                "b": SetupConfig(name="b", host="5.6.7.8", user="v"),
            },
            default_setup="a",
            pipelines={
                "main": PipelineConfig(
                    url="https://gl.test", project_id=99, token_env="TOK"
                )
            },
        )
        target = tmp_path / "config.yml"

        config_manager.write_config(original, path=target)
        loaded = config_manager.read_config(target)

        assert loaded.default_setup == original.default_setup
        assert set(loaded.setups.keys()) == set(original.setups.keys())
        for name in original.setups:
            orig = original.setups[name]
            got = loaded.setups[name]
            assert got.host == orig.host
            assert got.user == orig.user
            assert got.runner == orig.runner
        assert "main" in loaded.pipelines
        assert loaded.pipelines["main"].project_id == 99

    def test_round_trip_with_port(
        self, tmp_path: Path, config_manager: ConfigManager
    ) -> None:
        original = BifrostConfig(
            setups={
                "a": SetupConfig(name="a", host="1.2.3.4", user="u", port=2222),
            },
        )
        target = tmp_path / "config.yml"

        config_manager.write_config(original, path=target)
        loaded = config_manager.read_config(target)

        assert loaded.setups["a"].port == 2222
