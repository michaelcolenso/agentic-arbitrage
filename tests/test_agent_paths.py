import importlib
from datetime import datetime
from pathlib import Path

import pytest

import agents.constructor as constructor_module
import agents.mortician as mortician_module
import config.settings as settings_module
from core.models import Site, SiteStatus
from core.storage import Storage


def reload_agent_modules():
    settings = importlib.reload(settings_module)
    constructor = importlib.reload(constructor_module)
    mortician = importlib.reload(mortician_module)
    return settings, constructor, mortician


@pytest.mark.asyncio
async def test_constructor_writes_project_under_configured_sites_dir(
    monkeypatch, tmp_path, validated_opportunity
):
    monkeypatch.setenv("FACTORY_DATA_DIR", str(tmp_path / "data"))
    settings, constructor, _ = reload_agent_modules()

    build_storage = Storage(str(tmp_path / "test_factory.db"))
    agent = constructor.Constructor(build_storage)
    site = Site(
        opportunity_id=validated_opportunity.id,
        name="Test Site",
        niche=validated_opportunity.niche,
        status=SiteStatus.BUILDING,
        created_at=datetime.now(),
    )

    project_path = await agent._create_project_files(
        site=site,
        opportunity=validated_opportunity,
        schema={"tables": []},
        adapters={"example": "export const adapter = true;\n"},
        templates={"home": "export default function Home() { return null; }\n"},
    )

    expected_path = settings.config.data_dir.parent / "sites" / site.id
    assert project_path == expected_path
    assert (project_path / "package.json").exists()
    assert (project_path / "src/app/home.tsx").exists()


@pytest.mark.asyncio
async def test_archiver_uses_configured_archive_and_site_paths(monkeypatch, tmp_path, sample_site):
    monkeypatch.setenv("FACTORY_DATA_DIR", str(tmp_path / "data"))
    settings, _, mortician = reload_agent_modules()

    archiver = mortician.SiteArchiver()

    site_code_dir = settings.config.data_dir.parent / "sites" / sample_site.id
    site_code_dir.mkdir(parents=True, exist_ok=True)
    (site_code_dir / "README.md").write_text("archived site code\n")

    decision = mortician.CullDecision(
        site_id=sample_site.id,
        should_cull=True,
        reason="test",
        days_active=91,
        avg_daily_traffic=0.0,
        total_revenue=0.0,
        recommendation="CULL",
    )

    result = await archiver.archive(sample_site, decision)

    expected_archive_dir = settings.config.data_dir.parent / "archive"
    assert Path(archiver.archive_base_path) == expected_archive_dir
    assert result.archived is True
    assert Path(result.data_path).parent == expected_archive_dir
    assert Path(result.code_path) == expected_archive_dir / f"{sample_site.id}_code"
    assert (Path(result.code_path) / "README.md").exists()
