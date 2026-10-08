#!/bin/bash
# The follow-up question doesn't change the result: the platform is taken from the first step's
# verifier. This only records that the question was asked.
set -euo pipefail
mkdir -p /logs/verifier
echo '{"asked": 1}' > /logs/verifier/reward.json
