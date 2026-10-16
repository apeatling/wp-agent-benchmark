#!/bin/sh
# For credentials made while the site is seeded: put the value the seed wrote into the config, then start.
set -e
CONF=/etc/nginx/conf.d/default.conf
if grep -q __FROM_SEED__ "$CONF"; then
  VALUE=$(cat /run/wpab-connector/value)
  [ -n "$VALUE" ] || { echo "No connector credential from the seed" >&2; exit 1; }
  sed -i "s|__FROM_SEED__|$VALUE|" "$CONF"
fi
