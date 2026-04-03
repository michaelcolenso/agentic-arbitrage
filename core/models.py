"""
Data Models for Agentic Arbitrage Factory
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid

class OpportunityStatus(Enum):
    DISCOVERED = "discovered"
    VALIDATING = "validating"
    VALIDATED = "validated"
    BUILDING = "building"
    DEPLOYED = "deployed"
    MONITORING = "monitoring"
    WINNER = "winner"
    CULLED = "culled"
    ARCHIVED = "archived"

class SiteStatus(Enum):
    PENDING = "pending"
    BUILDING = "building"
    DEPLOYED = "deployed"
    INDEXING = "indexing"
    MONITORING = "monitoring"
    RANKING = "ranking"
    PROFITABLE = "profitable"
    CULLED = "culled"

@dataclass
class PainPoint:
    """Represents a detected pain point from user complaints"""
    source: str  # reddit, forum, etc.
    text: str
    sentiment_score: float
    engagement: int
    keywords: List[str]
    timestamp: datetime
    url: Optional[str] = None

@dataclass
class DataSource:
    """Represents an available data source"""
    name: str
    url: str
    type: str  # api, scrape, dataset
    schema: Dict[str, Any]
    update_frequency: str
    quality_score: float
    last_updated: datetime

@dataclass
class KeywordOpportunity:
    """Represents a keyword opportunity"""
    keyword: str
    monthly_volume: int
    difficulty: float
    cpc: float
    intent: str
    related_keywords: List[str]
    trending: bool = False

@dataclass
class FragmentationScore:
    """Fragmentation analysis result"""
    score: float  # 0-1, lower is more fragmented
    data_points_found: int
    sources_analyzed: int
    consistency_rating: float
    automation_potential: float

@dataclass
class MonetizationPotential:
    """Monetization analysis"""
    score: float  # 0-10
    affiliate_programs: List[Dict[str, Any]]
    lead_gen_potential: float
    ad_potential: float
    subscription_potential: float
    estimated_monthly_revenue: float

@dataclass
class Opportunity:
    """Main opportunity entity"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    niche: str = ""
    description: str = ""
    status: OpportunityStatus = OpportunityStatus.DISCOVERED
    
    # Discovery metrics
    pain_velocity: float = 0.0
    competition_gap: float = 0.0
    data_availability_score: float = 0.0
    
    # Related entities
    pain_points: List[PainPoint] = field(default_factory=list)
    data_sources: List[DataSource] = field(default_factory=list)
    keywords: List[KeywordOpportunity] = field(default_factory=list)
    
    # Validation results
    fragmentation: Optional[FragmentationScore] = None
    monetization: Optional[MonetizationPotential] = None
    validation_score: float = 0.0
    validated_at: Optional[datetime] = None
    
    # Build info
    site_id: Optional[str] = None
    repo_url: Optional[str] = None
    deployed_url: Optional[str] = None
    built_at: Optional[datetime] = None
    
    # Tracking
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def calculate_validation_score(self) -> float:
        """Calculate overall validation score (0-10)"""
        if not self.fragmentation or not self.monetization:
            return 0.0
        
        # Formula: average of automation_potential and monetization_score
        auto_score = self.fragmentation.automation_potential
        mono_score = self.monetization.score
        
        self.validation_score = (auto_score + mono_score) / 2
        return self.validation_score

@dataclass
class SiteMetrics:
    """Performance metrics for a deployed site"""
    site_id: str
    date: datetime
    
    # Traffic
    organic_users: int = 0
    total_users: int = 0
    pageviews: int = 0
    avg_session_duration: float = 0.0
    bounce_rate: float = 0.0
    
    # SEO
    indexed_pages: int = 0
    ranking_keywords: int = 0
    avg_position: float = 0.0
    backlinks: int = 0
    
    # Revenue
    revenue: float = 0.0
    affiliate_revenue: float = 0.0
    lead_gen_revenue: float = 0.0
    ad_revenue: float = 0.0

@dataclass
class Site:
    """Represents a deployed SEO site"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    opportunity_id: str = ""
    name: str = ""
    domain: str = ""
    niche: str = ""
    
    # Status
    status: SiteStatus = SiteStatus.PENDING
    
    # Technical
    repo_url: Optional[str] = None
    deploy_url: Optional[str] = None
    cloudflare_project_id: Optional[str] = None
    
    # Content
    data_schema: Dict[str, Any] = field(default_factory=dict)
    page_count: int = 0
    
    # Performance tracking
    metrics_history: List[SiteMetrics] = field(default_factory=list)
    
    # Lifecycle
    created_at: datetime = field(default_factory=datetime.now)
    deployed_at: Optional[datetime] = None
    last_evaluated: Optional[datetime] = None
    culled_at: Optional[datetime] = None
    
    def get_latest_metrics(self) -> Optional[SiteMetrics]:
        if not self.metrics_history:
            return None
        return sorted(self.metrics_history, key=lambda x: x.date, reverse=True)[0]
    
    def get_avg_daily_traffic(self, days: int = 7) -> float:
        """Get average daily traffic over last N days"""
        if not self.metrics_history:
            return 0.0
        recent = sorted(self.metrics_history, key=lambda x: x.date, reverse=True)[:days]
        if not recent:
            return 0.0
        return sum(m.organic_users for m in recent) / len(recent)

@dataclass
class FactoryStats:
    """Overall factory statistics"""
    total_opportunities: int = 0
    validated_opportunities: int = 0
    active_sites: int = 0
    winner_sites: int = 0
    culled_sites: int = 0
    
    total_revenue: float = 0.0
    total_mrr: float = 0.0
    portfolio_value: float = 0.0
    
    avg_build_time_minutes: float = 0.0
    avg_validation_time_hours: float = 0.0
    success_rate: float = 0.0
    
    last_updated: datetime = field(default_factory=datetime.now)
