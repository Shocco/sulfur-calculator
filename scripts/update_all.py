"""
Master runner: extract all data from a SULFUR wiki dump.

Usage:
    python -m scripts.update_all <dump_xml_path> [--output-dir public/data] [--backup]

Steps:
1. Back up existing data (if --backup)
2. Extract attachments (needed by weapon extractor for specificAttachments)
3. Extract weapons (uses attachment names)
4. Extract enchantments
5. Extract scrolls
6. Extract calibers
7. Print summary
"""

import argparse
import json
import os
import shutil
import sys

from scripts.extract_attachments import extract_attachments
from scripts.extract_weapons import extract_weapons
from scripts.extract_enchantments import extract_enchantments
from scripts.extract_scrolls import extract_scrolls
from scripts.extract_calibers import extract_calibers


def main():
    parser = argparse.ArgumentParser(description='Extract all SULFUR data from wiki dump')
    parser.add_argument('dump_path', help='Path to the wiki XML dump file')
    parser.add_argument('--output-dir', default='public/data', help='Output directory for JSON files')
    parser.add_argument('--backup', action='store_true', help='Back up existing data before overwriting')
    args = parser.parse_args()

    dump_path = args.dump_path
    output_dir = args.output_dir

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
