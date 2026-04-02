# 🏗️ Architecture Documentation

System architecture and design decisions for the Agentic Arbitrage Factory.

## Table of Contents

1. [System Overview](#system-overview)
2. [Design Principles](#design-principles)
3. [Component Architecture](#component-architecture)
4. [Data Flow](#data-flow)
5. [Database Schema](#database-schema)
6. [Scalability](#scalability)
7. [Security](#security)
8. [Monitoring](#monitoring)

---

## System Overview

The Agentic Arbitrage Factory is a distributed system of autonomous agents that discover, validate, build, and manage programmatic SEO sites at scale.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Agentic Arbitrage Factory                         │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │  Red Queen  │→ │  Midwife    │→ │ Constructor │→ │  Mortician  │   │
│  │  Discover   │  │  Validate   │  │    Build    │  │    Cull     │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │
│         │                │                │                │           │
│         └────────────────┴────────────────┴────────────────┘           │
│                                    │                                    │
│                           ┌────────┴────────┐                          │
│                           │   SQLite DB     │                          │
│                           │  (Persistence)  │                          │
│                           └────────┬────────┘                          │
│                                    │                                    │
│         ┌─────────────────────────┼─────────────────────────┐          │
│         ↓                         ↓                         ↓          │
│  ┌─────────────┐          ┌─────────────┐          ┌─────────────┐    │
│  │   Reddit    │          │  Data.gov   │          │ Cloudflare  │    │
│  │   (Web)     │          │    (API)    │          │  (Deploy)   │    │
│  └─────────────┘          └─────────────┘          └─────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Design Principles

### 1. Autonomous Agents

Each agent operates independently with:
- Clear inputs and outputs
- Defined success criteria
- Error handling and recovery
- No direct coupling to other agents

### 2. Event-Driven Architecture

Agents communicate through database state changes:
```
OpportunityStatus: DISCOVERED → VALIDATED → DEPLOYED → WINNER/CULLED
```

### 3. Fault Tolerance

- Agents retry failed operations
- Fallback to mock data if APIs unavailable
- Graceful degradation
- No single point of failure

### 4. Scalability

- Async/await for concurrent operations
- SQLite for local development (upgrade to PostgreSQL for scale)
- Stateless agents (state in database)
- Horizontal scaling ready

### 5. Observability

- Comprehensive logging
- Metrics collection
- Status dashboard
- Performance tracking

---

## Component Architecture

### Core Components

#### 1. Models (`core/models.py`)

Data models using Python dataclasses:

```python
@dataclass
class Opportunity:
    id: str
    niche: str
    status: OpportunityStatus
    pain_velocity: float
    competition_gap: float
    # ...

@dataclass
class Site:
    id: str
    opportunity_id: str
    status: SiteStatus
    deploy_url: str
    # ...
```

**Design Decision:** Dataclasses over dicts for:
- Type safety
- IDE autocomplete
- Validation
- Documentation

#### 2. Storage (`core/storage.py`)

SQLite abstraction layer:

```python
class Storage:
    def save_opportunity(self, opp: Opportunity) -> None
    def get_opportunity(self, id: str) -> Optional[Opportunity]
    def get_opportunities_by_status(self, status: OpportunityStatus) -> List[Opportunity]
    # ...
```

**Design Decision:** SQLite for:
- Zero configuration
- Single file
- ACID compliance
- Easy backups

**Future:** PostgreSQL for production scale

#### 3. Configuration (`config/settings.py`)

Centralized configuration using dataclasses:

```python
@dataclass
class DiscoveryConfig:
    pain_velocity_threshold: float = 2.0
    competition_gap_threshold: float = 0.8
    # ...
```

**Design Decision:** Dataclasses over dicts for:
- Type safety
- Validation
- Documentation
- IDE support

---

## Data Flow

### Opportunity Lifecycle

```
┌────────────────────────────────────────────────────────────────────┐
│                    Opportunity Lifecycle                            │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐ │
│   │ DISCOVER │────→│ VALIDATE │────→│  BUILD   │────→│ DEPLOYED │ │
│   │          │     │          │     │          │     │          │ │
│   │ Red Queen│     │ Midwife  │     │Constructor│    │          │ │
│   └──────────┘     └────┬─────┘     └──────────┘     └────┬─────┘ │
│                         │                                  │       │
│                    ┌────┴────┐                        ┌────┴────┐  │
│                    │ REJECT  │                        │  CULL   │  │
│                    └─────────┘                        └────┬────┘  │
│                                                            │       │
│                                                       ┌────┴────┐  │
│                                                       │  WINNER │  │
│                                                       └─────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

### State Transitions

| From | To | Trigger | Agent |
|------|-----|---------|-------|
| - | DISCOVERED | Pain point detected | Red Queen |
| DISCOVERED | VALIDATED | Passed validation | Midwife |
| DISCOVERED | - | Failed validation | Midwife |
| VALIDATED | DEPLOYED | Build successful | Constructor |
| VALIDATED | - | Build failed | Constructor |
| DEPLOYED | WINNER | Traffic > 500/day | Mortician |
| DEPLOYED | CULLED | Traffic < 100/day at day 90 | Mortician |
| DEPLOYED | RANKING | Traffic > 200/day | Mortician |

---

## Database Schema

### Entity Relationship Diagram

```
┌──────────────────┐       ┌──────────────────┐
│  opportunities   │       │      sites       │
├──────────────────┤       ├──────────────────┤
│ id (PK)          │◄──────│ opportunity_id   │
│ niche            │       │ id (PK)          │
│ status           │       │ status           │
│ pain_velocity    │       │ deploy_url       │
│ competition_gap  │       │ page_count       │
│ validation_score │       │ created_at       │
│ created_at       │       └──────────────────┘
└──────────────────┘              │
                                  │
                          ┌───────┴───────┐
                          │  site_metrics  │
                          ├───────────────┤
                          │ site_id (FK)  │
                          │ date          │
                          │ organic_users │
                          │ revenue       │
                          │ ranking_kw    │
                          └───────────────┘
```

### Table Definitions

#### opportunities

```sql
CREATE TABLE opportunities (
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
);
```

#### sites

```sql
CREATE TABLE sites (
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
);
```

#### site_metrics

```sql
CREATE TABLE site_metrics (
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
);
```

#### factory_stats

```sql
CREATE TABLE factory_stats (
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
);
```

---

## Scalability

### Current Limits (SQLite)

- **Opportunities:** 10,000+
- **Sites:** 1,000+
- **Metrics:** 1,000,000+ rows
- **Concurrent operations:** Limited by Python GIL

### Scaling Strategies

#### 1. Database Scaling

**SQLite → PostgreSQL**

```python
# config/settings.py
class DatabaseConfig:
    driver: str = "postgresql"  # or "sqlite"
    host: str = "localhost"
    port: int = 5432
    database: str = "factory"
    username: str = "factory"
    password: str = "..."
```

**Benefits:**
- Concurrent connections
- Better query performance
- Replication support
- Backup/restore tools

#### 2. Agent Scaling

**Single Process → Distributed**

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Queue                               │
│                   (Redis/RabbitMQ)                           │
└─────────────────────────────────────────────────────────────┘
       │              │              │              │
       ↓              ↓              ↓              ↓
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Red Queen   │ │  Midwife    │ │ Constructor │ │  Mortician  │
│  (Worker 1) │ │  (Worker 2) │ │  (Worker 3) │ │  (Worker 4) │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```

**Benefits:**
- Horizontal scaling
- Fault tolerance
- Load balancing
- Independent scaling per agent

#### 3. Caching

**Add Redis Cache**

```python
# Cache expensive operations
@cache(ttl=3600)
async def get_keyword_difficulty(keyword: str) -> float:
    # Expensive API call
    pass
```

**Cache Targets:**
- Keyword difficulty scores
- Data.gov datasets
- Reddit posts (short TTL)
- Site metrics

---

## Security

### Data Protection

1. **API Keys** - Stored in environment variables
2. **Database** - SQLite file permissions (600)
3. **Logs** - No sensitive data logged
4. **Backups** - Encrypted at rest

### API Security

1. **Rate Limiting** - Respect API limits
2. **User Agents** - Identify requests
3. **Retry Logic** - Exponential backoff
4. **Timeout** - Prevent hanging

### Deployment Security

1. **Cloudflare** - HTTPS by default
2. **D1 Database** - Encrypted at rest
3. **Secrets** - Use Cloudflare Secrets
4. **Access Control** - Minimal permissions

---

## Monitoring

### Metrics Collected

| Metric | Source | Frequency |
|--------|--------|-----------|
| Opportunities found | Red Queen | Every run |
| Validation pass rate | Midwife | Every run |
| Build success rate | Constructor | Every run |
| Sites culled | Mortician | Daily |
| Portfolio value | All | Real-time |
| Agent execution time | All | Every run |

### Alerting

**Conditions:**
- No opportunities found for 24 hours
- Validation pass rate < 10%
- Build success rate < 90%
- Site traffic drops > 50%
- Agent errors > 10/hour

**Channels:**
- Email
- Slack
- PagerDuty (critical)

### Dashboard

```bash
# View real-time dashboard
python dashboard.py

# Output:
# 🤖 AGENTIC ARBITRAGE FACTORY - STATUS
# 📊 PORTFOLIO STATS:
#    Total Opportunities: 150
#    Validated: 45
#    Active Sites: 23
#    Winner Sites: 3
#    Culled Sites: 12
```

---

## Performance

### Benchmarks

| Operation | Target | Current |
|-----------|--------|---------|
| Discovery cycle | <5 min | ~2 min |
| Validation | <1 min | ~30 sec |
| Build | <5 min | ~1 min |
| Portfolio eval | <1 min | ~30 sec |
| Database query | <100ms | ~50ms |

### Optimization Strategies

1. **Async Operations** - Concurrent API calls
2. **Connection Pooling** - Reuse HTTP connections
3. **Batch Processing** - Process multiple items at once
4. **Lazy Loading** - Load data only when needed
5. **Caching** - Cache expensive operations

---

## Deployment Architecture

### Development

```
┌─────────────────────────────────────┐
│         Development Setup            │
├─────────────────────────────────────┤
│  Laptop                              │
│   ├── Python 3.8+                   │
│   ├── SQLite                        │
│   └── Local config (.env)           │
└─────────────────────────────────────┘
```

### Production

```
┌─────────────────────────────────────────────────────────────┐
│                      Production                              │
├─────────────────────────────────────────────────────────────┤
│  VPS/Cloud Instance                                          │
│   ├── Python 3.8+                                           │
│   ├── PostgreSQL (or SQLite)                                │
│   ├── systemd service                                       │
│   └── Environment variables                                 │
│                                                              │
│  Cloudflare                                                  │
│   ├── Pages (static hosting)                                │
│   ├── D1 (database)                                         │
│   └── Workers (API)                                         │
└─────────────────────────────────────────────────────────────┘
```

### Docker (Optional)

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "factory.py", "continuous"]
```

---

## Future Architecture

### Phase 2: Distributed System

```
┌─────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Red Queen   │  │  Midwife    │  │ Constructor │         │
│  │ Deployment  │  │  Deployment │  │  Deployment │         │
│  │ (3 replicas)│  │ (2 replicas)│  │ (5 replicas)│         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              PostgreSQL Cluster                      │    │
│  │         (Primary + 2 Replicas)                       │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Redis Cluster                           │    │
│  │         (Cache + Queue)                              │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Phase 3: ML Enhancement

```
┌─────────────────────────────────────────────────────────────┐
│                    ML Pipeline                               │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Opportunity │  │   Content   │  │   Traffic   │         │
│  │   Scorer    │  │  Generator  │  │  Predictor  │         │
│  │  (TensorFlow)│  │   (GPT-4)   │  │  (Prophet)  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2024-01 | SQLite over PostgreSQL | Simplicity, zero-config |
| 2024-01 | Dataclasses over dicts | Type safety, IDE support |
| 2024-01 | Async over sync | Performance, scalability |
| 2024-01 | Web scraping over Reddit API | No auth required |
| 2024-01 | Cloudflare over AWS | Cost, simplicity |
| 2024-01 | Hono over Next.js | Performance, edge-ready |

---

For more information, see:
- [AGENTS.md](AGENTS.md) - Agent documentation
- [CONFIGURATION.md](CONFIGURATION.md) - Configuration guide
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment instructions
