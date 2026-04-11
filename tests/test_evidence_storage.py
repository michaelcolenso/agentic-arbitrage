"""
Tests for persisted evidence records.
"""
import pytest
from datetime import datetime

from core.models import Evidence, OpportunityStatus, SiteStatus
from core.storage import Storage


@pytest.fixture
def temp_storage(tmp_path):
    db_path = tmp_path / "test_evidence.db"
    return Storage(str(db_path))


class TestEvidenceStorage:
    """Tests for evidence CRUD operations."""

    def test_save_and_retrieve_evidence(self, temp_storage):
        evidence = Evidence(
            evidence_type="discovery",
            opportunity_id="opp123",
            data={
                "source": "reddit",
                "url": "https://reddit.com/r/test",
                "snippet": "hard to find EV rebates",
                "engagement": 245,
                "theme": "ev_charger_rebates",
                "confidence": 0.8
            }
        )
        temp_storage.save_evidence(evidence)

        retrieved = temp_storage.get_evidence_for_opportunity("opp123")
        assert len(retrieved) == 1
        assert retrieved[0].evidence_type == "discovery"
        assert retrieved[0].data["source"] == "reddit"
        assert retrieved[0].data["engagement"] == 245

    def test_get_evidence_by_type(self, temp_storage):
        for etype in ["discovery", "discovery", "deployment"]:
            temp_storage.save_evidence(Evidence(evidence_type=etype, data={"test": True}))

        discovery = temp_storage.get_evidence_by_type("discovery")
        deployment = temp_storage.get_evidence_by_type("deployment")

        assert len(discovery) == 2
        assert len(deployment) == 1

    def test_get_evidence_for_site(self, temp_storage):
        temp_storage.save_evidence(Evidence(
            evidence_type="metrics",
            site_id="site456",
            data={"organic_users": 100}
        ))

        retrieved = temp_storage.get_evidence_for_site("site456")
        assert len(retrieved) == 1
        assert retrieved[0].data["organic_users"] == 100

    def test_evidence_types_supported(self, temp_storage):
        types = ["discovery", "data_probe", "keyword", "monetization", "deployment", "metrics"]
        for etype in types:
            temp_storage.save_evidence(Evidence(evidence_type=etype, data={"type": etype}))

        all_evidence = []
        for etype in types:
            all_evidence.extend(temp_storage.get_evidence_by_type(etype))

        assert len(all_evidence) == len(types)
