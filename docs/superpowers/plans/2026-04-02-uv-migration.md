# UV Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `requirements*.txt`, `pip`, and manual virtualenv management with a single `uv`-managed workflow across local development, testing, documentation, and Docker.

**Architecture:** The repository remains a flat script-based project rather than being repackaged into `src/`. `pyproject.toml` becomes the dependency source of truth, `uv.lock` becomes the resolved lockfile, and all commands run via `uv sync` and `uv run`. A repo-level regression test guards the migration contract so the old `requirements*.txt` path does not reappear.

**Tech Stack:** Python 3.11, `uv`, pytest, Make, Docker

---

## File Structure

- Create: `pyproject.toml`
- Create: `uv.lock`
- Create: `tests/test_uv_packaging.py`
- Modify: `Makefile`
- Modify: `Dockerfile`
- Modify: `README.md`
- Modify: `CONTRIBUTING.md`
- Modify: `DEPLOYMENT.md`
- Delete: `requirements.txt`
- Delete: `requirements-dev.txt`

### Task 1: Add the regression test for the packaging contract

**Files:**
- Create: `tests/test_uv_packaging.py`
- Test: `tests/test_uv_packaging.py`

- [ ] **Step 1: Write the failing test**

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_uv_packaging_contract():
    pyproject = ROOT / "pyproject.toml"
    uv_lock = ROOT / "uv.lock"
    requirements = ROOT / "requirements.txt"
    requirements_dev = ROOT / "requirements-dev.txt"
    makefile = (ROOT / "Makefile").read_text()

    assert pyproject.exists()
    assert uv_lock.exists()
    assert not requirements.exists()
    assert not requirements_dev.exists()
    assert "uv sync" in makefile
    assert "uv run pytest" in makefile
    assert "uv run python factory.py" in makefile
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_uv_packaging.py -v`
Expected: FAIL because `pyproject.toml` and `uv.lock` do not exist yet, `requirements*.txt` still exist, and the `Makefile` still uses `pip` and raw `python`.

- [ ] **Step 3: Create the test file with the failing assertion**

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_uv_packaging_contract():
    pyproject = ROOT / "pyproject.toml"
    uv_lock = ROOT / "uv.lock"
    requirements = ROOT / "requirements.txt"
    requirements_dev = ROOT / "requirements-dev.txt"
    makefile = (ROOT / "Makefile").read_text()

    assert pyproject.exists()
    assert uv_lock.exists()
    assert not requirements.exists()
    assert not requirements_dev.exists()
    assert "uv sync" in makefile
    assert "uv run pytest" in makefile
    assert "uv run python factory.py" in makefile
```

- [ ] **Step 4: Re-run the single test and confirm the expected failure**

Run: `pytest tests/test_uv_packaging.py -v`
Expected: FAIL on the missing `pyproject.toml` assertion.

- [ ] **Step 5: Commit**

```bash
git add tests/test_uv_packaging.py
git commit -m "test: add uv packaging contract regression"
```

### Task 2: Replace `requirements*.txt` with `pyproject.toml` and `uv.lock`

**Files:**
- Create: `pyproject.toml`
- Create: `uv.lock`
- Delete: `requirements.txt`
- Delete: `requirements-dev.txt`
- Test: `tests/test_uv_packaging.py`

- [ ] **Step 1: Write the failing dependency-definition expectation**

Add this assertion block to `tests/test_uv_packaging.py` after the existence checks:

```python
    pyproject_text = pyproject.read_text()

    assert "[project]" in pyproject_text
    assert 'requires-python = ">=' in pyproject_text
    assert "[project.optional-dependencies]" in pyproject_text
    assert "dev = [" in pyproject_text
    assert "[tool.uv]" in pyproject_text
    assert "package = false" in pyproject_text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_uv_packaging.py -v`
Expected: FAIL because `pyproject.toml` still does not exist.

- [ ] **Step 3: Write the minimal dependency source of truth**

Create `pyproject.toml` with this content:

