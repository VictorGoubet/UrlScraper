from pydantic import BaseModel


class DiscoveredUrl(BaseModel):
    """
    Represents a discovered Wikipedia URL.
    :param str url: The discovered URL.
    """

    url: str


class ScrapeResult(BaseModel):
    """
    Represents the result of a Wikipedia scraping session.
    :param list[str] unique_links: List of unique discovered URLs.
    :param int count: Number of unique links.
    :param float elapsed: Elapsed time in seconds.
    """

    unique_links: list[str]
    count: int
    elapsed: float
