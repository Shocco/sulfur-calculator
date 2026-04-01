"""Extract attachment data from a MediaWiki XML dump for the SULFUR calculator.

Handles three kinds of items:
- attachment (kind=attachment): muzzle, sight, laser, chamber, insurance
- chisel (kind=chisel): caliber-conversion chamber chisels
- Insurance (special attachment with title=="Insurance")

Output is written as per-slot JSON files.
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union

from scripts.wiki_parser import (
    extract_section,
    extract_wikilink_text,
    iterate_pages,
    parse_infobox,
)

# ---------------------------------------------------------------------------
# Known rarities (not present in wiki infoboxes)
# ---------------------------------------------------------------------------

KNOWN_RARITIES: Dict[str, str] = {
    "A12C Muzzle Brake": "Uncommon",
    "Aftermarket Haukland Silencer": "Rare",
    "Barrel Extension 2\"": "Common",
    "Barrel Extension 4\"": "Uncommon",
    "Barrel Extension 6\"": "Rare",
    "Breznik BMD": "Uncommon",
    "Breznik BMD (Tactical)": "Rare",
    "Haukland Flash Hider": "Common",
    "Haukland Silencer": "Uncommon",
    "Improvised Barrel Extension": "Common",
    "M87 \"Albatross\" Silencer": "Rare",
    "SR-P3 Silencer": "Rare",
    "Shrouded Barrel Extension": "Uncommon",
    "Warmage Compensator": "Rare",
    "Assault Scope": "Uncommon",
    "Compact Sight": "Common",
    "Holographic Sight": "Uncommon",
    "Hunting Scope": "Rare",
    "Recon Scope": "Uncommon",
    "Reflex Sight": "Uncommon",
    "Sniper Scope": "Rare",
    "Laser Sight (Red)": "Common",
    "Laser Sight (Green)": "Uncommon",
    "Laser Sight (Yellow)": "Rare",
    "Gun Crank": "Uncommon",
    "Priming Bolt": "Rare",
    "Chamber Chisel (9mm)": "Uncommon",
    "Chamber Chisel (5.56mm)": "Uncommon",
    "Chamber Chisel (7.62mm)": "Rare",
    "Chamber Chisel (.50 BMG)": "Legendary",
    "Chamber Chisel (12Ga)": "Rare",
    "Insurance": "Legendary",
}

DEFAULT_RARITY = "Common"

# ---------------------------------------------------------------------------
# SubType display text -> slot identifier
# ---------------------------------------------------------------------------

SUBTYPE_TO_SLOT: Dict[str, str] = {
    "muzzle attachment": "muzzle",
    "muzzle attachments": "muzzle",
    "sights": "sight",
    "sight": "sight",
    "laser sights": "laser",
    "laser sight": "laser",
    "chamber attachment": "chamber",
    "chamber attachments": "chamber",
    # generic "attachment" display text is used for Insurance
    "attachment": "insurance",
}

# ---------------------------------------------------------------------------
# Slot -> output filename stem
# ---------------------------------------------------------------------------

SLOT_TO_FILENAME: Dict[str, str] = {
    "muzzle": "attachments-muzzle.json",
    "sight": "attachments-sights.json",
    "laser": "attachments-lasers.json",
    "chamber": "attachments-chamber.json",
    "chisel": "attachments-chisels.json",
    "insurance": "attachments-insurance.json",
}

# ---------------------------------------------------------------------------
# Chisel caliber descriptions
# ---------------------------------------------------------------------------

CHISEL_DESCRIPTIONS: Dict[str, str] = {
    "9mm": "Converts weapon to 9mm caliber - provides reduced recoil but lower damage",
    "5.56mm": "Converts weapon to 5.56mm caliber - balanced damage and recoil",
    "7.62mm": "Converts weapon to 7.62mm caliber - high damage with increased recoil",
    ".50 BMG": "Converts weapon to .50 BMG caliber - extreme damage with very high recoil",
    "12Ga": "Converts weapon to 12 Gauge shotgun shells - multiple pellets with spread",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _strip_html(text: str) -> str:
    """Remove HTML tags from a string."""
    return re.sub(r"<[^>]+>", "", text).strip()


def _first_description_line(wikitext: str) -> str:
    """Extract the first non-markup line from the Description section.

    Args:
        wikitext: Raw wikitext of the page.

    Returns:
        Plain-text description string, or empty string if none found.
    """
    section = extract_section(wikitext, "Description")
    if not section:
        return ""

    for line in section.splitlines():
        line = line.strip()
        if not line:
            continue
        # Skip lines that are pure wiki markup
        if line.startswith(("=", "{", "|", "!", "[[Category")):
            continue
        # Strip common wiki formatting
        line = re.sub(r"'''|''", "", line)
        line = re.sub(r"\[\[([^\]|]+\|)?([^\]]+)\]\]", r"\2", line)
        line = _strip_html(line)
        if line:
            return line

    return ""


def _normalize_caliber(caliber: str) -> str:
    """Normalize caliber display text.

    Specifically converts "50 BMG" (without leading dot) to ".50 BMG".

    Args:
        caliber: Raw caliber string extracted from a wikilink.

    Returns:
        Normalized caliber string.
    """
    if re.match(r"^50\s+BMG$", caliber, re.IGNORECASE):
        return ".50 BMG"
    return caliber


# ---------------------------------------------------------------------------
# Main parsers
# ---------------------------------------------------------------------------


def parse_attachment_page(title: str, wikitext: str) -> Optional[Dict]:
    """Parse a wiki page and return an attachment dict if it is an attachment.

    Handles kind=attachment pages and the special Insurance item.

    Args:
        title: Page title from the XML dump.
        wikitext: Raw wikitext content of the page.

    Returns:
        A dict representing the attachment, or None if the page is not an
        attachment.

    Example output::

        {
            "id": "Haukland_Silencer",
            "name": "Haukland Silencer",
            "type": "muzzle",
            "rarity": "Uncommon",
            "modifiers": {"Spread": -0.75},
            "specialEffects": {},
            "description": "...",
            "image": "/images/attachments/Haukland_Silencer.png"
        }
    """
    params = parse_infobox(wikitext)
    if params.get("kind", "").strip().lower() != "attachment":
        return None

    # --- Determine slot type from SubType wikilink display text ---
    raw_subtype = params.get("SubType", "")
    subtype_display = extract_wikilink_text(raw_subtype).lower().strip()
    slot = SUBTYPE_TO_SLOT.get(subtype_display)

    # Insurance special case: explicit title match overrides generic "attachment"
    if title == "Insurance":
        slot = "insurance"

    if slot is None:
        return None

    # --- Modifiers ---
    modifiers: Dict[str, Union[float, Dict]] = {}

    # Spread -> plain float
    raw_spread = params.get("Spread", "")
    if raw_spread:
        try:
            modifiers["Spread"] = float(raw_spread)
        except ValueError:
            pass

    # Speed -> MoveSpeed plain float
    raw_speed = params.get("Speed", "")
    if raw_speed:
        try:
            modifiers["MoveSpeed"] = float(raw_speed)
        except ValueError:
            pass

    # CritADS -> ADSCritChance plain float
    raw_crit = params.get("CritADS", "")
    if raw_crit:
        try:
            modifiers["ADSCritChance"] = float(raw_crit)
        except ValueError:
            pass

    # MoveAccuracy -> AccuracyWhileMoving plain float
    raw_move_acc = params.get("MoveAccuracy", "")
    if raw_move_acc:
        try:
            modifiers["AccuracyWhileMoving"] = float(raw_move_acc)
        except ValueError:
            pass

    # Dmg -> percent dict or plain float
    raw_dmg = params.get("Dmg", "")
    if raw_dmg:
        dmg_stripped = raw_dmg.strip()
        if "%" in dmg_stripped:
            try:
                pct_str = dmg_stripped.replace("%", "").strip()
                modifiers["Dmg"] = {"value": float(pct_str), "type": "percent"}
            except ValueError:
                pass
        else:
            try:
                modifiers["Dmg"] = float(dmg_stripped)
            except ValueError:
                pass

    # --- Special effects ---
    special_effects: Dict = {}

    # SilFire -> silencesFire
    if params.get("SilFire", ""):
        special_effects["silencesFire"] = True

    # ModeChange -> firingMode (strip HTML tags, lowercase)
    raw_mode = params.get("ModeChange", "")
    if raw_mode:
        mode_text = _strip_html(raw_mode).lower().strip()
        if mode_text:
            special_effects["firingMode"] = mode_text

    # Insurance protection effect
    if title == "Insurance" or slot == "insurance":
        slot = "insurance"
        special_effects["protection"] = "Returns weapon to Collection Box on death"

    # --- Description ---
    description = _first_description_line(wikitext)

    # --- Image ---
    image_name = title.replace(" ", "_")
    image = f"/images/attachments/{image_name}.png"

    # --- Rarity ---
    rarity = KNOWN_RARITIES.get(title, DEFAULT_RARITY)

    return {
        "id": title.replace(" ", "_"),
        "name": title,
        "type": slot,
        "rarity": rarity,
        "modifiers": modifiers,
        "specialEffects": special_effects,
        "description": description,
        "image": image,
    }


def parse_chisel_page(title: str, wikitext: str) -> Optional[Dict]:
    """Parse a wiki page and return a chisel dict if it is a chamber chisel.

    Args:
        title: Page title from the XML dump.
        wikitext: Raw wikitext content of the page.

    Returns:
        A dict representing the chisel, or None if the page is not a chisel.

    Example output::

        {
            "id": "Chamber_Chisel_(9mm)",
            "name": "Chamber Chisel (9mm)",
            "type": "chisel",
            "rarity": "Uncommon",
            "modifiers": {},
            "specialEffects": {"caliberConversion": "9mm"},
            "description": "Converts weapon to 9mm caliber - ...",
            "image": "/images/attachments/Chamber_Chisel_(9mm).png"
        }
    """
    params = parse_infobox(wikitext)
    if params.get("kind", "").strip().lower() != "chisel":
        return None

    # --- ChamberAmmo wikilink -> caliber ---
    raw_ammo = params.get("ChamberAmmo", "")
    caliber_raw = extract_wikilink_text(raw_ammo).strip() if raw_ammo else ""
    caliber = _normalize_caliber(caliber_raw)

    # --- Description from caliber lookup ---
    description = CHISEL_DESCRIPTIONS.get(caliber, "")

    # --- Image ---
    image_name = title.replace(" ", "_")
    image = f"/images/attachments/{image_name}.png"

    # --- Rarity ---
    rarity = KNOWN_RARITIES.get(title, DEFAULT_RARITY)

    result: Dict = {
        "id": title.replace(" ", "_"),
        "name": title,
        "type": "chisel",
        "rarity": rarity,
        "modifiers": {},
        "specialEffects": {},
        "description": description,
        "image": image,
    }

    if caliber:
        result["specialEffects"]["caliberConversion"] = caliber

    return result


# ---------------------------------------------------------------------------
# Bulk extractor
# ---------------------------------------------------------------------------


def extract_attachments(dump_path: str, output_dir: str) -> Dict[str, List[str]]:
    """Extract all attachment and chisel entries from a MediaWiki XML dump.

    Writes one JSON file per slot type into output_dir.

    Args:
        dump_path: Absolute path to the MediaWiki XML dump file.
        output_dir: Directory where the per-slot JSON files will be written.

    Returns:
        Dict mapping slot name to list of attachment names written for that slot.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Collect items by slot
    by_slot: Dict[str, List[Dict]] = {slot: [] for slot in SLOT_TO_FILENAME}

    for title, wikitext in iterate_pages(dump_path):
        params = parse_infobox(wikitext)
        kind = params.get("kind", "").strip().lower()

        if kind == "chisel":
            item = parse_chisel_page(title, wikitext)
            if item is not None:
                by_slot["chisel"].append(item)
        elif kind == "attachment":
            item = parse_attachment_page(title, wikitext)
            if item is not None:
                slot = item["type"]
                if slot in by_slot:
                    by_slot[slot].append(item)

    # Write files and build summary
    summary: Dict[str, List[str]] = {}
    for slot, filename in SLOT_TO_FILENAME.items():
        items = by_slot[slot]
        output_path = out / filename
        with open(output_path, "w", encoding="utf-8") as fh:
            json.dump(items, fh, indent=2, ensure_ascii=False)
        names = [item["name"] for item in items]
        summary[slot] = names
        print(f"Extracted {len(items)} {slot} attachments -> {output_path}")

    return summary


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage: python3 -m scripts.extract_attachments <dump_path> [output_dir]"
        )
        sys.exit(1)

    dump = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else "."
    extract_attachments(dump, output)
