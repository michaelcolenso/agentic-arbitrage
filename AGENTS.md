# 🤖 Agent Documentation

Detailed documentation for each agent in the Agentic Arbitrage Factory.

## Table of Contents

1. [The Red Queen (Discovery Agent)](#the-red-queen)
2. [The Midwife (Validation Agent)](#the-midwife)
3. [The Constructor (Build Agent)](#the-constructor)
4. [The Mortician (Culling Agent)](#the-mortician)
5. [Agent Communication](#agent-communication)
6. [Extending Agents](#extending-agents)

---

## The Red Queen

> *"The Red Queen must run as fast as she can just to stay in place."*

The Red Queen is the discovery agent responsible for finding and scoring opportunities.

### Purpose

Detects "pain-point pivots" — moments when:
1. User frustration is high (Reddit anger)
2. Data is available (new datasets published)
3. Commercial solutions are lacking (low competition)

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    The Red Queen                             │
├─────────────────────────────────────────────────────────────┤
│  RedditMonitor ──→ PainPoint Detection                       │
│       ↓                                                      │
│  DataGovMonitor ─→ DataSource Discovery                      │
│       ↓                                                      │
│  KeywordResearcher → Opportunity Validation                  │
│       ↓                                                      │
│  Opportunity Creation → Storage                              │
└─────────────────────────────────────────────────────────────┘
```

### Components

#### RedditMonitor

Monitors Reddit for pain points using web scraping.

**Pain Patterns Detected:**
- "hard to find"
- "difficult to locate"
- "where can i find"
- "is there a list of"
- "no central database"
- "fragmented"
- "scattered across"
- "have to check multiple"
- "no single source"
- "wish there was"
- "someone should create"
- "would be helpful if"
- "takes forever to"
- "so complicated to"
- "why isn't there"

**Usage:**
```python
from agents.red_queen import RedditMonitor

monitor = RedditMonitor()
pain_points = await monitor.scan_subreddits(['personalfinance', 'smallbusiness'])
```

**Implementation Details:**
- Uses Reddit's public JSON API (no authentication required)
- Fetches both `/hot` and `/new` endpoints
- Extracts comments for deeper analysis
- Falls back to mock data if rate-limited

#### DataGovMonitor

Monitors data.gov for new datasets.

**Features:**
- Searches catalog.data.gov API
- Extracts dataset metadata
- Scores data quality
- Identifies API vs. scrape sources

**Usage:**
```python
from agents.red_queen import DataGovMonitor

monitor = DataGovMonitor()
datasets = await monitor.get_recent_datasets(days=7)
```

#### KeywordResearcher

Researches keywords for discovered niches.

**Metrics Generated:**
- Monthly search volume
- Keyword difficulty (0-100)
- Cost per click (CPC)
- Search intent (informational/commercial/transactional/navigational)
- Related keywords

**Usage:**
```python
from agents.red_queen import KeywordResearcher

researcher = KeywordResearcher()
keywords = await researcher.research_keywords("ev_charger_rebates", pain_texts)
```

### Opportunity Scoring

The Red Queen scores opportunities using:

#### Pain Velocity (0-10)
```
pain_velocity = (engagement_score × sentiment_intensity × recency_factor)
```

- **Engagement Score:** Total upvotes + comments
- **Sentiment Intensity:** Negative sentiment magnitude
- **Recency Factor:** Bonus for recent posts

#### Competition Gap (0-1)
```
competition_gap = base_gap - government_bonus - fragmentation_bonus - engagement_bonus
```

- Lower = less competition = better opportunity
- Government data sources reduce competition
- Fragmented data indicates underserved market

### Configuration

```python
# config/settings.py
class DiscoveryConfig:
    reddit_subreddits = [
        "personalfinance", "smallbusiness", "realestateinvesting",
        "legaladvice", "government", "dataisbeautiful", "webdev"
    ]
    pain_velocity_threshold = 2.0
    competition_gap_threshold = 0.8
    min_monthly_searches = 100
    max_keyword_difficulty = 60
```

### Output

Creates `Opportunity` objects with:
- Niche name
- Pain points list
- Data sources
- Keywords
- Scores (pain_velocity, competition_gap)

---

## The Midwife

> *"The Midwife validates viability in 48 hours or less."*

The Midwife validates discovered opportunities before they proceed to build.

### Purpose

Perform 48-hour viability tests:
1. Test data fragmentation (can we automate?)
2. Check keyword difficulty (can we rank?)
3. Validate monetization (can we make money?)

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    The Midwife                               │
├─────────────────────────────────────────────────────────────┤
│  FragmentationAnalyzer ──→ Automation Potential              │
│       ↓                                                      │
│  MonetizationAnalyzer ───→ Revenue Potential                 │
│       ↓                                                      │
│  KeywordValidator ───────→ Ranking Potential                 │
│       ↓                                                      │
│  Gate Decision ──────────→ Pass/Fail                         │
└─────────────────────────────────────────────────────────────┘
```

### Components

#### FragmentationAnalyzer

Tests how fragmented the data is (fragmentation = opportunity).

**Process:**
1. Scrapes sample data points from sources
2. Checks consistency across sources
3. Measures automation difficulty

**Scoring:**
```python
fragmentation_score = 0.0-1.0  # Lower = more fragmented = better
automation_potential = 0.0-10.0  # Higher = easier to automate
```

**Usage:**
```python
from agents.midwife import FragmentationAnalyzer

analyzer = FragmentationAnalyzer()
result = await analyzer.analyze(opportunity)
```

#### MonetizationAnalyzer

Analyzes monetization potential.

**Revenue Streams Evaluated:**
- Affiliate programs (Amazon, ShareASale, CJ, etc.)
- Lead generation potential
- Advertising potential
- Subscription potential

**Affiliate Database:**
- EV charger: ChargePoint, Amazon Associates, EVgo
- Solar: SunPower, Tesla Solar, EnergySage
- Real estate: Zillow, Realtor.com
- Finance: NerdWallet, Credit Karma
- Health: Healthline, WebMD

**Usage:**
```python
from agents.midwife import MonetizationAnalyzer

analyzer = MonetizationAnalyzer()
result = await analyzer.analyze(opportunity)
```

#### KeywordValidator

Validates keyword difficulty and opportunity.

**Metrics:**
- Average keyword difficulty
- Total search volume
- Template keyword count (programmatic SEO)
- Opportunity score

**Template Keywords:**
Keywords with patterns like:
- "[X] in [Y]" (e.g., "EV chargers in California")
- "[X] near me" (e.g., "EV charger rebates near me")
- "best [X] for [Y]" (e.g., "best EV charger for Tesla")

**Usage:**
```python
from agents.midwife import KeywordValidator

validator = KeywordValidator()
result = await validator.validate(opportunity)
```

### Validation Gate

An opportunity passes if ALL conditions are met:

```python
def passes_gate(fragmentation, monetization, keywords, overall_score):
    return (
        fragmentation.score <= 0.9 and
        fragmentation.automation_potential >= 4.0 and
        monetization.score >= 4.0 and
        overall_score >= 5.0 and
        keywords["opportunity_score"] >= 1.0
    )
```

### Configuration

```python
# config/settings.py
class ValidationConfig:
    test_sample_size = 10
    fragmentation_threshold = 0.9
    min_automation_score = 4.0
    min_monetization_score = 4.0
    validation_timeout_hours = 48
```

### Output

Creates `ValidationResult` with:
- Pass/fail status
- Fragmentation score
- Monetization score
- Overall score
- Detailed notes

---

## The Constructor

> *"The Constructor builds complete SEO sites in under 5 minutes."*

The Constructor generates complete, deployable websites from validated opportunities.

### Purpose

Generate production-ready sites:
1. Database schema
2. Scraping adapters
3. SEO-optimized pages
4. Deployment configuration

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   The Constructor                            │
├─────────────────────────────────────────────────────────────┤
│  SchemaGenerator ────────→ Database Schema                   │
│       ↓                                                      │
│  ScrapingAdapterGenerator → Data Adapters                    │
│       ↓                                                      │
│  TemplateGenerator ──────→ Page Templates                    │
│       ↓                                                      │
│  Project Builder ────────→ GitHub + Cloudflare               │
└─────────────────────────────────────────────────────────────┘
```

### Components

#### SchemaGenerator

Generates Drizzle ORM schemas from data sources.

**Generated Tables:**
- Main entity table (e.g., `ev_charger_rebates`)
- Supporting tables for each data source
- Indexes for SEO-optimized queries
- Relations between tables

**Example Output:**
```typescript
// schema.ts
export const evChargerRebates = sqliteTable('ev_charger_rebates', {
  id: integer('id').primaryKey(),
  name: text('name').notNull(),
  slug: text('slug').notNull().unique(),
  state: text('state').notNull(),
  rebateAmount: real('rebate_amount'),
  eligibleVehicles: text('eligible_vehicles', { mode: 'json' }),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull(),
});
```

**Usage:**
```python
from agents.constructor import SchemaGenerator

generator = SchemaGenerator()
schema = generator.generate(opportunity)
```

#### ScrapingAdapterGenerator

Generates data scraping adapters.

**Types:**
1. **API Adapters** - For REST APIs
2. **Scrape Adapters** - For web scraping

**Example Output:**
```typescript
// adapters/EvChargingStationRebatesAdapter.ts
export class EvChargingStationRebatesAdapter {
  async fetchAll(params = {}) {
    const url = new URL(this.baseUrl);
    // ... implementation
  }
  
  transform(data) {
    // Transform to our schema
  }
}
```

**Usage:**
```python
from agents.constructor import ScrapingAdapterGenerator

generator = ScrapingAdapterGenerator()
adapters = generator.generate(opportunity)
```

#### TemplateGenerator

Generates SEO-optimized page templates.

**Generated Pages:**
1. **Home** - Hero, search, stats, featured items
2. **List** - Filterable list of all entities
3. **Detail** - Individual entity page
4. **Compare** - Side-by-side comparison

**SEO Features:**
- Semantic HTML
- Meta tags (title, description)
- Structured data (JSON-LD)
- Breadcrumb navigation
- Internal linking

**Example Output:**
```tsx
// app/home.tsx
export default function Home({ stats, featured }) {
  return (
    <Layout
      title="EV Charger Rebates Database | Find & Compare"
      description="Comprehensive database of EV charger rebates..."
    >
      <Hero title="Find the Best EV Charger Rebates" />
      <Stats stats={stats} />
      <FeaturedList items={featured} />
    </Layout>
  );
}
```

**Usage:**
```python
from agents.constructor import TemplateGenerator

generator = TemplateGenerator()
templates = generator.generate(opportunity)
```

### Build Process

1. **Generate Schema** - Create database structure
2. **Generate Adapters** - Create data access layer
3. **Generate Templates** - Create page components
4. **Create Project Files** - Package.json, wrangler.toml, etc.
5. **Setup Database** - Create D1 database
6. **Deploy** - Push to Cloudflare Pages

### Configuration

```python
# config/settings.py
class BuildConfig:
    template_repo = "template-seo-site"
    stack = {
        "framework": "hono",
        "database": "d1",
        "styling": "tailwind",
        "orm": "drizzle"
    }
    build_timeout_minutes = 5
    deploy_target = "cloudflare"
    auto_submit_search_console = True
```

### Output

Creates:
- GitHub repository
- Cloudflare Pages project
- D1 database
- Deployed URL

---

## The Mortician

> *"The Mortician shows no mercy. Zero emotion. Pure Darwin."*

The Mortician manages the portfolio and culls underperforming sites.

### Purpose

Ruthless portfolio management:
1. Monitor all sites daily
2. Kill underperformers at day 90
3. 301 redirect domains to winners
4. Archive data for training

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   The Mortician                              │
├─────────────────────────────────────────────────────────────┤
│  TrafficMonitor ─────────→ Collect Metrics                   │
│       ↓                                                      │
│  PerformanceAnalyzer ────→ Score Sites                       │
│       ↓                                                      │
│  CullDecision ───────────→ Keep/Kill                         │
│       ↓                                                      │
│  SiteArchiver ───────────→ Archive Data                      │
└─────────────────────────────────────────────────────────────┘
```

### Components

#### TrafficMonitor

Monitors site traffic and performance.

**Metrics Collected:**
- Organic users
- Total users
- Pageviews
- Bounce rate
- Indexed pages
- Ranking keywords
- Backlinks
- Revenue (all streams)

**Usage:**
```python
from agents.mortician import TrafficMonitor

monitor = TrafficMonitor()
metrics = await monitor.get_metrics(site)
```

#### PerformanceAnalyzer

Analyzes site performance and makes culling decisions.

**Decision Rules:**
1. **Time-based:** If days_active >= 90 AND avg_traffic < 100/day → CULL
2. **Revenue-based:** If days_active >= 60 AND total_revenue < $10 → CULL
3. **Growth-based:** If traffic declining >30% over 14 days → CULL
4. **Winner:** If avg_traffic > 500/day → WINNER
5. **Promising:** If avg_traffic > 200/day AND days < 60 → PROMISING

**Usage:**
```python
from agents.mortician import PerformanceAnalyzer

analyzer = PerformanceAnalyzer()
decision = analyzer.analyze(site, metrics)
```

#### SiteArchiver

Archives culled site data.

**Archives:**
- Performance metrics history
- Revenue data
- Site configuration
- Codebase (optional)

**Insights Generated:**
- Why the site failed
- What could have been improved
- Patterns for future agents

**Usage:**
```python
from agents.mortician import SiteArchiver

archiver = SiteArchiver()
result = await archiver.archive(site, decision)
```

### Culling Process

1. **Collect Metrics** - Gather traffic and revenue data
2. **Analyze Performance** - Score each site
3. **Make Decisions** - Cull, promote, or keep
4. **Execute Culling** - 301 redirect, archive data
5. **Update Stats** - Track success rate

### Configuration

```python
# config/settings.py
class CullingConfig:
    traffic_threshold_per_day = 100
    evaluation_days = 90
    auto_301_to_winner = True
    archive_data = True
    recycle_codebase = True
```

### Output

Updates:
- Site status (culled/winner/promising)
- Opportunity status
- Factory stats
- Archive files

---

## Agent Communication

Agents communicate through the shared SQLite database:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Red Queen  │────→│  Midwife    │────→│ Constructor │
│  (Discovers)│     │ (Validates) │     │   (Builds)  │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       └───────────────────┴───────────────────┘
                           │
                    ┌─────────────┐
                    │   SQLite    │
                    │  Database   │
                    └─────────────┘
                           │
                    ┌─────────────┐
                    │  Mortician  │
                    │  (Manages)  │
                    └─────────────┘
```

### Data Flow

1. **Red Queen** → Creates `Opportunity` (status: DISCOVERED)
2. **Midwife** → Updates `Opportunity` (status: VALIDATED or rejected)
3. **Constructor** → Creates `Site`, updates `Opportunity` (status: DEPLOYED)
4. **Mortician** → Updates `Site` and `Opportunity` (status: CULLED/WINNER)

### Database Tables

- **opportunities** - Opportunity lifecycle
- **sites** - Site deployment status
- **site_metrics** - Performance data
- **factory_stats** - Overall statistics

---

## Extending Agents

### Creating a Custom Agent

1. **Create a new file** in `agents/`:

```python
# agents/custom_agent.py
from core.storage import Storage
from core.models import Opportunity

class CustomAgent:
    def __init__(self, storage: Storage = None):
        self.storage = storage or Storage()
    
    async def process(self, opportunity: Opportunity):
        # Your logic here
        pass
```

2. **Register in factory.py**:

```python
from agents.custom_agent import CustomAgent

class ArbitrageFactory:
    def __init__(self):
        # ... existing agents ...
        self.custom_agent = CustomAgent(self.storage)
    
    async def run_full_cycle(self):
        # ... existing phases ...
        await self.custom_agent.process(opportunity)
```

### Customizing Agent Behavior

Override methods in subclasses:

```python
from agents.red_queen import RedditMonitor

class CustomRedditMonitor(RedditMonitor):
    PAIN_PATTERNS = [
        # Your custom patterns
        r"my custom pattern",
        *super().PAIN_PATTERNS,  # Include defaults
    ]
    
    async def scan_subreddits(self, subreddits=None):
        # Custom logic
        pass
```

---

## Agent Metrics

Track agent performance:

| Agent | Metric | Target |
|-------|--------|--------|
| Red Queen | Opportunities/day | 5+ |
| Midwife | Validation pass rate | 20-30% |
| Constructor | Build success rate | >95% |
| Constructor | Build time | <5 min |
| Mortician | Sites evaluated/day | All active |
| Mortician | Portfolio success rate | >10% |

---

## Troubleshooting

### Red Queen

**Problem:** No opportunities found
- Check Reddit connectivity
- Lower pain_velocity_threshold
- Expand subreddit list

**Problem:** Low-quality opportunities
- Raise pain_velocity_threshold
- Tighten competition_gap_threshold
- Add more data sources

### Midwife

**Problem:** All opportunities fail validation
- Lower min_automation_score
- Lower min_monetization_score
- Check data source quality

**Problem:** False positives
- Raise fragmentation_threshold
- Add more validation criteria

### Constructor

**Problem:** Build failures
- Check Cloudflare API token
- Verify GitHub token permissions
- Review template syntax

**Problem:** Slow builds
- Reduce template complexity
- Use caching
- Parallelize operations

### Mortician

**Problem:** No sites culled
- Lower traffic_threshold_per_day
- Reduce evaluation_days

**Problem:** Good sites culled
- Raise traffic_threshold_per_day
- Add more evaluation criteria

---

## Best Practices

1. **Start Conservative** - Use conservative thresholds, then relax
2. **Monitor Metrics** - Track agent performance daily
3. **Archive Everything** - Keep data for training future agents
4. **Test Changes** - Validate agent changes in isolation
5. **Scale Gradually** - Increase site count slowly

---

For more information, see:
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [CONFIGURATION.md](CONFIGURATION.md) - Configuration guide
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment instructions
