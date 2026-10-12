import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pytest  # noqa: E402

from trendminer.config import Settings  # noqa: E402
from trendminer.llm.mock import MockLLMClient  # noqa: E402
from trendminer.models import TopicInput  # noqa: E402


@pytest.fixture
def sample_topic() -> TopicInput:
    return TopicInput(topic="AI编程", industry="软件", horizon_years=5, scenario_count=4)


@pytest.fixture
def settings(tmp_path) -> Settings:
    cfg = Settings()
    cfg.output_dir = str(tmp_path / "output")
    cfg.retry_backoff_seconds = 0.0
    return cfg


@pytest.fixture
def mock_client(settings) -> MockLLMClient:
    return MockLLMClient(settings, seed=7)
