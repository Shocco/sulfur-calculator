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
    parse_modifier_value,
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
# Equipment Infobox type -> slot mapping
# ---------------------------------------------------------------------------

EQUIP_TYPE_TO_SLOT: Dict[str, str] = {
    "muzzle attachments": "muzzle",
    "muzzle": "muzzle",
    "sight": "sight",
    "sights": "sight",
    "laser sights": "laser",
    "laser sight": "laser",
    "chamber attachment": "chamber",
    "chamber attachments": "chamber",
    "attachment": "insurance",
}

# Equipment Infobox bare-line stat name -> attribute name
EQUIP_STAT_MAP: Dict[str, str] = {
    "spread": "Spread",
    "move speed": "MoveSpeed",
    "recoil": "Recoil",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_equipment_infoboxes(wikitext: str) -> List[Dict]:
    """Parse all {{Equipment Infobox ...}} blocks from a page.

    Returns a list of dicts, one per infobox, with parsed fields.
    """
    results = []
    for m in re.finditer(r'\{\{Equipment Infobox(.*?)\}\}', wikitext, re.DOTALL):
        body = m.group(1)
        info: Dict = {}

        # Parse |key=value params
        for pm in re.finditer(r'\|\s*([\w\s]+?)\s*=\s*(.*?)(?=\n\s*\||\n[A-Z]|$)', body, re.DOTALL):
            key = pm.group(1).strip()
            val = pm.group(2).strip()
            if val:
                info[key] = val

        # Parse bare "Key: value" or "Key value" stat lines
        for pm in re.finditer(r'^([A-Z][\w\s]+?):\s*(.+)$', body, re.MULTILINE):
            key = pm.group(1).strip()
            val = pm.group(2).strip()
            info['stat_' + key] = val

        results.append(info)
    return results


def _parse_misc_item_infobox(wikitext: str) -> Optional[Dict]:
    """Parse a {{Misc Item Infobox ...}} block.

    Returns a dict with parsed fields, or None if not found.
    """
    m = re.search(r'\{\{Misc Item Infobox(.*?)\}\}', wikitext, re.DOTALL)
    if not m:
        return None
    body = m.group(1)
    info: Dict = {}
    for pm in re.finditer(r'\|\s*([\w\s]+?)\s*=\s*(.*?)(?=\n\s*\||\n\s*\}\}|$)', body, re.DOTALL):
        key = pm.group(1).strip()
        val = pm.group(2).strip()
        if val:
            info[key] = val
    return info


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


def parse_equipment_attachment(title: str, wikitext: str) -> List[Dict]:
    """Parse Equipment Infobox attachments from a page.

    A single page may contain multiple Equipment Infobox blocks (e.g. variants).
    Returns a list of attachment dicts.
    """
    if '{{Equipment Infobox' not in wikitext:
        return []
    if 'Category:Attachments' not in wikitext:
        return []

    infoboxes = _parse_equipment_infoboxes(wikitext)
    description = _first_description_line(wikitext)
    results = []

    for info in infoboxes:
        # Determine slot from Type field
        raw_type = info.get('Type', '')
        type_text = extract_wikilink_text(raw_type).lower().strip()
        slot = EQUIP_TYPE_TO_SLOT.get(type_text)
        if slot is None:
            continue

        # Name: use title field or page title
        name = info.get('title', title)

        # Modifiers from |key=value params
        modifiers: Dict[str, Union[float, Dict]] = {}

        raw_spread = info.get('Spread', '')
        if raw_spread:
            try:
                modifiers['Spread'] = float(raw_spread)
            except ValueError:
                pass

        raw_crit = info.get('CritADS', '')
        if raw_crit:
            raw_crit = raw_crit.strip().rstrip('%')
            try:
                modifiers['ADSCritChance'] = float(raw_crit)
            except ValueError:
                pass

        # Modifiers from bare stat lines
        for stat_key, body_val in info.items():
            if not stat_key.startswith('stat_'):
                continue
            stat_name = stat_key[5:].lower()
            attr = EQUIP_STAT_MAP.get(stat_name)
            if attr and attr not in modifiers:
                body_val = body_val.strip()
                if '%' in body_val:
                    pct_str = body_val.replace('%', '').strip()
                    try:
                        modifiers[attr] = float(pct_str)
                    except ValueError:
                        pass
                else:
                    try:
                        modifiers[attr] = float(body_val)
                    except ValueError:
                        pass

        # Special effects
        special_effects: Dict = {}

        # Silencer detection from name
        if 'silencer' in name.lower():
            special_effects['silencesFire'] = True

        # Image
        raw_image = info.get('image', '')
        image_name = raw_image if raw_image else name.replace(' ', '_') + '.png'
        image = f'/images/attachments/{image_name}'

        rarity = KNOWN_RARITIES.get(name, DEFAULT_RARITY)

        results.append({
            'id': name.replace(' ', '_'),
            'name': name,
            'type': slot,
            'rarity': rarity,
            'modifiers': modifiers,
            'specialEffects': special_effects,
            'description': description,
            'image': image,
        })

    return results


def parse_chisel_from_misc_infobox(title: str, wikitext: str) -> Optional[Dict]:
    """Parse a chisel from {{Misc Item Infobox}} format.

    Returns a chisel dict or None.
    """
    if '{{Misc Item Infobox' not in wikitext:
        return None
    if 'Chamber Chisel' not in title:
        return None

    info = _parse_misc_item_infobox(wikitext)
    if info is None:
        return None

    name = info.get('title', title)

    # Extract caliber from title: "Chamber Chisel (9mm)" -> "9mm"
    cal_match = re.search(r'\(([^)]+)\)', name)
    caliber = _normalize_caliber(cal_match.group(1)) if cal_match else ''

    description = CHISEL_DESCRIPTIONS.get(caliber, _first_description_line(wikitext))

    raw_image = info.get('image', '')
    image_name = raw_image if raw_image else name.replace(' ', '_') + '.png'
    image = f'/images/attachments/{image_name}'

    rarity = KNOWN_RARITIES.get(name, DEFAULT_RARITY)

    result: Dict = {
        'id': name.replace(' ', '_'),
        'name': name,
        'type': 'chisel',
        'rarity': rarity,
        'modifiers': {},
        'specialEffects': {},
        'description': description,
        'image': image,
    }

    if caliber:
        result['specialEffects']['caliberConversion'] = caliber

    return result


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
        # Try old Item Infobox format first
        params = parse_infobox(wikitext)
        kind = params.get("kind", "").strip().lower()

        if kind == "chisel":
            item = parse_chisel_page(title, wikitext)
            if item is not None:
                by_slot["chisel"].append(item)
                continue
        elif kind == "attachment":
            item = parse_attachment_page(title, wikitext)
            if item is not None:
                slot = item["type"]
                if slot in by_slot:
                    by_slot[slot].append(item)
                continue

        # Try new Equipment Infobox format
        equip_items = parse_equipment_attachment(title, wikitext)
        for item in equip_items:
            slot = item["type"]
            if slot in by_slot:
                by_slot[slot].append(item)

        # Try Misc Item Infobox format (chisels)
        if not equip_items:
            chisel = parse_chisel_from_misc_infobox(title, wikitext)
            if chisel is not None:
                by_slot["chisel"].append(chisel)

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
