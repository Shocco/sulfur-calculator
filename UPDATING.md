# Updating game data

How to refresh the calculator's weapons, oils, scrolls, attachments, calibers and images from the [SULFUR Wiki](https://sulfur.wiki.gg) and publish the result to GitHub Pages.

This file lives in the repo root (not `docs/`) on purpose: `npm run build` empties `docs/`.

## TL;DR

From the repo root:

```bash
scripts/update_from_wiki.sh
```

Then review `git status` / `git diff`, commit, and push. The script never commits or pushes.

## Prerequisites

- Linux/WSL with `python3` (with `venv`), `perl`, `node` + `npm`, and `git`.
- `npm install` already run.
- The extractor venv `.venv/` exists with test dependencies (used for `update_all`, `sync_images`, `diff_data`, `pytest`):
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt   # the script does this for you if .venv is missing
  ```
- Network access to `https://sulfur.wiki.gg`.
- Disk space for the dumps (the image dump and full history dump are the largest).

The script creates a second, separate venv `.venv-wikiteam/` (gitignored) for the wiki dumper. Do not mix it with `.venv/`.

## The one command

```bash
scripts/update_from_wiki.sh [options]
```

| Option | Meaning | Default |
|---|---|---|
| `--date YYYYMMDD` | Label for this dump set (used in folder names) | today |
| `--dump-dir DIR` | Where dumps are stored | `$SULFUR_DUMP_DIR`, else `/mnt/z/Claude/sulfurdump` if it exists, else `./wikidumps/` (gitignored) |
| `--delay SECONDS` | Delay between wiki requests. The wiki returns HTTP 429 if requests are faster | `2.5` |
| `--skip-download` | Reuse dumps already in the dump dir for that date | off |
| `--no-history` | Skip the full-history dump | off |
| `--no-images` | Skip the image dump and the image sync | off |
| `--no-build` | Stop before `npm run build` | off |
| `-h`, `--help` | Show usage | |

Examples:

```bash
# Normal update, everything
scripts/update_from_wiki.sh

# Faster/lighter: no history archive, no images, don't build
scripts/update_from_wiki.sh --no-history --no-images --no-build

# Re-run processing on dumps you already downloaded on 2026-11-05
scripts/update_from_wiki.sh --date 20261105 --skip-download

# Wiki is rate-limiting you
scripts/update_from_wiki.sh --delay 5
```

## What the script does

1. **Dumper venv.** Creates/uses `.venv-wikiteam/` with `wikiteam3==4.4.8` (provides `wikiteam3dumpgenerator`).
2. **Three separate dumps**, run one after another (combining them in one run has been unreliable). All use `--api https://sulfur.wiki.gg/api.php --index https://sulfur.wiki.gg/index.php`:
   | Dump | wikiteam3 flags | Folder | Used for |
   |---|---|---|---|
   | Current pages | `--xml --curonly --xmlapiexport` | `sulfur.wiki.gg-<date>-current/` | **The input to the extractors** |
   | Full history | `--xml --xmlrevisions` | `sulfur.wiki.gg-<date>-history/` | Archive only |
   | Images | `--images --bypass-cdn-image-compression` | `sulfur.wiki.gg-<date>-images/images/` | Image sync |

   `--xmlapiexport` / `--xmlrevisions` fetch pages through `api.php`. The default `index.php` `Special:Export` mode gets rate-limited by wiki.gg (HTTP 429) until the dump dies; the API route has not been. It is still one page per request, so with ~3,150 titles (about half are `File:` pages) the current-pages dump takes **~3 hours** at the default delay. Plan for a long run (the whole thing is resumable).

   A dump folder containing `all_dumped.mark` is considered finished and skipped. An incomplete folder is resumed with `--resume`. Note: wikiteam3 names the files inside by the **UTC** date (e.g. `sulfur.wiki.gg-20261106-current.xml` inside the `-20261105-current/` folder); the script finds them by pattern.
3. **Fix unescaped `&`** in the current-pages XML with a perl one-liner, writing a `*-fixed.xml` copy (the original is untouched).
4. **Back up** `public/data/` to `data.bak/<timestamp>/` (gitignored).
5. **Extract and merge:** `python3 -m scripts.update_all <fixed.xml> --output-dir public/data --old-dir docs/data`. Merge rule: new items are kept, old-only items are preserved, zeroed-out stats on matched items are filled from the old values. Exceptions: old-only items renamed on the wiki (redirect page) or moved to another attachment slot are dropped, with a log line for each.
6. **Sync images:** `python3 -m scripts.sync_images <images dump>/images`. Copies missing or changed images into `public/images/{weapons,oils,scrolls,attachments}` and prints images that are still missing.
7. **Diff against the live site:** `python3 -m scripts.diff_data docs/data public/data`. This must run before the build, because the build copies `public/` into `docs/`, after which both would be identical.
8. **Tests:** `python3 -m pytest tests/ -q`.
9. **Build:** `npm run build` (skipped with `--no-build`). Output goes to `docs/`.
10. **Next steps.** Prints what to do next. It never commits or pushes.

