import pytest

from bifrost.core.config import find_config_file, load_config
from bifrost.core.errors import ConfigError

VALID_CONFIG = """\
version: 1

defaults:
  setup: office-a

gitlab:
  url: "https://gitlab.example.com"
  project_id: 12345
  token_env: "GITLAB_TOKEN"

setups:
  office-a:
    host: "10.0.0.5"
    user: "ci"
    runner: "pytest"
    artifacts:
      remote_dir: ".bifrost"
      local_dir: ".bifrost/office-a"

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


class TestFindConfigFile:
    def test_finds_bifrost_yml_in_directory(self, tmp_path):
        # Arrange
        config = tmp_path / ".bifrost.yml"
        config.write_text("version: 1")

        # Act
        result = find_config_file(tmp_path)

        # Assert
        assert result == config

    def test_raises_when_no_config_found(self, tmp_path):
        # Act / Assert
        with pytest.raises(ConfigError, match="No config file found"):
            find_config_file(tmp_path)


class TestLoadConfig:
    def test_loads_valid_full_config(self, tmp_config):
        # Arrange
        path = tmp_config(VALID_CONFIG)

        # Act
        config = load_config(path)

        # Assert
        assert config.default_setup == "office-a"
        assert "office-a" in config.setups
        assert "office-b" in config.setups
        assert config.setups["office-a"].host == "10.0.0.5"
        assert config.setups["office-a"].user == "ci"
        assert config.setups["office-a"].runner == "pytest"
        assert config.setups["office-a"].artifacts.remote_dir == ".bifrost"
        assert config.gitlab is not None
        assert config.gitlab.project_id == 12345
        assert config.gitlab.token_env == "GITLAB_TOKEN"

    def test_loads_minimal_config(self, tmp_config):
        # Arrange
        path = tmp_config(MINIMAL_CONFIG)

        # Act
        config = load_config(path)

        # Assert
        assert config.default_setup is None
        assert config.gitlab is None
        assert config.setups["lab"].host == "192.168.1.1"

    def test_defaults_artifact_local_dir_to_setup_name(self, tmp_config):
        # Arrange
        path = tmp_config(MINIMAL_CONFIG)

        # Act
        config = load_config(path)

        # Assert
        assert config.setups["lab"].artifacts.local_dir == ".bifrost/lab"

    def test_rejects_invalid_yaml(self, tmp_config):
        # Arrange
        path = tmp_config(": invalid: yaml: [")

        # Act / Assert
        with pytest.raises(ConfigError, match="Invalid YAML"):
            load_config(path)

    def test_rejects_wrong_version(self, tmp_config):
        # Arrange
        path = tmp_config("version: 99\nsetups:\n  x:\n    host: h\n    user: u")

        # Act / Assert
        with pytest.raises(ConfigError, match="Unsupported config version"):
            load_config(path)

    def test_rejects_missing_setups(self, tmp_config):
        # Arrange
        path = tmp_config("version: 1")

        # Act / Assert
        with pytest.raises(ConfigError, match="No setups defined"):
            load_config(path)

    def test_rejects_setup_without_host(self, tmp_config):
        # Arrange
        path = tmp_config("version: 1\nsetups:\n  bad:\n    user: ci")

        # Act / Assert
        with pytest.raises(ConfigError, match="must have 'host' and 'user'"):
            load_config(path)

    def test_rejects_invalid_default_setup(self, tmp_config):
        # Arrange
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

        # Act / Assert
        with pytest.raises(ConfigError, match="Default setup 'nonexistent' not found"):
            load_config(path)

    def test_rejects_incomplete_gitlab(self, tmp_config):
        # Arrange
        config_text = """\
version: 1
gitlab:
  url: "https://gitlab.example.com"
setups:
  lab:
    host: "1.2.3.4"
    user: "ci"
"""
        path = tmp_config(config_text)

        # Act / Assert
        with pytest.raises(ConfigError, match="GitLab config requires"):
            load_config(path)
