from pathlib import Path
import pandas as pd


def main():
    print("\n=== JOB LISTINGS ANALYTICS PIPELINE ===")

    raw_file = Path("data/raw/job_listings_raw.csv")
    cleaned_dir = Path("data/cleaned")
    processed_dir = Path("data/processed")

    if not raw_file.exists():
        raise FileNotFoundError(f"Raw CSV not found: {raw_file}")

    print("\n1. Loading raw data...")
    df = pd.read_csv(raw_file)
    print(f"Loaded {len(df)} rows and {len(df.columns)} columns.")

    if df.empty:
        raise ValueError("The raw CSV contains no job listings.")

    print("\n2. Cleaning data...")
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    for column in df.select_dtypes(include="object").columns:
        df[column] = df[column].map(
            lambda value: value.strip() if isinstance(value, str) else value
        )
        df[column] = df[column].replace("", pd.NA)

    df = df.drop_duplicates()

    cleaned_dir.mkdir(parents=True, exist_ok=True)
    cleaned_file = cleaned_dir / "job_listings_cleaned.csv"
    df.to_csv(cleaned_file, index=False)
    print(f"Saved: {cleaned_file}")

    print("\n3. Creating analytical features...")
    processed = df.copy()

    if "job_description" in processed.columns:
        processed["description_length"] = (
            processed["job_description"].fillna("").astype(str).str.len()
        )

    if "job_title" in processed.columns:
        processed["title_word_count"] = (
            processed["job_title"].fillna("").astype(str).str.split().str.len()
        )

    processed_dir.mkdir(parents=True, exist_ok=True)
    processed_file = processed_dir / "job_listings_processed.csv"
    processed.to_csv(processed_file, index=False)
    print(f"Saved: {processed_file}")

    print("\n4. Data quality report")
    print(f"Rows: {len(processed)}")
    print(f"Columns: {len(processed.columns)}")
    print(f"Duplicate rows: {processed.duplicated().sum()}")
    print(f"Missing cells: {processed.isna().sum().sum()}")

    print("\nSUCCESS: Pipeline completed!")


if __name__ == "__main__":
    main()