## After the script finishes

1. Read the diff output (step 7). Check that:
   - ADDED items are genuinely new game content.
   - REMOVED items are expected. The merge normally preserves old-only items, so removals are unusual.
   - CHANGED stats look plausible (no unexpected zeros, no huge swings).
2. Check the "missing images" list from the image sync. Missing images mean the wiki has no file under the expected name (see Image naming below).
3. Optionally try it locally: `npm run dev` and open http://localhost:5173.
4. Review and commit:
   ```bash
   git status
   git diff --stat
   git add public/data public/images docs
   git commit -m "data: update from wiki dump YYYYMMDD"
   git push
   ```
5. GitHub Pages redeploys from `docs/` on push. Data file URLs are cache-busted with the build timestamp, so no hard refresh is needed.
6. A minute or two after pushing, confirm the deploy:
   ```bash
   scripts/check_live.sh
   ```
   It compares every live data file with `docs/data/` and requests every referenced image from the live site. It exits non-zero if anything differs or 404s.

## Manual equivalent (no script)

Run from the repo root. Replace `20261105` with your date and adjust `DUMP` to your dump directory.

```bash
DATE=20261105
DUMP=./wikidumps            # or /mnt/z/Claude/sulfurdump, or $SULFUR_DUMP_DIR
mkdir -p "$DUMP"
```

### 1. Dumper venv

```bash
python3 -m venv .venv-wikiteam
.venv-wikiteam/bin/pip install wikiteam3==4.4.8
```

### 2. Dumps

Run these one at a time, not in parallel and not combined. Each is resumable: re-run the same command with `--resume` added.

```bash
DG=".venv-wikiteam/bin/wikiteam3dumpgenerator https://sulfur.wiki.gg \
  --api https://sulfur.wiki.gg/api.php --index https://sulfur.wiki.gg/index.php --delay 2.5"

# (a) current pages -- the one the extractors use
$DG --xml --curonly --xmlapiexport --path "$DUMP/sulfur.wiki.gg-$DATE-current"

# (b) full history -- archive only
$DG --xml --xmlrevisions --path "$DUMP/sulfur.wiki.gg-$DATE-history"

# (c) images
$DG --images --bypass-cdn-image-compression --path "$DUMP/sulfur.wiki.gg-$DATE-images"
```

Notes:
- `--path` must be a new folder per dump so the three don't overwrite each other.
- A finished dump contains `all_dumped.mark`. If it is missing, the dump is incomplete; rerun the same command with `--resume` added.
- Find the XML to use (the single `.xml` inside the current-pages dump folder):
  ```bash
  find "$DUMP/sulfur.wiki.gg-$DATE-current" -name '*.xml'
  ```

### 3. Fix unescaped `&`

```bash
XML=<path to the current-pages .xml found above>
FIXED="${XML%.xml}-fixed.xml"
cp "$XML" "$FIXED"
perl -i -pe 's/&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;|[a-zA-Z]\w*;)/&amp;/g' "$FIXED"
```

### 4. Back up current data

```bash
mkdir -p data.bak
cp -r public/data "data.bak/$(date +%Y%m%d-%H%M%S)"
```

### 5. Extract and merge

```bash
source .venv/bin/activate
python3 -m scripts.update_all "$FIXED" --output-dir public/data --old-dir docs/data
```

### 6. Sync images

```bash
python3 -m scripts.sync_images "$DUMP/sulfur.wiki.gg-$DATE-images/images"
```

### 7. Diff against the live site (before building)

```bash
python3 -m scripts.diff_data docs/data public/data
```

### 8. Tests

```bash
python3 -m pytest tests/ -q
```

### 9. Build

```bash
npm run build
```

### 10. Review and publish

```bash
git status
git diff --stat
git add public/data public/images docs
git commit -m "data: update from wiki dump $DATE"
git push
```

## Parser notes

- **Multipliers** (`×15`, `&times;15`, `+30x`) — the wiki writes Bullet Drop this way. They are stored as Flat `N` (modType 100): weapons have no base Bullet Drop and the calculator starts such stats at 0, so a multiplier would always show 0. Flat N displays the same number the site showed when the wiki wrote `+15`.
- **HTML comments** (`<!-- | Key = ... -->`) inside infoboxes are stripped before parsing.
- If extraction crashes with `could not convert string to float: '...'`, the wiki has a new value format: add a case to `parse_modifier_value` in `scripts/wiki_parser.py` with a test in `tests/test_wiki_parser.py`, then rerun with `--skip-download`.

