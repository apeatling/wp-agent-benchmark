#!/bin/bash
# Check the finished site from outside. See checks.py.
set -euo pipefail
python3 /tests/checks.py
