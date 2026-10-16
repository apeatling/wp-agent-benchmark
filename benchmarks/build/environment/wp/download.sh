#!/bin/bash
# Download the plugins and themes in the site's lists from wordpress.org, at their pinned versions, when the
# image is built. A version that can't be downloaded stops the build.
set -euo pipefail
mkdir -p /opt/wpab/plugins /opt/wpab/themes
for kind in plugin theme; do
  for list in /opt/wpab/seed/${kind}s.txt /opt/wpab/seed/request-${kind}s.txt /opt/wpab/seed/setup-${kind}s.txt; do
    [ -f "$list" ] || continue
    while read -r slug ver _; do
      [ -n "$slug" ] && [ "${slug:0:1}" != "#" ] || continue
      curl -fsSL -o "/opt/wpab/${kind}s/$slug.$ver.zip" "https://downloads.wordpress.org/$kind/$slug.$ver.zip" \
        || { echo "No download for $kind $slug $ver"; exit 1; }
    done < "$list"
  done
done
