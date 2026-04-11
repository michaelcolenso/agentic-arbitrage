"""
Tests that Mortician does not cull based on fabricated traffic outside demo mode.
"""
import pytest
from datetime import datetime, timedelta

from agents.mortician import PerformanceAnalyzer
from core.models import Site, SiteStatus
from core.storage import Storage


def test_no_metrics_in_staging_returns_metrics_unavailable(monkeypatch, tmp_path):
    import importlib
    import config.settings as settings_module
    import agents.mortician as mortician_module
    
    monkeypatch.setenv("FACTORY_MODE", "staging")
    importlib.reload(settings_module)
    importlib.reload(mortician_module)
    
    storage = Storage(str(tmp_path / "test.db"))
    analyzer = mortician_module.PerformanceAnalyzer()
    
    site = Site(
        id="site_no_metrics",
        niche="ev_charger_rebates",
        status=SiteStatus.DEPLOYED,
        deployed_at=datetime.now() - timedelta(days=100)
    )
    storage.save_site(site)
    
    decision = analyzer.analyze(site, None)
    
    assert decision.should_cull is False
    assert decision.recommendation == "METRICS_UNAVAILABLE"
    assert decision.reason == "No real metrics available"


def test_demo_mode_falls_back_to_mock_metrics(monkeypatch, tmp_path):
    import importlib
    import config.settings as settings_module
    import agents.mortician as mortician_module
    
    monkeypatch.setenv("FACTORY_MODE", "demo")
    importlib.reload(settings_module)
    importlib.reload(mortician_module)
    
    storage = Storage(str(tmp_path / "test.db"))
    analyzer = mortician_module.PerformanceAnalyzer()
    
    site = Site(
        id="site_demo",
        niche="ev_charger_rebates",
        status=SiteStatus.DEPLOYED,
        deployed_at=datetime.now() - timedelta(days=100),
        page_count=200
    )
    storage.save_site(site)
    
    import asyncio
    monitor = mortician_module.TrafficMonitor()
    metrics = asyncio.run(monitor.get_metrics(site))
    
    assert metrics is not None
    assert metrics.organic_users > 0
