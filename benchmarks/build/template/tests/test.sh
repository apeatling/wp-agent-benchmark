#!/bin/bash
# The checks' results, copied in. They ran in the task's checker, beside the site, after Harbor stopped the agent's
# sandbox (task.toml, [[verifier.collect]]), so nothing the agent left running could see the checks' login or change
# what they found. See environment/checker.
set -euo pipefail
cp /var/log/wpab/checks/checks.json /var/log/wpab/checks/reward.json /logs/verifier/
cat /var/log/wpab/checks/checks.txt
