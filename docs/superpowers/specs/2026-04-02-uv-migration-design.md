# UV Migration Design

Date: 2026-04-02
Topic: Convert the repository to use `uv` for all Python packaging and environment management

## Objective

Move the repository from `requirements.txt` plus ad hoc `pip` and `venv` workflows to a single `uv`-managed workflow. After this change, dependency definition, lockfile management, local execution, testing, and Docker builds should all flow through `uv`.

## Current State

The repository currently uses:

- `requirements.txt` for runtime dependencies
- `requirements-dev.txt` for development dependencies
- `pip install -r ...` in the `Makefile`, `Dockerfile`, and setup docs
- manual virtualenv creation in `README.md`, `CONTRIBUTING.md`, and `DEPLOYMENT.md`
- direct `python` and `pytest` commands in common workflows

This creates multiple sources of truth and leaves packaging behavior inconsistent between local development, CI-style workflows, and container builds.

## Decision

Adopt `uv` as the only supported Python packaging and environment workflow for this repository.

The new source of truth will be:

- `pyproject.toml` for project metadata and dependency declarations
- `uv.lock` for the resolved dependency graph

The old source-of-truth files will be removed:

- `requirements.txt`
- `requirements-dev.txt`

## Scope

This migration covers four areas.

### 1. Packaging

Add a root `pyproject.toml` that defines:

- project metadata
- supported Python version
- runtime dependencies
- optional `dev` dependencies for test and tooling workflows

Generate and commit `uv.lock` so installs and Docker builds resolve from the same locked dependency graph.

### 2. Developer Workflows

Update `Makefile` targets to use `uv` consistently:

- `uv sync` for runtime installs
- `uv sync --extra dev` for development installs
- `uv run pytest` for tests
- `uv run black`, `uv run isort`, `uv run flake8`, and `uv run mypy` for quality tasks
- `uv run python ...` for the factory, demo, dashboard, and utility entrypoints

The existing script layout stays in place. This migration does not convert the repository into a packaged `src/` project and does not change the CLI surface area.

### 3. Containerization

Update `Dockerfile` to install and use `uv` instead of `pip` and manual `venv` setup.

The container build should:

- copy `pyproject.toml` and `uv.lock` early for dependency-layer caching
- install dependencies using `uv`
- run the application through the environment created by `uv`
- avoid `pip install` and `python -m venv`

If the final Docker layout still needs an explicit environment path for runtime clarity, that is acceptable, but it must be produced and managed by `uv`, not by handwritten virtualenv commands.

### 4. Documentation

Update user-facing instructions in:

- `README.md`
- `CONTRIBUTING.md`
- `DEPLOYMENT.md`

Documentation should standardize on:

- `uv sync --extra dev` for local development setup
- `uv run ...` for execution and testing

Direct `.venv` references should only remain where the surrounding platform requires an absolute interpreter path, such as a service manager example.

## Non-Goals

This change does not include:

- restructuring the repository into a new package layout
- renaming modules or changing imports
- redesigning the CLI
- changing business logic or agent behavior
- keeping `requirements*.txt` as compatibility artifacts

## Alternatives Considered

### Keep generated `requirements.txt` files

Rejected because it would preserve multiple dependency definitions and undermine the goal of making `uv` the single source of truth.

### Add `uv` only for local development

Rejected because it would leave Docker and operational docs on the legacy path, which does not satisfy the request to use `uv` for all Python packaging and management.

## Risks and Mitigations

### Risk: operational instructions still assume an activated virtualenv

Mitigation: normalize commands to `uv run ...` everywhere practical and only retain explicit environment paths when an external tool requires them.

### Risk: dependency resolution changes slightly when moving from floating requirements files to `uv.lock`

Mitigation: commit the lockfile, verify the main commands through `uv`, and keep the dependency declarations aligned with the current runtime and dev tool usage.

### Risk: Docker build behavior diverges from local development

Mitigation: use the same `pyproject.toml` and `uv.lock` inside Docker so dependency installation follows the same source of truth.

## Verification Plan

Verification will use the new workflow rather than the legacy one.

### Packaging checks

- `pyproject.toml` exists
- `uv.lock` exists
- `requirements.txt` and `requirements-dev.txt` are removed

### Workflow checks

- `uv sync --extra dev`
- `uv run pytest`
- `uv run python factory.py status`

### Repository checks

Add a small regression test that asserts:

- the `uv` files exist
- the old requirements files do not exist
- key `Makefile` targets call `uv`

### Container checks

If the local environment permits it without extra approvals, validate the updated Docker build path against the `uv`-based configuration.

## Implementation Outline

1. Add `pyproject.toml` with runtime and dev dependency groups.
2. Generate `uv.lock`.
3. Replace `Makefile` install, test, lint, format, and run targets with `uv` commands.
4. Rewrite `Dockerfile` to install and use dependencies through `uv`.
5. Update docs to remove `pip` and manual `venv` guidance.
6. Add a regression test for the repo-level packaging contract.
7. Run verification using `uv`.

## Success Criteria

The migration is complete when:

- all Python dependency management is defined in `pyproject.toml` and locked in `uv.lock`
- the repository no longer depends on `requirements*.txt`
- standard local development flows run through `uv`
- Docker no longer uses `pip install` or handwritten virtualenv creation
- documentation consistently points contributors to `uv`
