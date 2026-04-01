# Wiki Data Update Pipeline — Design Spec
**Date:** 2026-03-31  
**Status:** Approved

## Overview

Pull a fresh MediaWiki XML dump from `https://sulfur.wiki.gg/` using wikiteam3 and regenerate all `public/data/*.json` files from the new dump. Produces a reproducible, offline-first extraction pipeline.

## Stage 1 — Download Fresh Wiki Dump

Run wikiteam3 to crawl `https://sulfur.wiki.gg/` and save the XML dump to:
```
/mnt/z/Claude/sulfurdump/sulfur.wiki.gg-YYYYMMDD-wikidump/
```
The existing Dec 2024 dump is preserved alongside the new one.

**Command (approximate):**
```bash
wikiteam3dumpgenerator --xml --images "https://sulfur.wiki.gg/"
```

## Stage 2 — Extraction Scripts

New Python scripts in `/opt/sulfur-calculator/`, each parsing the XML dump with `xml.etree.ElementTree` (iterparse, same pattern as existing scripts) and writing the output JSON to `public/data/`.

Before writing parsers, each script must first explore the relevant wiki infobox structure in the dump (e.g., `{{Weapon Infobox`, `{{Enchantment Infobox`) to map field names to JSON schema fields.

| Script | Wiki page type / infobox | Output |
|--------|--------------------------|--------|
| `extract_weapons.py` | Weapon pages / `{{Weapon Infobox` | `public/data/weapons.json` |
| `extract_enchantments.py` | Oil/enchantment pages / `{{Enchantment Infobox` or similar | `public/data/enchantments.json` |
| `extract_scrolls.py` | Scroll pages | `public/data/scrolls.json` |
| `extract_attachments.py` | Attachment pages (Muzzle, Sight, Laser, Chamber, Chisel, Insurance categories) | `public/data/attachments-muzzle.json`, `attachments-sights.json`, `attachments-lasers.json`, `attachments-chamber.json`, `attachments-chisels.json`, `attachments-insurance.json` |
| `extract_calibers.py` | Caliber/ammo pages | `public/data/caliber-modifiers.json` |

Existing scripts (`parse_wiki_weapon_attachments.py`, `extract_specific_attachments.py`) are updated to reference the new dump path.

A single `update_all.py` runner invokes all extraction scripts in sequence.

### JSON Schema Preservation

Each extraction script must output JSON that matches the existing schema exactly (same field names, types, nesting). The existing `public/data/*.json` files serve as the reference schema. If the wiki introduces genuinely new fields relevant to game mechanics (e.g., a new stat), add them to the schema and update the app accordingly.

## Stage 3 — Diff Report

`diff_data.py` takes two directories (old JSON files vs new) and prints:
- Weapons/items added or removed
- Stat values that changed
- New fields present in new data but not old

Output is human-readable stdout. User spot-checks before committing.

## Stage 4 — App Validation

```bash
npm run build
```

Confirms no schema breakage in the React app. If new fields were added to JSON that the app should display/use, update the relevant component(s) in `src/`.

## Files Changed

**New files:**
- `extract_weapons.py`
- `extract_enchantments.py`
- `extract_scrolls.py`
- `extract_attachments.py`
- `extract_calibers.py`
- `update_all.py`
- `diff_data.py`

**Modified files:**
- `parse_wiki_weapon_attachments.py` — update dump path
- `extract_specific_attachments.py` — update dump path
- `public/data/*.json` — regenerated from new dump
- `src/` components — only if schema changes require app updates

## Out of Scope

- Automating wikiteam3 invocation (user runs it manually)
- Image asset updates
- Any UI redesign
