# Agentic Arbitrage Factory - Docker Image
# Multi-stage build for production

# =============================================================================
# Stage 1: Builder
# =============================================================================
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOME=/app \
    UV_LINK_MODE=copy

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.5.1 /uv /uvx /bin/

WORKDIR $APP_HOME

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .
RUN uv sync --frozen --no-dev

# =============================================================================
# Stage 2: Production
# =============================================================================
FROM python:3.11-slim AS production

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

COPY --from=ghcr.io/astral-sh/uv:0.5.1 /uv /uvx /bin/
COPY --from=builder /app /app

RUN mkdir -p data sites archive && chown -R factory:factory $APP_HOME

USER factory

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD uv run python -c "import sys; sys.exit(0)" || exit 1

CMD ["uv", "run", "python", "factory.py", "continuous"]

# =============================================================================
# Stage 3: Development
# =============================================================================
FROM production AS development

USER root

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --extra dev

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    vim \
    && rm -rf /var/lib/apt/lists/*

USER factory

CMD ["uv", "run", "python", "factory.py", "run"]
