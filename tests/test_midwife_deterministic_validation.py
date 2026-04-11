"""
Tests for deterministic validation probes and keyword snapshot support.
"""
import pytest
from pathlib import Path

from agents.midwife import FragmentationAnalyzer, KeywordValidator, Midwife
from core.models import Opportunity, DataSource, KeywordOpportunity, OpportunityStatus


@pytest.mark.asyncio
async def test_fragmentation_analyzer_records_probe_results():
    opp = Opportunity(
        niche="ev_charger_rebates",
        data_sources=[
            DataSource(
                name="AFDC",
                url="https://afdc.energy.gov/data_download",
                type="api",
                schema={"fields": ["state"]},
                update_frequency="monthly",
                quality_score=8.0,
                last_updated=None
            )
        ]
    )
    # Set last_updated to avoid serialization issues
    from datetime import datetime
    opp.data_sources[0].last_updated = datetime.now()
    
    analyzer = FragmentationAnalyzer()
    result = await analyzer.analyze(opp)
    
    assert result.sources_analyzed >= 0
    assert isinstance(result.score, float)


def reload_midwife_module(monkeypatch, mode: str):
    import importlib
    monkeypatch.setenv("FACTORY_MODE", mode)
    import config.settings as settings_module
    import agents.midwife as midwife_module
    importlib.reload(settings_module)
    importlib.reload(midwife_module)
    return midwife_module


def test_keyword_validator_loads_csv_snapshot(monkeypatch, tmp_path):
    import importlib
    import config.settings as settings_module
    import agents.midwife as midwife_module
    
    snapshot_path = Path(__file__).parent / "fixtures" / "ev_charger_keyword_snapshot.csv"
    monkeypatch.setenv("FACTORY_MODE", "demo")
    importlib.reload(settings_module)
    importlib.reload(midwife_module)
    
    # Set snapshot path AFTER reloading so it sticks
    settings_module.config.validation.keyword_snapshot_path = str(snapshot_path)
    
    validator = midwife_module.KeywordValidator()
    opp = Opportunity(
        niche="ev_charger_rebates",
        keywords=[
            KeywordOpportunity(keyword="ev charger rebates", monthly_volume=0, difficulty=0, cpc=0, intent="commercial", related_keywords=[]),
            KeywordOpportunity(keyword="unknown keyword", monthly_volume=0, difficulty=0, cpc=0, intent="informational", related_keywords=[]),
        ]
    )
    
    import asyncio
    result = asyncio.run(validator.validate(opp))
    
    assert result["snapshot_hits"] == 1
    assert result["total_volume"] > 0


def test_keyword_validator_empty_without_snapshot_in_non_demo(monkeypatch):
    monkeypatch.setattr("config.settings.config.validation.keyword_snapshot_path", None)
    midwife_module = reload_midwife_module(monkeypatch, "staging")
    
    validator = midwife_module.KeywordValidator()
    opp = Opportunity(
        niche="ev_charger_rebates",
        keywords=[
            KeywordOpportunity(keyword="ev charger rebates", monthly_volume=1000, difficulty=40, cpc=2.0, intent="commercial", related_keywords=[]),
        ]
    )
    
    import asyncio
    result = asyncio.run(validator.validate(opp))
    
    # Without snapshot in non-demo, opportunity score should be 0
    assert result["opportunity_score"] == 0.0


def test_midwife_gate_uses_production_threshold(monkeypatch, sample_opportunity, sample_fragmentation, sample_monetization):
    midwife_module = reload_midwife_module(monkeypatch, "production")
    
    midwife = midwife_module.Midwife()
    sample_opportunity.fragmentation = sample_fragmentation
    sample_opportunity.monetization = sample_monetization
    
    keyword_results = {
        "template_keywords": ["ev charger rebates in california"],
        "avg_difficulty": 30.0,
        "total_volume": 50000,
        "opportunity_score": 8.0,
        "snapshot_hits": 1,
        "snapshot_source": None,
    }
    
    # High overall score should pass
    assert midwife._passes_gate(sample_fragmentation, sample_monetization, keyword_results, 8.0) is True
    
    # Low overall score should fail in production (threshold 7.0)
    assert midwife._passes_gate(sample_fragmentation, sample_monetization, keyword_results, 6.5) is False
