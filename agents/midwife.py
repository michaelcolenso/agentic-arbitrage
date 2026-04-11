"""
The Midwife (Validation Agent)

Performs 48-hour viability tests on discovered opportunities.
Validates: fragmentation, keyword difficulty, affiliate potential.
"""
import asyncio
import aiohttp
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import random

from core.models import (
    Opportunity, FragmentationScore, MonetizationPotential,
    OpportunityStatus, Evidence
)
from core.storage import Storage
from config.settings import config


@dataclass
class ValidationResult:
    """Result of validation test"""
    opportunity_id: str
    passed: bool
    fragmentation_score: FragmentationScore
    monetization: MonetizationPotential
    overall_score: float
    validation_time_hours: float
    notes: List[str]


class FragmentationAnalyzer:
    """Analyzes data fragmentation for automation potential"""
    
    async def analyze(self, opportunity: Opportunity) -> FragmentationScore:
        """Analyze how fragmented the data is"""
        print(f"  🔍 Analyzing fragmentation for {opportunity.niche}...")
        
        # In production, this would:
        # 1. Scrape sample data points from multiple sources
        # 2. Check consistency across sources
        # 3. Measure automation difficulty
        
        # For demo, simulate analysis
        data_sources = opportunity.data_sources
        
        if not data_sources:
            return FragmentationScore(
                score=0.5,
                data_points_found=0,
                sources_analyzed=0,
                consistency_rating=0.5,
                automation_potential=5.0
            )
        
        # Test scraping sample data points
        test_results = await self._test_data_access(data_sources)
        
        # Calculate metrics
        total_data_points = sum(r.get("sample_count", r.get("count", 0)) for r in test_results)
        sources_accessible = sum(1 for r in test_results if r.get("accessible"))
        consistency = self._calculate_consistency(test_results)
        
        # Fragmentation score (lower = more fragmented = better for us)
        if sources_accessible == 0:
            frag_score = 0.9  # High fragmentation if no access
        else:
            frag_score = 1.0 - (sources_accessible / len(data_sources) * 0.5)
        
        # Automation potential (higher = easier to automate)
        auto_potential = self._calculate_automation_potential(
            test_results, opportunity.keywords
        )
        
        return FragmentationScore(
            score=frag_score,
            data_points_found=total_data_points,
            sources_analyzed=sources_accessible,
            consistency_rating=consistency,
            automation_potential=auto_potential
        )
    
    async def _test_data_access(self, data_sources: List[Any]) -> List[Dict]:
        """Test access to data sources"""
        results = []
        
        async with aiohttp.ClientSession() as session:
            for source in data_sources:
                try:
                    # Try to access the data source
                    if source.type == "api":
                        result = await self._test_api_access(session, source)
                    else:
                        result = await self._test_scrape_access(session, source)
                    
                    results.append(result)
                except Exception as e:
                    results.append({
                        "source": source.name,
                        "accessible": False,
                        "count": 0,
                        "error": str(e)
                    })
        
        return results
    
    async def _test_api_access(self, session: aiohttp.ClientSession, source: Any) -> Dict:
        """Test API data access with a real HTTP probe"""
        try:
            async with session.get(source.url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                content_type = resp.headers.get("Content-Type", "unknown")
                body_sample = ""
                try:
                    body_sample = (await resp.text())[:500]
                except Exception:
                    pass
                
                schema_hints = []
                if "json" in content_type.lower() or body_sample.strip().startswith(("{", "[")):
                    schema_hints.append("json")
                
                return {
                    "source": source.name,
                    "accessible": resp.status < 400,
                    "status_code": resp.status,
                    "content_type": content_type,
                    "sample_count": len(body_sample),
                    "schema_hints": schema_hints,
                    "format": "json" if "json" in content_type.lower() else "unknown"
                }
        except Exception as e:
            if config.is_production:
                raise RuntimeError(
                    f"Production mode requires successful data probe for {source.name}: {e}"
                )
            return {
                "source": source.name,
                "accessible": False,
                "status_code": 0,
                "content_type": "error",
                "sample_count": 0,
                "schema_hints": [],
                "error": str(e)
            }
    
    async def _test_scrape_access(self, session: aiohttp.ClientSession, source: Any) -> Dict:
        """Test scrape data access with a real HTTP probe"""
        try:
            async with session.get(source.url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                content_type = resp.headers.get("Content-Type", "unknown")
                body_sample = ""
                try:
                    body_sample = (await resp.text())[:500]
                except Exception:
                    pass
                
                structure_consistent = "html" in content_type.lower() or "<" in body_sample
                
                return {
                    "source": source.name,
                    "accessible": resp.status < 400,
                    "status_code": resp.status,
                    "content_type": content_type,
                    "sample_count": len(body_sample),
                    "schema_hints": ["html"] if structure_consistent else [],
                    "pages_tested": 1,
                    "structure_consistent": structure_consistent
                }
        except Exception as e:
            if config.is_production:
                raise RuntimeError(
                    f"Production mode requires successful data probe for {source.name}: {e}"
                )
            return {
                "source": source.name,
                "accessible": False,
                "status_code": 0,
                "content_type": "error",
                "sample_count": 0,
                "schema_hints": [],
                "error": str(e)
            }
    
    def _calculate_consistency(self, results: List[Dict]) -> float:
        """Calculate data consistency across sources"""
        if not results:
            return 0.5
        
        accessible = [r for r in results if r.get("accessible")]
        if not accessible:
            return 0.0
        
        # Check if formats are consistent
        formats = set(r.get("format", "unknown") for r in accessible)
        consistency = 1.0 - (len(formats) - 1) * 0.2
        
        return max(0.0, min(1.0, consistency))
    
    def _calculate_automation_potential(
        self, 
        results: List[Dict], 
        keywords: List[Any]
    ) -> float:
        """Calculate automation potential score (0-10)"""
        score = 5.0
        
        # More accessible sources = higher score
        accessible = sum(1 for r in results if r.get("accessible"))
        score += accessible * 0.5
        
        # API access = higher score than scraping
        api_count = sum(1 for r in results if r.get("format") == "json")
        score += api_count * 1.0
        
        # Structured data sources = higher score
        for r in results:
            if r.get("structure_consistent"):
                score += 0.5
        
        # Keyword characteristics affect automation
        template_keywords = sum(1 for k in keywords if k.intent in ["commercial", "comparison"])
        score += template_keywords * 0.3
        
        return min(10.0, score)


class MonetizationAnalyzer:
    """Analyzes monetization potential"""
    
    AFFILIATE_PROGRAMS = {
        "ev_charger": [
            {"name": "ChargePoint", "commission": "$50-100/sale", "network": "Direct"},
            {"name": "Amazon Associates", "commission": "4%", "network": "Amazon"},
            {"name": "EVgo", "commission": "$25/signup", "network": "Impact"}
        ],
        "solar": [
            {"name": "SunPower", "commission": "$200-500/lead", "network": "Direct"},
            {"name": "Tesla Solar", "commission": "$100-250/lead", "network": "Direct"},
            {"name": "EnergySage", "commission": "$50/quote", "network": "CJ"}
        ],
        "real_estate": [
            {"name": "Zillow Premier Agent", "commission": "$20-50/lead", "network": "Direct"},
            {"name": "Realtor.com", "commission": "$15-30/lead", "network": "Direct"}
        ],
        "finance": [
            {"name": "NerdWallet", "commission": "$50-200/lead", "network": "Direct"},
            {"name": "Credit Karma", "commission": "$30-75/signup", "network": "Direct"}
        ],
        "health": [
            {"name": "Healthline", "commission": "$25-75/lead", "network": "Direct"},
            {"name": "WebMD", "commission": "$20-50/lead", "network": "Direct"}
        ],
        "general": [
            {"name": "Amazon Associates", "commission": "1-10%", "network": "Amazon"},
            {"name": "ShareASale", "commission": "Varies", "network": "ShareASale"},
            {"name": "CJ Affiliate", "commission": "Varies", "network": "CJ"}
        ]
    }
    
    async def analyze(self, opportunity: Opportunity) -> MonetizationPotential:
        """Analyze monetization potential"""
        print(f"  💰 Analyzing monetization for {opportunity.niche}...")
        
        # Find affiliate programs
        affiliate_programs = self._find_affiliate_programs(opportunity)
        
        # Calculate lead gen potential
        lead_gen = self._calculate_lead_gen_potential(opportunity)
        
        # Calculate ad potential
        ad_potential = self._calculate_ad_potential(opportunity)
        
        # Calculate subscription potential
        subscription = self._calculate_subscription_potential(opportunity)
        
        # Estimate monthly revenue
        estimated_revenue = self._estimate_revenue(
            opportunity, affiliate_programs, lead_gen, ad_potential
        )
        
        # Calculate overall score
        score = self._calculate_score(
            affiliate_programs, lead_gen, ad_potential, subscription, estimated_revenue
        )
        
        return MonetizationPotential(
            score=score,
            affiliate_programs=affiliate_programs,
            lead_gen_potential=lead_gen,
            ad_potential=ad_potential,
            subscription_potential=subscription,
            estimated_monthly_revenue=estimated_revenue
        )
    
    def _find_affiliate_programs(self, opportunity: Opportunity) -> List[Dict]:
        """Find relevant affiliate programs"""
        niche = opportunity.niche.lower()
        programs = []
        
        # Match niche to affiliate categories
        for category, progs in self.AFFILIATE_PROGRAMS.items():
            if category in niche or any(category in kw.keyword for kw in opportunity.keywords):
                programs.extend(progs)
        
        # Add general programs if no specific matches
        if not programs:
            programs = self.AFFILIATE_PROGRAMS["general"]
        
        return programs[:5]  # Return top 5
    
    def _calculate_lead_gen_potential(self, opportunity: Opportunity) -> float:
        """Calculate lead generation potential (0-10)"""
        score = 5.0
        
        # High commercial intent = better lead gen
        commercial_keywords = sum(
            1 for k in opportunity.keywords 
            if k.intent in ["commercial", "transactional"]
        )
        score += commercial_keywords * 0.5
        
        # High CPC = valuable leads
        high_cpc = sum(1 for k in opportunity.keywords if k.cpc > 2.0)
        score += high_cpc * 0.3
        
        # Local intent = good for lead gen
        local_keywords = sum(1 for k in opportunity.keywords if "near me" in k.keyword)
        score += local_keywords * 0.8
        
        return min(10.0, score)
    
    def _calculate_ad_potential(self, opportunity: Opportunity) -> float:
        """Calculate advertising potential (0-10)"""
        score = 5.0
        
        # High volume = good for ads
        high_volume = sum(1 for k in opportunity.keywords if k.monthly_volume > 5000)
        score += high_volume * 0.3
        
        # Informational content = good for display ads
        info_keywords = sum(1 for k in opportunity.keywords if k.intent == "informational")
        score += info_keywords * 0.2
        
        return min(10.0, score)
    
    def _calculate_subscription_potential(self, opportunity: Opportunity) -> float:
        """Calculate subscription potential (0-10)"""
        score = 3.0  # Default low for most niches
        
        # B2B/data-heavy niches = better for subscriptions
        b2b_indicators = ["database", "api", "enterprise", "professional", "industry"]
        niche_lower = opportunity.niche.lower()
        
        if any(ind in niche_lower for ind in b2b_indicators):
            score += 3.0
        
        # High-value data = subscription potential
        if opportunity.data_availability_score > 7:
            score += 2.0
        
        return min(10.0, score)
    
    def _estimate_revenue(
        self,
        opportunity: Opportunity,
        affiliate_programs: List[Dict],
        lead_gen: float,
        ad_potential: float
    ) -> float:
        """Estimate monthly revenue potential"""
        # Base calculation on keyword volumes
        total_monthly_searches = sum(k.monthly_volume for k in opportunity.keywords[:5])
        
        # Conservative conversion assumptions
        traffic_capture_rate = 0.05  # 5% of searches become visitors
        visitors = total_monthly_searches * traffic_capture_rate
        
        # Revenue per visitor by channel
        affiliate_revenue = visitors * 0.02 * 10  # 2% click, $10 avg commission
        lead_gen_revenue = visitors * 0.01 * 50  # 1% convert, $50 per lead
        ad_revenue = visitors * 0.003 * 5  # $5 RPM
        
        total = affiliate_revenue + lead_gen_revenue + ad_revenue
        
        return round(total, 2)
    
    def _calculate_score(
        self,
        affiliate_programs: List[Dict],
        lead_gen: float,
        ad_potential: float,
        subscription: float,
        estimated_revenue: float
    ) -> float:
        """Calculate overall monetization score"""
        # Weight factors
        weights = {
            "affiliate": 0.25,
            "lead_gen": 0.30,
            "ads": 0.20,
            "subscription": 0.15,
            "revenue": 0.10
        }
        
        # Normalize scores
        affiliate_score = min(len(affiliate_programs) * 2, 10)
        revenue_score = min(estimated_revenue / 100, 10)
        
        overall = (
            affiliate_score * weights["affiliate"] +
            lead_gen * weights["lead_gen"] +
            ad_potential * weights["ads"] +
            subscription * weights["subscription"] +
            revenue_score * weights["revenue"]
        )
        
        return round(overall, 1)


class KeywordValidator:
    """Validates keyword difficulty and opportunity"""
    
    def __init__(self):
        self._snapshot: Optional[List[Dict[str, Any]]] = None
    
    def _load_snapshot(self) -> List[Dict[str, Any]]:
        """Load manual CSV keyword/SERP snapshot if configured"""
        if self._snapshot is not None:
            return self._snapshot
        
        self._snapshot = []
        path = config.validation.keyword_snapshot_path
        if path and Path(path).exists():
            import csv
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self._snapshot.append({
                        "keyword": row.get("keyword", "").strip().strip('"').lower(),
                        "volume": int(row.get("volume", 0) or 0),
                        "difficulty": float(row.get("difficulty", 0) or 0),
                        "cpc": float(row.get("cpc", 0) or 0),
                        "source": row.get("source", "manual_snapshot").strip().strip('"'),
                        "captured_date": row.get("captured_date", "").strip().strip('"'),
                    })
        return self._snapshot
    
    def _lookup_snapshot(self, keyword: str) -> Optional[Dict[str, Any]]:
        """Look up a keyword in the manual snapshot"""
        snapshot = self._load_snapshot()
        keyword_lower = keyword.strip().lower()
        for entry in snapshot:
            if entry["keyword"] == keyword_lower:
                return entry
        return None
    
    async def validate(self, opportunity: Opportunity) -> Dict[str, Any]:
        """Validate keywords for the opportunity"""
        print(f"  🔑 Validating keywords for {opportunity.niche}...")
        
        results = {
            "template_keywords": [],
            "avg_difficulty": 0.0,
            "total_volume": 0,
            "opportunity_score": 0.0,
            "snapshot_hits": 0,
            "snapshot_source": config.validation.keyword_snapshot_path,
        }
        
        keywords = opportunity.keywords
        if not keywords:
            return results
        
        # Enrich keywords from snapshot if available
        snapshot = self._load_snapshot()
        for kw in keywords:
            entry = self._lookup_snapshot(kw.keyword)
            if entry:
                kw.monthly_volume = entry.get("volume", kw.monthly_volume)
                kw.difficulty = entry.get("difficulty", kw.difficulty)
                kw.cpc = entry.get("cpc", kw.cpc)
                results["snapshot_hits"] += 1
        
        # If not in demo and no snapshot data available, opportunity score should be low
        if not config.is_demo and not snapshot:
            results["opportunity_score"] = 0.0
            return results
        
        # Identify template keywords (programmatic SEO opportunities)
        for kw in keywords:
            if self._is_template_keyword(kw.keyword):
                results["template_keywords"].append(kw.keyword)
        
        # Calculate averages
        results["avg_difficulty"] = sum(k.difficulty for k in keywords) / len(keywords)
        results["total_volume"] = sum(k.monthly_volume for k in keywords)
        
        # Calculate opportunity score
        difficulty_factor = max(0, (50 - results["avg_difficulty"]) / 50)
        volume_factor = min(results["total_volume"] / 50000, 1.0)
        template_factor = len(results["template_keywords"]) / max(len(keywords), 1)
        
        results["opportunity_score"] = (
            difficulty_factor * 0.4 +
            volume_factor * 0.4 +
            template_factor * 0.2
        ) * 10
        
        return results
    
    def _is_template_keyword(self, keyword: str) -> bool:
        """Check if keyword is a template opportunity"""
        template_patterns = [
            " in ", " near ", " by ", " for ", " vs ", " vs. ",
            "best ", "top ", "compare ", "comparison"
        ]
        return any(pattern in keyword.lower() for pattern in template_patterns)


class Midwife:
    """
    The Midwife Validation Agent
    
    Performs 48-hour viability tests:
    1. Scrapes sample data points to test fragmentation
    2. Checks keyword difficulty for template keywords
    3. Validates affiliate/lead-gen potential
    4. Gates: Only niches scoring >7/10 proceed
    """
    
    def __init__(self, storage: Storage = None):
        self.storage = storage or Storage()
        self.fragmentation_analyzer = FragmentationAnalyzer()
        self.monetization_analyzer = MonetizationAnalyzer()
        self.keyword_validator = KeywordValidator()
    
    async def validate(self, opportunity: Opportunity) -> ValidationResult:
        """Validate a single opportunity"""
        print(f"\n🧪 Midwife: Validating {opportunity.niche}...")
        
        start_time = datetime.now()
        notes = []
        
        # Step 1: Analyze fragmentation
        fragmentation = await self.fragmentation_analyzer.analyze(opportunity)
        opportunity.fragmentation = fragmentation
        
        notes.append(f"Fragmentation score: {fragmentation.score:.2f}")
        notes.append(f"Data points found: {fragmentation.data_points_found}")
        notes.append(f"Automation potential: {fragmentation.automation_potential:.1f}/10")
        
        # Record data probe evidence
        self.storage.save_evidence(Evidence(
            evidence_type="data_probe",
            opportunity_id=opportunity.id,
            data={
                "fragmentation_score": fragmentation.score,
                "data_points_found": fragmentation.data_points_found,
                "sources_analyzed": fragmentation.sources_analyzed,
                "automation_potential": fragmentation.automation_potential,
                "consistency_rating": fragmentation.consistency_rating,
            }
        ))
        
        # Step 2: Analyze monetization
        monetization = await self.monetization_analyzer.analyze(opportunity)
        opportunity.monetization = monetization
        
        notes.append(f"Monetization score: {monetization.score:.1f}/10")
        notes.append(f"Estimated MRR: ${monetization.estimated_monthly_revenue}")
        notes.append(f"Affiliate programs found: {len(monetization.affiliate_programs)}")
        
        # Record monetization evidence
        self.storage.save_evidence(Evidence(
            evidence_type="monetization",
            opportunity_id=opportunity.id,
            data={
                "score": monetization.score,
                "estimated_monthly_revenue": monetization.estimated_monthly_revenue,
                "affiliate_programs": [p["name"] for p in monetization.affiliate_programs],
                "lead_gen_potential": monetization.lead_gen_potential,
                "ad_potential": monetization.ad_potential,
            }
        ))
        
        # Step 3: Validate keywords
        keyword_results = await self.keyword_validator.validate(opportunity)
        
        notes.append(f"Template keywords: {len(keyword_results['template_keywords'])}")
        notes.append(f"Avg keyword difficulty: {keyword_results['avg_difficulty']:.1f}")
        
        # Record keyword evidence
        self.storage.save_evidence(Evidence(
            evidence_type="keyword",
            opportunity_id=opportunity.id,
            data={
                "avg_difficulty": keyword_results["avg_difficulty"],
                "total_volume": keyword_results["total_volume"],
                "opportunity_score": keyword_results["opportunity_score"],
                "template_keywords": keyword_results["template_keywords"],
            }
        ))
        
        # Calculate weighted validation score per MVP spec:
        # Data access 30%, Keyword/SERP 30%, Monetization 25%, Buildability/automation 15%
        data_score = min(fragmentation.automation_potential, 10.0)
        keyword_score = min(keyword_results["opportunity_score"], 10.0)
        monetization_score = min(monetization.score, 10.0)
        automation_score = min(fragmentation.automation_potential, 10.0)
        
        overall_score = (
            data_score * 0.30 +
            keyword_score * 0.30 +
            monetization_score * 0.25 +
            automation_score * 0.15
        )
        opportunity.validation_score = overall_score
        
        # Determine if passes gate
        passes = self._passes_gate(
            fragmentation, monetization, keyword_results, overall_score
        )
        
        validation_time = (datetime.now() - start_time).total_seconds() / 3600
        
        # Update opportunity status
        if passes:
            opportunity.status = OpportunityStatus.VALIDATED
            opportunity.validated_at = datetime.now()
            notes.append("✅ PASSED validation gate")
        else:
            opportunity.status = OpportunityStatus.REJECTED
            notes.append("❌ FAILED validation gate")
        
        self.storage.save_opportunity(opportunity)
        
        result = ValidationResult(
            opportunity_id=opportunity.id,
            passed=passes,
            fragmentation_score=fragmentation,
            monetization=monetization,
            overall_score=overall_score,
            validation_time_hours=validation_time,
            notes=notes
        )
        
        self._print_result(result)
        return result
    
    def _passes_gate(
        self,
        fragmentation: FragmentationScore,
        monetization: MonetizationPotential,
        keyword_results: Dict,
        overall_score: float
    ) -> bool:
        """Check if opportunity passes validation gate"""
        cfg = config.validation
        
        # Check fragmentation threshold (lower is better)
        if fragmentation.score > cfg.fragmentation_threshold:
            return False
        
        # Check automation score
        if fragmentation.automation_potential < cfg.min_automation_score:
            return False
        
        # Check monetization score
        if monetization.score < cfg.min_monetization_score:
            return False
        
        # Use stricter threshold in production
        min_score = cfg.production_pass_threshold if config.is_production else 5.0
        if overall_score < min_score:
            return False
        
        # Check keyword opportunity
        if keyword_results["opportunity_score"] < 1.0:  # More lenient
            return False
        
        return True
    
    def _print_result(self, result: ValidationResult):
        """Print validation result"""
        status = "✅ PASSED" if result.passed else "❌ FAILED"
        print(f"\n  {status}")
        print(f"  Overall Score: {result.overall_score:.1f}/10")
        print(f"  Validation Time: {result.validation_time_hours:.2f} hours")
        print(f"  Notes:")
        for note in result.notes:
            print(f"    • {note}")
    
    async def validate_queue(self) -> List[ValidationResult]:
        """Validate all opportunities in discovered queue"""
        opportunities = self.storage.get_opportunities_by_status(OpportunityStatus.DISCOVERED)
        
        print(f"\n🧪 Midwife: Validating {len(opportunities)} opportunities...")
        
        results = []
        for opp in opportunities:
            # Mark as validating
            opp.status = OpportunityStatus.VALIDATING
            self.storage.save_opportunity(opp)
            
            # Validate
            result = await self.validate(opp)
            results.append(result)
        
        # Update stats
        passed = sum(1 for r in results if r.passed)
        print(f"\n✅ Midwife: {passed}/{len(results)} opportunities passed validation")
        
        return results
    
    async def run_continuous(self):
        """Run validation continuously"""
        while True:
            try:
                await self.validate_queue()
                print("Validation cycle complete. Sleeping for 6 hours...")
                await asyncio.sleep(6 * 3600)
            except Exception as e:
                print(f"Error in validation cycle: {e}")
                await asyncio.sleep(3600)


# For direct execution
if __name__ == "__main__":
    async def main():
        from agents.red_queen import RedQueen
        
        # First discover some opportunities
        red_queen = RedQueen()
        opportunities = await red_queen.discover()
        
        if opportunities:
            # Validate them
            midwife = Midwife()
            results = await midwife.validate_queue()
            
            print("\n" + "="*60)
            print("VALIDATION RESULTS")
            print("="*60)
            
            for result in results:
                status = "✅ PASSED" if result.passed else "❌ FAILED"
                print(f"\n{status} - Score: {result.overall_score:.1f}/10")
        else:
            print("No opportunities to validate")
    
    asyncio.run(main())
