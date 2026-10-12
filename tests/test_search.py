from trendminer.config import SearchConfig, Settings
from trendminer.search import build_search
from trendminer.search.base import NullSearch
from trendminer.search.tavily import TavilySearch


def test_search_disabled_returns_null_backend():
    backend = build_search(Settings())
    assert isinstance(backend, NullSearch)
    assert backend.available is False
    assert backend.degraded_reason


def test_tavily_missing_key_degrades(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    settings = Settings(search=SearchConfig(enabled=True, provider="tavily"))
    backend = build_search(settings)
    assert isinstance(backend, NullSearch)
    assert "TAVILY_API_KEY" in backend.degraded_reason


def test_tavily_enabled_with_key(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")
    settings = Settings(search=SearchConfig(enabled=True, provider="tavily"))
    backend = build_search(settings)
    assert isinstance(backend, TavilySearch)
    assert backend.available is True


def test_unknown_provider_degrades():
    settings = Settings(search=SearchConfig(enabled=True, provider="bing"))
    backend = build_search(settings)
    assert isinstance(backend, NullSearch)


def test_s1_marks_evidence_as_prior_when_search_offline(settings, sample_topic):
    from trendminer.context import PipelineContext
    from trendminer.llm.mock import MockLLMClient
    from trendminer.pipeline import s1_retrieval
    from trendminer.prompts import PromptLoader

    ctx = PipelineContext("run-x", settings.output_dir)
    llm = MockLLMClient(settings, seed=1)
    result = s1_retrieval.run(ctx, llm, PromptLoader(), sample_topic, settings)

    assert all(e.source_type == "先验" for e in [*result.old_era, *result.new_era])
    assert any("降级" in w or "先验" in w for w in ctx.warnings)
