#!/usr/bin/env python3
"""
Parse SULFUR wiki dump to extract weapon attachment compatibility.

For each weapon page, finds the "==Available Attachments==" section
and extracts all attachment names listed in that section.

Output: weapon_attachments_from_wiki.json
"""

import json
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

# Wiki dump path
WIKI_DUMP_PATH = "/mnt/z/Claude/sulfurdump/sulfur.wiki.gg-20251224-wikidump/sulfur.wiki.gg-20251224-history-fixed.xml"
OUTPUT_PATH = "/mnt/z/Claude/Sulfur_Data/sulfur-calculator-github/weapon_attachments_from_wiki.json"
WEAPONS_JSON_PATH = "/mnt/z/Claude/Sulfur_Data/sulfur-calculator-github/public/data/weapons.json"

# MediaWiki namespace
NS = {'mw': 'http://www.mediawiki.org/xml/export-0.11/'}


def extract_attachments_from_wikitext(wikitext, weapon_name):
    """
    Extract attachment names from the Available Attachments section.

    Returns list of attachment names.
    """
    attachments = []

    # Find the "Available Attachments" section
    match = re.search(r'==Available Attachments==\s*(.*?)(?:\n==|$)', wikitext, re.DOTALL | re.IGNORECASE)

    if not match:
        return attachments

    section_text = match.group(1)

    # Extract wikilinks: [[Attachment Name]] or [[Attachment Name|Display Text]]
    # Also extract plain text list items

    # Method 1: Extract wikilinks
    wikilink_pattern = r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]'
    for link_match in re.finditer(wikilink_pattern, section_text):
        attachment = link_match.group(1).strip()
        # Skip category links and file links
        if not attachment.startswith(('Category:', 'File:', 'Image:')):
            # Remove any namespace prefixes - but keep the full name for now
            if attachment and attachment not in attachments:
                attachments.append(attachment)

    # Method 2: Extract from bullet lists (lines starting with * or •)
    lines = section_text.split('\n')
    for line in lines:
        line = line.strip()
        # Check for bullet points (*, •, or other unicode bullets)
        if line.startswith(('*', '•', '·', '-')):
            # Remove the bullet
            content = line.lstrip('*•·- ').strip()

            # If the line contains wikilinks, extract them
            if '[[' in content:
                for link_match in re.finditer(wikilink_pattern, content):
                    attachment = link_match.group(1).strip()
                    if not attachment.startswith(('Category:', 'File:', 'Image:')):
                        if attachment and attachment not in attachments:
                            attachments.append(attachment)
            else:
                # Plain text - remove any markup
                content = re.sub(r"'''|''", '', content)
                content = content.strip()

                # Split by common separators if multiple attachments per line
                for part in re.split(r'[,;]', content):
                    part = part.strip()
                    if part and part not in attachments and len(part) > 2:
                        # Filter out common non-attachment words
                        if part.lower() not in ['none', 'n/a', 'tba', 'all', 'any']:
                            attachments.append(part)

    return attachments


def parse_wiki_dump():
    """
    Parse the MediaWiki XML dump and extract weapon attachment data.

    Returns dict mapping weapon_name -> [list of attachment names]
    """
    print(f"Parsing wiki dump: {WIKI_DUMP_PATH}")

    weapon_attachments = {}
    weapon_pages_found = 0
    pages_with_attachments = 0

    # Parse XML iteratively to handle large files
    context = ET.iterparse(WIKI_DUMP_PATH, events=('start', 'end'))
    context = iter(context)
    event, root = next(context)

    for event, elem in context:
        if event == 'end' and elem.tag == '{http://www.mediawiki.org/xml/export-0.11/}page':
            # Extract page title
            title_elem = elem.find('mw:title', NS)
            if title_elem is None:
                elem.clear()
                continue

            title = title_elem.text

            # Skip non-weapon pages (talk pages, templates, categories, etc.)
            if not title or ':' in title:
                elem.clear()
                continue

            # Get the FIRST (most recent) revision only
            # Wiki dumps have revisions in reverse chronological order (newest first)
            revision = elem.find('mw:revision', NS)
            if revision is None:
                elem.clear()
                continue

            text_elem = revision.find('mw:text', NS)
            if text_elem is None or text_elem.text is None:
                elem.clear()
                continue

            wikitext = text_elem.text

            # Check if this looks like a weapon page (has Weapon Infobox or Available Attachments)
            is_weapon_page = (
                '{{Weapon Infobox' in wikitext or
                '{{Item Infobox' in wikitext and '| kind = weapon' in wikitext.lower() or
                '==Available Attachments==' in wikitext
            )

            if is_weapon_page:
                weapon_pages_found += 1

                # Extract attachments
                attachments = extract_attachments_from_wikitext(wikitext, title)

                if attachments:
                    weapon_attachments[title] = attachments
                    pages_with_attachments += 1
                    print(f"  Found {len(attachments)} attachments for: {title}")

            # Clear element to save memory
            elem.clear()

    root.clear()

    print(f"\nParsing complete!")
    print(f"  Total weapon pages found: {weapon_pages_found}")
    print(f"  Pages with attachment data: {pages_with_attachments}")

    return weapon_attachments


