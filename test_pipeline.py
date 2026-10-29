from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"


def test_project_has_app_file():
    """The Streamlit dashboard file should exist."""
    assert (PROJECT_ROOT / "app.py").is_file()


def test_project_has_requirements_file():
    """The project should list its dependencies."""
    assert (PROJECT_ROOT / "requirements.txt").is_file()


def test_data_directory_exists():
    """The project should contain a data directory."""
    assert DATA_DIR.is_dir()


def test_pandas_is_available():
    """Pandas should be installed and importable."""
    assert pd.__version__