```toml
[project]
name = "agentic-arbitrage-factory"
version = "0.1.0"
description = "Autonomous system that discovers, validates, builds, deploys, and manages programmatic SEO sites."
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
  "aiohttp>=3.9.0",
  "aiohttp-retry>=2.8.0",
  "beautifulsoup4>=4.12.0",
  "click>=8.1.0",
  "colorama>=0.4.6",
  "diskcache>=5.6.0",
  "lxml>=4.9.0",
  "orjson>=3.9.0",
  "pydantic>=2.0.0",
  "python-dateutil>=2.8.0",
  "python-dotenv>=1.0.0",
  "rich>=13.5.0",
  "schedule>=1.2.0",
  "tqdm>=4.66.0",
]

[project.optional-dependencies]
dev = [
  "bandit>=1.7.5",
  "black>=23.7.0",
  "bumpversion>=0.6.0",
  "flake8>=6.1.0",
  "ipdb>=0.13.13",
  "ipython>=8.15.0",
  "isort>=5.12.0",
  "line-profiler>=4.1.0",
  "locust>=2.16.0",
  "memory-profiler>=0.61.0",
  "mkdocs>=1.5.0",
  "mkdocs-material>=9.2.0",
  "mypy>=1.5.0",
  "pre-commit>=3.4.0",
  "pytest>=7.4.0",
  "pytest-asyncio>=0.21.0",
  "pytest-cov>=4.1.0",
  "pytest-mock>=3.11.0",
  "safety>=2.3.0",
  "types-python-dateutil>=2.8.0",
  "types-requests>=2.31.0",
]

[tool.uv]
package = false
```

Then generate `uv.lock` with:

Run: `uv lock`
Expected: `Resolved ... packages` and a new `uv.lock` file in the repository root.

Delete `requirements.txt` and `requirements-dev.txt`.

- [ ] **Step 4: Run the focused test to verify it passes**

Run: `pytest tests/test_uv_packaging.py -v`
Expected: PASS for the dependency-definition assertions, with any remaining failures now limited to `Makefile` expectations that have not been implemented yet.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock tests/test_uv_packaging.py
git rm requirements.txt requirements-dev.txt
git commit -m "build: migrate dependency definitions to uv"
```

### Task 3: Convert Make targets to `uv sync` and `uv run`

**Files:**
- Modify: `Makefile`
- Test: `tests/test_uv_packaging.py`

- [ ] **Step 1: Write the failing Makefile expectations**

Extend `tests/test_uv_packaging.py` with these assertions:

```python
    assert "pip install" not in makefile
    assert "\tuv sync\n" in makefile
    assert "\tuv sync --extra dev\n" in makefile
    assert "\tuv run pytest tests/ -v\n" in makefile
    assert "\tuv run pytest tests/ --cov=. --cov-report=html --cov-report=term\n" in makefile
    assert "\tuv run python factory.py run\n" in makefile
    assert "\tuv run python demo.py\n" in makefile
    assert "\tuv run python dashboard.py\n" in makefile
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_uv_packaging.py -v`
Expected: FAIL because `Makefile` still contains `pip install` and raw `python` and `pytest` commands.

- [ ] **Step 3: Write the minimal Makefile conversion**

Update these target bodies in `Makefile`:

```make
install:
	uv sync

install-dev:
	uv sync --extra dev

test:
	uv run pytest tests/ -v

test-coverage:
	uv run pytest tests/ --cov=. --cov-report=html --cov-report=term

lint:
	uv run flake8 agents/ core/ config/ --max-line-length=100
	uv run mypy agents/ core/ config/ --ignore-missing-imports

format:
	uv run black agents/ core/ config/ --line-length=100
	uv run isort agents/ core/ config/ --profile=black

format-check:
	uv run black agents/ core/ config/ --line-length=100 --check
	uv run isort agents/ core/ config/ --profile=black --check

run:
	uv run python factory.py run

demo:
	uv run python demo.py

status:
	uv run python factory.py status

continuous:
	uv run python factory.py continuous

discover:
	uv run python factory.py discover

validate:
	uv run python factory.py validate

build:
	uv run python factory.py build

cull:
	uv run python factory.py cull

dashboard:
	uv run python dashboard.py

setup: install-dev
	uv run pre-commit install
	mkdir -p data sites archive
	cp .env.example .env
	@echo "Setup complete! Edit .env file with your API keys."
```

Delete the `requirements:` target entirely because lockfile management now lives in `uv lock`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_uv_packaging.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add Makefile tests/test_uv_packaging.py
git commit -m "build: route developer workflows through uv"
```

### Task 4: Convert Docker to the `uv` workflow

**Files:**
- Modify: `Dockerfile`
- Test: `tests/test_uv_packaging.py`

- [ ] **Step 1: Write the failing Dockerfile expectations**

Add this new test to `tests/test_uv_packaging.py`:

```python
def test_dockerfile_uses_uv():
    dockerfile = (ROOT / "Dockerfile").read_text()

    assert "pip install" not in dockerfile
    assert "python -m venv" not in dockerfile
    assert "COPY pyproject.toml uv.lock ./" in dockerfile
    assert "uv sync --frozen --no-dev" in dockerfile
    assert 'CMD ["uv", "run", "python", "factory.py", "continuous"]' in dockerfile
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_uv_packaging.py -v`
Expected: FAIL because the current `Dockerfile` still uses `pip` and manual virtualenv setup.

