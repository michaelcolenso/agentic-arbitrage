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

    pyproject_text = pyproject.read_text()

    assert "[project]" in pyproject_text
    assert 'requires-python = ">=' in pyproject_text
    assert "[project.optional-dependencies]" in pyproject_text
    assert "dev = [" in pyproject_text
    assert "[tool.uv]" in pyproject_text
    assert "package = false" in pyproject_text

    assert "pip install" not in makefile
    assert "\tuv sync\n" in makefile
    assert "\tuv sync --extra dev\n" in makefile
    assert "\tuv run pytest tests/ -v\n" in makefile
    assert "\tuv run pytest tests/ --cov=. --cov-report=html --cov-report=term\n" in makefile
    assert "\tuv run python factory.py run\n" in makefile
    assert "\tuv run python demo.py\n" in makefile
    assert "\tuv run python dashboard.py\n" in makefile

    assert "uv sync" in makefile
    assert "uv run pytest" in makefile
    assert "uv run python factory.py" in makefile


def test_dockerfile_uses_uv():
    dockerfile = (ROOT / "Dockerfile").read_text()

    assert "pip install" not in dockerfile
    assert "python -m venv" not in dockerfile
    assert "COPY pyproject.toml uv.lock ./" in dockerfile
    assert "uv sync --frozen --no-dev" in dockerfile
    assert 'CMD ["uv", "run", "python", "factory.py", "continuous"]' in dockerfile


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
