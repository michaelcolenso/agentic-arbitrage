"""
Tests for manual metrics import.
"""
import pytest
from datetime import datetime
from pathlib import Path

from core.models import SiteMetrics
from core.storage import Storage


@pytest.fixture
def metrics_csv(tmp_path):
    csv_path = tmp_path / "metrics.csv"
    csv_path.write_text(
        "site_id,date,organic_users,pageviews,conversions,revenue,source\n"
        "site123,2026-04-01,100,300,5,12.50,google_analytics\n"
        "site123,2026-04-02,120,360,3,15.00,google_analytics\n"
        "site456,2026-04-01,50,150,1,5.00,cloudflare\n"
    )
    return csv_path


def test_import_metrics_from_csv(metrics_csv, tmp_path):
    storage = Storage(str(tmp_path / "test.db"))
    count = storage.import_metrics_from_csv(str(metrics_csv))
    
    assert count == 3
    
    site123_metrics = storage.get_site_metrics("site123")
    assert len(site123_metrics) == 2
    assert site123_metrics[0].organic_users == 120
    
    site456_metrics = storage.get_site_metrics("site456")
    assert len(site456_metrics) == 1
    assert site456_metrics[0].pageviews == 150
    
    # Should also create evidence records
    evidence = storage.get_evidence_for_site("site123")
    assert len(evidence) == 2
    assert evidence[0].evidence_type == "metrics"


def test_import_metrics_creates_correct_revenue(metrics_csv, tmp_path):
    storage = Storage(str(tmp_path / "test.db"))
    storage.import_metrics_from_csv(str(metrics_csv))
    
    metrics = storage.get_site_metrics("site123")
    total_revenue = sum(m.revenue for m in metrics)
    assert total_revenue == 27.50
