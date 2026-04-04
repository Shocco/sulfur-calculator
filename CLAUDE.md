# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SULFUR Weapon Calculator — a React web app that calculates weapon stats with oils, scrolls, attachments, and caliber conversions for the game SULFUR. Data is extracted from MediaWiki XML dumps via Python scripts.

## Commands

```bash
# Frontend
npm install          # install deps
npm run dev          # dev server at http://localhost:5173
npm run build        # production build to docs/ (served via GitHub Pages)

# Python extraction pipeline (requires venv)
source .venv/bin/activate
python3 -m pytest tests/ -x -q                    # run all tests (214 tests)
python3 -m pytest tests/test_extract_weapons.py -q # run single test file
python3 -m pytest tests/ -k "test_muzzle_slot"     # run by test name

# Full extraction from wiki dump (with merge from old curated data)
python3 -m scripts.update_all <dump.xml> --output-dir public/data --old-dir docs/data

# Compare old vs new data
python3 -m scripts.diff_data docs/data public/data
```

Wiki dumps with unescaped `&` need pre-processing:
```bash
perl -i -pe 's/&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;|[a-zA-Z]\w*;)/&amp;/g' <dump.xml>
```

## Architecture

### Frontend (React + Vite + Tailwind)

- `src/App.jsx` — main state manager, loads all JSON data from `public/data/`, coordinates selection state
- `src/utils/calculator.js` — core stat calculation engine with modifier types: Flat(100), PercentAdd(200), PercentMult(300). ConvertWpn scrolls apply before oils.
- `src/components/` — WeaponSelector, EnchantmentSelector, AttachmentSelector, StatsDisplay, SavedConfigs
- Production builds output to `docs/` (GitHub Pages). Base path switches between `/` (dev) and `/sulfur-calculator/` (prod) via `vite.config.js`.

### Data Layer (`public/data/`)

JSON files consumed by the React app at runtime:
- `weapons.json` — array of weapon objects with `baseStats`, `allowedAttachments`, `specificAttachments`, `ammoType`
- `enchantments.json` — oils with `modifiers` array (attribute, modType, value)
- `scrolls.json` — scrolls with modifiers, specialEffects, effects
- `attachments-{muzzle,sights,lasers,chamber,chisels,insurance}.json` — per-slot attachment arrays
- `caliber-modifiers.json` — `baseAmmoDamage` and per-caliber `calibers` objects

`docs/data/` holds the previous known-good data used as merge fallback during extraction.

### Extraction Pipeline (`scripts/`)

Python scripts that parse MediaWiki XML dumps into the JSON data files. All use `scripts/wiki_parser.py` as shared parser.

- `wiki_parser.py` — iterparse-based XML walker, infobox parser, wikilink extractor, section extractor
- `extract_weapons.py` — parses Item Infobox (kind=weapon) and Weapon_Infobox templates
- `extract_enchantments.py` — parses Item Infobox (kind=oil), Equipment Infobox, and Enchantment Infobox with Type=Oil
- `extract_scrolls.py` — parses Item Infobox (kind=scroll) and Equipment/Enchantment Infobox with Type=Scroll Enchantment
- `extract_attachments.py` — parses kind=attachment, kind=chisel, Equipment Infobox, and Misc Item Infobox
- `extract_calibers.py` — parses caliber conversion tables from ammo wiki pages
- `update_all.py` — orchestrates all extractors in dependency order (attachments first), then merges with old data via `--old-dir`
- `diff_data.py` — compares two data directories and prints human-readable changes

### Wiki Template Formats

The wiki uses multiple infobox templates that evolved over time. Extractors handle all variants:
- `{{Item Infobox | kind = weapon/oil/scroll/attachment/chisel}}` — original format with structured params
- `{{Weapon_Infobox}}` / `{{Weapon Infobox}}` — newer weapon format
- `{{Equipment Infobox | Type=[[Oil]]/[[Scroll Enchantment]]}}` — newer format, modifiers in Description bullets
- `{{Enchantment Infobox}}` — same structure as Equipment Infobox
- `{{Misc Item Infobox}}` — used by some chisels

Attachment sections on weapon pages use either `*` asterisks with `===Category===` sub-headings (old) or `•` (U+2022) bullets in a flat list (new).

### Merge Strategy

Many wiki pages are stubs without infoboxes. `update_all.py --old-dir` merges extracted data with previously curated data: new items are kept, old-only items are preserved, and zeroed-out stats on matched items are filled from old values.
