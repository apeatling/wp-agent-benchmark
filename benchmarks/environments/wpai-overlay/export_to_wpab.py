#!/usr/bin/env python3
"""Export WPAI experiment runs (`runs.jsonl`) to `apeatling/wp-agent-benchmark` choose-run v1.0 schema.

Conforms strictly to `schema/choose-run.schema.json` (`schema_version: "1.0"`,
`additionalProperties: false`).

Usage:
    python3 benchmarks/wpab-integration/export_to_wpab.py \
        --input benchmarks/results/runs.jsonl \
        --output benchmarks/results/wpab-choose-runs.jsonl \
        --batch 2026-11
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PLATFORM_GROUPS: dict[str, str] = {
    "WordPress": "wp",
    "Next.js": "code",
    "Astro": "code",
    "Plain HTML or React": "code",
    "Static site generator": "code",
    "Web framework": "code",
    "Other code": "code",
    "Headless CMS": "cms",
    "Hosted builder": "hosted",
    "ChatGPT site": "hosted",
    "Shopify": "shop",
    "Nothing built": "none",
}

VALID_STATUSES = {"completed", "infra_error", "limit_reached", "model_switched"}


def _batch_to_yymm(batch: str) -> str:
    if not re.match(r"^[0-9]{4}-[0-9]{2}$", batch):
        raise ValueError(f"batch must match YYYY-MM (got {batch!r})")
    return batch[2:4] + batch[5:7]


def _iso_utc(value: str | None) -> str:
    if value:
        return value
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def convert_record(
    run: dict[str, Any],
    seq: int,
    *,
    batch: str,
    suite_version: str = "0.4.0",
    default_model: str = "google/gemini-antigravity",
    default_harness: str = "antigravity-subagent",
    default_harness_version: str = "wpai-0.1.0",
    default_auth: str = "plan",
) -> dict[str, Any]:
    """Convert a single WPAI run dict into a choose-run.schema.json v1.0 compliant record."""
    yymm = _batch_to_yymm(batch)
    run_id = f"C{yymm}-L{seq:04d}"

    condition = str(run.get("condition", "A")).strip().upper()
    request_id = str(run.get("request_id") or run.get("prompt_id") or f"unknown-{seq}")
    kind = str(run.get("kind") or request_id.split("-")[0])
    control = bool(run.get("control", kind in {"app", "docs", "page"}))

    model = str(run.get("model") or default_model)
    harness = str(run.get("harness") or default_harness)
    harness_version = str(run.get("harness_version") or default_harness_version)
    agent = str(run.get("agent") or f"wpai-cond-{condition.lower()}-{harness}")
    auth = str(run.get("auth") or default_auth)
    if auth not in ("api", "plan"):
        auth = "plan"

    status = str(run.get("status") or "completed")
    if status not in VALID_STATUSES:
        status = "infra_error"

    platform = run.get("platform")
    platform_group = run.get("platform_group") or (
        PLATFORM_GROUPS.get(str(platform), "code") if platform is not None else None
    )
    built = run.get("built")
    if built is None and platform is not None:
        built = platform != "Nothing built"

    evidence = str(run.get("evidence") or "")
    file_count = int(run.get("file_count") or 0)
    detection = (
        {
            "evidence": evidence,
            "file_count": file_count,
            "check_platform": None,
            "check_confidence": None,
            "agrees": None,
        }
        if platform is not None
        else None
    )

    env_map = {
        "A": "wpai-baseline",
        "B": "wpai-discovery-registry",
        "C": "wpai-discovery-registry-runtime",
    }

    record: dict[str, Any] = {
        "schema_version": "1.0",
        "run_id": run_id,
        "benchmark": "choose",
        "batch": batch,
        "suite_version": str(run.get("suite_version") or suite_version),
        "request_id": request_id,
        "kind": kind,
        "control": control,
        "agent": agent,
        "model": model,
        "harness": harness,
        "harness_version": harness_version,
        "effort": run.get("effort"),
        "environment": str(run.get("environment") or env_map.get(condition, f"wpai-{condition.lower()}")),
        "auth": auth,
        "status": status,
        "status_detail": run.get("status_detail"),
        "started_at": _iso_utc(run.get("started_at")),
        "finished_at": run.get("finished_at"),
        "duration_s": float(run["duration_s"]) if run.get("duration_s") is not None else None,
        "input_tokens": int(run["input_tokens"]) if run.get("input_tokens") is not None else None,
        "cached_tokens": int(run["cached_tokens"]) if run.get("cached_tokens") is not None else None,
        "output_tokens": int(run["output_tokens"]) if run.get("output_tokens") is not None else None,
        "cost_usd": float(run["cost_usd"]) if (auth == "api" and run.get("cost_usd") is not None) else None,
        "models_used": list(run.get("models_used") or [model]),
        "stalled": bool(run["stalled"]) if run.get("stalled") is not None else False,
        "nudged": bool(run["nudged"]) if run.get("nudged") is not None else False,
        "built": bool(built) if built is not None else None,
        "platform": platform,
        "platform_group": platform_group,
        "detection": detection,
        "considered_wordpress": None if platform == "WordPress" else run.get("considered_wordpress"),
        "offered_wordpress": None,
        "recommended_wordpress": None,
        "reason_deciding": run.get("reason_deciding"),
        "reasons_deciding": list(run.get("reasons_deciding") or []),
        "reason_asked": run.get("reason_asked"),
        "reasons_asked": list(run.get("reasons_asked") or []),
        "considered_answer": run.get("considered_answer"),
        "named_wordpress_unprompted": run.get("named_wordpress_unprompted"),
        "why_not_answer": run.get("why_not_answer"),
        "patterns": list(run.get("patterns") or []),
        "classifier": None,
        "job": str(run.get("job") or f"wpai-{batch}-cond-{condition.lower()}"),
        "trial": str(run.get("trial") or run.get("run_id") or f"{condition.lower()}-{request_id}"),
        "harbor_version": run.get("harbor_version"),
        "runner_commit": run.get("runner_commit"),
    }
    return record


def export_jsonl(input_path: Path, output_path: Path, *, batch: str) -> int:
    if not input_path.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("", encoding="utf-8")
        return 0

    lines = [ln.strip() for ln in input_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    converted = [convert_record(json.loads(ln), idx, batch=batch) for idx, ln in enumerate(lines, start=1)]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "\n".join(json.dumps(rec, separators=(",", ":")) for rec in converted) + ("\n" if converted else ""),
        encoding="utf-8",
    )
    return len(converted)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export WPAI runs.jsonl to wp-agent-benchmark choose-run v1.0 JSONL.")
    parser.add_argument("--input", type=Path, default=Path("benchmarks/results/runs.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("benchmarks/results/wpab-choose-runs.jsonl"))
    parser.add_argument("--batch", type=str, default=datetime.now(timezone.utc).strftime("%Y-%m"))
    args = parser.parse_args(argv)

    count = export_jsonl(args.input, args.output, batch=args.batch)
    print(f"Exported {count} record(s) to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
