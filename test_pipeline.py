from pathlib import Path

import pandas as pd

from run_pipeline import main


PROJECT_ROOT = Path(__file__).parent


def test_project_has_app_file():
    assert (PROJECT_ROOT / "app.py").is_file()


def test_project_has_requirements_file():
    assert (PROJECT_ROOT / "requirements.txt").is_file()


def test_data_directory_exists():
    assert (PROJECT_ROOT / "data").is_dir()


def test_pandas_is_available():
    assert pd.__version__


def test_pipeline_cleans_and_processes_csv(tmp_path, monkeypatch):
    """Check that the pipeline cleans data and creates features."""
    monkeypatch.chdir(tmp_path)

    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True)

    sample = pd.DataFrame({
        " Job Title ": [" Data Analyst ", "Data Analyst"],
        "Job Description": [" Analyze data ", " Analyze data "],
        "Company Name": [" Acme ", " Acme "],
    })

    sample.to_csv(raw_dir / "job_listings_raw.csv", index=False)

    main()

    cleaned_file = (
        tmp_path / "data" / "cleaned" / "job_listings_cleaned.csv"
    )
    processed_file = (
        tmp_path / "data" / "processed" / "job_listings_processed.csv"
    )

    assert cleaned_file.is_file()
    assert processed_file.is_file()

    cleaned = pd.read_csv(cleaned_file)
    processed = pd.read_csv(processed_file)

    assert len(cleaned) == 1
    assert "job_title" in cleaned.columns
    assert cleaned.loc[0, "job_title"] == "Data Analyst"

    assert "description_length" in processed.columns
    assert "title_word_count" in processed.columns
    assert processed.loc[0, "description_length"] == len("Analyze data")
    assert processed.loc[0, "title_word_count"] == 2


def test_pipeline_rejects_missing_raw_csv(tmp_path, monkeypatch):
    """Check that a missing input file raises a clear error."""
    monkeypatch.chdir(tmp_path)

    try:
        main()
    except FileNotFoundError as error:
        assert "Raw CSV not found" in str(error)
    else:
        raise AssertionError("Expected FileNotFoundError")