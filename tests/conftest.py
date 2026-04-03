"""
Pytest configuration and fixtures for Agentic Arbitrage Factory tests.
"""
import pytest
import asyncio
from datetime import datetime
from pathlib import Path
import tempfile
import shutil

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.models import (
    Opportunity, Site, PainPoint, DataSource, KeywordOpportunity,
    FragmentationScore, MonetizationPotential, OpportunityStatus, SiteStatus
)
from core.storage import Storage


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def storage():
    """Create a temporary storage instance for testing."""
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_factory.db"
    
    storage = Storage(str(db_path))
    
    yield storage
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_pain_point():
    """Create a sample pain point."""
    return PainPoint(
        source="reddit:r/test",
        text="Why is it so hard to find EV charger rebates?",
        sentiment_score=-0.7,
        engagement=245,
        keywords=["ev charger", "rebates", "hard to find"],
        timestamp=datetime.now(),
        url="https://reddit.com/r/test/comments/123"
    )


@pytest.fixture
def sample_data_source():
    """Create a sample data source."""
    return DataSource(
        name="EV Charging Station Rebates Database",
        url="https://afdc.energy.gov/data_download",
        type="api",
        schema={
            "fields": ["state", "rebate_amount", "eligible_vehicles"],
            "description": "Database of EV charging station rebates by state"
        },
        update_frequency="monthly",
        quality_score=8.5,
        last_updated=datetime.now()
    )


@pytest.fixture
def sample_keywords():
    """Create sample keyword opportunities."""
    return [
        KeywordOpportunity(
            keyword="ev charger rebates",
            monthly_volume=1000,
            difficulty=45,
            cpc=2.5,
            intent="commercial",
            related_keywords=["electric vehicle rebates", "ev incentives"],
            trending=True
        ),
        KeywordOpportunity(
            keyword="ev charger rebates near me",
            monthly_volume=800,
            difficulty=48,
            cpc=3.0,
            intent="transactional",
            related_keywords=["local ev rebates", "state ev incentives"],
            trending=False
        ),
        KeywordOpportunity(
            keyword="best ev charger rebates",
            monthly_volume=600,
            difficulty=50,
            cpc=2.8,
            intent="commercial",
            related_keywords=["top ev rebates", "compare ev incentives"],
            trending=True
        )
    ]


@pytest.fixture
def sample_fragmentation():
    """Create a sample fragmentation score."""
    return FragmentationScore(
        score=0.3,
        data_points_found=150,
        sources_analyzed=5,
        consistency_rating=0.8,
        automation_potential=7.5
    )


@pytest.fixture
def sample_monetization():
    """Create a sample monetization potential."""
    return MonetizationPotential(
        score=7.0,
        affiliate_programs=[
            {"name": "ChargePoint", "commission": "$50-100/sale", "network": "Direct"},
            {"name": "Amazon Associates", "commission": "4%", "network": "Amazon"}
        ],
        lead_gen_potential=7.5,
        ad_potential=6.0,
        subscription_potential=4.0,
        estimated_monthly_revenue=150.0
    )


@pytest.fixture
def sample_opportunity(sample_pain_point, sample_data_source, sample_keywords):
    """Create a sample opportunity."""
    opp = Opportunity(
        niche="ev_charger_rebates",
        description="Users struggle to find EV charger rebates in one place",
        status=OpportunityStatus.DISCOVERED,
        pain_velocity=7.5,
        competition_gap=0.3,
        data_availability_score=8.5,
        pain_points=[sample_pain_point],
        data_sources=[sample_data_source],
        keywords=sample_keywords
    )
    return opp


@pytest.fixture
def validated_opportunity(sample_opportunity, sample_fragmentation, sample_monetization):
    """Create a validated sample opportunity."""
    sample_opportunity.fragmentation = sample_fragmentation
    sample_opportunity.monetization = sample_monetization
    sample_opportunity.status = OpportunityStatus.VALIDATED
    sample_opportunity.validation_score = 7.25
    sample_opportunity.validated_at = datetime.now()
    return sample_opportunity


@pytest.fixture
def sample_site(validated_opportunity):
    """Create a sample site."""
    return Site(
        opportunity_id=validated_opportunity.id,
        name="EV Charger Rebates",
        domain="ev-charger-rebates.com",
        niche="ev_charger_rebates",
        status=SiteStatus.DEPLOYED,
        deploy_url="https://ev-charger-rebates.pages.dev",
        page_count=200,
        created_at=datetime.now(),
        deployed_at=datetime.now()
    )
