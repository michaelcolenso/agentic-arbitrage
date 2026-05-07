"""
Agentic Arbitrage Factory - Web Dashboard

FastAPI-based web dashboard for monitoring the factory.
Run with:
    uv run --extra dashboard python web_dashboard.py
"""
import json
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from core.storage import Storage
from core.models import Opportunity, Site, SiteMetrics, FactoryStats, OpportunityStatus, SiteStatus

# Setup paths
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"

# Ensure templates dir exists
TEMPLATES_DIR.mkdir(exist_ok=True)

# Setup FastAPI
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
templates.env.cache = None  # Workaround for Python 3.14 / Jinja2 3.1.6
storage = Storage()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager"""
    yield


app = FastAPI(
    title="Agentic Arbitrage Factory",
    description="Monitoring dashboard for the SEO site factory",
    version="0.1.0",
    lifespan=lifespan,
)


# ── Helpers ──────────────────────────────────────────────

def _status_color(status: str) -> str:
    """Map status to Tailwind color class"""
    colors = {
        "discovered": "bg-gray-100 text-gray-800",
        "validating": "bg-yellow-100 text-yellow-800",
        "validated": "bg-blue-100 text-blue-800",
        "rejected": "bg-red-100 text-red-800",
        "building": "bg-purple-100 text-purple-800",
        "build_failed": "bg-red-100 text-red-800",
        "deployed": "bg-green-100 text-green-800",
        "deployment_failed": "bg-red-100 text-red-800",
        "monitoring": "bg-blue-100 text-blue-800",
        "winner": "bg-emerald-100 text-emerald-800",
        "culled": "bg-gray-100 text-gray-800",
        "archived": "bg-gray-100 text-gray-800",
        # Site statuses
        "pending": "bg-gray-100 text-gray-800",
        "indexing": "bg-yellow-100 text-yellow-800",
        "ranking": "bg-blue-100 text-blue-800",
        "profitable": "bg-emerald-100 text-emerald-800",
        "failed": "bg-red-100 text-red-800",
    }
    return colors.get(status.lower(), "bg-gray-100 text-gray-800")


def _get_status_counts() -> Dict[str, Any]:
    """Get aggregate status counts"""
    opportunities = storage.get_all_opportunities()
    sites = storage.get_all_sites()
    stats = storage.get_stats()

    opp_statuses = {}
    for o in opportunities:
        opp_statuses[o.status.value] = opp_statuses.get(o.status.value, 0) + 1

    site_statuses = {}
    for s in sites:
        site_statuses[s.status.value] = site_statuses.get(s.status.value, 0) + 1

    return {
        "opportunities": opportunities,
        "sites": sites,
        "stats": stats,
        "opp_statuses": opp_statuses,
        "site_statuses": site_statuses,
        "recent_opportunities": opportunities[:10],
        "recent_sites": sites[:10],
    }


# ── Routes ───────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def dashboard_index(request: Request):
    data = _get_status_counts()
    stats = data["stats"]
    opportunities = data["opportunities"]
    sites = data["sites"]

    # Calculate additional metrics
    total_revenue = sum(
        (m.revenue for s in sites for m in s.metrics_history), 0.0
    )

    # Site metrics over time (for chart)
    site_metrics_chart = []
    for site in sites[:5]:
        if site.metrics_history:
            history = sorted(site.metrics_history, key=lambda x: x.date)
            site_metrics_chart.append({
                "name": site.name,
                "dates": [m.date.strftime("%Y-%m-%d") for m in history],
                "organic": [m.organic_users for m in history],
                "pageviews": [m.pageviews for m in history],
            })

    # Opportunity funnel data
    funnel = {
        "discovered": data["opp_statuses"].get("discovered", 0),
        "validated": data["opp_statuses"].get("validated", 0),
        "deployed": data["opp_statuses"].get("deployed", 0)
            + data["opp_statuses"].get("deployment_failed", 0),
        "winner": data["opp_statuses"].get("winner", 0),
    }

    return templates.TemplateResponse(request, "dashboard_index.html", {
        "stats": stats,
        "opportunities": opportunities,
        "sites": sites,
        "opp_statuses": data["opp_statuses"],
        "site_statuses": data["site_statuses"],
        "recent_opportunities": data["recent_opportunities"],
        "recent_sites": data["recent_sites"],
        "total_revenue": total_revenue,
        "site_metrics_chart": site_metrics_chart,
        "funnel": funnel,
        "status_color": _status_color,
        "now": datetime.now(),
    })


@app.get("/opportunities", response_class=HTMLResponse)
async def dashboard_opportunities(request: Request):
    opportunities = storage.get_all_opportunities()
    return templates.TemplateResponse(request, "dashboard_opportunities.html", {
        "opportunities": opportunities,
        "status_color": _status_color,
        "now": datetime.now(),
    })


@app.get("/sites", response_class=HTMLResponse)
async def dashboard_sites(request: Request):
    sites = storage.get_all_sites()
    return templates.TemplateResponse(request, "dashboard_sites.html", {
        "sites": sites,
        "status_color": _status_color,
        "now": datetime.now(),
    })


@app.get("/sites/{site_id}", response_class=HTMLResponse)
async def dashboard_site_detail(request: Request, site_id: str):
    site = storage.get_site(site_id)
    if not site:
        return HTMLResponse("Site not found", status_code=404)

    opportunity = None
    if site.opportunity_id:
        opportunity = storage.get_opportunity(site.opportunity_id)

    # Prepare metrics chart data
    metrics_chart = None
    if site.metrics_history:
        history = sorted(site.metrics_history, key=lambda x: x.date)
        metrics_chart = {
            "dates": [m.date.strftime("%Y-%m-%d") for m in history],
            "organic_users": [m.organic_users for m in history],
            "total_users": [m.total_users for m in history],
            "pageviews": [m.pageviews for m in history],
            "revenue": [m.revenue for m in history],
            "indexed_pages": [m.indexed_pages for m in history],
            "ranking_keywords": [m.ranking_keywords for m in history],
            "avg_position": [m.avg_position for m in history],
        }

    return templates.TemplateResponse(request, "dashboard_site_detail.html", {
        "site": site,
        "opportunity": opportunity,
        "metrics_chart": metrics_chart,
        "status_color": _status_color,
        "now": datetime.now(),
    })


@app.get("/api/status")
async def api_status():
    """JSON API for external integrations"""
    data = _get_status_counts()
    stats = data["stats"]
    return {
        "mode": "demo",  # Could be dynamic
        "stats": {
            "total_opportunities": stats.total_opportunities,
            "validated_opportunities": stats.validated_opportunities,
            "active_sites": stats.active_sites,
            "winner_sites": stats.winner_sites,
            "culled_sites": stats.culled_sites,
            "total_mrr": stats.total_mrr,
            "portfolio_value": stats.portfolio_value,
            "success_rate": stats.success_rate,
        },
        "opportunities_by_status": data["opp_statuses"],
        "sites_by_status": data["site_statuses"],
        "timestamp": datetime.now().isoformat(),
    }


# ── Main ─────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("web_dashboard:app", host="0.0.0.0", port=8080, reload=True)