- [ ] **Step 3: Write the minimal Docker conversion**

Replace the `Dockerfile` with this structure:

```dockerfile
FROM python:3.11-slim as builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOME=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR $APP_HOME

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .
RUN uv sync --frozen --no-dev

FROM python:3.11-slim as production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    APP_HOME=/app \
    PATH="/app/.venv/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r factory && useradd -r -g factory factory

WORKDIR $APP_HOME

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY --from=builder /app /app

RUN mkdir -p data sites archive && chown -R factory:factory $APP_HOME

USER factory

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD uv run python -c "import sys; sys.exit(0)" || exit 1

CMD ["uv", "run", "python", "factory.py", "continuous"]

FROM production as development

USER root

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --extra dev

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    vim \
    && rm -rf /var/lib/apt/lists/*

USER factory

CMD ["uv", "run", "python", "factory.py", "run"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_uv_packaging.py -v`
Expected: PASS for both packaging and Docker assertions.

- [ ] **Step 5: Commit**

```bash
git add Dockerfile tests/test_uv_packaging.py
git commit -m "build: convert docker workflow to uv"
```

### Task 5: Update documentation to the new `uv` workflow

**Files:**
- Modify: `README.md`
- Modify: `CONTRIBUTING.md`
- Modify: `DEPLOYMENT.md`
- Test: `tests/test_uv_packaging.py`

- [ ] **Step 1: Write the failing documentation expectations**

Add this test to `tests/test_uv_packaging.py`:

```python
def test_docs_reference_uv_workflow():
    readme = (ROOT / "README.md").read_text()
    contributing = (ROOT / "CONTRIBUTING.md").read_text()
    deployment = (ROOT / "DEPLOYMENT.md").read_text()

    assert "uv sync --extra dev" in readme
    assert "uv run python factory.py run" in readme
    assert "pip install -r requirements.txt" not in readme

    assert "uv sync --extra dev" in contributing
    assert "uv run pytest" in contributing
    assert "python -m venv venv" not in contributing

    assert "uv sync --extra dev" in deployment or "uv sync" in deployment
    assert "uv run python factory.py continuous" in deployment
    assert "pip install -r requirements.txt" not in deployment
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_uv_packaging.py -v`
Expected: FAIL because the docs still describe `venv`, `pip`, and raw `python`.

- [ ] **Step 3: Write the minimal documentation updates**

Make these replacements:

In `README.md`, replace:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python factory.py run
pytest tests/
```

with:

```bash
uv sync --extra dev
uv run python factory.py run
uv run pytest tests/
```

In `CONTRIBUTING.md`, replace setup and test snippets so they use:

```bash
uv sync --extra dev
uv run pre-commit install
uv run pytest
uv run pytest --cov=. --cov-report=html
uv run python -m cProfile -o profile.stats factory.py run
```

In `DEPLOYMENT.md`, replace setup and runtime snippets so they use:

```bash
uv sync --extra dev
uv run python factory.py run
uv run python factory.py continuous
nohup uv run python factory.py continuous > factory.log 2>&1 &
```

For service-manager examples that need an absolute interpreter path, update them to reference the `uv`-managed environment path:

```ini
Environment=PATH=/opt/agentic_factory/.venv/bin
ExecStart=/opt/agentic_factory/.venv/bin/python factory.py continuous
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_uv_packaging.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add README.md CONTRIBUTING.md DEPLOYMENT.md tests/test_uv_packaging.py
git commit -m "docs: update project workflows for uv"
```

### Task 6: Run full verification in the new workflow

**Files:**
- Modify: none
- Test: `tests/test_uv_packaging.py`, `tests/test_models.py`

- [ ] **Step 1: Sync the environment through `uv`**

Run: `uv sync --extra dev`
Expected: Environment resolves successfully and `.venv` is created or updated from `pyproject.toml` and `uv.lock`.

- [ ] **Step 2: Run the focused regression test**

Run: `uv run pytest tests/test_uv_packaging.py -v`
Expected: PASS.

- [ ] **Step 3: Run the existing test suite**

Run: `uv run pytest tests/ -v`
Expected: PASS.

- [ ] **Step 4: Run a smoke command through the new runtime path**

Run: `uv run python factory.py status`
Expected: Successful status output from the factory with no missing dependency errors.

- [ ] **Step 5: Optionally verify the container build**

Run: `docker build -t agentic-factory .`
Expected: Successful image build using the `uv`-based Dockerfile.

- [ ] **Step 6: Commit final verification-safe state**

```bash
git add pyproject.toml uv.lock Makefile Dockerfile README.md CONTRIBUTING.md DEPLOYMENT.md tests/test_uv_packaging.py
git commit -m "chore: finish uv migration"
```
