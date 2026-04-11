"""
Agentic Arbitrage Factory - Main Orchestrator

The factory that builds the factories. Orchestrates:
- Red Queen (Discovery)
- Midwife (Validation)
- Constructor (Build)
- Mortician (Culling)
"""
import asyncio
import argparse
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from core.storage import Storage
from core.models import FactoryStats, OpportunityStatus, SiteStatus
from agents.red_queen import RedQueen
from agents.midwife import Midwife
from agents.constructor import Constructor
from agents.mortician import Mortician
from config.settings import config


@dataclass
class FactoryRunResult:
    """Result of a factory run"""
    run_id: str
    timestamp: datetime
    discoveries: int
    validations_passed: int
    validations_failed: int
    builds_successful: int
    builds_failed: int
    sites_evaluated: int
    sites_culled: int
    winners_identified: int
    errors: List[str]


class ArbitrageFactory:
    """
    Main factory orchestrator
    
    Manages the complete lifecycle:
    1. Discover opportunities (Red Queen)
    2. Validate opportunities (Midwife)
    3. Build sites (Constructor)
    4. Manage portfolio (Mortician)
    """
    
    def __init__(self):
        self.storage = Storage()
        self.red_queen = RedQueen(self.storage)
        self.midwife = Midwife(self.storage)
        self.constructor = Constructor(self.storage)
        self.mortician = Mortician(self.storage)
    
    def assert_production_ready(self) -> None:
        """Fail closed in production if required providers are missing."""
        if not config.is_production:
            return
        
        missing = []
        if not config.cloudflare_api_token:
            missing.append("CLOUDFLARE_API_TOKEN")
        if not config.github_token:
            missing.append("GITHUB_TOKEN")
        
        if missing:
            raise RuntimeError(
                f"production mode requires missing provider(s): {', '.join(missing)}"
            )
    
    async def run_full_cycle(self) -> FactoryRunResult:
        """Run a complete factory cycle"""
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        print("\n" + "="*70)
        print(f"🤖 AGENTIC ARBITRAGE FACTORY - Run {run_id}")
        print("="*70)
        
        errors = []
        discoveries = 0
        validations_passed = 0
        validations_failed = 0
        builds_successful = 0
        builds_failed = 0
        sites_evaluated = 0
        sites_culled = 0
        winners_identified = 0
        
        try:
            # Phase 1: Discovery
            print("\n" + "-"*70)
            print("PHASE 1: DISCOVERY (Red Queen)")
            print("-"*70)
            
            opportunities = await self.red_queen.discover()
            discoveries = len(opportunities)
            
            # Phase 2: Validation
            print("\n" + "-"*70)
            print("PHASE 2: VALIDATION (Midwife)")
            print("-"*70)
            
            validation_results = await self.midwife.validate_queue()
            validations_passed = sum(1 for r in validation_results if r.passed)
            validations_failed = len(validation_results) - validations_passed
            
            # Phase 3: Build
            print("\n" + "-"*70)
            print("PHASE 3: BUILD (Constructor)")
            print("-"*70)
            
            build_results = await self.constructor.build_queue()
            builds_successful = sum(1 for r in build_results if r.success)
            builds_failed = len(build_results) - builds_successful
            
            # Phase 4: Portfolio Management
            print("\n" + "-"*70)
            print("PHASE 4: PORTFOLIO MANAGEMENT (Mortician)")
            print("-"*70)
            
            cull_result = await self.mortician.evaluate_portfolio()
            sites_evaluated = cull_result.get("evaluated", 0)
            sites_culled = cull_result.get("culled", 0)
            winners_identified = cull_result.get("winners", 0)
            
        except Exception as e:
            errors.append(str(e))
            print(f"\n❌ Error in factory cycle: {e}")
        
        # Create result
        result = FactoryRunResult(
            run_id=run_id,
            timestamp=datetime.now(),
            discoveries=discoveries,
            validations_passed=validations_passed,
            validations_failed=validations_failed,
            builds_successful=builds_successful,
            builds_failed=builds_failed,
            sites_evaluated=sites_evaluated,
            sites_culled=sites_culled,
            winners_identified=winners_identified,
            errors=errors
        )
        
        # Print summary
        self._print_summary(result)
        
        return result
    
    async def run_discovery_only(self) -> List[Any]:
        """Run only discovery phase"""
        print("\n" + "="*70)
        print("🔍 DISCOVERY ONLY MODE")
        print("="*70)
        
        return await self.red_queen.discover()
    
    async def run_validation_only(self) -> List[Any]:
        """Run only validation phase"""
        print("\n" + "="*70)
        print("🧪 VALIDATION ONLY MODE")
        print("="*70)
        
        return await self.midwife.validate_queue()
    
    async def run_build_only(self) -> List[Any]:
        """Run only build phase"""
        print("\n" + "="*70)
        print("🔨 BUILD ONLY MODE")
        print("="*70)
        
        return await self.constructor.build_queue()
    
    async def run_culling_only(self) -> Dict[str, Any]:
        """Run only culling phase"""
        print("\n" + "="*70)
        print("💀 CULLING ONLY MODE")
        print("="*70)
        
        return await self.mortician.evaluate_portfolio()
    
    def import_metrics(self, csv_path: str) -> int:
        """Import metrics from a CSV file"""
        return self.storage.import_metrics_from_csv(csv_path)
    
    async def run_continuous(self):
        """Run factory continuously"""
        print("\n" + "="*70)
        print("🔄 CONTINUOUS MODE - Press Ctrl+C to stop")
        print("="*70)
        
        while True:
            try:
                await self.run_full_cycle()
                
                print(f"\n⏳ Sleeping for {config.discovery_interval_hours} hours...")
                print("="*70)
                
                await asyncio.sleep(config.discovery_interval_hours * 3600)
                
            except KeyboardInterrupt:
                print("\n\n👋 Factory stopped by user")
                break
            except Exception as e:
                print(f"\n❌ Error in continuous mode: {e}")
                await asyncio.sleep(3600)  # Sleep 1 hour on error
    
    def get_status(self) -> Dict[str, Any]:
        """Get current factory status"""
        stats = self.storage.get_stats()
        
        # Get counts by status from actual persisted data
        all_opportunities = self.storage.get_all_opportunities()
        all_sites = self.storage.get_all_sites()
        
        opportunity_counts = {}
        for status in OpportunityStatus:
            opportunity_counts[status.value] = sum(
                1 for o in all_opportunities if o.status == status
            )
        
        site_counts = {}
        for status in SiteStatus:
            site_counts[status.value] = sum(
                1 for s in all_sites if s.status == status
            )
        
        # Active vertical
        ev_opps = [o for o in all_opportunities if o.niche == "ev_charger_rebates"]
        active_vertical = "ev_charger_rebates" if ev_opps else (all_opportunities[0].niche if all_opportunities else "none")
        
        # Evidence completeness
        evidence_counts = {}
        for etype in ["discovery", "data_probe", "keyword", "monetization", "deployment", "metrics"]:
            evidence_counts[etype] = len(self.storage.get_evidence_by_type(etype))
        evidence_completeness = sum(1 for c in evidence_counts.values() if c > 0) / len(evidence_counts)
        
        # Deployment health of recent deployed sites
        deployed_sites = [s for s in all_sites if s.status == SiteStatus.DEPLOYED]
        deployment_health = {
            "deployed_count": len(deployed_sites),
            "with_url": sum(1 for s in deployed_sites if s.deploy_url),
        }
        
        # Last real metrics date
        all_metrics_evidence = self.storage.get_evidence_by_type("metrics")
        last_metrics_date = None
        if all_metrics_evidence:
            last_metrics_date = all_metrics_evidence[0].data.get("date_range")
        
        # Ready to fund check
        has_validated_ev = any(o.status == OpportunityStatus.VALIDATED for o in ev_opps)
        has_deployed_ev_site = any(
            s.niche == "ev_charger_rebates" and s.status == SiteStatus.DEPLOYED
            for s in all_sites
        )
        has_build_pass = any(
            s.niche == "ev_charger_rebates" and s.status in (SiteStatus.DEPLOYED, SiteStatus.RANKING)
            for s in all_sites
        )
        has_metrics_source = len(all_metrics_evidence) > 0 or config.validation.keyword_snapshot_path
        has_conversion_path = has_deployed_ev_site  # Checklist page is part of deployed site
        
        ready_to_fund = (
            has_validated_ev and
            has_build_pass and
            has_deployed_ev_site and
            has_metrics_source and
            has_conversion_path
        )
        
        return {
            "mode": config.factory_mode,
            "active_vertical": active_vertical,
            "ready_to_fund": ready_to_fund,
            "evidence_completeness": evidence_completeness,
            "evidence_counts": evidence_counts,
            "deployment_health": deployment_health,
            "last_real_metrics_date": last_metrics_date,
            "stats": {
                "total_opportunities": len(all_opportunities),
                "validated_opportunities": opportunity_counts.get("validated", 0),
                "active_sites": site_counts.get("deployed", 0) + site_counts.get("monitoring", 0) + site_counts.get("ranking", 0),
                "winner_sites": site_counts.get("profitable", 0),
                "culled_sites": site_counts.get("culled", 0),
                "total_mrr": stats.total_mrr,
                "portfolio_value": stats.portfolio_value,
                "success_rate": stats.success_rate
            },
            "opportunities": opportunity_counts,
            "sites": site_counts,
            "recent_opportunities": [
                {
                    "id": o.id,
                    "niche": o.niche,
                    "status": o.status.value,
                    "validation_score": o.validation_score,
                    "created_at": o.created_at.isoformat()
                }
                for o in sorted(all_opportunities, key=lambda x: x.created_at, reverse=True)[:5]
            ],
            "recent_sites": [
                {
                    "id": s.id,
                    "name": s.name,
                    "status": s.status.value,
                    "url": s.deploy_url,
                    "created_at": s.created_at.isoformat()
                }
                for s in sorted(all_sites, key=lambda x: x.created_at, reverse=True)[:5]
            ]
        }
    
    def _print_summary(self, result: FactoryRunResult):
        """Print run summary"""
        print("\n" + "="*70)
        print("📊 FACTORY RUN SUMMARY")
        print("="*70)
        print(f"Run ID: {result.run_id}")
        print(f"Timestamp: {result.timestamp.isoformat()}")
        print()
        print("PHASE RESULTS:")
        print(f"  🔍 Discovery:     {result.discoveries} opportunities found")
        print(f"  🧪 Validation:    {result.validations_passed} passed, {result.validations_failed} failed")
        print(f"  🔨 Build:         {result.builds_successful} succeeded, {result.builds_failed} failed")
        print(f"  💀 Portfolio:     {result.sites_evaluated} evaluated, {result.sites_culled} culled, {result.winners_identified} winners")
        print()
        
        # Calculate ROI metrics
        if result.builds_successful > 0:
            success_rate = (result.winners_identified / result.builds_successful) * 100
            print(f"SUCCESS RATE: {success_rate:.1f}%")
        
        if result.errors:
            print(f"\n⚠️ ERRORS ({len(result.errors)}):")
            for error in result.errors:
                print(f"  • {error}")
        
        print("="*70)


