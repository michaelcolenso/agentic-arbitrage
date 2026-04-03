# 🤝 Contributing Guide

Thank you for your interest in contributing to the Agentic Arbitrage Factory!

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Setup](#development-setup)
3. [Code Standards](#code-standards)
4. [Testing](#testing)
5. [Submitting Changes](#submitting-changes)
6. [Code Review Process](#code-review-process)
7. [Community Guidelines](#community-guidelines)

---

## Getting Started

### Ways to Contribute

- **Bug Reports** - Report issues you encounter
- **Feature Requests** - Suggest new features or improvements
- **Code Contributions** - Fix bugs or implement features
- **Documentation** - Improve docs, add examples
- **Testing** - Write tests, improve coverage
- **Reviews** - Review pull requests

### Before You Start

1. Check existing [issues](https://github.com/yourusername/agentic_arbitrage_factory/issues)
2. Join [discussions](https://github.com/yourusername/agentic_arbitrage_factory/discussions)
3. Read this guide completely

---

## Development Setup

### Prerequisites

- Python 3.8+
- Git
- GitHub account

### Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/agentic_arbitrage_factory.git
cd agentic_arbitrage_factory

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/agentic_arbitrage_factory.git
```

### Development Environment

```bash
# Install runtime and development dependencies
uv sync --extra dev
```

### Pre-commit Hooks

```bash
# Install hooks
uv run pre-commit install

# Run manually
uv run pre-commit run --all-files
```

---

## Code Standards

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with some modifications:

**Line Length:**
- Maximum 100 characters
- Use parentheses for line continuation

```python
# Good
result = some_function(
    arg1=value1,
    arg2=value2,
    arg3=value3
)

# Bad
result = some_function(arg1=value1, arg2=value2, arg3=value3, arg4=value4, arg5=value5)
```

**Imports:**
```python
# Order: stdlib, third-party, local
import os
import sys
from datetime import datetime

import aiohttp
from dotenv import load_dotenv

from core.models import Opportunity
from config.settings import config
```

**Type Hints:**
```python
from typing import List, Optional, Dict, Any

async def discover_opportunities(
    subreddits: List[str],
    max_results: int = 50
) -> List[Opportunity]:
    """Discover opportunities from subreddits."""
    pass
```

**Docstrings:**
```python
def calculate_pain_velocity(pain_points: List[PainPoint]) -> float:
    """
    Calculate pain velocity score.
    
    Args:
        pain_points: List of pain points to analyze
        
    Returns:
        Pain velocity score (0-10)
        
    Raises:
        ValueError: If pain_points is empty
        
    Example:
        >>> points = [PainPoint(...), PainPoint(...)]
        >>> score = calculate_pain_velocity(points)
        >>> print(score)
        7.5
    """
    if not pain_points:
        raise ValueError("pain_points cannot be empty")
    # ... implementation
```

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Classes | PascalCase | `RedQueen`, `Opportunity` |
| Functions | snake_case | `discover_opportunities()` |
| Variables | snake_case | `pain_points` |
| Constants | UPPER_CASE | `MAX_RETRIES` |
| Private | _leading_underscore | `_internal_helper()` |

### Code Organization

```
agents/
├── __init__.py           # Public API exports
├── red_queen.py         # Single agent per file
├── base_agent.py        # Abstract base classes
└── utils.py             # Shared utilities

core/
├── models.py            # Data models
├── storage.py           # Database layer
└── exceptions.py        # Custom exceptions

tests/
├── conftest.py          # Pytest fixtures
├── test_red_queen.py    # Test per agent
└── test_models.py       # Test models
```

---

## Testing

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=. --cov-report=html

# Run specific test file
uv run pytest tests/test_red_queen.py

# Run specific test
uv run pytest tests/test_red_queen.py::test_discover_opportunities

# Run with verbose output
uv run pytest -v

# Run failed tests only
uv run pytest --lf
```

### Writing Tests

**Test Structure:**
```python
# tests/test_red_queen.py
import pytest
from agents.red_queen import RedQueen

class TestRedQueen:
    """Test suite for Red Queen agent."""
    
    @pytest.fixture
    def red_queen(self):
        """Create RedQueen instance."""
        return RedQueen()
    
    @pytest.mark.asyncio
    async def test_discover_opportunities(self, red_queen):
        """Test opportunity discovery."""
        opportunities = await red_queen.discover()
        
        assert isinstance(opportunities, list)
        assert len(opportunities) > 0
        
        opp = opportunities[0]
        assert opp.niche
        assert opp.pain_velocity > 0
    
    def test_calculate_pain_velocity(self, red_queen):
        """Test pain velocity calculation."""
        pain_points = [
            PainPoint(engagement=100, sentiment_score=-0.5),
            PainPoint(engagement=200, sentiment_score=-0.7),
        ]
        
        velocity = red_queen._calculate_pain_velocity(pain_points)
        
        assert velocity > 0
        assert velocity <= 10
```

**Test Coverage:**
- Minimum 80% coverage required
- 100% coverage for critical paths
- Test both success and failure cases

### Mocking

```python
import pytest
from unittest.mock import Mock, patch

@pytest.mark.asyncio
async def test_with_mock():
    """Test with mocked dependencies."""
    
    # Mock external API
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_get.return_value.__aenter__.return_value.status = 200
        mock_get.return_value.__aenter__.return_value.json = Mock(
            return_value={'data': []}
        )
        
        # Run test
        result = await fetch_data()
        
        # Assert
        assert result == []
        mock_get.assert_called_once()
```

---

## Submitting Changes

### Branch Naming

```
feature/description        # New features
bugfix/description         # Bug fixes
docs/description           # Documentation
refactor/description       # Code refactoring
test/description           # Tests only
chore/description          # Maintenance
```

Examples:
- `feature/add-ml-scoring`
- `bugfix/fix-reddit-rate-limit`
- `docs/update-readme`

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): subject

body (optional)

footer (optional)
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `style` - Formatting
- `refactor` - Code refactoring
- `test` - Tests
- `chore` - Maintenance

**Examples:**
```
feat(red_queen): add sentiment analysis

Implement sentiment analysis for pain points using
TextBlob. Improves pain velocity calculation accuracy.

Closes #123
```

```
fix(midwife): correct validation score calculation

Validation score was incorrectly multiplied by 10.
Now properly averages automation and monetization scores.

Fixes #456
```

### Pull Request Process

1. **Create Branch**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make Changes**
   - Write code
   - Add tests
   - Update docs

3. **Run Checks**
   ```bash
   # Run tests
   pytest
   
   # Run linter
   flake8
   
   # Run type checker
   mypy
   
   # Run pre-commit
   pre-commit run --all-files
   ```

4. **Commit**
   ```bash
   git add .
   git commit -m "feat(scope): description"
   ```

5. **Push**
   ```bash
   git push origin feature/my-feature
   ```

6. **Create PR**
   - Go to GitHub
   - Click "New Pull Request"
   - Fill out template
   - Request review

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] Coverage > 80%

## Checklist
- [ ] Code follows style guide
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings

## Related Issues
Fixes #123
```

---

## Code Review Process

### Review Criteria

**Must Have:**
- [ ] Code works as intended
- [ ] Tests pass
- [ ] No security issues
- [ ] Follows style guide

**Should Have:**
- [ ] Adequate test coverage
- [ ] Clear documentation
- [ ] Efficient implementation
- [ ] Error handling

**Nice to Have:**
- [ ] Performance optimizations
- [ ] Additional tests
- [ ] Code simplification

### Review Timeline

- Initial review: 2-3 days
- Follow-up reviews: 1-2 days
- Final approval: 1 day

### Review Comments

**Be Constructive:**
```
❌ "This is wrong"
✅ "Consider using X instead for better performance"

❌ "Fix this"
✅ "Could you add error handling for Y case?"
```

---

## Community Guidelines

### Code of Conduct

**Be Respectful:**
- Welcome newcomers
- Assume good intentions
- No harassment or discrimination

**Be Constructive:**
- Provide helpful feedback
- Focus on code, not people
- Suggest improvements

**Be Professional:**
- Stay on topic
- No spam or advertising
- Respect maintainers' time

### Communication Channels

- **GitHub Issues** - Bug reports, feature requests
- **GitHub Discussions** - Questions, ideas
- **Discord** (optional) - Real-time chat
- **Email** - Private: maintainers@agenticfactory.dev

### Reporting Issues

**Bug Reports:**
```markdown
**Description**
Clear description of the bug

**Steps to Reproduce**
1. Step 1
2. Step 2
3. Step 3

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Environment**
- OS: Ubuntu 22.04
- Python: 3.11
- Version: 1.2.3

**Logs**
```
Relevant log output
```
```

**Feature Requests:**
```markdown
**Description**
What feature would you like?

**Use Case**
Why do you need this?

**Proposed Solution**
How should it work?

**Alternatives**
What else have you considered?
```

---

## Development Tips

### Debugging

```python
# Add breakpoints
import pdb; pdb.set_trace()

# Or use ipdb for better experience
import ipdb; ipdb.set_trace()

# Log debugging info
import logging
logger = logging.getLogger(__name__)
logger.debug(f"Variable value: {variable}")
```

### Profiling

```bash
# Time execution
uv run python -m cProfile -o profile.stats factory.py run

# View profile
uv run python -m pstats profile.stats

# Memory profiling
uv run python -m memory_profiler factory.py
```

### Database Inspection

```bash
# SQLite CLI
sqlite3 data/factory.db

# Common queries
.tables
.schema opportunities
SELECT * FROM opportunities LIMIT 5;
SELECT status, COUNT(*) FROM opportunities GROUP BY status;
```

---

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in documentation

Thank you for contributing! 🎉

---

For questions, contact:
- Email: maintainers@agenticfactory.dev
- GitHub: [@yourusername](https://github.com/yourusername)
