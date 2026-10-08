#!/bin/sh
# Renders templates/social-card.html to site/social-card.png (1200x630) with headless Chrome.
set -e
cd "$(dirname "$0")/.."
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
"$CHROME" --headless=new --hide-scrollbars --force-device-scale-factor=1 --window-size=1200,630 \
  --virtual-time-budget=5000 --screenshot="$PWD/site/social-card.png" "file://$PWD/templates/social-card.html" 2>/dev/null
echo "Wrote site/social-card.png"
