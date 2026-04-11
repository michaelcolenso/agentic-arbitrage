"""
The Mortician (Culling Agent)

Ruthless portfolio management:
- Kills sites with <100 users/day by day 90
- 301s domains to nearest winner
- Archives data for training
- Recycles codebase
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from core.models import Site, SiteMetrics, Opportunity, SiteStatus, OpportunityStatus, Evidence
from core.storage import Storage
from config.settings import config


@dataclass
class CullDecision:
    """Decision to cull a site"""
    site_id: str
    should_cull: bool
    reason: str
    days_active: int
    avg_daily_traffic: float
    total_revenue: float
    recommendation: str


@dataclass
class ArchiveResult:
    """Result of archiving a site"""
    site_id: str
    archived: bool
    data_path: Optional[str]
    code_path: Optional[str]
    insights: List[str]


class TrafficMonitor:
    """Monitors site traffic and performance"""
    
    async def get_metrics(self, site: Site, days: int = 7) -> Optional[SiteMetrics]:
        """Get latest metrics for a site"""
        # In production, this would fetch from:
        # - Google Analytics
        # - Cloudflare Analytics
        # - Search Console
        
        if config.is_production:
            raise RuntimeError(
                "Production mode requires real metrics providers or manual imports"
            )
        
        # Try to get real metrics from storage first
        storage = Storage()
        history = storage.get_site_metrics(site.id)
        if history:
            # Return the most recent metrics
            return sorted(history, key=lambda x: x.date, reverse=True)[0]
        
        if not config.is_demo:
            # In staging, do not fabricate metrics
            return None
        
        # For demo, generate mock metrics
        return self._generate_mock_metrics(site, days)
    
    def _generate_mock_metrics(self, site: Site, days: int) -> SiteMetrics:
        """Generate mock metrics for demo"""
        # Simulate realistic traffic patterns
        days_since_deploy = (datetime.now() - (site.deployed_at or datetime.now())).days
        
        # Traffic grows over time (or doesn't for failing sites)
        base_traffic = 50
        growth_rate = 1.05 if days_since_deploy > 30 else 1.02
        
        # Some sites fail to get traction
        if hash(site.id) % 5 == 0:  # 20% fail
            organic_users = max(10, int(base_traffic * 0.3))
        else:
            organic_users = int(base_traffic * (growth_rate ** min(days_since_deploy, 60)))
        
        return SiteMetrics(
            site_id=site.id,
            date=datetime.now(),
            organic_users=organic_users,
            total_users=int(organic_users * 1.2),
            pageviews=organic_users * 3,
            avg_session_duration=120.0,
            bounce_rate=0.65,
            indexed_pages=site.page_count // 2,
            ranking_keywords=organic_users // 5,
            avg_position=15.0,
            backlinks=organic_users // 10,
            revenue=organic_users * 0.1,
            affiliate_revenue=organic_users * 0.05,
            lead_gen_revenue=organic_users * 0.03,
            ad_revenue=organic_users * 0.02
        )
    
    async def collect_all_metrics(self, sites: List[Site]) -> Dict[str, SiteMetrics]:
        """Collect metrics for all sites"""
        metrics = {}
        
        for site in sites:
            try:
                metric = await self.get_metrics(site)
                metrics[site.id] = metric
                
                # Save to storage
                storage = Storage()
                storage.save_metrics(metric)
                
                # Record metrics evidence
                storage.save_evidence(Evidence(
                    evidence_type="metrics",
                    site_id=site.id,
                    data={
                        "provider": "demo",
                        "date_range": metric.date.isoformat(),
                        "organic_users": metric.organic_users,
                        "pageviews": metric.pageviews,
                        "revenue": metric.revenue,
                    }
                ))
            except Exception as e:
                print(f"  Error collecting metrics for {site.id}: {e}")
        
        return metrics


class PerformanceAnalyzer:
    """Analyzes site performance and makes culling decisions"""
    
    def __init__(self):
        self.storage = Storage()
    
    def analyze(self, site: Site, metrics: Optional[SiteMetrics]) -> CullDecision:
        """Analyze site and make culling decision"""
        days_active = (datetime.now() - (site.deployed_at or datetime.now())).days
        
        # Get historical metrics
        history = self.storage.get_site_metrics(site.id)
        
        # If no real metrics available outside demo, do not cull
        if not history and not config.is_demo:
            return CullDecision(
                site_id=site.id,
                should_cull=False,
                reason="No real metrics available",
                days_active=days_active,
                avg_daily_traffic=0.0,
                total_revenue=0.0,
                recommendation="METRICS_UNAVAILABLE"
            )
        
        avg_traffic = self._calculate_avg_traffic(history, days=7)
        total_revenue = sum(m.revenue for m in history) if history else 0
        
        # Decision logic
        should_cull = False
        reasons = []
        recommendation = "KEEP"
        
        # Rule 1: Time-based evaluation
        if days_active >= config.culling.evaluation_days:
            if avg_traffic < config.culling.traffic_threshold_per_day:
                should_cull = True
                reasons.append(f"Traffic below threshold: {avg_traffic:.0f} < {config.culling.traffic_threshold_per_day}")
        
        # Rule 2: Revenue-based (if any revenue generated)
        if days_active >= 60 and total_revenue < 10:
            should_cull = True
            reasons.append(f"No revenue generated after {days_active} days")
        
        # Rule 3: Growth trajectory
        if len(history) >= 14:
            recent_growth = self._calculate_growth(history, days=7)
            if recent_growth < -0.3:  # 30% decline
                should_cull = True
                reasons.append(f"Declining traffic: {recent_growth:.1%} change")
        
        # Rule 4: Exception for promising sites
        if avg_traffic > 200 and days_active < 60:
            should_cull = False
            reasons.clear()
            recommendation = "PROMISING - ACCELERATE"
        
        # Rule 5: Winners get special status
        if avg_traffic > 500:
            should_cull = False
            reasons.clear()
            recommendation = "WINNER - SCALE"
        
        reason_str = "; ".join(reasons) if reasons else "Performing within expectations"
        
        return CullDecision(
            site_id=site.id,
            should_cull=should_cull,
            reason=reason_str,
            days_active=days_active,
            avg_daily_traffic=avg_traffic,
            total_revenue=total_revenue,
            recommendation=recommendation
        )
    
    def _calculate_avg_traffic(self, history: List[SiteMetrics], days: int = 7) -> float:
        """Calculate average daily traffic"""
        if not history:
            return 0.0
        
        recent = sorted(history, key=lambda x: x.date, reverse=True)[:days]
        if not recent:
            return 0.0
        
        return sum(m.organic_users for m in recent) / len(recent)
    
    def _calculate_growth(self, history: List[SiteMetrics], days: int = 7) -> float:
        """Calculate traffic growth rate"""
        if len(history) < days * 2:
            return 0.0
        
        sorted_history = sorted(history, key=lambda x: x.date)
        
        recent = sorted_history[-days:]
        previous = sorted_history[-(days*2):-days]
        
        recent_avg = sum(m.organic_users for m in recent) / len(recent)
        previous_avg = sum(m.organic_users for m in previous) / len(previous)
        
        if previous_avg == 0:
            return 0.0
        
        return (recent_avg - previous_avg) / previous_avg
    
    def identify_winners(self, decisions: List[CullDecision]) -> List[str]:
        """Identify winner sites"""
        return [d.site_id for d in decisions if d.recommendation == "WINNER - SCALE"]
    
    def identify_promising(self, decisions: List[CullDecision]) -> List[str]:
        """Identify promising sites"""
        return [d.site_id for d in decisions if d.recommendation == "PROMISING - ACCELERATE"]


class SiteArchiver:
    """Archives site data and code for future use"""
    
    def __init__(self):
        self.storage = Storage()
        self.archive_base_path = str(config.archive_dir)
    
    async def archive(self, site: Site, decision: CullDecision) -> ArchiveResult:
        """Archive a culled site"""
        print(f"  📦 Archiving {site.name}...")
        
        import json
        from pathlib import Path
        
        Path(self.archive_base_path).mkdir(parents=True, exist_ok=True)
        
        insights = []
        
        # Archive 1: Performance data
        history = self.storage.get_site_metrics(site.id)
        data_archive = {
            "site_id": site.id,
            "niche": site.niche,
            "deployed_at": site.deployed_at.isoformat() if site.deployed_at else None,
            "culled_at": datetime.now().isoformat(),
            "days_active": decision.days_active,
            "avg_traffic": decision.avg_daily_traffic,
            "total_revenue": decision.total_revenue,
            "metrics_history": [
                {
                    "date": m.date.isoformat(),
                    "organic_users": m.organic_users,
                    "revenue": m.revenue,
                    "ranking_keywords": m.ranking_keywords
                }
                for m in history
            ]
        }
        
        data_path = f"{self.archive_base_path}/{site.id}_data.json"
        with open(data_path, "w") as f:
            json.dump(data_archive, f, indent=2)
        
        # Generate insights
        insights = self._generate_insights(data_archive)
        
        # Archive 2: Code (if exists)
        code_path = None
        site_code_path = str(config.sites_dir / site.id)
        if Path(site_code_path).exists():
            import shutil
            archive_code_path = f"{self.archive_base_path}/{site.id}_code"
            shutil.copytree(site_code_path, archive_code_path, dirs_exist_ok=True)
            code_path = archive_code_path
        
        print(f"  ✅ Archived to {data_path}")
        
        return ArchiveResult(
            site_id=site.id,
            archived=True,
            data_path=data_path,
            code_path=code_path,
            insights=insights
        )
    
    def _generate_insights(self, data: Dict) -> List[str]:
        """Generate insights from archived data"""
        insights = []
        
        days_active = data.get("days_active", 0)
        avg_traffic = data.get("avg_traffic", 0)
        total_revenue = data.get("total_revenue", 0)
        
        if days_active > 60 and avg_traffic < 50:
            insights.append("Low traffic despite extended runtime - consider niche selection")
        
        if total_revenue == 0 and days_active > 30:
            insights.append("No monetization - review affiliate integration")
        
        history = data.get("metrics_history", [])
        if len(history) >= 14:
            early = sum(m["organic_users"] for m in history[:7]) / 7
            late = sum(m["organic_users"] for m in history[-7:]) / 7
            
            if late < early * 0.5:
                insights.append("Significant traffic decline - potential indexing issues")
            elif late > early * 1.5:
                insights.append("Positive growth trajectory - consider longer evaluation period")
        
        return insights


class DomainRedirector:
    """Handles 301 redirects to winner sites"""
    
    async def redirect_to_winner(self, culled_site: Site, winner_site: Site) -> bool:
        """Setup 301 redirect from culled site to winner"""
        print(f"  🔄 Setting up 301: {culled_site.domain} → {winner_site.domain}")
        
        # In production, this would:
        # 1. Update DNS records
        # 2. Configure Cloudflare Pages redirect rules
        # 3. Submit redirect to search engines
        
        # For demo, just log it
        return True


class Mortician:
    """
    The Mortician Culling Agent
    
    Ruthless portfolio management:
    - Evaluates all sites daily
    - Kills underperformers at day 90
    - 301s domains to winners
    - Archives data for training
    - Recycles codebase
    """
    
    def __init__(self, storage: Storage = None):
        self.storage = storage or Storage()
        self.traffic_monitor = TrafficMonitor()
        self.performance_analyzer = PerformanceAnalyzer()
        self.site_archiver = SiteArchiver()
        self.domain_redirector = DomainRedirector()
    
    async def evaluate_portfolio(self) -> Dict[str, Any]:
        """Evaluate entire portfolio and make culling decisions"""
        print("\n💀 Mortician: Evaluating portfolio...")
        
        # Get all active sites
        active_sites = self.storage.get_sites_by_status(SiteStatus.DEPLOYED)
        monitoring_sites = self.storage.get_sites_by_status(SiteStatus.MONITORING)
        ranking_sites = self.storage.get_sites_by_status(SiteStatus.RANKING)
        
        all_sites = active_sites + monitoring_sites + ranking_sites
        
        print(f"  Evaluating {len(all_sites)} sites...")
        
        if not all_sites:
            return {"evaluated": 0, "culled": 0, "winners": 0}
        
        # Collect metrics
        metrics = await self.traffic_monitor.collect_all_metrics(all_sites)
        
        # Analyze each site
        decisions = []
        culled = []
        winners = []
        promising = []
        
        metrics_unavailable = []
        
        for site in all_sites:
            site_metrics = metrics.get(site.id)
            if not site_metrics:
                # No metrics at all
                decision = self.performance_analyzer.analyze(site, None)
                decisions.append(decision)
                if decision.recommendation == "METRICS_UNAVAILABLE":
                    metrics_unavailable.append(site.id)
                continue
            
            decision = self.performance_analyzer.analyze(site, site_metrics)
            decisions.append(decision)
            
            if decision.should_cull:
                await self._cull_site(site, decision)
                culled.append(site.id)
            elif decision.recommendation == "WINNER - SCALE":
                await self._promote_to_winner(site)
                winners.append(site.id)
            elif decision.recommendation == "PROMISING - ACCELERATE":
                await self._mark_promising(site)
                promising.append(site.id)
        
        # Update stats
        self._update_stats(decisions)
        
        print(f"\n💀 Mortician: Portfolio evaluation complete")
        print(f"  Evaluated: {len(decisions)}")
        print(f"  Culled: {len(culled)}")
        print(f"  Winners: {len(winners)}")
        print(f"  Promising: {len(promising)}")
        print(f"  Metrics Unavailable: {len(metrics_unavailable)}")
        
        return {
            "evaluated": len(decisions),
            "culled": len(culled),
            "winners": len(winners),
            "promising": len(promising),
            "metrics_unavailable": len(metrics_unavailable),
            "decisions": decisions
        }
    
    async def _cull_site(self, site: Site, decision: CullDecision):
        """Cull a site"""
        print(f"  🪦 Culling {site.name}...")
        print(f"     Reason: {decision.reason}")
        
        # Find nearest winner for redirect
        winners = self.storage.get_sites_by_status(SiteStatus.PROFITABLE)
        
        if winners and config.culling.auto_301_to_winner:
            # Find winner in same or similar niche
            winner = self._find_nearest_winner(site, winners)
            if winner:
                await self.domain_redirector.redirect_to_winner(site, winner)
        
        # Archive site
        if config.culling.archive_data:
            await self.site_archiver.archive(site, decision)
        
        # Update site status
        site.status = SiteStatus.CULLED
        site.culled_at = datetime.now()
        self.storage.save_site(site)
        
        # Update opportunity
        opportunity = self.storage.get_opportunity(site.opportunity_id)
        if opportunity:
            opportunity.status = OpportunityStatus.CULLED
            self.storage.save_opportunity(opportunity)
        
        print(f"  ✅ Culled {site.name}")
    
    def _find_nearest_winner(self, site: Site, winners: List[Site]) -> Optional[Site]:
        """Find the nearest winner site for redirect"""
        # Simple matching by niche similarity
        site_niche = set(site.niche.lower().split("_"))
        
        best_match = None
        best_score = 0
        
        for winner in winners:
            winner_niche = set(winner.niche.lower().split("_"))
            intersection = site_niche & winner_niche
            score = len(intersection)
            
            if score > best_score:
                best_score = score
                best_match = winner
        
        return best_match
    
    async def _promote_to_winner(self, site: Site):
        """Promote site to winner status"""
        print(f"  🏆 Promoting {site.name} to WINNER")
        
        site.status = SiteStatus.PROFITABLE
        site.last_evaluated = datetime.now()
        self.storage.save_site(site)
        
        # Update opportunity
        opportunity = self.storage.get_opportunity(site.opportunity_id)
        if opportunity:
            opportunity.status = OpportunityStatus.WINNER
            self.storage.save_opportunity(opportunity)
    
    async def _mark_promising(self, site: Site):
        """Mark site as promising"""
        print(f"  📈 Marking {site.name} as PROMISING")
        
        site.status = SiteStatus.RANKING
        site.last_evaluated = datetime.now()
        self.storage.save_site(site)
    
    def _update_stats(self, decisions: List[CullDecision]):
        """Update factory stats"""
        stats = self.storage.get_stats()
        
        culled_count = sum(1 for d in decisions if d.should_cull)
        winner_count = sum(1 for d in decisions if d.recommendation == "WINNER - SCALE")
        
        stats.culled_sites += culled_count
        stats.winner_sites += winner_count
        
        # Calculate success rate
        total_evaluated = len(decisions)
        if total_evaluated > 0:
            total_sites = stats.winner_sites + stats.culled_sites
            if total_sites > 0:
                stats.success_rate = (stats.winner_sites / total_sites) * 100
        
        self.storage.update_stats(stats)
    
    async def run_continuous(self):
        """Run culling continuously"""
        while True:
            try:
                await self.evaluate_portfolio()
                print("Culling cycle complete. Sleeping for 24 hours...")
                await asyncio.sleep(24 * 3600)
            except Exception as e:
                print(f"Error in culling cycle: {e}")
                await asyncio.sleep(3600)


# For direct execution
if __name__ == "__main__":
    async def main():
        mortician = Mortician()
        result = await mortician.evaluate_portfolio()
        
        print("\n" + "="*60)
        print("CULLING RESULTS")
        print("="*60)
        print(f"Evaluated: {result['evaluated']}")
        print(f"Culled: {result['culled']}")
        print(f"Winners: {result['winners']}")
        
        if result.get('decisions'):
            print("\nDetailed Decisions:")
            for decision in result['decisions']:
                action = "CULL" if decision.should_cull else decision.recommendation
                print(f"  {decision.site_id}: {action}")
                print(f"    Traffic: {decision.avg_daily_traffic:.0f}/day, Revenue: ${decision.total_revenue:.2f}")
    
    asyncio.run(main())