def create_cli():
    """Create CLI interface"""
    parser = argparse.ArgumentParser(
        description="Agentic Arbitrage Factory - Build SEO sites at scale",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python factory.py run              Run full factory cycle
  python factory.py discover         Run discovery only
  python factory.py validate         Run validation only
  python factory.py build            Run build only
  python factory.py cull             Run culling only
  python factory.py continuous       Run continuously
  python factory.py status           Show factory status
  python factory.py metrics import <csv>   Import metrics from CSV
        """
    )
    
    parser.add_argument(
        "--max-sites",
        type=int,
        default=50,
        help="Maximum concurrent sites (default: 50)"
    )
    
    parser.add_argument(
        "--mode",
        choices=["demo", "staging", "production"],
        default=config.factory_mode,
        help="Factory runtime mode (default: from FACTORY_MODE env or demo)"
    )
    
    subparsers = parser.add_subparsers(dest="command")
    
    # Lifecycle commands
    for cmd in ["run", "discover", "validate", "build", "cull", "continuous", "status"]:
        subparsers.add_parser(cmd, help=f"{cmd} command")
    
    # Metrics command
    metrics_parser = subparsers.add_parser("metrics", help="Metrics management")
    metrics_sub = metrics_parser.add_subparsers(dest="metrics_action")
    import_parser = metrics_sub.add_parser("import", help="Import metrics from CSV")
    import_parser.add_argument("csv_path", help="Path to CSV file")
    
    return parser


async def main():
    """Main entry point"""
    parser = create_cli()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Set runtime mode from CLI argument
    os.environ["FACTORY_MODE"] = args.mode
    
    factory = ArbitrageFactory()
    
    # Production fail-closed check
    factory.assert_production_ready()
    
    if args.command == "run":
        await factory.run_full_cycle()
    
    elif args.command == "discover":
        opportunities = await factory.run_discovery_only()
        print(f"\n✅ Discovered {len(opportunities)} opportunities")
        for opp in opportunities:
            print(f"  • {opp.niche} (score: {opp.pain_velocity:.1f})")
    
    elif args.command == "validate":
        results = await factory.run_validation_only()
        passed = sum(1 for r in results if r.passed)
        print(f"\n✅ Validation complete: {passed}/{len(results)} passed")
    
    elif args.command == "build":
        results = await factory.run_build_only()
        successful = sum(1 for r in results if r.success)
        print(f"\n✅ Build complete: {successful}/{len(results)} succeeded")
    
    elif args.command == "cull":
        result = await factory.run_culling_only()
        print(f"\n✅ Culling complete: {result.get('culled', 0)} culled, {result.get('winners', 0)} winners")
    
    elif args.command == "continuous":
        await factory.run_continuous()
    
    elif args.command == "status":
        status = factory.get_status()
        
        print("\n" + "="*70)
        print("🏭 FACTORY STATUS")
        print("="*70)
        
        print(f"\n🎚️ MODE: {status['mode']}")
        
        print("\n📊 OVERALL STATS:")
        for key, value in status["stats"].items():
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")
        
        print("\n📋 OPPORTUNITIES BY STATUS:")
        for status_name, count in status["opportunities"].items():
            print(f"  {status_name}: {count}")
        
        print("\n🌐 SITES BY STATUS:")
        for status_name, count in status["sites"].items():
            print(f"  {status_name}: {count}")
        
        print("\n🆕 RECENT OPPORTUNITIES:")
        for opp in status["recent_opportunities"]:
            print(f"  • {opp['niche']} ({opp['status']}) - score: {opp['validation_score']:.1f}")
        
        print("\n🌐 RECENT SITES:")
        for site in status["recent_sites"]:
            print(f"  • {site['name']} ({site['status']})")
            if site['url']:
                print(f"    URL: {site['url']}")
    
    elif args.command == "metrics":
        if args.metrics_action == "import":
            count = factory.import_metrics(args.csv_path)
            print(f"\n✅ Imported {count} metrics records")
        else:
            print("\n⚠️ Usage: factory.py metrics import <csv_path>")


if __name__ == "__main__":
    asyncio.run(main())
