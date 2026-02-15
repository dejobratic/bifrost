from bifrost.core.models import ArtifactsConfig, RunMetadata, SetupConfig


class TestSetupConfig:
    def test_creates_with_required_fields(self):
        # Arrange / Act
        setup = SetupConfig(name="lab-a", host="10.0.0.1", user="ci")

        # Assert
        assert setup.name == "lab-a"
        assert setup.host == "10.0.0.1"
        assert setup.user == "ci"
        assert setup.runner is None
        assert setup.artifacts == ArtifactsConfig()

    def test_is_immutable(self):
        # Arrange
        setup = SetupConfig(name="lab-a", host="10.0.0.1", user="ci")

        # Act / Assert
        try:
            setup.host = "changed"  # type: ignore[misc]
            assert False, "Should have raised"
        except AttributeError:
            pass


class TestRunMetadata:
    def test_creates_with_defaults(self):
        # Arrange / Act
        meta = RunMetadata(
            run_id="abc123",
            setup="lab-a",
            ref="main",
            command=["pytest", "-m", "smoke"],
        )

        # Assert
        assert meta.run_id == "abc123"
        assert meta.exit_code == 0
        assert meta.artifact_paths == []
        assert meta.timestamp  # not empty