## Image naming

The wiki stores file names with underscores. The app expects:

| Category | Folder | Name pattern | Example |
|---|---|---|---|
| Weapons | `public/images/weapons/` | the weapon's `image` field (underscores) | `Ploika_Compact.png` |
| Oils | `public/images/oils/` | `<oil name>.png` (spaces) | `Action Oil.png` |
| Scrolls | `public/images/scrolls/` | `<scroll name>.png` (spaces) | `Scroll of Charm.png` |
| Attachments | `public/images/attachments/` | basename of the attachment `image` field (underscores) | `A12C_Muzzle_Brake.png` |

`sync_images` looks each target up in the dump by its underscored name, case-insensitive on the first letter, and copies it if it is missing or its contents differ. Anything it cannot find in the dump and that is not already in `public/images/` is reported as `missing`.

## Troubleshooting

**"XML export on this wiki is broken, quitting"**
wikiteam3 auto-detects the index URL as `https://sulfur.wiki.gg/SULFUR_Wiki`, which breaks `Special:Export`. Always pass `--index https://sulfur.wiki.gg/index.php` explicitly. The script does this; do the same when running manually.

**HTTP 429 (Too Many Requests)**
The wiki rate-limits fast clients. Make sure the page dumps use the API modes (`--xmlapiexport` / `--xmlrevisions`, as the script does) — per-page `Special:Export` gets 429'd even at 2.5 s and fails with `too many 429 error responses`. If it still happens, raise the delay: `scripts/update_from_wiki.sh --delay 5` (default is 2.5 s), then rerun to resume.

**`RuntimeError: Found cf-polished header in response`** (image dump)
wiki.gg serves images through Cloudflare Polish, which recompresses them. wikiteam3 refuses those unless you pass `--bypass-cdn-image-compression` (the script does). Rerun to resume — the finished page dumps are skipped.

**An image 404s on the live site but works locally**
GitHub Pages runs Jekyll by default, and Jekyll skips files whose names start with `.` or `_` (e.g. `.357_Balthazar.png`). `public/.nojekyll` turns that off; the build copies it into `docs/`. Don't delete it.

**A dump was interrupted**
Re-run the same command with the same `--date`. Finished dumps (`all_dumped.mark` present) are skipped and unfinished ones are resumed with `--resume`. To reuse everything that is already downloaded and only redo processing, add `--skip-download`.

**`docs/` files disappeared after the build**
`npm run build` empties `docs/` (Vite `emptyOutDir`). Do not keep untracked files there. Plans and notes live in `plans/`. Tracked files that vanish can be restored with `git checkout -- <path>`.

**An item vanished or a stat became 0**
Many wiki pages are stubs without infoboxes, which is why extraction merges with `docs/data` (`--old-dir`). Look at the `diff_data` output: the item should appear under REMOVED or CHANGED. Renamed items are handled automatically: if an old-only item's wiki page is now a `#REDIRECT` to a name that was extracted, it is dropped and logged as `dropped 'X' (renamed on wiki -> 'Y')`. An old-only attachment that is now extracted into a different slot file is dropped too (`now extracted into another attachment file`). Review those lines in the output.

**Missing images after sync**
The wiki may not have a file under the expected name, or the image dump is incomplete. Check the `missing:` lines, confirm the file exists on the wiki (File: namespace), and re-run the image dump if needed. Remember oils and scrolls are stored with spaces, weapons and attachments with underscores.

**Tests fail after extraction**
Run `python3 -m pytest tests/ -x -q` inside `.venv`. Failures usually mean the wiki template format changed; see "Wiki Template Formats" in `CLAUDE.md`. Fix the extractor before publishing, or roll back (below).

**Roll back the data**
```bash
ls data.bak/                                  # pick a timestamp
rm -rf public/data
cp -r data.bak/<timestamp> public/data
```
If you already built, rebuild with `npm run build`. If you have not committed, `git checkout -- docs public` also restores the last committed state of tracked files (this discards uncommitted changes there, including image updates).

## Related files

- `scripts/update_from_wiki.sh` -- the one-command updater
- `scripts/update_all.py` -- runs all extractors and the merge
- `scripts/sync_images.py` -- image sync
- `scripts/diff_data.py` -- old vs new data diff
- `CLAUDE.md` -- architecture, wiki template formats, merge strategy
