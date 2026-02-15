from pathlib import Path

import pytest


@pytest.fixture
def tmp_config(tmp_path: Path):
    def _write(content: str) -> Path:
        config_file = tmp_path / ".bifrost.yml"
        config_file.write_text(content)
        return config_file

    return _write
