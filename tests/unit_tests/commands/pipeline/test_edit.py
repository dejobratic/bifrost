from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

from bifrost.commands.pipeline import pipeline_app
from bifrost.di import Container
from bifrost.shared import BifrostConfig, PipelineConfig

runner = CliRunner()


@pytest.fixture
def mock_container() -> MagicMock:
    container = MagicMock(spec=Container)
    config_manager = MagicMock()
    config = BifrostConfig(
        setups={},
        pipelines={
            "my-pipeline": PipelineConfig(
                url="https://gitlab.example.com",
                project_id=123,
                token_env="GITLAB_TOKEN",
            )
        },
    )
    container.get_config_manager.return_value = config_manager
    container.get_config.return_value = config
    return container


class TestEditPipeline:
    def test_edits_existing_pipeline(self, mock_container: MagicMock) -> None:
        result = runner.invoke(
            pipeline_app,
            ["edit", "my-pipeline", "--url", "https://gitlab.new.com"],
            obj=mock_container,
        )

        assert result.exit_code == 0
        assert "updated successfully" in result.stdout
        mock_container.get_config_manager.return_value.write_config.assert_called_once()

    def test_rejects_unknown_pipeline(self, mock_container: MagicMock) -> None:
        result = runner.invoke(
            pipeline_app,
            ["edit", "nonexistent", "--url", "https://gitlab.new.com"],
            obj=mock_container,
        )

        assert result.exit_code == 3

    def test_edits_project_id(self, mock_container: MagicMock) -> None:
        result = runner.invoke(
            pipeline_app,
            ["edit", "my-pipeline", "--project-id", "456"],
            obj=mock_container,
        )

        assert result.exit_code == 0
        assert "updated successfully" in result.stdout
        config_manager = mock_container.get_config_manager.return_value
        config_manager.write_config.assert_called_once()
        written_config = config_manager.write_config.call_args[0][0]
        assert written_config.pipelines["my-pipeline"].project_id == 456

    def test_edits_token_env(self, mock_container: MagicMock) -> None:
        result = runner.invoke(
            pipeline_app,
            ["edit", "my-pipeline", "--token-env", "NEW_TOKEN"],
            obj=mock_container,
        )

        assert result.exit_code == 0
        assert "updated successfully" in result.stdout
        config_manager = mock_container.get_config_manager.return_value
        config_manager.write_config.assert_called_once()
        written_config = config_manager.write_config.call_args[0][0]
        assert written_config.pipelines["my-pipeline"].token_env == "NEW_TOKEN"

    def test_edits_multiple_fields(self, mock_container: MagicMock) -> None:
        result = runner.invoke(
            pipeline_app,
            [
                "edit",
                "my-pipeline",
                "--url",
                "https://gitlab.updated.com",
                "--project-id",
                "789",
                "--token-env",
                "UPDATED_TOKEN",
            ],
            obj=mock_container,
        )

        assert result.exit_code == 0
        assert "updated successfully" in result.stdout
        config_manager = mock_container.get_config_manager.return_value
        config_manager.write_config.assert_called_once()
        written_config = config_manager.write_config.call_args[0][0]
        pipeline = written_config.pipelines["my-pipeline"]
        assert pipeline.url == "https://gitlab.updated.com"
        assert pipeline.project_id == 789
        assert pipeline.token_env == "UPDATED_TOKEN"
