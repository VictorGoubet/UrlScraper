help:
	@echo "Available commands:"
	@echo "  run-sync   - Run the Wikipedia scraper (sync.py)"
	@echo "  run-async  - Run the Wikipedia scraper (async.py)"

run-sync:
	.venv/bin/python src/sync.py

run-async:
	.venv/bin/python src/async.py

install:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt