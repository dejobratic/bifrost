from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class ArtifactsConfig:
    remote_dir: str = ".bifrost"
    local_dir: str = ".bifrost"


@dataclass(frozen=True)
class SetupConfig:
    name: str
    host: str
    user: str
    runner: str | None = None
    artifacts: ArtifactsConfig = field(default_factory=ArtifactsConfig)


@dataclass(frozen=True)
class GitLabConfig:
    url: str
    project_id: int
    token_env: str


@dataclass(frozen=True)
class BifrostConfig:
    setups: dict[str, SetupConfig]
    default_setup: str | None = None
    gitlab: GitLabConfig | None = None


@dataclass(frozen=True)
class RunMetadata:
    run_id: str
    setup: str
    ref: str | None
    command: list[str]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    exit_code: int = 0
    artifact_paths: list[str] = field(default_factory=list)
