"""
Master runner: extract all data from a SULFUR wiki dump.

Usage:
    python -m scripts.update_all <dump_xml_path> [--output-dir public/data] [--backup]
    python -m scripts.update_all <dump_xml_path> --output-dir public/data --old-dir docs/data

Steps:
1. Back up existing data (if --backup)
2. Extract attachments (needed by weapon extractor for specificAttachments)
3. Extract weapons (uses attachment names)
4. Extract enchantments
5. Extract scrolls
6. Extract calibers
7. Merge with old data (if --old-dir provided) to fill gaps
8. Print summary
"""

import argparse
import json
import os
import shutil
import sys
from typing import Any, Dict, List, Optional

from scripts.extract_attachments import extract_attachments
from scripts.extract_weapons import extract_weapons
from scripts.extract_enchantments import extract_enchantments
from scripts.extract_scrolls import extract_scrolls
from scripts.extract_calibers import extract_calibers
from scripts.wiki_parser import find_redirects


def _merge_array_data(
    new_items: List[Dict[str, Any]],
    old_items: List[Dict[str, Any]],
    key: str = "name",
    renamed: Optional[Dict[str, str]] = None,
    elsewhere: Optional[set] = None,
) -> List[Dict[str, Any]]:
    """Merge new extracted data with old data, keeping old items not in new.

    Old-only items whose wiki page is now a redirect (``renamed``: old -> new
    title) are dropped: the item was renamed, and the new name is extracted.
    Old-only items whose name is in ``elsewhere`` (extracted into a different
    output file, e.g. an attachment that moved slot) are dropped too.

    For items present in both, the new version is kept but any empty fields
    are filled from the old version.
    """
    old_by_key = {item[key]: item for item in old_items}
    new_by_key = {item[key]: item for item in new_items}

    merged = []
    seen = set()

    # First pass: new items, enriched with old data where new fields are empty
    for item in new_items:
        name = item[key]
        seen.add(name)
        if name in old_by_key:
            old_item = old_by_key[name]
            enriched = dict(item)
            # Fill empty descriptive lists and zero-valued stats from old data.
            # Modifiers are never restored: a page that was extracted and lists
            # none has had them removed, and old values would be stale.
            for field, new_val in enriched.items():
                if field == "modifiers":
                    continue
                if isinstance(new_val, list) and not new_val and old_item.get(field):
                    enriched[field] = old_item[field]
                elif isinstance(new_val, dict) and field == "baseStats":
                    old_stats = old_item.get("baseStats", {})
                    for stat_key, stat_val in enriched[field].items():
                        if stat_val == 0.0 and stat_key in old_stats and old_stats[stat_key] != 0.0:
                            enriched[field][stat_key] = old_stats[stat_key]
            merged.append(enriched)
        else:
            merged.append(item)

    # Second pass: old items not in new (wiki stubs without infoboxes)
    renamed = renamed or {}
    elsewhere = elsewhere or set()
    for item in old_items:
        if item[key] in seen:
            continue
        # Renamed on the wiki and the new name was extracted -> stale, drop it
        if renamed.get(item[key]) in new_by_key:
            continue
        if item[key] in elsewhere:
            continue
        merged.append(item)

    return merged


def _fill_slots_from_specific_attachments(
    weapons: List[Dict[str, Any]], slot_by_name: Dict[str, str]
) -> None:
    """Give weapons with no wiki-listed slots the slots their specificAttachments imply.

    A weapon page without an Available Attachments section extracts as
    ``allowedAttachments == ['insurance']`` (insurance fits every weapon), which
    hides every other slot in the UI. Its specificAttachments, kept from curated
    data by the merge, still name the items it takes, so use their slots.
    Weapons the wiki does list slots for are left alone. Modifies in place.
    """
    for weapon in weapons:
        if weapon.get("allowedAttachments") != ["insurance"]:
            continue
        slots: List[str] = []
        for name in weapon.get("specificAttachments", []):
            slot = slot_by_name.get(name)
            if slot and slot != "insurance" and slot not in slots:
                slots.append(slot)
        weapon["allowedAttachments"] = slots + ["insurance"]


OVERRIDES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data_overrides.json')


