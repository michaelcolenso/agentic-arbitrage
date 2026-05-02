"""
The Red Queen (Discovery Agent)

Detects "pain-point pivots" — moments when user frustration correlates with 
data availability but precedes commercial solution.
"""
import asyncio
import aiohttp
# import praw  # Using web scraping instead
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json
import re
from collections import Counter

from core.models import (
    Opportunity, PainPoint, DataSource, KeywordOpportunity,
    OpportunityStatus, Evidence
)
from core.storage import Storage
from config.settings import config


@dataclass
class PainPivot:
    """A detected pain-point pivot opportunity"""
    niche: str
    pain_points: List[PainPoint]
    data_sources: List[DataSource]
    keywords: List[KeywordOpportunity]
    pain_velocity: float
    competition_gap: float
    description: str


class RedditMonitor:
    """Monitors Reddit for pain points and complaints.

    Reddit's www.reddit.com endpoints (JSON and RSS) reliably 403 from
    datacenter IPs regardless of User-Agent. Strategy, in priority order:

    1. Pushshift-style community mirrors (pullpush.io, arctic-shift) — return
       Reddit's native post shape via unauthenticated archive APIs.
    2. www.reddit.com /<sub>/<listing>.json — kept as a last resort for
       environments where Reddit isn't IP-blocking the caller.
    3. Mock seed pain points (demo/staging only).
    """

    PUSHSHIFT_MIRRORS = [
        "https://arctic-shift.photon-reddit.com/api/posts/search",
        "https://api.pullpush.io/reddit/search/submission",
    ]

    PAIN_PATTERNS = [
        r"hard to find",
        r"difficult to locate",
        r"where can i find",
        r"is there a list of",
        r"no central database",
        r"fragmented",
        r"scattered across",
        r"have to check multiple",
        r"no single source",
        r"wish there was",
        r"someone should create",
        r"would be helpful if",
        r"takes forever to",
        r"so complicated to",
        r"why isn't there",
    ]
    
    EV_SEARCH_PATTERNS = [
        r"ev charger rebate",
        r"level 2 charger rebate",
        r"charger tax credit",
        r"8911",
        r"30c",
        r"utility rebate",
        r"charger install cost",
        r"qualifying census tract",
    ]
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self._seen_hashes: set = set()
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; AgenticArbitrageFactory/1.0; +https://example.com/bot)"
                }
            )
        return self.session
    
    def _hash_pain(self, url: str, text: str) -> str:
        import hashlib
        normalized = (url or "").strip().lower() + "::" + text.strip().lower()[:200]
        return hashlib.md5(normalized.encode()).hexdigest()
    
    async def scan_subreddits(self, subreddits: List[str] = None) -> List[PainPoint]:
        """Scan subreddits for pain points across multiple unauthenticated sources."""
        subreddits = subreddits or config.discovery.reddit_subreddits
        pain_points: List[PainPoint] = []

        session = await self._get_session()

        for subreddit_name in subreddits:
            posts = await self._fetch_subreddit_posts(session, subreddit_name)
            for post in posts:
                pain = self._analyze_post(subreddit_name, post)
                if pain and self._dedupe(pain):
                    pain_points.append(pain)

        if not pain_points and not config.is_production:
            mock_points = self._get_mock_pain_points()
            for p in mock_points:
                if self._dedupe(p):
                    pain_points.append(p)

        return pain_points

    async def _fetch_subreddit_posts(
        self, session: aiohttp.ClientSession, subreddit_name: str
    ) -> List[Dict[str, Any]]:
        """Fetch posts for one subreddit, trying each source until one yields data."""
        for mirror in self.PUSHSHIFT_MIRRORS:
            posts = await self._fetch_via_pushshift(session, mirror, subreddit_name)
            if posts:
                print(f"  r/{subreddit_name}: {len(posts)} posts via {mirror.split('/')[2]}")
                return posts

        # Last resort: official Reddit (likely 403 from datacenter IPs)
        posts = await self._fetch_via_reddit(session, subreddit_name)
        if posts:
            print(f"  r/{subreddit_name}: {len(posts)} posts via www.reddit.com")
        return posts

    async def _fetch_via_pushshift(
        self, session: aiohttp.ClientSession, base_url: str, subreddit_name: str
    ) -> List[Dict[str, Any]]:
        """Fetch recent submissions from a Pushshift-compatible mirror."""
        # arctic-shift expects `limit`, pullpush expects `size`; both default to recent-first.
        if "arctic-shift" in base_url:
            params = {"subreddit": subreddit_name, "limit": 100, "sort": "desc"}
        else:
            params = {"subreddit": subreddit_name, "size": 100, "sort": "desc"}
        try:
            async with session.get(base_url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    print(f"  {base_url.split('/')[2]} r/{subreddit_name} returned {resp.status}")
                    return []
                payload = await resp.json()
            await asyncio.sleep(0.5)
            return payload.get("data", []) or []
        except Exception as e:
            print(f"  {base_url.split('/')[2]} r/{subreddit_name} error: {e}")
            return []

    async def _fetch_via_reddit(
        self, session: aiohttp.ClientSession, subreddit_name: str
    ) -> List[Dict[str, Any]]:
        """Fallback: hit www.reddit.com directly. Often 403s from cloud IPs."""
        collected: List[Dict[str, Any]] = []
        for listing in ["hot", "new"]:
            url = f"https://www.reddit.com/r/{subreddit_name}/{listing}.json"
            try:
                async with session.get(url, params={"limit": 50}, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status != 200:
                        print(f"  www.reddit.com r/{subreddit_name}/{listing} returned {resp.status}")
                        continue
                    data = await resp.json()
                    for post_wrapper in data.get("data", {}).get("children", []):
                        collected.append(post_wrapper.get("data", {}))
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"  www.reddit.com r/{subreddit_name}/{listing} error: {e}")
        return collected
    
    def _dedupe(self, pain: PainPoint) -> bool:
        h = self._hash_pain(pain.url, pain.text)
        if h in self._seen_hashes:
            return False
        self._seen_hashes.add(h)
        return True
    
    def _analyze_post(self, subreddit_name: str, post: Dict) -> Optional[PainPoint]:
        """Analyze a post for pain patterns"""
        title = post.get("title", "")
        selftext = post.get("selftext", "")
        text = f"{title} {selftext}".lower()
        
        # Check for general pain patterns OR EV-specific search patterns
        matched = False
        for pattern in self.PAIN_PATTERNS:
            if re.search(pattern, text):
                matched = True
                break
        if not matched:
            for pattern in self.EV_SEARCH_PATTERNS:
                if re.search(pattern, text):
                    matched = True
                    break
        
        if matched:
            sentiment = self._estimate_sentiment(text)
            keywords = self._extract_keywords(text)
            permalink = post.get("permalink", "")
            
            return PainPoint(
                source=f"reddit:r/{subreddit_name}",
                text=title,
                sentiment_score=sentiment,
                engagement=post.get("score", 0) + post.get("num_comments", 0),
                keywords=keywords,
                timestamp=datetime.fromtimestamp(post.get("created_utc", 0)),
                url=f"https://reddit.com{permalink}" if permalink else None
            )
        return None
    
    def _estimate_sentiment(self, text: str) -> float:
        """Simple sentiment estimation (-1 to 1)"""
        negative_words = ['frustrated', 'annoying', 'difficult', 'hard', 'impossible', 
                         'terrible', 'awful', 'hate', 'worst', 'pain', 'struggle']
        positive_words = ['easy', 'simple', 'great', 'love', 'best', 'helpful', 'useful']
        
        text_lower = text.lower()
        neg_count = sum(1 for w in negative_words if w in text_lower)
        pos_count = sum(1 for w in positive_words if w in text_lower)
        
        total = neg_count + pos_count
        if total == 0:
            return 0.0
        return (pos_count - neg_count) / total
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract potential keywords from text"""
        # Simple keyword extraction
        words = re.findall(r'\b[a-z]{4,}\b', text.lower())
        stopwords = {'this', 'that', 'with', 'from', 'they', 'have', 'there', 
                    'their', 'what', 'when', 'where', 'would', 'could', 'should'}
        words = [w for w in words if w not in stopwords]
        
        # Return most common words
        return [word for word, _ in Counter(words).most_common(5)]
    
    def _get_mock_pain_points(self) -> List[PainPoint]:
        """Generate mock pain points for testing"""
        mock_data = [
            {
                "text": "Why is it so hard to find all the EV charger rebates in one place?",
                "source": "reddit:r/electricvehicles",
                "keywords": ["ev charger", "rebates", "incentives"],
                "engagement": 245
            },
            {
                "text": "I wish there was a central database for all municipal zoning changes",
                "source": "reddit:r/realestateinvesting",
                "keywords": ["zoning", "municipal", "database"],
                "engagement": 189
            },
            {
                "text": "Takes forever to check multiple county sites for foreclosure auctions",
                "source": "reddit:r/realestateinvesting",
                "keywords": ["foreclosure", "auctions", "county"],
                "engagement": 312
            },
            {
                "text": "Is there a list of all active clinical trials for diabetes?",
                "source": "reddit:r/diabetes",
                "keywords": ["clinical trials", "diabetes", "list"],
                "engagement": 156
            },
            {
                "text": "Why isn't there a single source for all product recalls?",
                "source": "reddit:r/personalfinance",
                "keywords": ["product recalls", "safety", "database"],
                "engagement": 423
            },
            {
                "text": "Hard to find which patents are expiring soon in pharma",
                "source": "reddit:r/investing",
                "keywords": ["patents", "pharma", "expiring"],
                "engagement": 278
            },
            {
                "text": "No central place to compare solar panel installers by city",
                "source": "reddit:r/solar",
                "keywords": ["solar", "installers", "comparison"],
                "engagement": 198
            },
            {
                "text": "Wish someone would aggregate all the small business grants by state",
                "source": "reddit:r/smallbusiness",
                "keywords": ["small business", "grants", "state"],
                "engagement": 367
            }
        ]
        
        return [
            PainPoint(
                source=d["source"],
                text=d["text"],
                sentiment_score=-0.5,
                engagement=d["engagement"],
                keywords=d["keywords"],
                timestamp=datetime.now() - timedelta(hours=i*2)
            )
            for i, d in enumerate(mock_data)
        ]


class DataGovMonitor:
    """Monitors data.gov for new datasets"""
    
    DATA_GOV_BASE = "https://catalog.data.gov/api/3"
    
    async def get_recent_datasets(self, days: int = 7) -> List[DataSource]:
        """Get recently added datasets from data.gov"""
        async with aiohttp.ClientSession() as session:
            try:
                # Search for recent datasets
                params = {
                    "sort": "score desc",
                    "rows": 50,
                    "start": 0
                }
                async with session.get(
                    f"{self.DATA_GOV_BASE}/action/package_search", 
                    params=params
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return self._parse_datasets(data)
            except Exception as e:
                print(f"Error fetching data.gov: {e}")
        
        if config.is_production:
            raise RuntimeError(
                "Production mode requires successful data.gov access"
            )
        return self._get_mock_datasets()
    
    def _parse_datasets(self, data: Dict) -> List[DataSource]:
        """Parse data.gov API response"""
        datasets = []
        results = data.get("result", {}).get("results", [])
        
        for result in results:
            resources = result.get("resources", [])
            if not resources:
                continue
            
            # Get the best resource (prefer API, then CSV)
            best_resource = None
            for r in resources:
                fmt = r.get("format", "").lower()
                if "api" in fmt or "json" in fmt:
                    best_resource = r
                    break
                elif "csv" in fmt and not best_resource:
                    best_resource = r
            
            if not best_resource:
                best_resource = resources[0]
            
            datasets.append(DataSource(
                name=result.get("title", "Unknown"),
                url=best_resource.get("url", ""),
                type="api" if "api" in best_resource.get("format", "").lower() else "dataset",
                schema=self._infer_schema(result),
                update_frequency=result.get("frequency", "unknown"),
                quality_score=self._calculate_quality(result),
                last_updated=datetime.now()
            ))
        
        return datasets
    
    def _infer_schema(self, result: Dict) -> Dict[str, Any]:
        """Infer data schema from dataset metadata"""
        notes = result.get("notes", "")
        # Extract potential fields from description
        fields = []
        if "name" in notes.lower():
            fields.append("name")
        if "address" in notes.lower():
            fields.append("address")
        if "date" in notes.lower() or "time" in notes.lower():
            fields.append("date")
        if "location" in notes.lower() or "city" in notes.lower():
            fields.append("location")
        
        return {"fields": fields, "description": notes[:200]}
    
    def _calculate_quality(self, result: Dict) -> float:
        """Calculate quality score for dataset"""
        score = 5.0
        
        # More resources = better
        resources = result.get("resources", [])
        if len(resources) > 1:
            score += 1
        
        # Has organization = better
        if result.get("organization"):
            score += 1
        
        # Recent update = better
        if result.get("metadata_modified"):
            score += 1
        
        # Has tags = better
        if result.get("tags"):
            score += 1
        
        return min(score, 10.0)
    
    def _get_mock_datasets(self) -> List[DataSource]:
        """Generate mock datasets for testing"""
        mock_data = [
            {
                "name": "EV Charging Station Rebates Database",
                "url": "https://afdc.energy.gov/data_download",
                "type": "api",
                "schema": {"fields": ["state", "rebate_amount", "eligible_vehicles"]},
                "update_frequency": "monthly",
                "quality_score": 8.5
            },
            {
                "name": "Clinical Trials API",
                "url": "https://clinicaltrials.gov/api/query",
                "type": "api",
                "schema": {"fields": ["nct_id", "condition", "intervention", "status"]},
                "update_frequency": "daily",
                "quality_score": 9.0
            },
            {
                "name": "USPTO Patent Grants",
                "url": "https://developer.uspto.gov/api/patents",
                "type": "api",
                "schema": {"fields": ["patent_number", "title", "assignee", "expiration_date"]},
                "update_frequency": "weekly",
                "quality_score": 8.0
            },
            {
                "name": "CPSC Product Recalls",
                "url": "https://www.cpsc.gov/cgibin/recalls/feed",
                "type": "api",
                "schema": {"fields": ["product_name", "recall_date", "hazard", "remedy"]},
                "update_frequency": "daily",
                "quality_score": 7.5
            },
            {
                "name": "Small Business Grants by State",
                "url": "https://grants.gov/grantsws/rest/opportunities/search/",
                "type": "api",
                "schema": {"fields": ["title", "agency", "deadline", "eligibility"]},
                "update_frequency": "weekly",
                "quality_score": 8.0
            }
        ]
        
        return [
            DataSource(
                name=d["name"],
                url=d["url"],
                type=d["type"],
                schema=d["schema"],
                update_frequency=d["update_frequency"],
                quality_score=d["quality_score"],
                last_updated=datetime.now()
            )
            for d in mock_data
        ]


class KeywordResearcher:
    """Researches keywords for opportunities"""
    
    async def research_keywords(self, niche: str, pain_points: List[str]) -> List[KeywordOpportunity]:
        """Research keywords for a niche"""
        # In production, this would use Ahrefs API, Google Keyword Planner, etc.
        # For now, generate plausible keywords based on niche
        
        keywords = []
        base_terms = self._generate_base_terms(niche, pain_points)
        
        for term in base_terms:
            # Generate variations
            variations = [
                term,
                f"best {term}",
                f"{term} near me",
                f"{term} comparison",
                f"{term} database",
                f"{term} list",
                f"how to find {term}",
                f"{term} guide"
            ]
            
            for kw in variations:
                volume, difficulty = self._estimate_metrics(kw, term)
                keywords.append(KeywordOpportunity(
                    keyword=kw,
                    monthly_volume=volume,
                    difficulty=difficulty,
                    cpc=self._estimate_cpc(kw),
                    intent=self._classify_intent(kw),
                    related_keywords=[v for v in variations if v != kw][:3],
                    trending=volume > 5000
                ))
        
        # Sort by volume and return top keywords
        return sorted(keywords, key=lambda x: x.monthly_volume, reverse=True)[:10]
    
    def _generate_base_terms(self, niche: str, pain_points: List[str]) -> List[str]:
        """Generate base search terms from niche and pain points"""
        terms = [niche.replace("_", " ")]
        
        # Extract terms from pain points
        for pain in pain_points:
            words = pain.lower().split()
            # Look for noun phrases
            for i, word in enumerate(words):
                if word in ["find", "search", "looking", "need"] and i < len(words) - 1:
                    phrase = " ".join(words[i+1:i+4])
                    if len(phrase) > 5:
                        terms.append(phrase)
        
        return list(set(terms))[:5]
    
    def _estimate_metrics(self, keyword: str, base_term: str) -> tuple:
        """Estimate search volume and difficulty"""
        # Simple estimation based on keyword characteristics
        base_volume = 1000
        
        # Longer keywords = lower volume
        word_count = len(keyword.split())
        volume_modifier = max(0.3, 1.5 - (word_count * 0.2))
        
        # Modifiers affect volume
        if "best" in keyword:
            volume_modifier *= 1.5
        if "near me" in keyword:
            volume_modifier *= 2.0
        if "how to" in keyword:
            volume_modifier *= 1.3
        
        volume = int(base_volume * volume_modifier * (0.8 + hash(keyword) % 40 / 100))
        
        # Difficulty estimation
        difficulty = 20 + (word_count * 5) + (hash(keyword) % 30)
        if "best" in keyword or "comparison" in keyword:
            difficulty += 10
        
        return volume, min(difficulty, 100)
    
    def _estimate_cpc(self, keyword: str) -> float:
        """Estimate cost per click"""
        base_cpc = 1.0
        
        # Commercial intent = higher CPC
        if any(w in keyword for w in ["best", "top", "comparison", "vs"]):
            base_cpc *= 2.5
        if "near me" in keyword:
            base_cpc *= 1.8
        if any(w in keyword for w in ["buy", "price", "cost"]):
            base_cpc *= 3.0
        
        return round(base_cpc, 2)
    
    def _classify_intent(self, keyword: str) -> str:
        """Classify search intent"""
        if any(w in keyword for w in ["buy", "price", "cost", "deal"]):
            return "transactional"
        elif any(w in keyword for w in ["how to", "guide", "tutorial"]):
            return "informational"
        elif any(w in keyword for w in ["best", "top", "comparison", "vs"]):
            return "commercial"
        elif any(w in keyword for w in ["database", "list", "find", "search"]):
            return "navigational"
        else:
            return "informational"


class RedQueen:
    """
    The Red Queen Discovery Agent
    
    Detects pain-point pivots by correlating:
    - User frustration (Reddit anger)
    - Data availability (new datasets)
    - Competition gap (low commercial solution)
    """
    
    def __init__(self, storage: Storage = None):
        self.storage = storage or Storage()
        self.reddit_monitor = RedditMonitor()
        self.data_gov_monitor = DataGovMonitor()
        self.keyword_researcher = KeywordResearcher()
    
    async def discover(self) -> List[Opportunity]:
        """Run discovery cycle and return new opportunities"""
        print("🎯 Red Queen: Starting discovery cycle...")
        
        # Gather inputs in parallel
        pain_points_task = self.reddit_monitor.scan_subreddits()
        datasets_task = self.data_gov_monitor.get_recent_datasets()
        
        pain_points, datasets = await asyncio.gather(
            pain_points_task, datasets_task
        )
        
        print(f"  Found {len(pain_points)} pain points")
        print(f"  Found {len(datasets)} data sources")
        
        # Correlate pain points with data sources
        pivots = self._correlate_pain_with_data(pain_points, datasets)
        print(f"  Identified {len(pivots)} pain-point pivots")
        
        # Convert pivots to opportunities
        opportunities = []
        for pivot in pivots:
            opp = await self._create_opportunity(pivot)
            if opp:
                opportunities.append(opp)
                self.storage.save_opportunity(opp)
                
                # Record discovery evidence for the first pain point
                if pivot.pain_points:
                    first_pain = pivot.pain_points[0]
                    self.storage.save_evidence(Evidence(
                        evidence_type="discovery",
                        opportunity_id=opp.id,
                        data={
                            "source": first_pain.source,
                            "url": first_pain.url,
                            "snippet": first_pain.text[:300],
                            "timestamp": first_pain.timestamp.isoformat(),
                            "engagement": first_pain.engagement,
                            "theme": pivot.niche,
                            "confidence": 0.7,
                        }
                    ))
        
        print(f"✅ Red Queen: Created {len(opportunities)} new opportunities")
        return opportunities
    
    def _correlate_pain_with_data(
        self, 
        pain_points: List[PainPoint], 
        datasets: List[DataSource]
    ) -> List[PainPivot]:
        """Correlate pain points with available data sources"""
        pivots = []
        
        # Group pain points by theme
        pain_themes = self._cluster_pain_points(pain_points)
        
        for theme, points in pain_themes.items():
            # Find matching datasets
            matching_datasets = self._find_matching_datasets(theme, datasets)
            
            if not matching_datasets:
                continue
            
            # Calculate metrics
            pain_velocity = self._calculate_pain_velocity(points)
            competition_gap = self._estimate_competition_gap(theme, points)
            
            # Only proceed if thresholds met (more lenient for demo)
            if pain_velocity < 2.0:  # Very lenient
                continue
            if competition_gap > 0.8:  # Very lenient
                continue
            
            # Generate niche name
            niche = self._generate_niche_name(theme, matching_datasets[0])
            
            pivots.append(PainPivot(
                niche=niche,
                pain_points=points,
                data_sources=matching_datasets,
                keywords=[],  # Will be filled later
                pain_velocity=pain_velocity,
                competition_gap=competition_gap,
                description=self._generate_description(points, matching_datasets)
            ))
        
        return pivots
    
    def _cluster_pain_points(self, pain_points: List[PainPoint]) -> Dict[str, List[PainPoint]]:
        """Cluster pain points by theme/topic"""
        themes = {}
        
        for point in pain_points:
            # Use keywords to determine theme
            theme = self._identify_theme(point.keywords, point.text)
            
            if theme not in themes:
                themes[theme] = []
            themes[theme].append(point)
        
        # Only keep themes with multiple pain points
        return {k: v for k, v in themes.items() if len(v) >= 1}
    
    def _identify_theme(self, keywords: List[str], text: str) -> str:
        """Identify the theme of a pain point"""
        # Map keywords to themes
        theme_mapping = {
            "ev charger": "ev_charger_rebates",
            "electric vehicle": "ev_charger_rebates",
            "rebate": "ev_charger_rebates",
            "incentive": "ev_charger_rebates",
            "zoning": "municipal_zoning",
            "municipal": "municipal_zoning",
            "foreclosure": "foreclosure_auctions",
            "auction": "foreclosure_auctions",
            "sheriff sale": "foreclosure_auctions",
            "clinical trial": "clinical_trials",
            "diabetes": "clinical_trials",
            "recall": "product_recalls",
            "safety": "product_recalls",
            "patent": "patent_expirations",
            "uspto": "patent_expirations",
            "solar": "solar_installers",
            "panel": "solar_installers",
            "small business": "small_business_grants",
            "grant": "small_business_grants",
            "sba": "small_business_grants"
        }
        
        text_lower = text.lower()
        for key, theme in theme_mapping.items():
            if key in text_lower or any(key in kw for kw in keywords):
                return theme
        
        # Default theme from keywords
        if keywords:
            return "_".join(keywords[:2])
        return "general"
    
    def _find_matching_datasets(
        self, 
        theme: str, 
        datasets: List[DataSource]
    ) -> List[DataSource]:
        """Find datasets that match a theme"""
        matches = []
        theme_keywords = theme.replace("_", " ").split()
        
        for dataset in datasets:
            dataset_text = f"{dataset.name} {dataset.schema.get('description', '')}".lower()
            
            # Check for keyword matches
            score = sum(1 for kw in theme_keywords if kw in dataset_text)
            
            if score >= 1:
                matches.append((score, dataset))
        
        # Return sorted by match score
        matches.sort(key=lambda x: x[0], reverse=True)
        return [d for _, d in matches[:3]]
    
    def _calculate_pain_velocity(self, pain_points: List[PainPoint]) -> float:
        """Calculate how 'hot' a pain point is"""
        if not pain_points:
            return 0.0
        
        # Factors:
        # - Total engagement
        # - Recency
        # - Sentiment intensity
        
        total_engagement = sum(p.engagement for p in pain_points)
        avg_sentiment = sum(abs(p.sentiment_score) for p in pain_points) / len(pain_points)
        
        # Recency bonus
        now = datetime.now()
        recent_count = sum(1 for p in pain_points if (now - p.timestamp).days < 7)
        recency_factor = 1 + (recent_count / len(pain_points))
        
        # Normalize to 0-10 scale
        velocity = (min(total_engagement, 1000) / 100) * avg_sentiment * recency_factor
        return min(velocity, 10.0)
    
    def _estimate_competition_gap(self, theme: str, pain_points: List[PainPoint]) -> float:
        """Estimate how underserved this niche is (0-1, lower = less competition)"""
        # In production, this would check:
        # - Number of existing sites
        # - Domain authority of competitors
        # - Content quality of existing solutions
        
        # For now, estimate based on pain point characteristics
        base_gap = 0.5
        
        # Government data = less competition
        if any(kw in theme for kw in ["government", "municipal", "county", "federal"]):
            base_gap -= 0.2
        
        # Fragmented data = less competition
        fragmented_indicators = ["multiple", "scattered", "fragmented", "no central"]
        for pain in pain_points:
            if any(ind in pain.text.lower() for ind in fragmented_indicators):
                base_gap -= 0.15
                break
        
        # High engagement but no solution = big gap
        total_engagement = sum(p.engagement for p in pain_points)
        if total_engagement > 500:
            base_gap -= 0.1
        
        return max(0.0, min(1.0, base_gap))
    
    def _generate_niche_name(self, theme: str, primary_dataset: DataSource) -> str:
        """Generate a clean niche name"""
        # Use theme if it's already good
        if len(theme) > 5 and "_" in theme:
            return theme
        
        # Generate from dataset name
        dataset_name = primary_dataset.name.lower()
        
        # Extract key terms
        terms = []
        for word in dataset_name.split():
            if word not in ["database", "api", "dataset", "the", "of", "and"]:
                terms.append(word)
        
        return "_".join(terms[:3])
    
    def _generate_description(
        self, 
        pain_points: List[PainPoint], 
        datasets: List[DataSource]
    ) -> str:
        """Generate opportunity description"""
        pain_summary = pain_points[0].text[:100] if pain_points else ""
        data_summary = datasets[0].name if datasets else ""
        
        return (
            f"Users struggle with: '{pain_summary}...' "
            f"Available data: {data_summary}"
        )
    
    async def _create_opportunity(self, pivot: PainPivot) -> Optional[Opportunity]:
        """Create a full opportunity from a pivot"""
        # Research keywords
        pain_texts = [p.text for p in pivot.pain_points]
        keywords = await self.keyword_researcher.research_keywords(
            pivot.niche, pain_texts
        )
        
        # Filter keywords
        valid_keywords = [
            k for k in keywords 
            if k.monthly_volume >= config.discovery.min_monthly_searches
            and k.difficulty <= config.discovery.max_keyword_difficulty
        ]
        
        if not valid_keywords:
            return None
        
        pivot.keywords = valid_keywords
        
        # Create opportunity
        opp = Opportunity(
            niche=pivot.niche,
            description=pivot.description,
            status=OpportunityStatus.DISCOVERED,
            pain_velocity=pivot.pain_velocity,
            competition_gap=pivot.competition_gap,
            data_availability_score=sum(d.quality_score for d in pivot.data_sources) / len(pivot.data_sources),
            pain_points=pivot.pain_points,
            data_sources=pivot.data_sources,
            keywords=pivot.keywords
        )
        
        return opp
    
    async def run_continuous(self, interval_hours: int = None):
        """Run discovery continuously"""
        interval = interval_hours or config.discovery_interval_hours
        
        while True:
            try:
                opportunities = await self.discover()
                print(f"Discovery cycle complete. Found {len(opportunities)} opportunities.")
                print(f"Sleeping for {interval} hours...")
                await asyncio.sleep(interval * 3600)
            except Exception as e:
                print(f"Error in discovery cycle: {e}")
                await asyncio.sleep(3600)  # Sleep 1 hour on error


# For direct execution
if __name__ == "__main__":
    async def main():
        red_queen = RedQueen()
        opportunities = await red_queen.discover()
        
        print("\n" + "="*60)
        print("DISCOVERED OPPORTUNITIES")
        print("="*60)
        
        for opp in opportunities:
            print(f"\n🎯 {opp.niche}")
            print(f"   Pain Velocity: {opp.pain_velocity:.1f}/10")
            print(f"   Competition Gap: {opp.competition_gap:.2f}")
            print(f"   Data Quality: {opp.data_availability_score:.1f}/10")
            print(f"   Top Keywords: {', '.join(k.keyword for k in opp.keywords[:3])}")
            print(f"   Description: {opp.description[:100]}...")
    
    asyncio.run(main())
