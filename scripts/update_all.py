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
from typing import Any, Dict, List

from scripts.extract_attachments import extract_attachments
from scripts.extract_weapons import extract_weapons
from scripts.extract_enchantments import extract_enchantments
from scripts.extract_scrolls import extract_scrolls
from scripts.extract_calibers import extract_calibers


def _merge_array_data(
    new_items: List[Dict[str, Any]],
    old_items: List[Dict[str, Any]],
    key: str = "name",
) -> List[Dict[str, Any]]:
    """Merge new extracted data with old data, keeping old items not in new.

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
            # Fill empty lists, empty modifiers dicts, and zero-valued stats from old data
            for field, new_val in enriched.items():
                if isinstance(new_val, list) and not new_val and old_item.get(field):
                    enriched[field] = old_item[field]
                elif isinstance(new_val, dict) and field == "modifiers" and not new_val and old_item.get(field):
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
    for item in old_items:
        if item[key] not in seen:
            merged.append(item)

    return merged


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
        merge_files = [
            'weapons.json', 'enchantments.json', 'scrolls.json',
            'attachments-muzzle.json', 'attachments-sights.json',
            'attachments-lasers.json', 'attachments-chamber.json',
            'attachments-chisels.json', 'attachments-insurance.json',
        ]
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
                merged = _merge_array_data(new_data, old_data)
                with open(new_path, 'w', encoding='utf-8') as f:
                    json.dump(merged, f, indent=2, ensure_ascii=False)
                added = len(merged) - before
                if added > 0:
                    print(f"  {filename}: merged {before} new + {added} old-only = {len(merged)} total")
                else:
                    print(f"  {filename}: {len(merged)} entries (no old-only items to add)")

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
