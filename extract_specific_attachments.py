#!/usr/bin/env python3
"""
Extract specific attachment names for each weapon from SULFUR wiki dump.

The wiki lists attachment types (categories) for each weapon, not individual attachments.
This script:
1. Extracts all individual attachments and their categories
2. Extracts weapon pages and their supported attachment types
3. Maps weapons to specific attachment names based on categories
"""

import json
import re
from typing import Dict, List, Set

# Path to wiki dump
WIKI_DUMP_PATH = "/mnt/z/Claude/sulfurdump/sulfur.wiki.gg-20251224-wikidump/sulfur.wiki.gg-20251224-history.xml"
OUTPUT_PATH = "/mnt/z/Claude/Sulfur_Data/sulfur-calculator-github/weapon_specific_attachments.json"


def parse_wiki_links(text: str) -> List[str]:
    """
    Extract wiki links from text.
    Format: [[Link]] or [[Link|Display Text]]
    Returns the link part (before |).
    """
    pattern = r'\[\[([^\]|]+)(?:\|[^\]]*)?\]\]'
    return re.findall(pattern, text)


def extract_categories(text: str) -> List[str]:
    """Extract category tags from page text."""
    # Categories are at the bottom: [[Category:CategoryName]]
    pattern = r'\[\[Category:([^\]]+)\]\]'
    return re.findall(pattern, text)


def parse_available_attachments(text: str) -> List[str]:
    """
    Parse the ==Available Attachments== section.
    Returns list of attachment type names.
    """
    # Find the Available Attachments section
    match = re.search(r'==Available Attachments==(.+?)(?:==|$)', text, re.DOTALL)
    if not match:
        return []

    section_text = match.group(1)

    # Extract all wiki links from bullet points
    # Format: • [[Attachment Type]] or • [[Link|Display Text]]
    links = parse_wiki_links(section_text)

    # Filter out generic links like "Attachments"
    attachment_types = []
    for link in links:
        # Skip the generic "Attachments" link
        if link == "Attachments":
            continue
        # Include actual attachment types
        attachment_types.append(link)

    return attachment_types


def normalize_attachment_type(name: str) -> str:
    """
    Normalize attachment type names for matching.
    E.g., "Sight" -> "Sights", "Laser Sights" -> "Laser Sights"
    """
    # Handle common variations
    mappings = {
        "Sight": "Sights",
        "Chamber Chisel": "Chamber Chisels",
        "Muzzle Attachment": "Muzzle Attachments",
        "Laser Sight": "Laser Sights",
        "Chamber Attachment": "Chamber Attachments",
    }
    return mappings.get(name, name)


def main():
    print("Parsing SULFUR wiki dump...")
    print(f"Reading from: {WIKI_DUMP_PATH}")

    # Data structures
    attachment_categories: Dict[str, List[str]] = {}  # category -> [attachment names]
    weapon_attachment_types: Dict[str, List[str]] = {}  # weapon -> [attachment types]

    # Read file line by line and extract pages manually
    current_page = {"title": None, "text": None, "in_text": False}
    text_lines = []

    page_count = 0
    weapon_count = 0
    attachment_count = 0

    attachment_category_types = [
        "Muzzle Attachments",
        "Sights",
        "Laser Sights",
        "Chamber Attachments",
        "Chamber Chisels"
    ]

    print("Reading file...")
    with open(WIKI_DUMP_PATH, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            # Check for page title
            title_match = re.search(r'<title>([^<]+)</title>', line)
            if title_match:
                current_page["title"] = title_match.group(1)

            # Check for start of text
            if '<text xml:space="preserve"' in line:
                current_page["in_text"] = True
                # Extract text from this line if it's on the same line
                text_match = re.search(r'<text[^>]*>(.+)', line)
                if text_match:
                    text_lines.append(text_match.group(1))

            # Check for end of text
            elif '</text>' in line:
                # Add remaining text
                text_match = re.search(r'(.+)</text>', line)
                if text_match:
                    text_lines.append(text_match.group(1))

                # Process the complete page
                if current_page["title"] and text_lines:
                    page_count += 1
                    title = current_page["title"]
                    text = '\n'.join(text_lines)

                    # Extract categories
                    categories = extract_categories(text)

                    # Check if this is an attachment
                    for cat_type in attachment_category_types:
                        if cat_type in categories:
                            if cat_type not in attachment_categories:
                                attachment_categories[cat_type] = []
                            attachment_categories[cat_type].append(title)
                            attachment_count += 1
                            if attachment_count % 10 == 0:
                                print(f"  Found {attachment_count} attachments...")
                            break

                    # Check if this is a weapon (has Available Attachments section)
                    if "==Available Attachments==" in text and "Weapons" in categories:
                        attachment_types = parse_available_attachments(text)
                        if attachment_types:
                            weapon_attachment_types[title] = attachment_types
                            weapon_count += 1
                            if weapon_count % 10 == 0:
                                print(f"  Found {weapon_count} weapons...")

                    # Progress update
                    if page_count % 1000 == 0:
                        print(f"Processed {page_count} pages...")

                # Reset for next page
                current_page = {"title": None, "text": None, "in_text": False}
                text_lines = []

            # Collect text lines
            elif current_page["in_text"]:
                text_lines.append(line)

    print(f"\nParsing complete!")
    print(f"Total pages processed: {page_count}")
    print(f"Weapons found: {weapon_count}")
    print(f"Attachments found: {attachment_count}")

    # Print attachment categories summary
    print(f"\nAttachment categories:")
    for cat, attachments in sorted(attachment_categories.items()):
        print(f"  {cat}: {len(attachments)} attachments")
        # Print first few examples
        for att in sorted(attachments)[:5]:
            print(f"    - {att}")
        if len(attachments) > 5:
            print(f"    ... and {len(attachments) - 5} more")

    # Build weapon -> specific attachments mapping
    weapon_specific_attachments: Dict[str, List[str]] = {}

    for weapon, attachment_types in weapon_attachment_types.items():
        specific_attachments = []

        for att_type in attachment_types:
            # Normalize the attachment type name
            normalized = normalize_attachment_type(att_type)

            # Get all attachments in this category
            if normalized in attachment_categories:
                specific_attachments.extend(attachment_categories[normalized])
            else:
                # If it's an individual attachment (like "Gun Crank"), add it directly
                specific_attachments.append(att_type)

        # Remove duplicates and sort
        weapon_specific_attachments[weapon] = sorted(list(set(specific_attachments)))

    # Print sample results
    print(f"\nSample weapon attachments:")
    for weapon in sorted(weapon_specific_attachments.keys())[:5]:
        attachments = weapon_specific_attachments[weapon]
        print(f"\n{weapon} ({len(attachments)} attachments):")
        for att in attachments[:10]:
            print(f"  - {att}")
        if len(attachments) > 10:
            print(f"  ... and {len(attachments) - 10} more")

    # Save to JSON
    print(f"\nSaving to {OUTPUT_PATH}...")
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(weapon_specific_attachments, f, indent=2, ensure_ascii=False)

    print(f"Done! Saved {len(weapon_specific_attachments)} weapons with specific attachments.")


if __name__ == "__main__":
    main()
