import json
import logging
import re
import time
from collections import deque
from pathlib import Path

import requests
from requests.compat import urljoin

from models import DiscoveredUrl, ScrapeResult

logging.basicConfig(level=logging.INFO, format="%(message)s")


class WikipediaScraper:
    """Sync Wikipedia link scraper."""

    def __init__(
        self,
        start_url: str = "https://www.wikipedia.org/",
        duration: int = 20,
    ):
        """
        :param str start_url: First page to visit.
        :param int duration: Max run time (seconds).
        """
        self.start_url = start_url
        self.duration = duration

    def log(self, message: str, emoji: str = ""):
        """Tiny helper for pretty logs."""
        logging.info(f"{emoji} {message}")

    def extract_links(self, html: str, base_url: str) -> list[str]:
        """
        Grab absolute Wikipedia links from raw HTML.
        :param str html: Page HTML.
        :param str base_url: Needed for relative links.
        :return list[str]: Found URLs.
        """
        href_pattern = re.compile(
            r'<a\s+(?:[^>]*?\s+)?href=["\'](.*?)["\']', re.IGNORECASE
        )
        links = set()
        for match in href_pattern.findall(html):
            href = match
            if href.startswith("http") or href.startswith("/"):
                if href.startswith("/"):
                    href = urljoin(base_url, href)
                if "wikipedia.org" in href:
                    links.add(href)
        return list(links)

    def scrape(self) -> ScrapeResult:
        """
        Run the crawl.
        :return ScrapeResult: Links, count, time.
        """
        # init
        start_time = time.monotonic()
        unique_links: set[str] = set()
        queue: deque[str] = deque()
        session = requests.Session()
        queue.append(self.start_url)
        unique_links.add(self.start_url)
        delta = 0.1  # small buffer

        self.log(f"Starting scraping from {self.start_url}", "💡")
        while queue and (time.monotonic() - start_time) < (self.duration - delta):
            url = queue.popleft()
            try:
                resp = session.get(url, timeout=3)
                if resp.status_code != 200:
                    self.log(f"Failed to fetch {url} (status {resp.status_code})", "⚠️")
                    continue
                links = self.extract_links(resp.text, url)
                for link in links:
                    if link not in unique_links:
                        unique_links.add(link)
                        queue.append(link)
            except Exception as e:
                self.log(f"Error fetching {url}: {e}", "❌")
        elapsed = time.monotonic() - start_time

        # Validation via Pydantic
        discovered = [DiscoveredUrl(url=link).url for link in unique_links]
        return ScrapeResult(
            unique_links=discovered,
            count=len(discovered),
            elapsed=elapsed,
        )

    def save(
        self,
        result: ScrapeResult,
        filename: str = "wikipedia_links.json",
    ) -> None:
        """
        Dump result to JSON.
        :param ScrapeResult result: Data to save.
        :param str filename: Output file.
        """
        output = {
            "💡 unique_links": [str(url) for url in result.unique_links],
            "💡 count": result.count,
            "⏰ elapsed": result.elapsed,
        }
        with open(Path.cwd() / filename, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"✅ Results saved to {filename}")


def main():
    scraper = WikipediaScraper()
    result = scraper.scrape()
    print(f"Count: {result.count}")
    print(f"Elapsed time: {result.elapsed:.2f}s")
    scraper.save(result)


if __name__ == "__main__":
    main()
