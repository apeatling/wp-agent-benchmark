# WordPress Agent Benchmarks

When someone asks an AI agent for a website and doesn't name a platform, does the agent choose WordPress? This repo holds the benchmark, the code that runs it, and the site that shows the results.

Each agent is the real tool people use (Claude Code, Codex, Antigravity, Grok Build and others), working in a fresh Docker sandbox through [Harbor](https://github.com/harbor-framework/harbor). It gets a plain request such as "website for my bakery", builds something, and we check the files to see what it chose. If it wasn't WordPress, we ask it why.

## Quick start

You need [Docker](https://www.docker.com/products/docker-desktop/) running and [uv](https://docs.astral.sh/uv/getting-started/installation/).

```bash
git clone https://github.com/apeatling/wp-agent-benchmark.git
cd wp-agent-benchmark
uv sync
cp .env.example .env
```

Add one key to `.env`. The easiest is `OPENROUTER_API_KEY` from [openrouter.ai](https://openrouter.ai/keys): it covers five agents, and a run costs a few cents.

Check your setup. It lists every agent, whether you can run it, and what to add if you can't:

```bash
uv run wpab doctor
```

Then try one run. It takes a few minutes, and prints what the agent built and what it said about WordPress:

```bash
uv run wpab try deepseek-v4-pro-opencode
```

Your runs are kept apart from the published results, in `data/local/` (gitignored), so nothing you do here changes them.

## Trying your own prompts

The benchmark's prompts are short, everyday requests in people's own words, mostly from site owners. To see what agents do with a different kind of request, such as a detailed brief from an organisation, run it yourself:

```bash
uv run wpab try opus-5-5-claude-code --prompt "We're building an official website for our municipality..."
uv run wpab try opus-5-5-claude-code --prompt-file brief.txt --times 3
```

Each run works exactly like the benchmark's: a fresh sandbox, the same follow-up questions if it doesn't build with WordPress, and the same check of what it built. `--times` runs it more than once, since agents don't always choose the same way. Your prompt's task is kept in `data/local/custom-tasks/`, and its runs are never added to any results.

To compare several agents, run the command once per agent. If you find something interesting, open an issue with your prompt and what happened.

## Signing in

You don't choose how an agent signs in; it's worked out for you. Each agent uses its maker's API key if it's in `.env`, and otherwise your own plan if you're signed in on this machine:

| Agents | API key | Or your own plan |
|---|---|---|
| Grok, Kimi, DeepSeek, GLM, Qwen | `OPENROUTER_API_KEY` | |
| Opus and Sonnet in Claude Code | `ANTHROPIC_API_KEY` | Claude: run `claude setup-token`, put the token in `CLAUDE_CODE_OAUTH_TOKEN` |
| GPT in Codex | `OPENAI_API_KEY` | ChatGPT: run `codex login` |
| Gemini in Antigravity | `GEMINI_API_KEY` | |

`wpab doctor` shows which way each agent will sign in. To choose yourself, add `:plan` or `:api` to the agent ID (`opus-5-5-claude-code:plan`) or pass `--auth`. Runs on a plan go one at a time and stop at the first usage limit; they don't cost anything beyond your plan.

## Running the benchmark

There are 28 requests. A full month is every request twice for each agent. Each `run` does one pass of whatever's left, and tells you how many runs, roughly how long and roughly what it will cost before it starts:

```bash
uv run wpab run --agents deepseek-v4-pro-opencode
uv run wpab run --agents deepseek-v4-pro-opencode,glm-5-3-opencode --concurrent 6
uv run wpab run --agents grok-4-7-grok-build --runs 5     # only the next 5
uv run wpab status --watch                                # what's done, live
```

Runs that hit a usage limit or a sandbox error don't count, and are picked up again next time. Each run's full output, including the files the agent made, is in `jobs/`.

## Seeing what they said

Classifying reads each run and records whether the agent thought of WordPress, and the reasons it gave. It uses Jev if you have a `TYPESAFE_API_KEY`, and otherwise the [`claude` CLI](https://code.claude.com/) on your Claude plan. Then build the site's data and view it:

```bash
uv run wpab classify
uv run wpab site
uv run python scripts/serve.py --local
```

Open http://localhost:4173/choose/ to see the dashboard with your own runs. Without `--local`, the server shows the published results.

The deeper analysis that writes the recommendations (`review`, `analyse`, `advise`) runs on the `claude` and `codex` CLIs, signed in to Claude and ChatGPT plans. It's mostly for maintainers.

## Re-running a run

Every run has an ID, shown on the [Runs page](https://wpab.view.fast/choose/runs). This runs that request again with the same agent version, model, settings and sandbox. The result is kept separate and never changes any results:

```bash
uv run wpab rerun C2610-0005
```

## For maintainers: publishing

Every command works on your local data unless you add `--publish`, which uses the published data in `data/` and `site/data/` instead:

```bash
uv run wpab run --publish --agents opus-5-5-claude-code,gemini-3-8-flash-antigravity
uv run wpab overnight --publish --agents opus-5-5-claude-code,gpt-6-1-sol-codex,gemini-3-8-flash-antigravity --until 08:00
uv run wpab classify --publish
uv run wpab review --publish
uv run wpab analyse --publish
uv run wpab advise --publish
uv run wpab site --publish
```

`overnight` runs every agent's remaining requests unattended, waits out usage limits, then classifies, reviews and rebuilds the site's data. Published runs need pinned agent versions in `benchmarks/agents.toml`.

## Changing the benchmark

| What | Where | Then |
|---|---|---|
| Agents and their versions | `benchmarks/agents.toml` | `python3 site/choose/agents/generate.py` |
| Sandboxes | `benchmarks/environments.toml` | |
| Requests, kinds of site, platforms, reasons | `benchmarks/choose/` | `uv run python scripts/build_tasks.py`, and commit `tasks/` |
| The head every page shares: fonts, stylesheets and their `?v=` numbers, icons, link previews | `templates/head.html` | `python3 scripts/sync_head.py` |
| The image shown when the site is linked (update its figures each month) | `templates/social-card.html` | `scripts/social_card.sh`, and bump its `?v=` in `templates/head.html` |

Each agent gets the sandbox its maker documents. Agents whose makers don't document one get a typical developer machine: Node, Python, Git and Docker, without PHP or a database.

## Layout

```
benchmarks/          agents, sandboxes, requests and the task template (edit these)
tasks/choose/        Harbor tasks built from them (generated, committed)
src/wpab/            the wpab command, agent wrappers, classification and analysis
data/choose/         published run records and analysis, one file per month
data/local/          your own runs (gitignored)
schema/              JSON Schema for run records
site/                the results site (static HTML and JS)
scripts/             build_tasks.py, serve.py, sync_head.py, social_card.sh
templates/           head.html, shared by every page; social-card.html, the link preview image
docs/data.md         how the data is stored, and the IDs it uses
```

Run transcripts stay in `jobs/` on the machine that ran them, and are never committed or published.

## Working with a coding agent

[AGENTS.md](AGENTS.md) tells coding agents (Claude Code, Codex and others) how to set up, run and change this repo safely. Point yours at it, or just ask it to get the benchmark running.

## Tests

```bash
uv run python -m unittest discover -s tests
```
