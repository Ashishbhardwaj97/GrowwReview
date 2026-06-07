# Groww Weekly Review Pulse

> Automated system that ingests Groww's Google Play Store reviews, clusters them into semantic themes using ML, and delivers a weekly insight report via Google Docs and Gmail — powered by MCP servers.

---

## Overview

This project automates the weekly review analysis workflow for the Groww mobile app:

1. **Ingest** — Scrape recent reviews from the Google Play Store
2. **Preprocess** — PII scrubbing, deduplication, normalisation
3. **Embed** — Generate semantic embeddings (sentence-transformers)
4. **Cluster** — UMAP dimensionality reduction → HDBSCAN density clustering
5. **Summarise** — LLM-powered theme naming, quote extraction, and action ideas (via Groq)
6. **Deliver** — Append a weekly section to a running Google Doc and email a teaser to stakeholders

## Quick Start

```bash
# 1. Clone the repository
git clone <repo-url> && cd GrowwReview

# 2. Create a virtual environment
python -m venv .venv && .venv\Scripts\activate   # Windows
# python -m venv .venv && source .venv/bin/activate  # macOS/Linux

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Configure environment variables
copy .env.example .env
# Edit .env and add your GROQ_API_KEY

# 5. Review and customise config.yaml
# Update google_doc_id, stakeholder emails, etc.

# 6. Run the pipeline (dry run — no delivery side effects)
python src/cli.py --product groww --week auto --dry-run
```

## Project Structure

See [`docs/architecture.md`](docs/architecture.md) for the full architecture and directory layout.

## Documentation

- [Problem Statement](docs/problemStatement.md)
- [Architecture](docs/architecture.md)
- [Implementation Plan](docs/implementation-plan.md)
- [Edge Cases](docs/edge-cases.md)

## Configuration

All settings are in [`config.yaml`](config.yaml). Secrets (API keys) go in `.env`.

---

> **Note:** Full setup guide, CLI reference, and MCP server documentation will be added in Phase 6.