def _apply_overrides(items: List[Dict[str, Any]], overrides: Dict[str, Any]) -> List[str]:
    """Apply hand-checked modifier corrections where the wiki lags the game.

    ``overrides`` maps item name -> {"modifiers": {attribute: {"wikiValue": x,
    "value": y}}, "source": "..."}. A correction is applied only while the
    extracted value still equals ``wikiValue``; once the wiki changes, the
    override is skipped and reported so it can be deleted. Nothing is ever
    added: a missing item or attribute is reported and left alone.
    Modifies ``items`` in place and returns one note per correction.
    """
    notes: List[str] = []
    by_name = {item.get("name"): item for item in items}
    for name, entry in overrides.items():
        item = by_name.get(name)
        for attribute, change in entry.get("modifiers", {}).items():
            mods = item.get("modifiers", []) if item else []
            mod = next((m for m in mods if m.get("attribute") == attribute), None)
            if mod is None:
                notes.append(f"override for '{name}' {attribute} not found in extracted data; nothing changed")
            elif mod["value"] == change["wikiValue"]:
                mod["value"] = change["value"]
                notes.append(f"override applied: '{name}' {attribute} {change['wikiValue']} -> {change['value']} "
                             f"({entry.get('source', 'no source given')})")
            elif mod["value"] == change["value"]:
                notes.append(f"override for '{name}' {attribute} no longer needed: the wiki now says "
                             f"{mod['value']}; remove it from data_overrides.json")
            else:
                notes.append(f"override for '{name}' {attribute} not applied: the wiki now says {mod['value']}, "
                             f"expected {change['wikiValue']}; check it and update or remove the override")
    return notes


