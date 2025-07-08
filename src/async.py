import asyncio
import json
import re
import time
from pathlib import Path
from typing import Set

import aiohttp
import janus
from requests.compat import urljoin

from models import DiscoveredUrl, ScrapeResult


class WikipediaScraperAsync:
    """
    Async Wikipedia link scraper.
    """

    def __init__(
        self,
        start_url: str = "https://www.wikipedia.org/",
        duration: int = 20,
        max_workers: int = 50,
        max_connections: int = 50,
    ):
        """
        Initializes the WikipediaScraperAsync instance.
        :param str start_url: First page to visit.
        :param int duration: Max run time (seconds).
        :param int max_workers: Parallel tasks.
        :param int max_connections: Maximum connections.
        """
        self.start_url = start_url
        self.duration = duration
        self.max_workers = max_workers
        self.max_connections = max_connections

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

    async def worker(
        self,
        session: aiohttp.ClientSession,
        queue: janus.Queue,
        unique_links: Set[str],
    ):
        """
        Worker: fetch a URL, parse, push new ones.
        :param aiohttp.ClientSession session: HTTP client.
        :param janus.Queue queue: Shared URL queue.
        :param Set[str] unique_links: Already seen URLs.
        """
        while True:
            try:
                url = await queue.async_q.get()
            except asyncio.CancelledError:
                break
            if url is None:
                queue.async_q.task_done()
                break
            try:
                async with session.get(url, timeout=3) as resp:
                    if resp.status != 200:
                        queue.async_q.task_done()
                        continue
                    text = await resp.text()
                    links = self.extract_links(text, url)
                    for link in links:
                        if link not in unique_links:
                            unique_links.add(link)
                            await queue.async_q.put(link)
            except Exception:
                continue
            queue.async_q.task_done()

    async def scrape_async(self) -> ScrapeResult:
        """
        Run the crawl.
        :return ScrapeResult: Links, count, time.
        """
        start_time = time.monotonic()
        unique_links: Set[str] = set()
        queue = janus.Queue()
        await queue.async_q.put(self.start_url)
        unique_links.add(self.start_url)

        connector = aiohttp.TCPConnector(
            limit=self.max_connections,
            limit_per_host=self.max_connections,
            ttl_dns_cache=300,
        )

        headers = {"Accept-Encoding": "gzip, br"}

        async with aiohttp.ClientSession(
            connector=connector, headers=headers
        ) as session:
            workers = [
                asyncio.create_task(self.worker(session, queue, unique_links))
                for _ in range(self.max_workers)
            ]

            # small buffer so we don't overshoot
            delta = 0.05
            timeout = max(0.1, self.duration - delta)

            try:
                await asyncio.wait_for(asyncio.gather(*workers), timeout=timeout)
            except asyncio.TimeoutError:
                # kill overrunning tasks
                for w in workers:
                    w.cancel()
                await asyncio.gather(*workers, return_exceptions=True)

        elapsed = time.monotonic() - start_time
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
        :return None
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
    """
    Quick CLI test run.
    :return None
    """
    scraper = WikipediaScraperAsync()
    result = asyncio.run(scraper.scrape_async())
    print(f"Count: {result.count}")
    print(f"Elapsed time: {result.elapsed:.2f}s")
    scraper.save(result)


if __name__ == "__main__":
    main()
