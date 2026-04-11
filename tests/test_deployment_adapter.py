"""
Tests for deployment adapters and health checks.
"""
import pytest
from pathlib import Path

from agents.constructor import DemoDeploymentAdapter, LocalDeploymentAdapter, CloudflareDeploymentAdapter
from core.models import Site


@pytest.mark.asyncio
async def test_demo_adapter_returns_fake_url():
    adapter = DemoDeploymentAdapter()
    site = Site(niche="ev_charger_rebates")
    result = await adapter.deploy(site, Path("/tmp/fake"))
    assert result["url"].endswith(".pages.dev")
    assert result["adapter"] == "demo"


@pytest.mark.asyncio
async def test_local_adapter_copies_files(tmp_path):
    adapter = LocalDeploymentAdapter()
    site = Site(niche="ev_charger_rebates")
    
    project_path = tmp_path / "project"
    project_path.mkdir()
    (project_path / "dist").mkdir()
    (project_path / "dist" / "index.html").write_text("<html></html>")
    
    result = await adapter.deploy(site, project_path)
    
    assert result["url"].startswith("file://")
    assert result["adapter"] == "local"
    
    deploy_dir = Path(result["url"].replace("file://", ""))
    assert (deploy_dir / "index.html").exists()
    
    healthy = await adapter.health_check(result["url"])
    assert healthy is True


@pytest.mark.asyncio
async def test_local_adapter_health_check_fails_for_missing_index():
    adapter = LocalDeploymentAdapter()
    healthy = await adapter.health_check("file:///nonexistent/path")
    assert healthy is False


def test_constructor_selects_adapter_by_mode(monkeypatch):
    import importlib
    import config.settings as settings_module
    import agents.constructor as constructor_module
    
    # Demo mode
    monkeypatch.setenv("FACTORY_MODE", "demo")
    importlib.reload(settings_module)
    importlib.reload(constructor_module)
    
    constructor = constructor_module.Constructor()
    assert isinstance(constructor._get_deployment_adapter(), constructor_module.DemoDeploymentAdapter)
    
    # Staging mode
    monkeypatch.setenv("FACTORY_MODE", "staging")
    importlib.reload(settings_module)
    importlib.reload(constructor_module)
    
    constructor = constructor_module.Constructor()
    assert isinstance(constructor._get_deployment_adapter(), constructor_module.LocalDeploymentAdapter)
    
    # Production mode
    monkeypatch.setenv("FACTORY_MODE", "production")
    importlib.reload(settings_module)
    importlib.reload(constructor_module)
    
    constructor = constructor_module.Constructor()
    assert isinstance(constructor._get_deployment_adapter(), constructor_module.CloudflareDeploymentAdapter)
