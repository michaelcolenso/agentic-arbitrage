# ⚙️ Configuration Guide

Complete configuration reference for the Agentic Arbitrage Factory.

## Table of Contents

1. [Configuration Overview](#configuration-overview)
2. [Environment Variables](#environment-variables)
3. [Discovery Configuration](#discovery-configuration)
4. [Validation Configuration](#validation-configuration)
5. [Build Configuration](#build-configuration)
6. [Culling Configuration](#culling-configuration)
7. [Advanced Configuration](#advanced-configuration)
8. [Configuration Examples](#configuration-examples)

---

## Configuration Overview

The factory uses a hierarchical configuration system:

1. **Default values** (in code)
2. **Configuration file** (`config/settings.py`)
3. **Environment variables** (`.env` file)
4. **Runtime overrides** (command-line args)

Priority: Runtime > Environment > Config File > Defaults

---

## Environment Variables

Create a `.env` file in the project root:

```bash
# Reddit (optional - uses web scraping if not provided)
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret

# OpenAI (optional - for enhanced analysis)
OPENAI_API_KEY=sk-...

# Ahrefs (optional - for keyword research)
AHREFS_API_KEY=...

# Cloudflare (optional - for deployment)
CLOUDFLARE_API_TOKEN=...
CLOUDFLARE_ACCOUNT_ID=...

# GitHub (optional - for repo creation)
GITHUB_TOKEN=ghp_...

# Database (optional - defaults to SQLite)
DATABASE_URL=sqlite:///data/factory.db
```

### Loading Environment Variables

```python
from dotenv import load_dotenv
load_dotenv()  # Loads .env file
```

---

## Discovery Configuration

Controls the Red Queen (Discovery Agent).

### Settings

```python
# config/settings.py
@dataclass
class DiscoveryConfig:
    # Subreddits to monitor
    reddit_subreddits: List[str] = field(default_factory=lambda: [
        "personalfinance",
        "smallbusiness",
        "realestateinvesting",
        "legaladvice",
        "government",
        "dataisbeautiful",
        "webdev"
    ])
    
    # Geographic focus
    google_trends_geo: str = "US"
    
    # Data.gov datasets to monitor
    data_gov_datasets: List[str] = field(default_factory=lambda: [
        "recalls",
        "patents",
        "clinical-trials",
        "contract-data",
        "usajobs",
        "grants",
        "small-business"
    ])
    
    # Opportunity thresholds
    pain_velocity_threshold: float = 2.0      # Min pain velocity (0-10)
    competition_gap_threshold: float = 0.8    # Max competition (0-1)
    min_monthly_searches: int = 100           # Min keyword volume
    max_keyword_difficulty: int = 60          # Max keyword difficulty (0-100)
```

### Threshold Guidelines

| Setting | Conservative | Moderate | Aggressive |
|---------|--------------|----------|------------|
| pain_velocity_threshold | 6.0 | 4.0 | 2.0 |
| competition_gap_threshold | 0.3 | 0.5 | 0.8 |
| min_monthly_searches | 1000 | 500 | 100 |
| max_keyword_difficulty | 40 | 50 | 60 |

### Custom Subreddits

Add niche-specific subreddits:

```python
# config/settings.py
class DiscoveryConfig:
    reddit_subreddits = [
        # Default
        "personalfinance",
        "smallbusiness",
        
        # Niche-specific
        "electricvehicles",
        "solar",
        "realestateinvesting",
        "startups",
        "sidehustle",
        "passive_income",
    ]
```

---

## Validation Configuration

Controls the Midwife (Validation Agent).

### Settings

```python
# config/settings.py
@dataclass
class ValidationConfig:
    # Test parameters
    test_sample_size: int = 10              # Data points to test
    validation_timeout_hours: int = 48      # Max validation time
    
    # Fragmentation thresholds
    fragmentation_threshold: float = 0.9    # Max fragmentation (0-1)
    min_automation_score: float = 4.0       # Min automation (0-10)
    
    # Monetization thresholds
    min_monetization_score: float = 4.0     # Min monetization (0-10)
    
    # Affiliate networks to check
    affiliate_check_domains: List[str] = field(default_factory=lambda: [
        "amazon.com",
        "shareasale.com",
        "cj.com",
        "impact.com",
        "clickbank.com",
        "rakuten.com"
    ])
```

### Validation Logic

An opportunity passes if:

```python
def passes_validation(opp):
    return (
        opp.fragmentation.score <= config.fragmentation_threshold and
        opp.fragmentation.automation_potential >= config.min_automation_score and
        opp.monetization.score >= config.min_monetization_score and
        opp.validation_score >= 5.0 and
        keyword_opportunity_score >= 1.0
    )
```

### Tuning Validation

**Too Strict (everything fails):**
- Lower `min_automation_score`
- Lower `min_monetization_score`
- Raise `fragmentation_threshold`

**Too Lenient (everything passes):**
- Raise `min_automation_score`
- Raise `min_monetization_score`
- Lower `fragmentation_threshold`

---

## Build Configuration

Controls the Constructor (Build Agent).

### Settings

```python
# config/settings.py
@dataclass
class BuildConfig:
    # Template settings
    template_repo: str = "template-seo-site"
    
    # Tech stack
    stack: Dict[str, str] = field(default_factory=lambda: {
        "framework": "hono",        # Web framework
        "database": "d1",           # Database (D1 = Cloudflare)
        "styling": "tailwind",      # CSS framework
        "orm": "drizzle"            # ORM
    })
    
    # Build parameters
    build_timeout_minutes: int = 5
    deploy_target: str = "cloudflare"
    auto_submit_search_console: bool = True
```

### Stack Options

**Framework:**
- `hono` - Fast, edge-ready (recommended)
- `next` - Full-featured React
- `svelte` - Lightweight

**Database:**
- `d1` - Cloudflare D1 (recommended)
- `sqlite` - Local SQLite
- `postgres` - PostgreSQL

**Styling:**
- `tailwind` - Utility-first CSS (recommended)
- `bootstrap` - Component-based
- `none` - No styling

**ORM:**
- `drizzle` - Type-safe, lightweight (recommended)
- `prisma` - Full-featured
- `none` - Raw SQL

### Custom Templates

Override template generation:

```python
# agents/constructor.py
class TemplateGenerator:
    def _generate_home_template(self, niche_title, niche_lower):
        # Your custom template
        return f'''
export default function Home() {{
  return (
    <div className="custom-home">
      <h1>{niche_title}</h1>
      <!-- Your custom components -->
    </div>
  );
}}
'''
```

---

## Culling Configuration

Controls the Mortician (Culling Agent).

### Settings

```python
# config/settings.py
@dataclass
class CullingConfig:
    # Traffic thresholds
    traffic_threshold_per_day: int = 100    # Min daily organic traffic
    evaluation_days: int = 90               # Days before evaluation
    
    # Actions
    auto_301_to_winner: bool = True         # Redirect culled sites
    archive_data: bool = True               # Archive before culling
    recycle_codebase: bool = True           # Save templates
```

### Culling Rules

**Automatic Culling:**
1. If `days_active >= 90` AND `avg_traffic < 100/day` → CULL
2. If `days_active >= 60` AND `total_revenue < $10` → CULL
3. If `traffic_decline > 30%` over 14 days → CULL

**Automatic Promotion:**
1. If `avg_traffic > 500/day` → WINNER
2. If `avg_traffic > 200/day` AND `days < 60` → PROMISING

### Culling Schedule

Default: Daily at midnight

```python
# Customize schedule
async def run_continuous(self):
    while True:
        await self.evaluate_portfolio()
        await asyncio.sleep(24 * 3600)  # 24 hours
```

---

## Advanced Configuration

### Logging

```python
# config/settings.py
class FactoryConfig:
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
    log_file: str = "data/factory.log"
```

**Log Levels:**
- `DEBUG` - Detailed debugging info
- `INFO` - General operational info
- `WARNING` - Warning messages
- `ERROR` - Error messages only

### Database

```python
# config/settings.py
class FactoryConfig:
    database_url: str = "sqlite:///data/factory.db"
    # OR
    database_url: str = "postgresql://user:pass@localhost/factory"
```

### Concurrency

```python
# config/settings.py
class FactoryConfig:
    max_concurrent_sites: int = 50
    max_concurrent_requests: int = 10
```

### Rate Limiting

```python
# config/settings.py
class FactoryConfig:
    reddit_rate_limit: float = 1.0  # requests per second
    datagov_rate_limit: float = 0.5
    ahrefs_rate_limit: float = 0.1
```

---

## Configuration Examples

### Example 1: Conservative Setup

```python
# config/settings.py

class DiscoveryConfig:
    pain_velocity_threshold = 6.0
    competition_gap_threshold = 0.3
    min_monthly_searches = 1000
    max_keyword_difficulty = 40

class ValidationConfig:
    fragmentation_threshold = 0.6
    min_automation_score = 7.0
    min_monetization_score = 7.0

class CullingConfig:
    traffic_threshold_per_day = 200
    evaluation_days = 60
```

**Use Case:** High-quality, low-risk opportunities. Expect 5-10% pass rate.

### Example 2: Aggressive Setup

```python
# config/settings.py

class DiscoveryConfig:
    pain_velocity_threshold = 2.0
    competition_gap_threshold = 0.8
    min_monthly_searches = 100
    max_keyword_difficulty = 60

class ValidationConfig:
    fragmentation_threshold = 0.9
    min_automation_score = 4.0
    min_monetization_score = 4.0

class CullingConfig:
    traffic_threshold_per_day = 50
    evaluation_days = 120
```

**Use Case:** Volume-based approach. Expect 30-50% pass rate, higher culling.

### Example 3: Niche-Focused Setup

```python
# config/settings.py

class DiscoveryConfig:
    reddit_subreddits = [
        "electricvehicles",
        "teslamotors",
        "evcharging",
        "solar",
        "renewableenergy"
    ]
    data_gov_datasets = [
        "energy-data",
        "transportation-data"
    ]

class ValidationConfig:
    affiliate_check_domains = [
        "amazon.com",
        "chargepoint.com",
        "tesla.com",
        "sunpower.com"
    ]
```

**Use Case:** Focus on EV/energy niche only.

### Example 4: Development Setup

```python
# config/settings.py

class FactoryConfig:
    log_level = "DEBUG"
    max_concurrent_sites = 5

class DiscoveryConfig:
    reddit_subreddits = ["testsubreddit"]
    
class BuildConfig:
    deploy_target = "local"  # Don't actually deploy
    auto_submit_search_console = False
```

**Use Case:** Local development and testing.

---

## Environment-Specific Configuration

### Development

```bash
# .env.development
LOG_LEVEL=DEBUG
DATABASE_URL=sqlite:///data/factory_dev.db
DEPLOY_TARGET=local
```

### Staging

```bash
# .env.staging
LOG_LEVEL=INFO
DATABASE_URL=postgresql://user:pass@staging-db/factory
DEPLOY_TARGET=cloudflare-staging
```

### Production

```bash
# .env.production
LOG_LEVEL=WARNING
DATABASE_URL=postgresql://user:pass@prod-db/factory
DEPLOY_TARGET=cloudflare
```

### Loading Environment-Specific Config

```python
import os
from dotenv import load_dotenv

env = os.getenv("ENV", "development")
load_dotenv(f".env.{env}")
```

---

## Configuration Validation

Validate configuration on startup:

```python
# config/settings.py
class FactoryConfig:
    def __post_init__(self):
        # Validate settings
        if self.discovery.pain_velocity_threshold < 0:
            raise ValueError("pain_velocity_threshold must be >= 0")
        
        if self.validation.min_automation_score > 10:
            raise ValueError("min_automation_score must be <= 10")
```

---

## Troubleshooting Configuration

### Problem: No opportunities found

**Solution:**
```python
# Lower thresholds
pain_velocity_threshold = 1.0
competition_gap_threshold = 0.9
```

### Problem: All builds fail

**Solution:**
```python
# Check deployment config
deploy_target = "local"  # Test locally first
```

### Problem: Database locked

**Solution:**
```python
# Reduce concurrency
max_concurrent_sites = 10
```

### Problem: Rate limited

**Solution:**
```python
# Slow down requests
reddit_rate_limit = 0.5  # 1 request per 2 seconds
```

---

## Best Practices

1. **Start Conservative** - Use higher thresholds initially
2. **Monitor Metrics** - Track pass rates and adjust
3. **Version Control** - Commit config changes
4. **Document Changes** - Comment why thresholds changed
5. **Test Changes** - Validate in development first

---

For more information, see:
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [AGENTS.md](AGENTS.md) - Agent documentation
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment instructions
