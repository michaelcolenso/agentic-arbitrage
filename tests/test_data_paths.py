import importlib
from pathlib import Path

import config.settings as settings_module
import core.storage as storage_module


def reload_config_and_storage():
    settings = importlib.reload(settings_module)
    storage = importlib.reload(storage_module)
    return settings, storage


def test_default_data_dir_is_repo_local(monkeypatch):
    monkeypatch.delenv("FACTORY_DATA_DIR", raising=False)

    settings, storage = reload_config_and_storage()
    expected_data_dir = Path(settings.__file__).resolve().parent.parent / "data"

    assert settings.config.data_dir == expected_data_dir

    db_path = storage.Storage().db_path
    assert db_path == expected_data_dir / "factory.db"


def test_factory_data_dir_env_override(monkeypatch, tmp_path):
    expected_data_dir = tmp_path / "factory-data"
    monkeypatch.setenv("FACTORY_DATA_DIR", str(expected_data_dir))

    settings, storage = reload_config_and_storage()

    assert settings.config.data_dir == expected_data_dir

    db_path = storage.Storage().db_path
    assert db_path == expected_data_dir / "factory.db"
    assert db_path.parent.exists()
