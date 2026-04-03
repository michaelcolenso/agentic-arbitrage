"""
Storage layer for Agentic Arbitrage Factory
Uses SQLite for local persistence with JSON serialization for complex objects
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

from config.settings import config
from core.models import (
    Opportunity, Site, SiteMetrics, FactoryStats,
    OpportunityStatus, SiteStatus, PainPoint, DataSource,
    KeywordOpportunity, FragmentationScore, MonetizationPotential
)

class Storage:
    """SQLite-based storage for the factory"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = config.data_dir / "factory.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    @contextmanager
    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    
    def _init_db(self):
        """Initialize database tables"""
        with self._get_conn() as conn:
            # Opportunities table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS opportunities (
                    id TEXT PRIMARY KEY,
                    niche TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL,
                    pain_velocity REAL DEFAULT 0,
                    competition_gap REAL DEFAULT 0,
                    data_availability_score REAL DEFAULT 0,
                    pain_points TEXT,  -- JSON
                    data_sources TEXT,  -- JSON
                    keywords TEXT,  -- JSON
                    fragmentation TEXT,  -- JSON
                    monetization TEXT,  -- JSON
                    validation_score REAL DEFAULT 0,
                    validated_at TEXT,
                    site_id TEXT,
                    repo_url TEXT,
                    deployed_url TEXT,
                    built_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Sites table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sites (
                    id TEXT PRIMARY KEY,
                    opportunity_id TEXT,
                    name TEXT NOT NULL,
                    domain TEXT,
                    niche TEXT,
                    status TEXT NOT NULL,
                    repo_url TEXT,
                    deploy_url TEXT,
                    cloudflare_project_id TEXT,
                    data_schema TEXT,  -- JSON
                    page_count INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    deployed_at TEXT,
                    last_evaluated TEXT,
                    culled_at TEXT
                )
            """)
            
            # Site metrics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS site_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    site_id TEXT NOT NULL,
                    date TEXT NOT NULL,
                    organic_users INTEGER DEFAULT 0,
                    total_users INTEGER DEFAULT 0,
                    pageviews INTEGER DEFAULT 0,
                    avg_session_duration REAL DEFAULT 0,
                    bounce_rate REAL DEFAULT 0,
                    indexed_pages INTEGER DEFAULT 0,
                    ranking_keywords INTEGER DEFAULT 0,
                    avg_position REAL DEFAULT 0,
                    backlinks INTEGER DEFAULT 0,
                    revenue REAL DEFAULT 0,
                    affiliate_revenue REAL DEFAULT 0,
                    lead_gen_revenue REAL DEFAULT 0,
                    ad_revenue REAL DEFAULT 0,
                    UNIQUE(site_id, date)
                )
            """)
            
            # Factory stats table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS factory_stats (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    total_opportunities INTEGER DEFAULT 0,
                    validated_opportunities INTEGER DEFAULT 0,
                    active_sites INTEGER DEFAULT 0,
                    winner_sites INTEGER DEFAULT 0,
                    culled_sites INTEGER DEFAULT 0,
                    total_revenue REAL DEFAULT 0,
                    total_mrr REAL DEFAULT 0,
                    portfolio_value REAL DEFAULT 0,
                    avg_build_time_minutes REAL DEFAULT 0,
                    avg_validation_time_hours REAL DEFAULT 0,
                    success_rate REAL DEFAULT 0,
                    last_updated TEXT NOT NULL
                )
            """)
            
            # Initialize stats row
            conn.execute("""
                INSERT OR IGNORE INTO factory_stats (id, last_updated)
                VALUES (1, ?)
            """, (datetime.now().isoformat(),))
    
    # Opportunity operations
    def save_opportunity(self, opp: Opportunity) -> None:
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO opportunities (
                    id, niche, description, status, pain_velocity, competition_gap,
                    data_availability_score, pain_points, data_sources, keywords,
                    fragmentation, monetization, validation_score, validated_at,
                    site_id, repo_url, deployed_url, built_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                opp.id, opp.niche, opp.description, opp.status.value,
                opp.pain_velocity, opp.competition_gap, opp.data_availability_score,
                json.dumps([self._pain_point_to_dict(p) for p in opp.pain_points]),
                json.dumps([self._data_source_to_dict(d) for d in opp.data_sources]),
                json.dumps([self._keyword_to_dict(k) for k in opp.keywords]),
                json.dumps(self._fragmentation_to_dict(opp.fragmentation)) if opp.fragmentation else None,
                json.dumps(self._monetization_to_dict(opp.monetization)) if opp.monetization else None,
                opp.validation_score,
                opp.validated_at.isoformat() if opp.validated_at else None,
                opp.site_id, opp.repo_url, opp.deployed_url,
                opp.built_at.isoformat() if opp.built_at else None,
                opp.created_at.isoformat(), datetime.now().isoformat()
            ))
    
    def get_opportunity(self, opp_id: str) -> Optional[Opportunity]:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM opportunities WHERE id = ?", (opp_id,)
            ).fetchone()
            if row:
                return self._row_to_opportunity(row)
            return None
    
    def get_opportunities_by_status(self, status: OpportunityStatus) -> List[Opportunity]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM opportunities WHERE status = ? ORDER BY created_at DESC",
                (status.value,)
            ).fetchall()
            return [self._row_to_opportunity(row) for row in rows]
    
    def get_all_opportunities(self) -> List[Opportunity]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM opportunities ORDER BY created_at DESC"
            ).fetchall()
            return [self._row_to_opportunity(row) for row in rows]
    
    # Site operations
    def save_site(self, site: Site) -> None:
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO sites (
                    id, opportunity_id, name, domain, niche, status,
                    repo_url, deploy_url, cloudflare_project_id, data_schema,
                    page_count, created_at, deployed_at, last_evaluated, culled_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                site.id, site.opportunity_id, site.name, site.domain, site.niche,
                site.status.value, site.repo_url, site.deploy_url,
                site.cloudflare_project_id, json.dumps(site.data_schema),
                site.page_count, site.created_at.isoformat(),
                site.deployed_at.isoformat() if site.deployed_at else None,
                site.last_evaluated.isoformat() if site.last_evaluated else None,
                site.culled_at.isoformat() if site.culled_at else None
            ))
    
    def get_site(self, site_id: str) -> Optional[Site]:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM sites WHERE id = ?", (site_id,)
            ).fetchone()
            if row:
                site = self._row_to_site(row)
                # Load metrics
                site.metrics_history = self.get_site_metrics(site_id)
                return site
            return None
    
    def get_sites_by_status(self, status: SiteStatus) -> List[Site]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM sites WHERE status = ? ORDER BY created_at DESC",
                (status.value,)
            ).fetchall()
            sites = []
            for row in rows:
                site = self._row_to_site(row)
                site.metrics_history = self.get_site_metrics(site.id)
                sites.append(site)
            return sites
    
    def get_all_sites(self) -> List[Site]:
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM sites ORDER BY created_at DESC").fetchall()
            sites = []
            for row in rows:
                site = self._row_to_site(row)
                site.metrics_history = self.get_site_metrics(site.id)
                sites.append(site)
            return sites
    
    # Metrics operations
    def save_metrics(self, metrics: SiteMetrics) -> None:
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO site_metrics (
                    site_id, date, organic_users, total_users, pageviews,
                    avg_session_duration, bounce_rate, indexed_pages, ranking_keywords,
                    avg_position, backlinks, revenue, affiliate_revenue, lead_gen_revenue, ad_revenue
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.site_id, metrics.date.isoformat(),
                metrics.organic_users, metrics.total_users, metrics.pageviews,
                metrics.avg_session_duration, metrics.bounce_rate,
                metrics.indexed_pages, metrics.ranking_keywords, metrics.avg_position,
                metrics.backlinks, metrics.revenue, metrics.affiliate_revenue,
                metrics.lead_gen_revenue, metrics.ad_revenue
            ))
    
    def get_site_metrics(self, site_id: str) -> List[SiteMetrics]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM site_metrics WHERE site_id = ? ORDER BY date DESC",
                (site_id,)
            ).fetchall()
            return [self._row_to_metrics(row) for row in rows]
    
    # Stats operations
    def get_stats(self) -> FactoryStats:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM factory_stats WHERE id = 1").fetchone()
            if row:
                return self._row_to_stats(row)
            return FactoryStats()
    
    def update_stats(self, stats: FactoryStats) -> None:
        with self._get_conn() as conn:
            conn.execute("""
                UPDATE factory_stats SET
                    total_opportunities = ?,
                    validated_opportunities = ?,
                    active_sites = ?,
                    winner_sites = ?,
                    culled_sites = ?,
                    total_revenue = ?,
                    total_mrr = ?,
                    portfolio_value = ?,
                    avg_build_time_minutes = ?,
                    avg_validation_time_hours = ?,
                    success_rate = ?,
                    last_updated = ?
                WHERE id = 1
            """, (
                stats.total_opportunities, stats.validated_opportunities,
                stats.active_sites, stats.winner_sites, stats.culled_sites,
                stats.total_revenue, stats.total_mrr, stats.portfolio_value,
                stats.avg_build_time_minutes, stats.avg_validation_time_hours,
                stats.success_rate, datetime.now().isoformat()
            ))
    
    # Helper methods for serialization
    def _pain_point_to_dict(self, p: PainPoint) -> dict:
        return {
            "source": p.source, "text": p.text, "sentiment_score": p.sentiment_score,
            "engagement": p.engagement, "keywords": p.keywords,
            "timestamp": p.timestamp.isoformat(), "url": p.url
        }
    
    def _data_source_to_dict(self, d: DataSource) -> dict:
        return {
            "name": d.name, "url": d.url, "type": d.type, "schema": d.schema,
            "update_frequency": d.update_frequency, "quality_score": d.quality_score,
            "last_updated": d.last_updated.isoformat()
        }
    
    def _keyword_to_dict(self, k: KeywordOpportunity) -> dict:
        return {
            "keyword": k.keyword, "monthly_volume": k.monthly_volume,
            "difficulty": k.difficulty, "cpc": k.cpc, "intent": k.intent,
            "related_keywords": k.related_keywords, "trending": k.trending
        }
    
    def _fragmentation_to_dict(self, f: FragmentationScore) -> dict:
        return {
            "score": f.score, "data_points_found": f.data_points_found,
            "sources_analyzed": f.sources_analyzed, "consistency_rating": f.consistency_rating,
            "automation_potential": f.automation_potential
        }
    
    def _monetization_to_dict(self, m: MonetizationPotential) -> dict:
        return {
            "score": m.score, "affiliate_programs": m.affiliate_programs,
            "lead_gen_potential": m.lead_gen_potential, "ad_potential": m.ad_potential,
            "subscription_potential": m.subscription_potential,
            "estimated_monthly_revenue": m.estimated_monthly_revenue
        }
    
    def _row_to_opportunity(self, row: sqlite3.Row) -> Opportunity:
        return Opportunity(
            id=row["id"],
            niche=row["niche"],
            description=row["description"] or "",
            status=OpportunityStatus(row["status"]),
            pain_velocity=row["pain_velocity"],
            competition_gap=row["competition_gap"],
            data_availability_score=row["data_availability_score"],
            pain_points=[PainPoint(**{**p, "timestamp": datetime.fromisoformat(p["timestamp"])}) 
                        for p in json.loads(row["pain_points"] or "[]")],
            data_sources=[DataSource(**{**d, "last_updated": datetime.fromisoformat(d["last_updated"])}) 
                         for d in json.loads(row["data_sources"] or "[]")],
            keywords=[KeywordOpportunity(**k) for k in json.loads(row["keywords"] or "[]")],
            fragmentation=FragmentationScore(**json.loads(row["fragmentation"])) if row["fragmentation"] else None,
            monetization=MonetizationPotential(**json.loads(row["monetization"])) if row["monetization"] else None,
            validation_score=row["validation_score"],
            validated_at=datetime.fromisoformat(row["validated_at"]) if row["validated_at"] else None,
            site_id=row["site_id"],
            repo_url=row["repo_url"],
            deployed_url=row["deployed_url"],
            built_at=datetime.fromisoformat(row["built_at"]) if row["built_at"] else None,
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"])
        )
    
    def _row_to_site(self, row: sqlite3.Row) -> Site:
        return Site(
            id=row["id"],
            opportunity_id=row["opportunity_id"] or "",
            name=row["name"],
            domain=row["domain"] or "",
            niche=row["niche"] or "",
            status=SiteStatus(row["status"]),
            repo_url=row["repo_url"],
            deploy_url=row["deploy_url"],
            cloudflare_project_id=row["cloudflare_project_id"],
            data_schema=json.loads(row["data_schema"] or "{}"),
            page_count=row["page_count"],
            created_at=datetime.fromisoformat(row["created_at"]),
            deployed_at=datetime.fromisoformat(row["deployed_at"]) if row["deployed_at"] else None,
            last_evaluated=datetime.fromisoformat(row["last_evaluated"]) if row["last_evaluated"] else None,
            culled_at=datetime.fromisoformat(row["culled_at"]) if row["culled_at"] else None
        )
    
    def _row_to_metrics(self, row: sqlite3.Row) -> SiteMetrics:
        return SiteMetrics(
            site_id=row["site_id"],
            date=datetime.fromisoformat(row["date"]),
            organic_users=row["organic_users"],
            total_users=row["total_users"],
            pageviews=row["pageviews"],
            avg_session_duration=row["avg_session_duration"],
            bounce_rate=row["bounce_rate"],
            indexed_pages=row["indexed_pages"],
            ranking_keywords=row["ranking_keywords"],
            avg_position=row["avg_position"],
            backlinks=row["backlinks"],
            revenue=row["revenue"],
            affiliate_revenue=row["affiliate_revenue"],
            lead_gen_revenue=row["lead_gen_revenue"],
            ad_revenue=row["ad_revenue"]
        )
    
    def _row_to_stats(self, row: sqlite3.Row) -> FactoryStats:
        return FactoryStats(
            total_opportunities=row["total_opportunities"],
            validated_opportunities=row["validated_opportunities"],
            active_sites=row["active_sites"],
            winner_sites=row["winner_sites"],
            culled_sites=row["culled_sites"],
            total_revenue=row["total_revenue"],
            total_mrr=row["total_mrr"],
            portfolio_value=row["portfolio_value"],
            avg_build_time_minutes=row["avg_build_time_minutes"],
            avg_validation_time_hours=row["avg_validation_time_hours"],
            success_rate=row["success_rate"],
            last_updated=datetime.fromisoformat(row["last_updated"])
        )
