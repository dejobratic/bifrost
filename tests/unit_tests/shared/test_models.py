import pytest

from bifrost.shared import LogConfig, RunMetadata, SetupConfig


class TestSetupConfig:
    def test_creates_with_required_fields(self) -> None:
        setup = SetupConfig(name="lab-a", host="10.0.0.1", user="ci")

        assert setup.name == "lab-a"
        assert setup.host == "10.0.0.1"
        assert setup.user == "ci"
        assert setup.runner is None
        assert setup.logs == LogConfig()

    def test_is_immutable(self) -> None:
        setup = SetupConfig(name="lab-a", host="10.0.0.1", user="ci")

        with pytest.raises(AttributeError):
            setup.host = "changed"  # type: ignore[misc]

    def test_creates_with_port(self) -> None:
        setup = SetupConfig(name="lab-a", host="10.0.0.1", user="ci", port=2222)

        assert setup.port == 2222

    def test_port_is_optional(self) -> None:
        setup = SetupConfig(name="lab-a", host="10.0.0.1", user="ci")

        assert setup.port is None


class TestRunMetadata:
    def test_creates_with_defaults(self) -> None:
        meta = RunMetadata(
            run_id="abc123",
            setup="lab-a",
            ref="main",
            command=["pytest", "-m", "smoke"],
        )

        assert meta.run_id == "abc123"
        assert meta.exit_code == 0
        assert meta.log_paths == []
        assert meta.timestamp
