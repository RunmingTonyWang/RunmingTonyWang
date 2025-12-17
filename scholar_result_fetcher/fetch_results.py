"""Fetch Google Scholar result counts for a keyword using Selenium only.

This tool builds a Google Scholar query restricted to 2025 results using the
"allintitle" operator, drives a headless Selenium browser to fetch the page,
and extracts the reported result count (e.g., "About 12,400 results").
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys
import time
import urllib.parse
from typing import Iterable

RESULT_PATTERN = re.compile(r"About ([\d,]+) results")
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
)


def build_query_url(keyword: str) -> str:
    """Construct the Google Scholar URL for the supplied keyword."""
    query = f'allintitle: "{keyword}"'
    encoded_query = urllib.parse.quote_plus(query)
    return (
        "https://scholar.google.com/scholar?q="
        f"{encoded_query}&as_sdt=0%2C21&as_ylo=2025&as_yhi=2025"
    )


def _parse_result_count(html: str) -> int:
    match = RESULT_PATTERN.search(html)
    if not match:
        raise ValueError("Could not locate result count in the response")

    return int(match.group(1).replace(",", ""))


def _read_html_file(path: pathlib.Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"HTML file not found: {path}")
    return path.read_text(encoding="utf-8", errors="ignore")


def _create_driver(chrome_options: Iterable[str]):
    """Create a Chrome driver with a slightly more human-like fingerprint.

    Uses the guidance from Bright Data's Google Scholar scraping tutorial to set
    the user agent, window size, and automation flags, which can reduce 403
    responses. Selenium is imported lazily to keep module import fast and to
    emit a clear error when Selenium is missing.
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
    except Exception as exc:  # noqa: BLE001
        raise ImportError(
            "Selenium is required. Install it with `pip install -r requirements.txt`."
        ) from exc

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument(f"--user-agent={USER_AGENT}")
    options.add_argument("--window-size=1280,900")
    options.add_argument("--lang=en-US,en;q=0.9")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    for opt in chrome_options:
        options.add_argument(opt)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(options=options)
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})",
        },
    )
    return driver


def fetch_result_count_selenium(
    keyword: str,
    wait_seconds: float = 8.0,
    chrome_options: Iterable[str] | None = None,
) -> int:
    """Return the parsed result count using a headless Selenium browser.

    Requires a Chrome-compatible driver on PATH. This approach closely mimics
    user behavior and follows the Bright Data tutorial suggestions that reduce
    the likelihood of 403 responses from Scholar.
    """
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    driver = _create_driver(chrome_options or [])
    driver.get(build_query_url(keyword))
    try:
        WebDriverWait(driver, wait_seconds).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#gs_ab_md"))
        )
        time.sleep(1.5)  # allow late-loading dynamic content to settle
        html = driver.page_source
    finally:
        driver.quit()

    return _parse_result_count(html)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--keyword",
        help="Keyword to search (if omitted, you will be prompted).",
    )
    parser.add_argument(
        "--selenium-wait",
        type=float,
        default=8.0,
        help="Seconds to wait for the results bar when using Selenium.",
    )
    parser.add_argument(
        "--html-file",
        type=pathlib.Path,
        help=(
            "Parse a saved HTML file instead of fetching live content. Useful for "
            "offline verification."
        ),
    )
    parser.add_argument(
        "--chrome-option",
        action="append",
        default=[],
        help="Extra Chrome option to pass through to Selenium (repeatable).",
    )
    return parser.parse_args()


def main() -> None:
    """Prompt for a keyword, fetch the result count, and display it."""
    args = _parse_args()
    if args.html_file:
        try:
            html = _read_html_file(args.html_file)
            count = _parse_result_count(html)
        except Exception as exc:  # noqa: BLE001
            sys.exit(f"Failed to parse saved HTML: {exc}")
    else:
        keyword = args.keyword or input("Enter keyword: ").strip()
        if not keyword:
            sys.exit("Keyword is required")

        try:
            count = fetch_result_count_selenium(
                keyword,
                wait_seconds=args.selenium_wait,
                chrome_options=args.chrome_option,
            )
        except Exception as exc:  # noqa: BLE001
            sys.exit(f"Failed to fetch result count: {exc}")

    print(f"Result count: {count}")


if __name__ == "__main__":
    main()