def load_weapons_json():
    """Load the weapons.json file to get list of weapons."""
    try:
        with open(WEAPONS_JSON_PATH, 'r', encoding='utf-8') as f:
            weapons = json.load(f)
        weapon_names = {w['name'] for w in weapons}
        print(f"Loaded {len(weapon_names)} weapons from weapons.json")
        return weapon_names
    except FileNotFoundError:
        print(f"Warning: Could not find {WEAPONS_JSON_PATH}")
        return set()


def generate_summary(weapon_attachments, weapon_names_from_json):
    """Generate summary statistics and comparisons."""

    print("\n" + "="*80)
    print("SUMMARY REPORT")
    print("="*80)

    print(f"\nTotal weapons found with attachment data: {len(weapon_attachments)}")

    # Show example weapons with attachment counts
    print("\nExample weapons and their attachment counts:")
    examples = sorted(weapon_attachments.items(), key=lambda x: len(x[1]), reverse=True)[:10]
    for weapon, attachments in examples:
        print(f"  {weapon}: {len(attachments)} attachments")

    # Find weapons in JSON but not in wiki
    if weapon_names_from_json:
        wiki_weapon_names = set(weapon_attachments.keys())
        in_json_not_wiki = weapon_names_from_json - wiki_weapon_names
        in_wiki_not_json = wiki_weapon_names - weapon_names_from_json

        if in_json_not_wiki:
            print(f"\nWeapons in weapons.json but NOT found in wiki ({len(in_json_not_wiki)}):")
            for name in sorted(in_json_not_wiki):
                print(f"  - {name}")
        else:
            print("\nAll weapons from weapons.json were found in wiki!")

        if in_wiki_not_json:
            print(f"\nWeapons in wiki but NOT in weapons.json ({len(in_wiki_not_json)}):")
            for name in sorted(in_wiki_not_json):
                print(f"  - {name}")

    # Find unique attachments across all weapons
    all_attachments = set()
    for attachments in weapon_attachments.values():
        all_attachments.update(attachments)

    print(f"\nTotal unique attachments found: {len(all_attachments)}")
    print("\nAll unique attachments:")
    for att in sorted(all_attachments):
        print(f"  - {att}")

    # Check for inconsistencies
    print("\n" + "="*80)
    print("POTENTIAL INCONSISTENCIES OR SPECIAL CASES")
    print("="*80)

    # Weapons with unusually few attachments
    few_attachments = [(w, a) for w, a in weapon_attachments.items() if len(a) < 3]
    if few_attachments:
        print(f"\nWeapons with fewer than 3 attachments (might be incomplete):")
        for weapon, attachments in few_attachments:
            print(f"  {weapon}: {attachments}")

    # Weapons with many attachments
    many_attachments = [(w, a) for w, a in weapon_attachments.items() if len(a) > 20]
    if many_attachments:
        print(f"\nWeapons with more than 20 attachments (might include duplicates):")
        for weapon, attachments in many_attachments:
            print(f"  {weapon}: {len(attachments)} attachments")


def main():
    """Main execution function."""

    # Parse wiki dump
    weapon_attachments = parse_wiki_dump()

    # Load weapons.json for comparison
    weapon_names_from_json = load_weapons_json()

    # Save to JSON
    print(f"\nSaving results to: {OUTPUT_PATH}")
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(weapon_attachments, f, indent=2, ensure_ascii=False)

    # Generate summary report
    generate_summary(weapon_attachments, weapon_names_from_json)

    print(f"\n✓ Output saved to: {OUTPUT_PATH}")


if __name__ == '__main__':
    main()
