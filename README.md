# Wikipedia Link Scraper

This repo contains two small tools that crawl Wikipedia and collect unique links:

* **`src/sync.py`** – classic, blocking version.
* **`src/async.py`** – high-throughput asynchronous version powered by `aiohttp`.

Both scripts stop after a user-defined duration and export the result to `wikipedia_links.json`.

## Quick start

```bash
# create venv + install deps
make install

# run the simple synchronous crawler
make run-sync

# run the fast async crawler
make run-async
```

The saved JSON file looks like:

```json
{
  "💡 unique_links": ["https://en.wikipedia.org/wiki/Python" , ...],
  "💡 count": 12345,
  "⏰ elapsed": 4.98
}
```

Feel free to tweak `duration`, `max_workers` and `max_connections` in `src/async.py` to suit your machine and network connection. 