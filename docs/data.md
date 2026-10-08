# Data

How benchmark data is stored, from definitions to what the site shows. Every layer is plain, standard files, so the same data can live in this repo, on Hugging Face, or anywhere else.

## Layers

| Layer | Format | Where | Edited by |
|---|---|---|---|
| Definitions: agents, requests, kinds of site, platforms, reasons, patterns | TOML | `benchmarks/` | People, reviewed in pull requests |
| Raw runs: Harbor results, transcripts, files | Harbor job folders; transcripts in Harbor's trajectory format (ATIF) and each tool's own logs | `jobs/` locally, never committed | Nobody: written once by Harbor |
| Run records: one per run | JSON Lines, one object per line, checked against a JSON Schema | `data/<benchmark>/runs/<batch>.jsonl` | `wpab export` and `wpab classify` only |
| Site data | One JSON file per benchmark | `site/data/` | `wpab site` only |

Everything above is the published data. Runs made without `--publish` go through the same layers in `data/local/` and `site/data-local/` instead, which are gitignored.

Raw runs are the evidence. Run records are the dataset: everything on the site is computed from them and the definitions, so anyone can rebuild the site's numbers from the published records.

## Run records

- Schema: [`schema/choose-run.schema.json`](../schema/choose-run.schema.json). Every record carries `schema_version`; a breaking change bumps the major version.
- One file per monthly batch, named by batch: `2026-10.jsonl`. Records are appended as runs finish and are never edited by hand. If classification is redone, the whole file is rewritten by the tool.
- Each record names the exact versions behind it: suite, agent harness, model, Harbor, runner commit and classifier model.
- Every run is kept, including ones that didn't count (`status` other than `completed`), so excluded runs are visible rather than silently dropped.
- For Hugging Face, the JSON Lines files convert directly to Parquet, one split per batch plus `latest`.

## IDs

- **Agent:** model then harness, as a slug: `opus-5-5-claude-code`. The same ID is used in definitions, run records, the site and its URLs.
- **Request:** kind and number: `business-2`.
- **Run:** benchmark letter, batch and sequence: `C2610-0001`. Stable once published. Local runs have an L before the sequence: `C2610-L0001`.
- **Batch:** the month the runs belong to: `2026-10`.

## What's public

All definitions, run records and transcripts are public. API keys and plan logins never appear in any of them; a run records only how it was signed in (`api` or `plan`).
