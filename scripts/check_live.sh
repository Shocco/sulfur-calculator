#!/usr/bin/env bash
# Verify the deployed GitHub Pages site matches docs/ in this repo:
# every data file is byte-identical and every referenced image loads.
# Usage: scripts/check_live.sh [SITE_URL]
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SITE="${1:-https://shocco.github.io/sulfur-calculator}"
cd "$REPO"
fail=0
bust="v=$(date +%s)"

echo "Site: $SITE"
echo "== Data files (live vs docs/data)"
for f in docs/data/*.json; do
  n="$(basename "$f")"
  live="$(curl -sf "$SITE/data/$n?$bust" | sha1sum | cut -d' ' -f1)"
  local_="$(sha1sum < "$f" | cut -d' ' -f1)"
  if [[ "$live" == "$local_" ]]; then echo "  ok      $n"; else echo "  DIFFER  $n"; fail=1; fi
done

echo "== Images referenced by docs/data"
urls="$(.venv/bin/python3 - "$SITE" <<'EOF'
import sys, urllib.parse
from scripts.sync_images import wanted_images
for cat, name in wanted_images('docs/data'):
    print(f"{sys.argv[1]}/images/{cat}/{urllib.parse.quote(name)}")
EOF
)"
total="$(wc -l <<< "$urls")"
bad="$(xargs -P 8 -n 1 curl -s -o /dev/null -w '%{http_code} %{url_effective}\n' <<< "$urls" | grep -v '^200 ' || true)"
if [[ -z "$bad" ]]; then echo "  ok      $total/$total images load"
else echo "$bad" | sed 's/^/  BROKEN  /'; fail=1; fi

if [[ $fail -eq 0 ]]; then echo "Live site matches the repo."; else echo "Live site does NOT match (deploy pending, or see above)."; fi
exit $fail
