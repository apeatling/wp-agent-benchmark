#!/bin/sh
# Starts Docker inside the sandbox, as it would be running on a machine that has it, then runs the command.
if command -v dockerd >/dev/null 2>&1; then
  dockerd > /var/log/dockerd.log 2>&1 &
fi
exec "$@"