def main():
    parser = argparse.ArgumentParser(description='Extract all SULFUR data from wiki dump')
    parser.add_argument('dump_path', help='Path to the wiki XML dump file')
    parser.add_argument('--output-dir', default='public/data', help='Output directory for JSON files')
    parser.add_argument('--old-dir', default=None, help='Directory with old JSON data for merge fallback')
    parser.add_argument('--backup', action='store_true', help='Back up existing data before overwriting')
    args = parser.parse_args()

    dump_path = args.dump_path
    output_dir = args.output_dir
    old_dir = args.old_dir

    if not os.path.exists(dump_path):
        print(f"Error: Dump file not found: {dump_path}")
        sys.exit(1)

    # Step 0: Backup
    if args.backup and os.path.exists(output_dir):
        backup_dir = output_dir + '.bak'
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)
        shutil.copytree(output_dir, backup_dir)
        print(f"Backed up {output_dir} -> {backup_dir}")

    # Step 1: Extract attachments first (weapon extractor needs the names)
    print("\n=== Extracting Attachments ===")
    attachment_names = extract_attachments(dump_path, output_dir)

    # Step 2: Extract weapons with attachment data
    print("\n=== Extracting Weapons ===")
    weapons_path = os.path.join(output_dir, 'weapons.json')
    extract_weapons(dump_path, weapons_path, attachment_data=attachment_names)

    # Step 3: Extract enchantments
    print("\n=== Extracting Enchantments ===")
    enchantments_path = os.path.join(output_dir, 'enchantments.json')
    extract_enchantments(dump_path, enchantments_path)

    # Step 4: Extract scrolls
    print("\n=== Extracting Scrolls ===")
    scrolls_path = os.path.join(output_dir, 'scrolls.json')
    extract_scrolls(dump_path, scrolls_path)

    # Step 5: Extract calibers
    print("\n=== Extracting Calibers ===")
    calibers_path = os.path.join(output_dir, 'caliber-modifiers.json')
    extract_calibers(dump_path, calibers_path)

    # Step 6: Merge with old data if --old-dir provided
    if old_dir and os.path.isdir(old_dir):
        print(f"\n=== Merging with old data from {old_dir} ===")
        renamed = find_redirects(dump_path)
        merge_files = [
            'weapons.json', 'enchantments.json', 'scrolls.json',
            'attachments-muzzle.json', 'attachments-sights.json',
            'attachments-lasers.json', 'attachments-chamber.json',
            'attachments-chisels.json', 'attachments-insurance.json',
        ]
        # Names extracted into each attachment file, to catch items that moved slot
        att_names = {}
        for fn in merge_files:
            if fn.startswith('attachments-') and os.path.exists(os.path.join(output_dir, fn)):
                with open(os.path.join(output_dir, fn), encoding='utf-8') as f:
                    att_names[fn] = {i.get('name') for i in json.load(f)}
        for filename in merge_files:
            new_path = os.path.join(output_dir, filename)
            old_path = os.path.join(old_dir, filename)
            if not os.path.exists(old_path) or not os.path.exists(new_path):
                continue
            with open(new_path, encoding='utf-8') as f:
                new_data = json.load(f)
            with open(old_path, encoding='utf-8') as f:
                old_data = json.load(f)
            if isinstance(new_data, list) and isinstance(old_data, list):
                before = len(new_data)
                new_names = {i.get('name') for i in new_data}
                new_by_name = {i.get('name'): i for i in new_data}
                elsewhere = set().union(*(v for k, v in att_names.items() if k != filename)) \
                    if filename in att_names else set()
                for old in old_data:
                    n = old.get('name')
                    if n in new_names:
                        if old.get('modifiers') and not new_by_name[n].get('modifiers'):
                            print(f"  {filename}: '{n}' has no modifiers on the wiki any more; "
                                  f"old ones not kept: {json.dumps(old['modifiers'])}")
                        continue
                    if renamed.get(n) in new_names:
                        print(f"  {filename}: dropped '{n}' (renamed on wiki -> '{renamed[n]}')")
                    elif n in elsewhere:
                        print(f"  {filename}: dropped '{n}' (now extracted into another attachment file)")
                merged = _merge_array_data(new_data, old_data, renamed=renamed, elsewhere=elsewhere)
                with open(new_path, 'w', encoding='utf-8') as f:
                    json.dump(merged, f, indent=2, ensure_ascii=False)
                added = len(merged) - before
                if added > 0:
                    print(f"  {filename}: merged {before} new + {added} old-only = {len(merged)} total")
                else:
                    print(f"  {filename}: {len(merged)} entries (no old-only items to add)")

    # Step 7: weapons the wiki lists no slots for get them from specificAttachments
    slot_by_name: Dict[str, str] = {}
    for filename in sorted(os.listdir(output_dir)):
        if filename.startswith('attachments-') and filename.endswith('.json'):
            with open(os.path.join(output_dir, filename), encoding='utf-8') as f:
                for item in json.load(f):
                    slot_by_name[item['name']] = item['type']
    with open(weapons_path, encoding='utf-8') as f:
        weapons = json.load(f)
    before = [list(w['allowedAttachments']) for w in weapons]
    _fill_slots_from_specific_attachments(weapons, slot_by_name)
    for weapon, old_slots in zip(weapons, before):
        if weapon['allowedAttachments'] != old_slots:
            print(f"  weapons.json: '{weapon['name']}' has no attachment list on the wiki; "
                  f"slots taken from its specificAttachments: {weapon['allowedAttachments']}")
    with open(weapons_path, 'w', encoding='utf-8') as f:
        json.dump(weapons, f, indent=2, ensure_ascii=False)

    # Step 8: hand-checked corrections where the wiki lags the game (data_overrides.json)
    if os.path.exists(OVERRIDES_PATH):
        with open(OVERRIDES_PATH, encoding='utf-8') as f:
            all_overrides = json.load(f)
        for filename, overrides in all_overrides.items():
            target = os.path.join(output_dir, filename)
            if not os.path.exists(target):
                continue
            with open(target, encoding='utf-8') as f:
                items = json.load(f)
            for note in _apply_overrides(items, overrides):
                print(f"  {filename}: {note}")
            with open(target, 'w', encoding='utf-8') as f:
                json.dump(items, f, indent=2, ensure_ascii=False)

    print("\n=== Extraction Complete ===")
    print(f"All data written to {output_dir}/")

    # Summary counts
    for filename in sorted(os.listdir(output_dir)):
        if filename.endswith('.json'):
            filepath = os.path.join(output_dir, filename)
            with open(filepath) as f:
                data = json.load(f)
            count = len(data) if isinstance(data, list) else len(data.keys())
            print(f"  {filename}: {count} entries")


if __name__ == '__main__':
    main()
