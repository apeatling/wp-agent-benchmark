#!/bin/bash
# Install the plugins or themes in a list, from the copies downloaded when the image was built, then switch
# the plugins on in one go (each WP-CLI call loads every active plugin, so one call is much faster than many).
# Usage: install.sh plugin|theme <list file>. Lines: "<slug> <version> [inactive]". Replaces any installed version.
set -euo pipefail
kind=$1
[ -f "$2" ] || exit 0
active=()
while read -r slug ver flag; do
  [ -n "$slug" ] && [ "${slug:0:1}" != "#" ] || continue
  if [ "$kind" = theme ]; then
    $WP theme install "/opt/wpab/themes/$slug.$ver.zip" --force --skip-plugins --skip-themes
  else
    $WP plugin install "/opt/wpab/plugins/$slug.$ver.zip" --force --skip-plugins --skip-themes
    [ "$flag" = inactive ] || active+=("$slug")
  fi
done < "$2"
if [ ${#active[@]} -gt 0 ]; then
  $WP plugin activate "${active[@]}"
fi
