"""
Tests that factory status and dashboard reflect persisted state truthfully.
"""
import pytest
from datetime import datetime

from factory import ArbitrageFactory
from core.models import Opportunity, Site, OpportunityStatus, SiteStatus, Evidence
from core.storage import Storage


@pytest.fixture
def factory_with_data(tmp_path):
    storage = Storage(str(tmp_path / "test.db"))
    factory = ArbitrageFactory()
    factory.storage = storage
    
    # Create EV opportunity
    opp = Opportunity(
        niche="ev_charger_rebates",
        status=OpportunityStatus.VALIDATED,
        validation_score=8.0
    )
    storage.save_opportunity(opp)
    
    # Create deployed EV site
    site = Site(
        opportunity_id=opp.id,
        niche="ev_charger_rebates",
        status=SiteStatus.DEPLOYED,
        deploy_url="https://ev-charger-rebates.pages.dev",
    )
    storage.save_site(site)
    
    # Add some evidence
    for etype in ["discovery", "deployment", "metrics"]:
        storage.save_evidence(Evidence(
            evidence_type=etype,
            site_id=site.id,
            data={"test": True}
        ))
    
    return factory


def test_status_derives_counts_from_persisted_data(factory_with_data):
    status = factory_with_data.get_status()
    
    assert status["opportunities"]["validated"] >= 1
    assert status["sites"]["deployed"] >= 1
    assert status["active_vertical"] == "ev_charger_rebates"


def test_status_includes_evidence_completeness(factory_with_data):
    status = factory_with_data.get_status()
    
    assert "evidence_completeness" in status
    assert status["evidence_completeness"] > 0
    assert "evidence_counts" in status
    assert status["evidence_counts"]["discovery"] >= 1
    assert status["evidence_counts"]["deployment"] >= 1


def test_status_includes_deployment_health(factory_with_data):
    status = factory_with_data.get_status()
    
    assert "deployment_health" in status
    assert status["deployment_health"]["deployed_count"] >= 1
    assert status["deployment_health"]["with_url"] >= 1


def test_status_ready_to_fund_when_criteria_met(factory_with_data):
    status = factory_with_data.get_status()
    
    # Should be ready because we have validated opp, deployed site, and evidence
    assert status["ready_to_fund"] is True


def test_status_not_ready_without_validated_opportunity(tmp_path):
    storage = Storage(str(tmp_path / "test.db"))
    factory = ArbitrageFactory()
    factory.storage = storage
    
    # Only a discovered opportunity, not validated
    opp = Opportunity(niche="ev_charger_rebates", status=OpportunityStatus.DISCOVERED)
    storage.save_opportunity(opp)
    
    status = factory.get_status()
    assert status["ready_to_fund"] is False
