# Notes for coding agents

This repo runs a benchmark: real AI coding agents get a plain website request in a Docker sandbox, and we record whether they choose WordPress and why. The README explains it for people; this file is what you need to work in it.

## Getting someone set up

When asked to "set this up" or "get it running", do this in order and stop at the first problem:

1. Check Docker is running (`docker info`) and `uv` is installed. If not, tell the person how to install them; don't try to install Docker yourself.
2. `uv sync`
3. If there's no `.env`, `cp .env.example .env`. Then ask the person to add a key; never ask them to paste a key into the chat, and never write a key into any file but `.env`. `OPENROUTER_API_KEY` is the easiest start.
4. `uv run wpab doctor`. It reports what's set up and which agents can run, and ends with the next command to run.
5. `uv run wpab try <agent id>` for one run. It takes a few minutes and costs cents with an OpenRouter agent.

Before starting anything that runs agents, say how many runs and roughly what they'll cost. `wpab run` prints this itself and asks before starting more than five runs; don't pass `-y` unless the person said to.

## Commands

| Command | What it does |
|---|---|
| `uv run wpab doctor` | What's set up, and which agents can run |
| `uv run wpab try [agent]` | One run, not added to any results |
| `uv run wpab run --agents a,b` | One pass of this month's remaining requests for those agents |
| `uv run wpab status` | What's done this month |
| `uv run wpab rerun <run id>` | One earlier run again, the same way, kept separate |
| `uv run wpab classify` then `uv run wpab site` | Read the runs, then rebuild the site's data |
| `uv run python scripts/serve.py --local` | View the site with local runs at http://localhost:4173/choose/ |
| `uv run python -m unittest discover -s tests` | Tests |

Agent IDs are in `benchmarks/agents.toml` and in `wpab doctor`'s output. Sign-in is automatic (an API key if set, otherwise the person's plan); see the README's "Signing in".

## Local and published data

Every command reads and writes local data (`data/local/`, `site/data-local/`, both gitignored) unless it's given `--publish`. Published data in `data/` and `site/data/` is what the public site shows. Never use `--publish`, or edit anything in `data/choose/runs/` or `site/data/`, unless a maintainer explicitly asks.

## Rules

- Never read, print or commit `.env`, and never put a key in a command line, log or file you write. Keys can show up in process lists and Docker output; don't print those either.
- Never commit or publish run transcripts (`jobs/`, `**/trajectory.json`). Agents sometimes print environment variables in them. Only derived fields go in run records.
- After editing anything in `benchmarks/choose/`, run `uv run python scripts/build_tasks.py` and commit the regenerated `tasks/` with it.
- After changing `benchmarks/agents.toml` or `site/choose/agents/_template.html`, run `python3 site/choose/agents/generate.py`.
- Don't commit to `trunk`; work on a branch and open a pull request. Don't skip commit hooks.
- The site is static HTML and JS in `site/`; there's no build step. When you change a CSS or JS file, bump its `?v=` number where it's included.

## Where things are

- `src/wpab/cli.py`: the `wpab` command. `agents.py`: wrappers around Harbor's agents. `records.py`: turns Harbor results into run records. `classify.py`, `review.py`, `deep.py`: reading the runs. `site.py`: builds the site's data.
- `benchmarks/`: definitions people edit. `tasks/`: generated from them.
- `docs/data.md`: the data layers, record schema and IDs.
