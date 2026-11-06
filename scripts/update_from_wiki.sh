#!/usr/bin/env bash
# Update all game data (and images) from sulfur.wiki.gg in one go.
# See UPDATING.md for the full guide. Never commits or pushes.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WIKI="https://sulfur.wiki.gg"
WIKITEAM_VERSION="4.4.8"

DATE=""
DELAY="2.5"
DO_DOWNLOAD=1; DO_HISTORY=1; DO_IMAGES=1; DO_BUILD=1
if [[ -n "${SULFUR_DUMP_DIR:-}" ]]; then DUMP_DIR="$SULFUR_DUMP_DIR"
elif [[ -d /mnt/z/Claude/sulfurdump ]]; then DUMP_DIR=/mnt/z/Claude/sulfurdump
else DUMP_DIR="$REPO/wikidumps"; fi

usage() {
  sed -n '2,3p' "$0"
  cat <<EOF

Usage: scripts/update_from_wiki.sh [options]
  --date YYYYMMDD   dump label (default: today; with --skip-download, the newest
                    existing dump). Pass the original date to resume a dump
                    that was started on an earlier day.
  --dump-dir DIR    where dumps are stored (default: $DUMP_DIR)
  --delay SECONDS   delay between wiki requests (default: $DELAY; raise if you see HTTP 429)
  --skip-download   reuse dumps already in the dump dir for --date
  --no-history      skip the full-history dump (archive only)
  --no-images       skip the image dump and image sync
  --no-build        stop before npm run build
  -h, --help        show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --date) DATE="$2"; shift 2 ;;
    --dump-dir) DUMP_DIR="$2"; shift 2 ;;
    --delay) DELAY="$2"; shift 2 ;;
    --skip-download) DO_DOWNLOAD=0; shift ;;
    --no-history) DO_HISTORY=0; shift ;;
    --no-images) DO_IMAGES=0; shift ;;
    --no-build) DO_BUILD=0; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1"; usage; exit 1 ;;
  esac
done

step() { echo; echo "==> $*"; }
if [[ -z "$DATE" && $DO_DOWNLOAD -eq 0 ]]; then
  latest="$(ls -d "$DUMP_DIR"/sulfur.wiki.gg-*-current 2>/dev/null | sort | tail -1 || true)"
  [[ -n "$latest" ]] || { echo "ERROR: no sulfur.wiki.gg-*-current dump in $DUMP_DIR"; exit 1; }
  DATE="$(basename "$latest" | sed -E 's/^sulfur\.wiki\.gg-([0-9]{8})-current$/\1/')"
  echo "Using newest dump: $DATE"
fi
DATE="${DATE:-$(date +%Y%m%d)}"
PREFIX="$DUMP_DIR/sulfur.wiki.gg-$DATE"
mkdir -p "$DUMP_DIR"
cd "$REPO"

# --- 1. Tool venvs -----------------------------------------------------------
WT="$REPO/.venv-wikiteam"
if [[ $DO_DOWNLOAD -eq 1 && ! -x "$WT/bin/wikiteam3dumpgenerator" ]]; then
  step "Creating .venv-wikiteam with wikiteam3==$WIKITEAM_VERSION"
  python3 -m venv "$WT"
  "$WT/bin/pip" install -q "wikiteam3==$WIKITEAM_VERSION"
fi
if [[ ! -x "$REPO/.venv/bin/python3" ]]; then
  step "Creating .venv for the extractors"
  python3 -m venv "$REPO/.venv"
  "$REPO/.venv/bin/pip" install -q -r "$REPO/requirements.txt"
fi
PY="$REPO/.venv/bin/python3"

# --- 2. Three separate dumps, one after another ------------------------------
dump() {  # dump <kind> <wikiteam flags...>
  local kind="$1"; shift
  local path="$PREFIX-$kind"
  if [[ -f "$path/all_dumped.mark" ]]; then
    echo "    $kind dump already complete: $path"; return
  fi
  local resume=()
  [[ -f "$path/config.json" ]] && resume=(--resume)
  step "Dumping $kind -> $path ${resume[*]:-}"
  "$WT/bin/wikiteam3dumpgenerator" "$WIKI" \
    --api "$WIKI/api.php" --index "$WIKI/index.php" \
    --delay "$DELAY" --path "$path" "${resume[@]}" "$@"
  [[ -f "$path/all_dumped.mark" ]] || { echo "ERROR: $kind dump did not finish (rerun to resume)"; exit 1; }
}
if [[ $DO_DOWNLOAD -eq 1 ]]; then
  # Export through api.php: index.php Special:Export gets rate-limited
  # (HTTP 429) by wiki.gg until the dump dies; the API route does not.
  dump current --xml --curonly --xmlapiexport
  if [[ $DO_HISTORY -eq 1 ]]; then dump history --xml --xmlrevisions; fi
  # wiki.gg's Cloudflare "Polish" recompresses images; without this flag
  # wikiteam3 aborts on the first image ("Found cf-polished header").
  if [[ $DO_IMAGES -eq 1 ]]; then dump images --images --bypass-cdn-image-compression; fi
fi

# --- 3. Fix unescaped & in the current-pages XML -----------------------------
XML="$(ls "$PREFIX-current"/*-current.xml 2>/dev/null | grep -v -- '-fixed.xml' | head -1 || true)"
[[ -n "$XML" ]] || { echo "ERROR: no *-current.xml in $PREFIX-current"; exit 1; }
FIXED="${XML%.xml}-fixed.xml"
step "Escaping stray & -> $FIXED"
perl -pe 's/&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;|[a-zA-Z]\w*;)/&amp;/g' "$XML" > "$FIXED"

# --- 4. Back up current data -------------------------------------------------
BAK="$REPO/data.bak/$(date +%Y%m%d-%H%M%S)"
step "Backing up public/data -> $BAK"
mkdir -p "$BAK" && cp -r "$REPO/public/data/." "$BAK/"

# --- 5. Extract + merge ------------------------------------------------------
step "Extracting data"
"$PY" -m scripts.update_all "$FIXED" --output-dir public/data --old-dir docs/data

# --- 6. Images ---------------------------------------------------------------
if [[ $DO_IMAGES -eq 1 ]]; then
  if [[ -d "$PREFIX-images/images" ]]; then
    step "Syncing images"
    "$PY" -m scripts.sync_images "$PREFIX-images/images" --data-dir public/data --images-dir public/images
  else
    echo "    No image dump at $PREFIX-images/images — skipping image sync"
  fi
fi

# --- 7. Diff against live data (before build overwrites docs/data) -----------
step "Changes vs. live site data (docs/data -> public/data)"
"$PY" -m scripts.diff_data docs/data public/data || true

# --- 8. Tests ----------------------------------------------------------------
step "Running tests"
"$PY" -m pytest tests/ -q

# --- 9. Build ----------------------------------------------------------------
if [[ $DO_BUILD -eq 1 ]]; then
  step "Building production bundle (docs/)"
  [[ -d node_modules ]] || npm install
  npm run build
fi

step "Done. Nothing was committed. Next:"
cat <<EOF
    git status                      # review changed data/images/bundle
    git add public docs && git commit -m "data: update from wiki dump $DATE"
    git push                        # deploys to GitHub Pages
    Roll back data: cp -r "$BAK/." public/data/
EOF
