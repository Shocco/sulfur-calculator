#!/usr/bin/env python3
"""
Parse SULFUR wiki XML dump to extract weapon attachment compatibility.

This script reads the MediaWiki XML dump and extracts the "Available Attachments"
section for each weapon page, mapping weapons to their compatible attachment types.
"""

import json
import re
from typing import Dict, List
from pathlib import Path


# Mapping from wiki terms to attachment type IDs
ATTACHMENT_MAPPING = {
    'muzzle attachments': 'muzzle',
    'muzzle attachment': 'muzzle',
    'muzzle': 'muzzle',
    'sight': 'sight',
    'sights': 'sight',
    'laser sight': 'laser',
    'laser sights': 'laser',
    'laser': 'laser',
    'gun crank': 'chamber',
    'chamber attachments': 'chamber',
    'chamber attachment': 'chamber',
    'chamber': 'chamber',
    'chamber chisel': 'chisel',
    'chamber chisels': 'chisel',
    'chisel': 'chisel',
    'insurance': 'insurance',
}


def extract_weapon_name_from_title(title: str) -> str:
    """Extract clean weapon name from page title."""
    return title.strip()


def parse_attachments_section(text: str) -> List[str]:
    """
    Parse the 'Available Attachments' section from wiki markup.

    Args:
        text: Wiki page text content

    Returns:
        List of attachment types found for this weapon
    """
    attachments_set = set()

    # Find the "Available Attachments" section
    # Match both == and === level headers (allow optional spaces around header)
    attachment_pattern = r'={2,3}\s*Available Attachments\s*={2,3}(.*?)(?:={2,}[^=]|$)'
    match = re.search(attachment_pattern, text, re.DOTALL | re.IGNORECASE)

    if not match:
        return []

    section_text = match.group(1)

    # Extract all wiki links in the section
    # Pattern matches [[Link]] or [[Link|Display Text]]
    link_pattern = r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]'
    links = re.findall(link_pattern, section_text)

    for link in links:
        link_lower = link.strip().lower()
        if link_lower in ATTACHMENT_MAPPING:
            attachments_set.add(ATTACHMENT_MAPPING[link_lower])

    # Also extract plain text bullet points (for newer wiki format)
    # Look for lines starting with bullet (• or *) followed by attachment name
    bullet_pattern = r'[•\*]\s*([^\n\r]+)'
    bullet_items = re.findall(bullet_pattern, section_text)

    for item in bullet_items:
        item_lower = item.strip().lower()
        if item_lower in ATTACHMENT_MAPPING:
            attachments_set.add(ATTACHMENT_MAPPING[item_lower])

    return sorted(list(attachments_set))


def parse_wiki_xml_simple(xml_path: str) -> Dict[str, List[str]]:
    """
    Parse MediaWiki XML dump using simple text processing.
    This is more robust than XML parsing for malformed XML.

    For each page, extracts data from the LATEST revision only
    (the last <revision> block in each <page> block).

    Args:
        xml_path: Path to the MediaWiki XML dump file

    Returns:
        Dictionary mapping weapon names to lists of compatible attachment types
    """
    weapon_attachments: Dict[str, List[str]] = {}

    print(f"Reading XML file: {xml_path}")
    print("This may take a moment for large files...")

    with open(xml_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    print(f"File loaded ({len(content):,} characters)")
    print("Parsing pages...")

    # Split into pages using <page> tags
    # Use non-greedy matching to get individual pages
    page_pattern = r'<page>(.*?)</page>'
    pages = re.findall(page_pattern, content, re.DOTALL)

    print(f"Found {len(pages)} pages")

    weapons_found = 0

    for i, page_content in enumerate(pages):
        # Extract title
        title_match = re.search(r'<title>(.*?)</title>', page_content)
        if not title_match:
            continue

        weapon_name = title_match.group(1)

        # Find all revisions in this page
        revision_pattern = r'<revision>(.*?)</revision>'
        revisions = re.findall(revision_pattern, page_content, re.DOTALL)

        if not revisions:
            continue

        # Find the most recent revision that has "Available Attachments"
        # Iterate backwards through revisions (most recent first)
        page_text = None
        for rev in reversed(revisions):
            text_match = re.search(r'<text[^>]*>(.*?)</text>', rev, re.DOTALL)
            if text_match:
                candidate_text = text_match.group(1)
                if 'Available Attachments' in candidate_text:
                    page_text = candidate_text
                    break

        if page_text is None:
            continue

        # Parse attachments
        attachments = parse_attachments_section(page_text)

        if attachments:
            weapon_attachments[weapon_name] = attachments
            weapons_found += 1
            print(f"  Found: {weapon_name} -> {attachments}")

        # Progress indicator
        if (i + 1) % 1000 == 0:
            print(f"  Processed {i + 1:,} pages, found {weapons_found} weapons with attachments...")

    print(f"\nCompleted! Processed {len(pages):,} total pages")
    print(f"Found {weapons_found} weapons with attachment data")

    return weapon_attachments


def main():
    """Main execution function."""
    # Input and output paths
    wiki_xml_path = '/mnt/z/Claude/sulfurdump/sulfur.wiki.gg-20251224-wikidump/sulfur.wiki.gg-20251224-history.xml'
    output_path = '/mnt/z/Claude/Sulfur_Data/sulfur-calculator-github/weapon_attachments_compatibility.json'

    # Verify input file exists
    if not Path(wiki_xml_path).exists():
        print(f"ERROR: Wiki XML file not found at: {wiki_xml_path}")
        return 1

    # Parse the XML dump
    weapon_attachments = parse_wiki_xml_simple(wiki_xml_path)

    if not weapon_attachments:
        print("\nWARNING: No weapon attachment data found!")
        return 1

    # Sort weapons alphabetically
    sorted_weapons = dict(sorted(weapon_attachments.items()))

    # Write output JSON
    print(f"\nWriting output to: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sorted_weapons, f, indent=2, ensure_ascii=False)

    print(f"Successfully wrote {len(sorted_weapons)} weapons to JSON file")

    # Print summary statistics
    print("\n=== Summary Statistics ===")
    attachment_counts = {}
    for attachments in sorted_weapons.values():
        for att in attachments:
            attachment_counts[att] = attachment_counts.get(att, 0) + 1

    print("\nAttachment type frequency:")
    for att_type in sorted(attachment_counts.keys()):
        print(f"  {att_type}: {attachment_counts[att_type]} weapons")

    # Show some examples
    print("\n=== Example Entries ===")
    for i, (weapon, attachments) in enumerate(sorted_weapons.items()):
        if i < 10:
            print(f"  {weapon}: {attachments}")
        else:
            break

    return 0


if __name__ == '__main__':
    exit(main())
