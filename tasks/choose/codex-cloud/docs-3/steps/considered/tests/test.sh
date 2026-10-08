#!/bin/bash
# A neutral question, asked before WordPress is named, so whether it comes up is the agent's own doing. It
# doesn't change the result: the platform is taken from the first step's verifier.
set -euo pipefail
mkdir -p /logs/verifier
echo '{"asked": 1}' > /logs/verifier/reward.json
