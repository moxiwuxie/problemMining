"""配置加载：YAML + 环境变量（含简易 .env 解析，避免额外依赖）。"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"
PROMPTS_DIR = PROJECT_ROOT / "prompts"
TEMPLATES_DIR = PROJECT_ROOT / "templates"

DEFAULT_SEARCH_DIMENSIONS = ["技术", "政策", "市场", "资本", "社会", "人才"]

DEFAULT_SCORE_WEIGHTS = {
    "difficulty": 0.25,
    "urgency": 0.25,
    "revenue_potential": 0.35,
    "cost": 0.15,
}


def _load_dotenv(path: Path) -> None:
    """把 .env 中的键值写入 os.environ（不覆盖已存在的变量）。"""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


class ProviderConfig(BaseModel):
    base_url: str
    model: str
    api_key_env: str = "LLM_API_KEY"
    supports_json_object: bool = True
    default_temperature: float = 0.4

    @property
    def api_key(self) -> str:
        return os.environ.get(self.api_key_env, "")


class ServerConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8770
    port_scan_limit: int = 50


class SearchConfig(BaseModel):
    enabled: bool = False
    provider: str = "tavily"
    api_key_env: str = "TAVILY_API_KEY"
    max_results_per_dimension: int = 3
    dimensions: List[str] = Field(default_factory=lambda: list(DEFAULT_SEARCH_DIMENSIONS))

    @property
    def api_key(self) -> str:
        return os.environ.get(self.api_key_env, "")


class Settings(BaseModel):
    default_provider: str = "deepseek"
    output_dir: str = "output"
    max_retries: int = 3
    retry_backoff_seconds: float = 1.0
    request_timeout: int = 120
    max_tokens: int = 4096
    max_evidence: int = 12
    max_inflections: int = 10
    max_problems: int = 15
    server: ServerConfig = Field(default_factory=ServerConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    score_weights: Dict[str, float] = Field(default_factory=lambda: dict(DEFAULT_SCORE_WEIGHTS))


def load_settings(path: Optional[Path] = None) -> Settings:
    _load_dotenv(PROJECT_ROOT / ".env")
    path = path or (CONFIG_DIR / "settings.yaml")
    data: Dict = {}
    if path.exists():
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    settings = Settings(**data)
    # 环境变量可覆盖默认 provider
    env_provider = os.environ.get("LLM_PROVIDER")
    if env_provider:
        settings.default_provider = env_provider
    return settings


def load_providers(path: Optional[Path] = None) -> Dict[str, ProviderConfig]:
    path = path or (CONFIG_DIR / "providers.yaml")
    if not path.exists():
        raise FileNotFoundError(f"缺少 provider 配置: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    raw = data.get("providers", {})
    return {name: ProviderConfig(**cfg) for name, cfg in raw.items()}


def resolve_provider(settings: Settings, override: Optional[str] = None) -> Tuple[str, ProviderConfig]:
    providers = load_providers()
    name = override or settings.default_provider
    if name not in providers:
        raise KeyError(f"未定义的 provider: {name}，可选: {', '.join(providers)}")
    return name, providers[name]
