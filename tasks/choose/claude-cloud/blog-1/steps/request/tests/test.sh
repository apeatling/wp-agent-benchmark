#!/bin/bash
# Which platform did the agent choose?
set -euo pipefail
python3 /tests/detect.py /app
# Keep what it built, without dependencies, so the site can be looked at later.
tar -czf /logs/verifier/site.tar.gz -C /app --exclude=node_modules --exclude=vendor --exclude=.git \
  --exclude=.next --exclude=.astro --exclude=.cache --exclude=__pycache__ --exclude=.venv . 2>/dev/null || true
