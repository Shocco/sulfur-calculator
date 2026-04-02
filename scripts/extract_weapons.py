"""Extract weapon data from a MediaWiki XML dump for the SULFUR calculator."""

import json
import re
import sys
from typing import Dict, List, Optional, Set

from scripts.wiki_parser import (
    extract_section,
    extract_wikilink_text,
    extract_wikilinks,
    iterate_pages,
    parse_damage_field,
    parse_infobox,
    parse_weapon_infobox,
)

ATTACHMENT_CATEGORY_TO_SLOT: Dict[str, str] = {
    "Muzzle Attachments": "muzzle",
    "Sight": "sight",
    "Sights": "sight",
    "Laser Sights": "laser",
    "Laser Sight": "laser",
    "Chamber Attachments": "chamber",
    "Chamber Attachment": "chamber",
    "Chamber Chisel": "chisel",
    "Chamber Chisels": "chisel",
    "Gun Crank": "chamber",
    "Priming Bolt": "chamber",
    "Insurance": "insurance",
}

# Attachment names that go into specificAttachments instead of allowedAttachments slots
INDIVIDUAL_ATTACHMENTS: Set[str] = {"Gun Crank", "Priming Bolt", "Insurance"}


def _extract_attachments_section(wikitext: str) -> Optional[str]:
    """
    Extract the ==Available Attachments== section including all === sub-sections.

    Unlike extract_section from wiki_parser, this stops only at the next true
    == (level-2) heading, not at === (level-3) sub-headings.

    Args:
        wikitext: Full page wikitext.

    Returns:
        Section content string, or None if the heading is absent.
    """
    # Stop at a newline followed by == that is NOT === (negative lookahead for =)
    pattern = r'==Available Attachments==\s*(.*?)(?=\n==[^=]|\Z)'
    match = re.search(pattern, wikitext, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def _parse_attachments_section(
    section_text: str, attachment_data: Optional[Dict[str, List[str]]] = None
) -> tuple[List[str], List[str]]:
    """
    Parse the Available Attachments section.

    Args:
        section_text: Raw wikitext of the Available Attachments section.
        attachment_data: Optional mapping of slot -> list of attachment names
            used to resolve which attachments belong to which slot.

    Returns:
        A tuple of (allowed_attachment_slots, specific_attachment_names).
    """
    allowed_slots: List[str] = []
    specific_attachments: List[str] = []

    # Walk through lines looking for category headers (===Category===) and
    # list items (* [[AttachmentName]])
    current_category: Optional[str] = None
    current_slot: Optional[str] = None

    for line in section_text.split("\n"):
        line = line.strip()
        if not line:
            continue

        # Match ===Category Name=== or ==Category Name==
        heading_match = re.match(r"={2,3}\s*(.+?)\s*={2,3}", line)
        if heading_match:
            current_category = heading_match.group(1).strip()
            current_slot = ATTACHMENT_CATEGORY_TO_SLOT.get(current_category)

            # Individual attachments categories go to specificAttachments
            if current_category in INDIVIDUAL_ATTACHMENTS:
                current_slot = None  # handled per-item below
            continue

        # Match bullet list items
        if line.startswith("*"):
            item_text = line.lstrip("* ").strip()
            # Extract the display text from wikilinks
            links = extract_wikilinks(item_text)
            display = extract_wikilink_text(item_text)

            # Determine attachment name (prefer wikilink target, fall back to display)
            name = links[0] if links else display

            if current_category in INDIVIDUAL_ATTACHMENTS:
                if name not in specific_attachments:
                    specific_attachments.append(name)
            elif current_slot is not None:
                if current_slot not in allowed_slots:
                    allowed_slots.append(current_slot)

    return allowed_slots, specific_attachments


def parse_weapon_page(title: str, wikitext: str) -> Optional[Dict]:
    """
    Parse a wiki page and return a weapon dict if it is a weapon, else None.

    Args:
        title: Page title from the XML dump.
        wikitext: Raw wikitext content of the page.

    Returns:
        A dict conforming to the weapon JSON schema, or None if the page is
        not a weapon.
    """
    infobox = parse_infobox(wikitext)
    is_weapon_infobox = False

    if infobox.get("kind", "").strip().lower() != "weapon":
        # Try Weapon_Infobox format
        weapon_ib = parse_weapon_infobox(wikitext)
        if weapon_ib is not None:
            infobox = weapon_ib
            is_weapon_infobox = True
        else:
            return None

    # --- id ---
    name = infobox.get("title", title) if is_weapon_infobox else title
    weapon_id = "Weapon_" + name.replace(" ", "_")

    # --- type ---
    raw_subtype = infobox.get("SubType", "") or infobox.get("Type", "")
    weapon_type = extract_wikilink_text(raw_subtype) if raw_subtype else ""

    # --- ammoType ---
    raw_ammo = infobox.get("Ammo", "")
    ammo_type = extract_wikilink_text(raw_ammo) if raw_ammo else ""

    # --- image ---
    image = infobox.get("image", "") or (name.replace(" ", "_") + ".png")

    # --- baseStats ---
    base_stats: Dict = {}

    # Damage (may encode projectile count)
    raw_damage = infobox.get("Damage", "")
    projectile_count = 1
    if raw_damage:
        damage_val, projectile_count = parse_damage_field(raw_damage)
        base_stats["Damage"] = damage_val
    else:
        base_stats["Damage"] = 0.0

    def _safe_float(raw: str) -> float:
        """Parse a float from a potentially dirty infobox value."""
        if not raw:
            return 0.0
        m = re.match(r'-?[\d.]+', raw.strip())
        return float(m.group()) if m else 0.0

    # RPM
    base_stats["RPM"] = _safe_float(infobox.get("RPM", ""))

    # MagazineSize
    base_stats["MagazineSize"] = _safe_float(infobox.get("Mag", ""))

    # Spread
    base_stats["Spread"] = _safe_float(infobox.get("Spread", ""))

    # Recoil
    base_stats["Recoil"] = _safe_float(infobox.get("Recoil", ""))

    # Durability (also MaxDurability)
    durability_val = _safe_float(infobox.get("Durability", ""))
    base_stats["Durability"] = durability_val
    base_stats["MaxDurability"] = durability_val

    # Weight
    base_stats["Weight"] = _safe_float(infobox.get("Weight", ""))

    # Defaults
    base_stats["ProjectileSpeed"] = 100.0
    base_stats["MoveSpeed"] = 1.0
    base_stats["ProjectileCount"] = float(projectile_count)

    # --- attachments ---
    allowed_attachments: List[str] = []
    specific_attachments: List[str] = []

    attachments_section = _extract_attachments_section(wikitext)
    if attachments_section:
        allowed_attachments, specific_attachments = _parse_attachments_section(
            attachments_section
        )

    return {
        "id": weapon_id,
        "name": name,
        "type": weapon_type,
        "ammoType": ammo_type,
        "image": image,
        "baseStats": base_stats,
        "allowedAttachments": allowed_attachments,
        "specificAttachments": specific_attachments,
    }


def extract_weapons(
    dump_path: str,
    output_path: str,
    attachment_data: Optional[Dict[str, List[str]]] = None,
) -> List[Dict]:
    """
    Extract all weapon entries from a MediaWiki XML dump and write to JSON.

    Args:
        dump_path: Path to the MediaWiki XML dump file.
        output_path: Path where the output JSON will be written.
        attachment_data: Optional dict mapping slot IDs to lists of attachment
            names, used for resolving attachment slots.

    Returns:
        List of weapon dicts that were written to the output file.
    """
    weapons: List[Dict] = []

    for title, wikitext in iterate_pages(dump_path):
        weapon = parse_weapon_page(title, wikitext)
        if weapon is not None:
            weapons.append(weapon)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(weapons, f, indent=2, ensure_ascii=False)

    print(f"Extracted {len(weapons)} weapons -> {output_path}")
    return weapons


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 -m scripts.extract_weapons <dump_path> [output_path]")
        sys.exit(1)

    dump = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "weapons.json"
    extract_weapons(dump, out)
