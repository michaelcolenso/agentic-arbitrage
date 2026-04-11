"""
Tests for explicit failed/rejected status transitions.
"""
import pytest
from datetime import datetime

from core.models import Opportunity, Site, OpportunityStatus, SiteStatus, FragmentationScore, MonetizationPotential
from core.storage import Storage


@pytest.fixture
def temp_storage(tmp_path):
    db_path = tmp_path / "test_status.db"
    return Storage(str(db_path))


class TestOpportunityStatusTransitions:
    """Tests that failed stages move to explicit failed statuses."""

    def test_validation_failure_moves_to_rejected(self, temp_storage):
        opp = Opportunity(niche="test", status=OpportunityStatus.VALIDATING)
        opp.status = OpportunityStatus.REJECTED
        temp_storage.save_opportunity(opp)

        retrieved = temp_storage.get_opportunity(opp.id)
        assert retrieved.status == OpportunityStatus.REJECTED

    def test_build_failure_moves_to_build_failed(self, temp_storage):
        opp = Opportunity(niche="test", status=OpportunityStatus.BUILDING)
        opp.status = OpportunityStatus.BUILD_FAILED
        temp_storage.save_opportunity(opp)

        retrieved = temp_storage.get_opportunity(opp.id)
        assert retrieved.status == OpportunityStatus.BUILD_FAILED

    def test_deployment_failure_moves_to_deployment_failed(self, temp_storage):
        opp = Opportunity(niche="test", status=OpportunityStatus.BUILDING)
        opp.status = OpportunityStatus.DEPLOYMENT_FAILED
        temp_storage.save_opportunity(opp)

        retrieved = temp_storage.get_opportunity(opp.id)
        assert retrieved.status == OpportunityStatus.DEPLOYMENT_FAILED

    def test_all_failed_statuses_persist_and_retrieve(self, temp_storage):
        for status in [OpportunityStatus.REJECTED, OpportunityStatus.BUILD_FAILED, OpportunityStatus.DEPLOYMENT_FAILED]:
            opp = Opportunity(niche=f"test_{status.value}", status=status)
            temp_storage.save_opportunity(opp)

            retrieved = temp_storage.get_opportunity(opp.id)
            assert retrieved.status == status


class TestSiteStatusTransitions:
    """Tests for site failed status."""

    def test_site_failed_status_persists(self, temp_storage):
        site = Site(name="Test Site", status=SiteStatus.FAILED)
        temp_storage.save_site(site)

        retrieved = temp_storage.get_site(site.id)
        assert retrieved.status == SiteStatus.FAILED
