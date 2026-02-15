from __future__ import annotations

from pathlib import Path

import pytest

from bifrost.core.config import load_config
from bifrost.core.configure import build_config, config_to_dict, write_config
from bifrost.core.errors import ConfigError
from bifrost.core.models import (
    ArtifactsConfig,
    BifrostConfig,
    GitLabConfig,
    SetupConfig,
)


def _minimal_setup(name: str = "lab") -> SetupConfig:
    return SetupConfig(name=name, host="10.0.0.1", user="ci")


def _full_setup(name: str = "office") -> SetupConfig:
    return SetupConfig(
        name=name,
        host="10.0.0.5",
        user="ci",
        runner="pytest",
        artifacts=ArtifactsConfig(remote_dir="build/out", local_dir="local/out"),
    )


class TestConfigToDict:
    def test_minimal(self) -> None:
        config = BifrostConfig(setups={"lab": _minimal_setup()})

        result = config_to_dict(config)

        assert result["version"] == 1
        assert result["setups"]["lab"] == {"host": "10.0.0.1", "user": "ci"}
        assert "defaults" not in result
        assert "gitlab" not in result

    def test_full(self) -> None:
        config = BifrostConfig(
            setups={"office": _full_setup()},
            default_setup="office",
            gitlab=GitLabConfig(
                url="https://gitlab.example.com",
                project_id=42,
                token_env="GL_TOKEN",
            ),
        )

        result = config_to_dict(config)

        assert result["defaults"] == {"setup": "office"}
        assert result["gitlab"]["project_id"] == 42
        setup = result["setups"]["office"]
        assert setup["runner"] == "pytest"
        assert setup["artifacts"]["remote_dir"] == "build/out"

    def test_omits_default_artifacts(self) -> None:
        config = BifrostConfig(setups={"lab": _minimal_setup()})

        result = config_to_dict(config)

        assert "artifacts" not in result["setups"]["lab"]

    def test_omits_none_runner(self) -> None:
        config = BifrostConfig(setups={"lab": _minimal_setup()})

        result = config_to_dict(config)

        assert "runner" not in result["setups"]["lab"]


class TestBuildConfig:
    def test_valid(self) -> None:
        setups = {"lab": _minimal_setup()}

        config = build_config(setups, default_setup="lab")

        assert config.default_setup == "lab"
        assert "lab" in config.setups

    def test_empty_setups_raises(self) -> None:
        with pytest.raises(ConfigError, match="At least one setup"):
            build_config({})

    def test_invalid_default_raises(self) -> None:
        with pytest.raises(ConfigError, match="not found in setups"):
            build_config({"lab": _minimal_setup()}, default_setup="nope")


class TestWriteConfigRoundTrip:
    def test_round_trip(self, tmp_path: Path) -> None:
        original = BifrostConfig(
            setups={
                "a": SetupConfig(name="a", host="1.2.3.4", user="u", runner="make"),
                "b": SetupConfig(name="b", host="5.6.7.8", user="v"),
            },
            default_setup="a",
            gitlab=GitLabConfig(url="https://gl.test", project_id=99, token_env="TOK"),
        )
        target = tmp_path / "config.yml"

        write_config(original, path=target)
        loaded = load_config(target)

        assert loaded.default_setup == original.default_setup
        assert set(loaded.setups.keys()) == set(original.setups.keys())
        for name in original.setups:
            orig = original.setups[name]
            got = loaded.setups[name]
            assert got.host == orig.host
            assert got.user == orig.user
            assert got.runner == orig.runner
        assert loaded.gitlab is not None
        assert loaded.gitlab.project_id == 99
