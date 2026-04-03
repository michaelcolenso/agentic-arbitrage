"""
Agentic Arbitrage Factory - Configuration Settings
"""
import os
from dataclasses import dataclass, field
from typing import List, Dict, Any
from pathlib import Path

@dataclass
class DiscoveryConfig:
    """Configuration for The Red Queen (Discovery Agent)"""
    reddit_subreddits: List[str] = field(default_factory=lambda: [
        "personalfinance", "smallbusiness", "realestateinvesting",
        "legaladvice", "government", "dataisbeautiful", "webdev"
    ])
    google_trends_geo: str = "US"
    data_gov_datasets: List[str] = field(default_factory=lambda: [
        "recalls", "patents", "clinical-trials", "contract-data",
        "usajobs", "grants", "small-business"
    ])
    pain_velocity_threshold: float = 2.0
    competition_gap_threshold: float = 0.8
    min_monthly_searches: int = 100
    max_keyword_difficulty: int = 60

@dataclass
class ValidationConfig:
    """Configuration for The Midwife (Validation Agent)"""
    test_sample_size: int = 10
    fragmentation_threshold: float = 0.9  # More lenient
    min_automation_score: float = 4.0  # More lenient
    min_monetization_score: float = 4.0  # More lenient
    validation_timeout_hours: int = 48
    affiliate_check_domains: List[str] = field(default_factory=lambda: [
        "amazon.com", "shareasale.com", "cj.com", "impact.com"
    ])

@dataclass
class BuildConfig:
    """Configuration for The Constructor (Build Agent)"""
    template_repo: str = "template-seo-site"
    stack: Dict[str, str] = field(default_factory=lambda: {
        "framework": "hono",
        "database": "d1",
        "styling": "tailwind",
        "orm": "drizzle"
    })
    build_timeout_minutes: int = 5
    deploy_target: str = "cloudflare"
    auto_submit_search_console: bool = True

@dataclass
class CullingConfig:
    """Configuration for The Mortician (Culling Agent)"""
    traffic_threshold_per_day: int = 100
    evaluation_days: int = 90
    auto_301_to_winner: bool = True
    archive_data: bool = True
    recycle_codebase: bool = True

@dataclass
class MonetizationConfig:
    """Configuration for monetization tracking"""
    revenue_streams: List[str] = field(default_factory=lambda: [
        "affiliate", "lead_gen", "ads", "subscription"
    ])
    min_mrr_threshold: int = 100
    portfolio_valuation_multiple: float = 40.0

@dataclass
class FactoryConfig:
    """Main factory configuration"""
    project_name: str = "AgenticArbitrageFactory"
    data_dir: Path = field(default_factory=lambda: Path("/mnt/okcomputer/output/agentic_arbitrage_factory/data"))
    log_level: str = "INFO"
    max_concurrent_sites: int = 50
    discovery_interval_hours: int = 24
    
    # Sub-configs
    discovery: DiscoveryConfig = field(default_factory=DiscoveryConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    build: BuildConfig = field(default_factory=BuildConfig)
    culling: CullingConfig = field(default_factory=CullingConfig)
    monetization: MonetizationConfig = field(default_factory=MonetizationConfig)
    
    # API Keys (load from environment)
    @property
    def openai_api_key(self) -> str:
        return os.getenv("OPENAI_API_KEY", "")
    
    @property
    def reddit_client_id(self) -> str:
        return os.getenv("REDDIT_CLIENT_ID", "")
    
    @property
    def reddit_client_secret(self) -> str:
        return os.getenv("REDDIT_CLIENT_SECRET", "")
    
    @property
    def ahrefs_api_key(self) -> str:
        return os.getenv("AHREFS_API_KEY", "")
    
    @property
    def cloudflare_api_token(self) -> str:
        return os.getenv("CLOUDFLARE_API_TOKEN", "")
    
    @property
    def github_token(self) -> str:
        return os.getenv("GITHUB_TOKEN", "")

# Global config instance
config = FactoryConfig()
