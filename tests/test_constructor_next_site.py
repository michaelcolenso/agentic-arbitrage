"""
Tests for Constructor Next.js EV charger site generation and build gate.
"""
import pytest
from datetime import datetime
from pathlib import Path

from agents.constructor import Constructor, EVChargerTemplateGenerator
from core.models import Opportunity, SiteStatus, OpportunityStatus
from core.storage import Storage


@pytest.fixture
def ev_opportunity():
    return Opportunity(
        niche="ev_charger_rebates",
        description="EV charger rebates database",
        status=OpportunityStatus.VALIDATED,
        pain_velocity=7.5,
        competition_gap=0.3,
        data_availability_score=8.5,
        pain_points=[],
        data_sources=[],
        keywords=[],
    )


@pytest.mark.asyncio
async def test_ev_template_generator_creates_required_routes():
    gen = EVChargerTemplateGenerator()
    templates = gen.generate()
    
    required = [
        "layout",
        "page",
        "ev-charger-rebates/page",
        "ev-charger-rebates/[state]/page",
        "ev-charger-tax-credit/page",
        "level-2-charger-rebate-checklist/page",
        "api/health/route",
        "robots",
        "sitemap",
        "next-config",
    ]
    for key in required:
        assert key in templates, f"Missing template: {key}"


def test_ev_templates_include_deadline_language():
    gen = EVChargerTemplateGenerator()
    templates = gen.generate()
    
    tax_credit = templates["ev-charger-tax-credit/page"]
    assert "June 30, 2026" in tax_credit
    assert "30C" in tax_credit
    
    checklist = templates["level-2-charger-rebate-checklist/page"]
    assert "ZIP" in checklist or "zip" in checklist.lower()
    assert "email" in checklist.lower()


@pytest.mark.asyncio
async def test_constructor_creates_nextjs_project_structure(monkeypatch, tmp_path, ev_opportunity):
    monkeypatch.setenv("FACTORY_MODE", "demo")
    import importlib
    import config.settings as settings_module
    import agents.constructor as constructor_module
    importlib.reload(settings_module)
    importlib.reload(constructor_module)
    
    storage = Storage(str(tmp_path / "test.db"))
    constructor = constructor_module.Constructor(storage)
    
    result = await constructor.build(ev_opportunity)
    
    assert result.success is True
    site = storage.get_site(result.site_id)
    assert site.status == SiteStatus.DEPLOYED
    
    project_path = settings_module.config.sites_dir / site.id
    assert (project_path / "package.json").exists()
    assert (project_path / "next.config.js").exists()
    assert (project_path / "public" / "robots.txt").exists()
    assert (project_path / "src" / "app" / "page.tsx").exists()
    assert (project_path / "src" / "app" / "ev-charger-rebates" / "page.tsx").exists()
    assert (project_path / "src" / "app" / "ev-charger-rebates" / "[state]" / "page.tsx").exists()
    assert (project_path / "src" / "app" / "api" / "health" / "route.ts").exists()
