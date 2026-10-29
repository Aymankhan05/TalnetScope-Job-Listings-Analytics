"""
Job Listings Analytics Dashboard
Module: Web scraper

Collects practice job listings and saves the original records to CSV.
"""

from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup


BASE_URL = "https://realpython.github.io/fake-jobs/"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
RAW_DATA_FILE = RAW_DATA_DIR / "job_listings_raw.csv"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
    )
}

COLUMNS = [
    "job_title",
    "company_name",
    "location",
    "job_description",
    "apply_link",
]


def fetch_page(url: str = BASE_URL) -> str:
    """Download the webpage and return its HTML."""
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.text


def parse_job_listings(html: str) -> list[dict]:
    """Extract job information from the supplied HTML."""
    soup = BeautifulSoup(html, "html.parser")
    jobs = []

    for card in soup.select("div.card"):
        title = card.select_one("h2.title")
        company = card.select_one("h3.company")
        location = card.select_one("p.location")
        description = card.select_one("div.content")

        apply_button = card.select_one('a[href*="apply"], a.card-footer-item')

        if not title or not company:
            continue

        apply_link = ""
        if apply_button and apply_button.get("href"):
            apply_link = requests.compat.urljoin(
                BASE_URL, apply_button["href"]
            )

        jobs.append(
            {
                "job_title": title.get_text(" ", strip=True),
                "company_name": company.get_text(" ", strip=True),
                "location": (
                    location.get_text(" ", strip=True)
                    if location else ""
                ),
                "job_description": (
                    description.get_text(" ", strip=True)
                    if description else ""
                ),
                "apply_link": apply_link,
            }
        )

    return jobs


def scrape_jobs(url: str = BASE_URL) -> pd.DataFrame:
    """Fetch, parse, and return job listings as a DataFrame."""
    html = fetch_page(url)
    jobs = parse_job_listings(html)

    if not jobs:
        raise ValueError(
            "No job listings were extracted. "
            "The website structure may have changed."
        )

    return pd.DataFrame(jobs, columns=COLUMNS)


def save_raw_dataset(data: pd.DataFrame) -> Path:
    """Save the uncleaned dataset without overwriting other files."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    data.to_csv(RAW_DATA_FILE, index=False, encoding="utf-8-sig")
    return RAW_DATA_FILE


def main() -> None:
    """Run the scraper and display a brief collection summary."""
    try:
        print("Starting job listings scraper...")
        jobs = scrape_jobs()
        output_path = save_raw_dataset(jobs)

        print(f"\nSuccessfully collected {len(jobs)} job listings.")
        print(f"Raw dataset saved to: {output_path}")
        print("\nPreview:")
        print(jobs.head(5).to_string(index=False))

    except requests.RequestException as error:
        print(f"Website request failed: {error}")
        raise SystemExit(1) from error
    except (ValueError, OSError) as error:
        print(f"Scraping or file-saving error: {error}")
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()