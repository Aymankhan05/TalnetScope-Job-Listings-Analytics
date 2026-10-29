from pathlib import Path
import json

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT_DIR / "data" / "processed" / "job_listings_processed.csv"
REPORT_DIR = ROOT_DIR / "reports"
OUTPUT_FILE = REPORT_DIR / "analytics_summary.json"


def load_data() -> pd.DataFrame:
    """Load processed job listings and validate the dataset."""
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Processed dataset not found: {DATA_FILE}. "
            "Run run_pipeline.py first."
        )

    df = pd.read_csv(DATA_FILE)

    required_columns = {"job_title", "company_name", "location"}
    missing_columns = required_columns.difference(df.columns)

    if missing_columns:
        raise ValueError(
            f"Dataset is missing required columns: {sorted(missing_columns)}"
        )

    if df.empty:
        raise ValueError("The processed dataset contains no job listings.")

    return df


def count_values(df: pd.DataFrame, column: str, limit: int = 10) -> list:
    """Return the most frequent non-empty values for a column."""
    values = (
        df[column]
        .dropna()
        .astype(str)
        .str.strip()
    )

    values = values[values.ne("")]

    counts = values.value_counts().head(limit)

    return [
        {"name": str(name), "count": int(count)}
        for name, count in counts.items()
    ]


def build_summary(df: pd.DataFrame) -> dict:
    """Calculate dashboard metrics and chart-ready analytics."""
    total_rows = len(df)

    missing_by_column = {
        str(column): int(count)
        for column, count in df.isna().sum().items()
    }

    if "apply_link" in df.columns:
        links = df["apply_link"].fillna("").astype(str).str.strip()
        valid_links = int(
            links.str.startswith(("http://", "https://")).sum()
        )
    else:
        valid_links = 0

    if "description_length" in df.columns:
        average_description_length = round(
            float(df["description_length"].fillna(0).mean()), 2
        )
    else:
        average_description_length = 0.0

    if "title_word_count" in df.columns:
        average_title_words = round(
            float(df["title_word_count"].fillna(0).mean()), 2
        )
    else:
        average_title_words = 0.0

    summary = {
        "overview": {
            "total_listings": int(total_rows),
            "unique_job_titles": int(df["job_title"].nunique()),
            "unique_companies": int(df["company_name"].nunique()),
            "unique_locations": int(df["location"].nunique()),
            "duplicate_rows": int(df.duplicated().sum()),
            "missing_cells": int(df.isna().sum().sum()),
            "valid_http_links": valid_links,
            "average_description_length": average_description_length,
            "average_title_words": average_title_words,
        },
        "charts": {
            "top_job_titles": count_values(df, "job_title"),
            "top_companies": count_values(df, "company_name"),
            "top_locations": count_values(df, "location"),
        },
        "data_quality": {
            "rows": int(total_rows),
            "columns": int(len(df.columns)),
            "missing_by_column": missing_by_column,
        },
    }

    return summary


def main() -> None:
    print("\n=== JOB LISTINGS ANALYTICS ===")

    df = load_data()
    summary = build_summary(df)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    OUTPUT_FILE.write_text(
        json.dumps(summary, indent=4, ensure_ascii=False),
        encoding="utf-8",
    )

    print("\nOVERVIEW")
    for metric, value in summary["overview"].items():
        print(f"{metric.replace('_', ' ').title()}: {value}")

    print("\nTOP 5 JOB TITLES")
    for item in summary["charts"]["top_job_titles"][:5]:
        print(f"{item['name']}: {item['count']}")

    print("\nTOP 5 COMPANIES")
    for item in summary["charts"]["top_companies"][:5]:
        print(f"{item['name']}: {item['count']}")

    print("\nTOP 5 LOCATIONS")
    for item in summary["charts"]["top_locations"][:5]:
        print(f"{item['name']}: {item['count']}")

    print(f"\nAnalytics report saved to: {OUTPUT_FILE}")
    print("SUCCESS: Analytics completed!")


if __name__ == "__main__":
    main()