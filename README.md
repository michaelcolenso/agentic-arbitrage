# 🤖 Agentic Arbitrage Factory

> **"Stop building websites. Build the machine that builds the websites."**

An autonomous system that identifies, validates, builds, deploys, and manages programmatic SEO sites without human intervention.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Async](https://img.shields.io/badge/async-aiohttp-green.svg)](https://docs.aiohttp.org/)

## 🎯 The Concept

Instead of building one SaleScout-style site, you build the **factory** that launches 50 variants in 30 days, measures which 3 get traction, and automatically liquidates the other 47.

**The Meta-Play:** Become the Digital Frontier's land speculator. Claim thousands of keyword territories simultaneously, keep only the profitable ones, sell the data on what worked.

### Why This Destroys Traditional SEO

| Traditional SEO | The Factory |
|----------------|-------------|
| Single point of failure (one niche) | Portfolio hedging (law of large numbers) |
| High maintenance per dollar earned | Zero marginal cost per new site |
| Linear growth (add counties one by one) | Exponential growth (add niches exponentially) |
| You grind | Agents grind |

## 🏗️ Architecture

The factory consists of four autonomous agents working in harmony:

### 1. 🔍 The Red Queen (Discovery Agent)
- **Input:** Reddit feeds, Google Trends API, data.gov releases
- **Logic:** Detects "pain-point pivots" — moments when user frustration correlates with data availability but precedes commercial solution
- **Output:** Ranked opportunity queue with pain velocity and competition gap scores

### 2. 🧪 The Midwife (Validation Agent)
- **Function:** 48-hour viability test
- **Actions:**
  - Scrapes sample data points to test fragmentation
  - Checks keyword difficulty for template keywords
  - Validates affiliate/lead-gen potential
- **Gate:** Only niches scoring >7/10 on "automation potential × monetization clarity" proceed

### 3. 🔨 The Constructor (Build Agent)
- **Function:** Repo generation in < 5 minutes
- **Stack:** Hono + D1 + Tailwind + Drizzle
- **Magic:** Reads data schema, generates:
  - Database schema (Drizzle migrations)
  - Scraping adapters (modular scrapers)
  - SEO content templates (structured outputs)
  - Comparison tools (programmatic pages that rank)
- **Output:** GitHub repo + Cloudflare project + Search Console submission

### 4. 💀 The Mortician (Culling Agent)
- **Function:** Ruthless portfolio management
- **Rule:** If no organic traffic >100 users/day by day 90 → full liquidation
- **Actions:**
  - Domain 301'd to nearest winner
  - Data archived for training future agents
  - Codebase recycled into template library
- **Philosophy:** Zero emotion. Pure Darwin.

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip
- (Optional) Cloudflare account for deployment
- (Optional) GitHub account for repo creation

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd agentic_arbitrage_factory

# Install runtime and development dependencies
uv sync --extra dev
```

### Configuration

Create a `.env` file in the project root (optional for demo mode):

```bash
# Reddit (optional - uses web scraping if not provided)
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret

# APIs (optional)
OPENAI_API_KEY=your_openai_key
AHREFS_API_KEY=your_ahrefs_key

# Deployment (optional)
CLOUDFLARE_API_TOKEN=your_cloudflare_token
GITHUB_TOKEN=your_github_token
```

### Running the Factory

```bash
# Run complete factory cycle
uv run python factory.py run

# Run specific phases
uv run python factory.py discover      # Only discovery
uv run python factory.py validate      # Only validation
uv run python factory.py build         # Only build
uv run python factory.py cull          # Only portfolio management

# Run continuously (recommended for production)
uv run python factory.py continuous

# Check factory status
uv run python factory.py status

# Run demo
uv run python demo.py

# View dashboard
uv run python dashboard.py
```

## 📊 Example Output

```
======================================================================
🤖 AGENTIC ARBITRAGE FACTORY - Run 20260403_042727
======================================================================

PHASE 1: DISCOVERY (Red Queen)
  Found 8 pain points
  Found 49 data sources
  Identified 1 pain-point pivots
  ✅ Created 1 new opportunities

PHASE 2: VALIDATION (Midwife)
  ✅ PASSED - ev_charger_rebates
  Overall Score: 5.8/10
  Estimated MRR: $181.36

PHASE 3: BUILD (Constructor)
  Built ev_charger_rebates in 0s
  URL: https://ev-charger-rebates.pages.dev
  ✅ 1/1 sites built successfully

PHASE 4: PORTFOLIO MANAGEMENT (Mortician)
  Evaluating 1 sites...
  ✅ Portfolio evaluation complete

======================================================================
📊 FACTORY RUN SUMMARY
======================================================================
  🔍 Discovery:     1 opportunities found
  🧪 Validation:    1 passed, 0 failed
  🔨 Build:         1 succeeded, 0 failed
  💀 Portfolio:     1 evaluated, 0 culled, 0 winners
```

## 💰 The Monetization Stack

### Layer 1: The Portfolio (Owned Assets)
- Keep equity in winners
- 20 sites × $2k MRR each = $40k MRR
- Sell portfolio at 40x = $1.6M exit

### Layer 2: The Intelligence (B2B SaaS)
- Sell the "opportunity feed" to other SEO operators
- "$99/mo for early access to validated niches before we build them"

### Layer 3: The Infrastructure (PaaS)
- Open-source the factory framework
- Charge for:
  - Managed Cloudflare Workers hosting ($29/site/month)
  - Premium data connectors (county court scrapers, patent APIs)
  - Culling insurance (guarantee traffic or refund build cost)

## 📁 Project Structure

```
agentic_arbitrage_factory/
├── agents/                    # The Four Agents
│   ├── red_queen.py          # 🔍 Discovery Agent
│   ├── midwife.py            # 🧪 Validation Agent
│   ├── constructor.py        # 🔨 Build Agent
│   └── mortician.py          # 💀 Culling Agent
├── core/                      # Core Infrastructure
│   ├── models.py             # Data models
│   └── storage.py            # SQLite persistence
├── config/                    # Configuration
│   └── settings.py           # Factory settings
├── data/                      # Database and archives
├── sites/                     # Generated site projects
├── factory.py                 # Main orchestrator
├── dashboard.py               # Monitoring dashboard
├── demo.py                    # Quick demo
├── pyproject.toml             # uv project definition
├── uv.lock                    # Locked dependency graph
└── README.md                  # This file
```

## 🎛️ Configuration

All configuration is managed through `config/settings.py`:

```python
# Discovery thresholds
pain_velocity_threshold: float = 2.0      # Min pain velocity (0-10)
competition_gap_threshold: float = 0.8    # Max competition (0-1)
min_monthly_searches: int = 100           # Min keyword volume
max_keyword_difficulty: int = 60          # Max keyword difficulty

# Validation thresholds
fragmentation_threshold: float = 0.9      # Max fragmentation
min_automation_score: float = 4.0         # Min automation (0-10)
min_monetization_score: float = 4.0       # Min monetization (0-10)

# Culling rules
traffic_threshold_per_day: int = 100      # Min daily traffic
evaluation_days: int = 90                 # Days before culling
```

## 🧪 Testing

```bash
# Run tests
uv run pytest tests/

# Run with coverage
uv run pytest --cov=.

# Run specific agent tests
uv run pytest tests/test_red_queen.py
uv run pytest tests/test_midwife.py
```

## 📈 Risk Profiles

### Conservative
Factory builds only "data.gov derivatives" — sites based on federal datasets (recalls, NPI, patents) where data quality is standardized.

### Aggressive
Factory builds "regulatory arbitrage" sites — monitoring municipal code changes, zoning variances, permit expirations (high value, high maintenance).

### Degenerate
Factory builds "synthetic authority" sites — AI-generated expert analysis of public datasets (SEC filings + clinical trial data) positioned as niche newsletters, monetized via institutional subscriptions.

## 🔌 Data Sources

The factory integrates with:

- **Reddit** (Web Scraping) - Pain point discovery
- **Data.gov API** - Government datasets
- **Google Trends** (Optional) - Trend analysis
- **Ahrefs API** (Optional) - Keyword research
- **Cloudflare API** (Optional) - Deployment
- **GitHub API** (Optional) - Repository management

## 🛠️ Development

### Adding a New Agent

1. Create a new file in `agents/` directory
2. Inherit from base agent class (if applicable)
3. Implement required methods
4. Register in `factory.py`

### Customizing Templates

Templates are generated in `agents/constructor.py`. Modify:
- `_generate_home_template()` - Homepage
- `_generate_list_template()` - List pages
- `_generate_detail_template()` - Detail pages
- `_generate_compare_template()` - Comparison pages

## 📝 Logging

Logs are written to:
- Console (INFO level and above)
- `data/factory.log` (DEBUG level and above)

Configure logging in `config/settings.py`:
```python
log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by the concept of "pain-point pivots" from market microstructure
- Built with [aiohttp](https://docs.aiohttp.org/) for async operations
- Database powered by SQLite

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/yourusername/agentic_arbitrage_factory/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/agentic_arbitrage_factory/discussions)
- **Email:** support@agenticfactory.dev

## 🗺️ Roadmap

- [ ] Add more data sources (Twitter, Hacker News, etc.)
- [ ] Implement ML-based opportunity scoring
- [ ] Add A/B testing framework for site variants
- [ ] Build web-based management dashboard
- [ ] Add multi-language support
- [ ] Implement automatic content generation

---

**Built with 🤖 by the Agentic Arbitrage Factory**

*Remember: You're not building SaleScout. You're building the ability to validate 100 SaleScouts per month for $50 in compute costs.*
