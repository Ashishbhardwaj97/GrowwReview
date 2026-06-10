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

## Setup Guide & Configuration Reference

### Environment Variables (`.env`)

See `.env.example` for the required keys.
- `GROQ_API_KEY`: Required for LLM summarisation.
- `MCP_SERVER_URL`: Optional. URL to your Google MCP server (overrides `config.yaml`).

### `config.yaml` Reference

- `delivery.google_doc_id`: The ID of the target Google Doc where reports will be appended.
- `delivery.stakeholders`: List of email addresses to receive the draft email.
- `mcp_server.url`: The Server-Sent Events (SSE) endpoint of the MCP server (e.g., `https://web-production-131a3.up.railway.app/sse`).
- `delivery.draft_only`: If `true`, the email will only be created as a draft. `false` sends the email.

### Remote MCP Server

This system relies on a remote **Google MCP Server** to perform actions in Google Docs and Gmail securely.
1. The server should expose an SSE endpoint (e.g. `/sse`) and accept JSON-RPC tool calls.
2. The current production endpoint is `https://web-production-131a3.up.railway.app/sse`. Ensure this server is running and authenticated.

## CLI Usage

```bash
# Full dry-run (does not connect to MCP, just logs what would happen)
python src/cli.py --product groww --week auto --dry-run

# Draft-only mode (appends to Docs, creates Gmail draft but does not send)
python src/cli.py --product groww --week auto --draft-only

# Force a re-run (ignores the run log and processes again)
python src/cli.py --product groww --week auto --force
```

## Scheduling

This pipeline is designed to run periodically (e.g., weekly on Mondays at 09:00 IST).
A GitHub Actions workflow `.github/workflows/weekly-pulse.yml` is provided for automatic execution. 

To use the GitHub Actions scheduler:
1. Go to your GitHub repository settings -> **Secrets and variables** -> **Actions**.
2. Add a new repository secret named `GROQ_API_KEY`.
3. Optionally add `MCP_SERVER_URL` if you want to override the default URL in `config.yaml`.
4. The workflow will automatically trigger based on the cron schedule (`30 3 * * 1` which is Monday 09:00 IST / 03:30 UTC).

## Project Structure

See [`docs/architecture.md`](docs/architecture.md) for the full architecture and directory layout.

## Documentation

- [Problem Statement](docs/problemStatement.md)
- [Architecture](docs/architecture.md)
- [Implementation Plan](docs/implementation-plan.md)
- [Edge Cases](docs/edge-cases.md)
