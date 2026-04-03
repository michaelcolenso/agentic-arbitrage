# 📋 Changelog

All notable changes to the Agentic Arbitrage Factory will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Web scraping for Reddit (no API key required)
- Docker support
- Kubernetes deployment configs
- Health check endpoint
- Prometheus metrics

### Changed
- Improved opportunity scoring algorithm
- Faster build process (30% reduction)
- Updated dependencies

### Fixed
- Memory leak in long-running processes
- Database locking issues
- Rate limiting handling

## [1.0.0] - 2024-04-03

### Added
- Initial release of Agentic Arbitrage Factory
- Four autonomous agents:
  - Red Queen (Discovery Agent)
  - Midwife (Validation Agent)
  - Constructor (Build Agent)
  - Mortician (Culling Agent)
- SQLite database for persistence
- Web scraping for Reddit, Data.gov
- Automated site generation with Hono + D1 + Tailwind
- Portfolio management with automatic culling
- Dashboard for monitoring
- CLI interface with multiple commands
- Comprehensive documentation

### Features
- **Discovery**: Monitors Reddit and Data.gov for opportunities
- **Validation**: 48-hour viability testing
- **Build**: Generates complete SEO sites in < 5 minutes
- **Culling**: Ruthless portfolio management (90-day rule)
- **Monetization**: Tracks MRR, portfolio value, success rates
- **Deployment**: Cloudflare Pages integration
- **Monitoring**: Real-time dashboard and logging

### Technical
- Python 3.8+ with asyncio
- SQLite database
- aiohttp for async HTTP
- Dataclasses for type safety
- pytest for testing
- GitHub Actions for CI/CD

## [0.9.0] - 2024-03-15 (Beta)

### Added
- Beta release for testing
- All four agents functional
- Basic dashboard
- CLI interface

### Known Issues
- Database locking under high concurrency
- Memory usage grows over time
- Reddit API rate limiting

## [0.8.0] - 2024-02-28 (Alpha)

### Added
- Alpha release for internal testing
- Red Queen and Midwife agents
- SQLite storage layer
- Basic configuration system

### Changed
- Refactored from monolithic to agent-based architecture

## [0.5.0] - 2024-01-15 (Prototype)

### Added
- Initial prototype
- Single-agent discovery
- Mock data generation
- Basic site templates

## [0.1.0] - 2024-01-01 (Proof of Concept)

### Added
- Proof of concept
- Reddit API integration
- Opportunity scoring
- Console output

---

## Versioning Guide

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR** - Breaking changes
- **MINOR** - New features (backward compatible)
- **PATCH** - Bug fixes (backward compatible)

Examples:
- `1.0.0` → `2.0.0` - Breaking API changes
- `1.0.0` → `1.1.0` - New features added
- `1.0.0` → `1.0.1` - Bug fixes

---

## Release Checklist

- [ ] Update version in `__init__.py`
- [ ] Update CHANGELOG.md
- [ ] Run all tests
- [ ] Update documentation
- [ ] Create git tag
- [ ] Build Docker image
- [ ] Push to PyPI (if applicable)
- [ ] Create GitHub release
- [ ] Announce on social media

---

## Contributing to Changelog

When making changes, add entry under `[Unreleased]`:

```markdown
### Added
- New feature description

### Changed
- Change description

### Deprecated
- Feature to be removed

### Removed
- Removed feature

### Fixed
- Bug fix description

### Security
- Security fix description
```

Categories:
- **Added** - New features
- **Changed** - Changes to existing functionality
- **Deprecated** - Soon-to-be removed features
- **Removed** - Removed features
- **Fixed** - Bug fixes
- **Security** - Security fixes
