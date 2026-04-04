"""Extract oil/enchantment data from a MediaWiki XML dump for the SULFUR calculator."""

import re
from typing import Dict, List, Optional, Tuple

from scripts.wiki_parser import (
    extract_section,
    extract_wikilink_text,
    iterate_pages,
    parse_infobox,
    parse_modifier_value,
)


# Mapping from wiki infobox param names to JSON attribute names.
PARAM_TO_ATTRIBUTE: Dict[str, str] = {
    "Dmg": "Damage",
    "Spread": "Spread",
    "Recoil": "Recoil",
    "RPM": "RPM",
    "RldSpeed": "ReloadSpeed",
    "BltSpeed": "BulletSpeed",
    "BltBounces": "BulletBounces",
    "BltBounciness": "BulletBounciness",
    "BltDrop": "BulletDrop",
    "BltSize": "BulletSize",
    "BltPen": "BulletPenetrations",
    "Speed": "MoveSpeed",
    "CritChance": "CritChance",
    "LootChance": "LootChance",
    "ProjecAmnt": "ProjectileCount",
    "JumpPwr": "JumpPower",
    "MaxDrb": "MaxDurability",
    "AmmoConsume": "AmmoConsumeChance",
    "AmmoExConsume": "AmmoConsumeChance",
    "MoveAccuracy": "MoveAccuracy",
}

# Mapping from description bullet text labels to JSON attribute names.
# Used for parsing Equipment/Enchantment Infobox description-based modifiers.
DESCRIPTION_LABEL_TO_ATTRIBUTE: Dict[str, str] = {
    "damage": "Damage",
    "spread": "Spread",
    "recoil": "Recoil",
    "rpm": "RPM",
    "reload speed": "ReloadSpeed",
    "bullet speed": "BulletSpeed",
    "bullet bounces": "BulletBounces",
    "bullet bounciness": "BulletBounciness",
    "bullet drop": "BulletDrop",
    "bullet size": "BulletSize",
    "bullet penetrations": "BulletPenetrations",
    "bullet penetration": "BulletPenetrations",
    "move speed": "MoveSpeed",
    "movement speed": "MoveSpeed",
    "crit chance": "CritChance",
    "critical chance": "CritChance",
    "loot chance": "LootChance",
    "projectile count": "ProjectileCount",
    "projectile amount": "ProjectileCount",
    "jump power": "JumpPower",
    "max durability": "MaxDurability",
    "durability": "MaxDurability",
    "ammo consume chance": "AmmoConsumeChance",
    "move accuracy": "MoveAccuracy",
    "accuracy while moving": "MoveAccuracy",
    "fire rate": "RPM",
    "rate of fire": "RPM",
    "magazine size": "MagazineSize",
    "mag size": "MagazineSize",
    "weight": "Weight",
}

# Mapping from wiki infobox param names to special effect definitions.
# Each entry is (specialEffects_key, specialEffects_value, effects_label).
SPECIAL_EFFECTS: Dict[str, Tuple[str, bool, str]] = {
    "AimDisabled": ("disablesAiming", True, "Disables aiming"),
    "NoDrb": ("noDurability", True, "No durability loss"),
    "NoMoney": ("noMoney", True, "No money drops"),
    "NoOrgans": ("noOrgans", True, "No organ drops"),
}


def parse_oil_page(title: str, wikitext: str) -> Optional[Dict]:
    """Parse a wiki page and return an oil/enchantment JSON object if applicable.

    Args:
        title: The page title from the MediaWiki dump.
        wikitext: The raw wikitext content of the page.

    Returns:
        A dict representing the oil item, or None if the page is not an oil.

    Example output::

        {
            "id": "Action_Oil",
            "name": "Action Oil",
            "modifiers": [
                {"attribute": "Recoil", "modType": 200, "value": 1.0},
                {"attribute": "ReloadSpeed", "modType": 200, "value": 0.4}
            ]
        }
    """
    params = parse_infobox(wikitext)
    if params.get("kind") != "oil":
        return None

    modifiers: List[Dict] = []
    special_effects: Dict[str, bool] = {}
    effects: List[str] = []

    for param_key, raw_value in params.items():
        if param_key in PARAM_TO_ATTRIBUTE:
            cleaned = raw_value.strip()
            # Skip boolean/symbol values that aren't numeric modifiers
            if cleaned in ('√', '✓', '✔', '&check;', '↑', '↓', 'ᛏ'):
                continue
            # Strip leading <br> tags
            cleaned = re.sub(r'^<br\s*/?>\s*', '', cleaned)
            if not cleaned:
                continue
            attribute = PARAM_TO_ATTRIBUTE[param_key]
            mod_type, value = parse_modifier_value(cleaned)
            modifiers.append({"attribute": attribute, "modType": mod_type, "value": value})

        elif param_key in SPECIAL_EFFECTS:
            se_key, se_value, label = SPECIAL_EFFECTS[param_key]
            special_effects[se_key] = se_value
            effects.append(label)

    result: Dict = {
        "id": title.replace(" ", "_"),
        "name": title,
        "modifiers": modifiers,
    }

    if special_effects:
        result["specialEffects"] = special_effects
    if effects:
        result["effects"] = effects

    return result


def _parse_description_modifiers(wikitext: str) -> List[Dict]:
    """Parse modifier values from Description section bullet points.

    Handles formats like:
    - '''Damage: +25'''
    - '''Bullet speed: -80%'''
    - * '''Recoil: +15%'''

    Returns list of modifier dicts.
    """
    section = extract_section(wikitext, "Description")
    if not section:
        return []

    modifiers: List[Dict] = []
    for line in section.split('\n'):
        line = line.strip()
        # Strip bullet markers and bold markup
        line = line.lstrip('*\u2022\u00b7- ').strip()
        line = re.sub(r"'''|''", '', line).strip()
        if not line:
            continue

        # Match "Label: +/-value%" or "Label: +/-value"
        m = re.match(r'^(.+?):\s*([+-]?\d+(?:\.\d+)?%?)$', line)
        if not m:
            continue

        label = m.group(1).strip().lower()
        raw_value = m.group(2).strip()

        attribute = DESCRIPTION_LABEL_TO_ATTRIBUTE.get(label)
        if attribute is None:
            continue

        mod_type, value = parse_modifier_value(raw_value)
        modifiers.append({"attribute": attribute, "modType": mod_type, "value": value})

    return modifiers


def _parse_equip_or_enchant_infobox(wikitext: str) -> Optional[Dict[str, str]]:
    """Parse an Equipment Infobox or Enchantment Infobox from wikitext.

    Returns the infobox params dict, or None if not found.
    """
    for template in ('Equipment Infobox', 'Enchantment Infobox'):
        pattern = r'\{\{' + re.escape(template) + r'(.*?)\}\}'
        match = re.search(pattern, wikitext, re.DOTALL)
        if match:
            body = match.group(1)
            result: Dict[str, str] = {}
            for pm in re.finditer(r'\|\s*([\w\s]+?)\s*=\s*(.*?)(?=\n\s*\||\n\s*\}\}|$)', body, re.DOTALL):
                key = pm.group(1).strip()
                val = pm.group(2).strip()
                if val:
                    result[key] = val
            return result
    return None


def parse_oil_from_equipment_infobox(title: str, wikitext: str) -> Optional[Dict]:
    """Parse an oil from Equipment Infobox or Enchantment Infobox format.

    These templates use Type=[[Oil]] and store modifiers in Description bullets.
    """
    params = _parse_equip_or_enchant_infobox(wikitext)
    if params is None:
        return None

    raw_type = params.get('Type', '')
    type_text = extract_wikilink_text(raw_type).lower().strip()
    if type_text not in ('oil', 'oils'):
        return None

    modifiers = _parse_description_modifiers(wikitext)

    # Normalize CritChance flat values: wiki sometimes writes "+10" meaning "+10%".
    # Display code multiplies CritChance by 100, so values must be in 0-1 range.
    for mod in modifiers:
        if mod.get('attribute') == 'CritChance' and mod.get('modType') == 100 and mod.get('value', 0) > 1.0:
            mod['value'] = mod['value'] / 100.0

    result: Dict = {
        "id": title.replace(" ", "_"),
        "name": title,
        "modifiers": modifiers,
    }

    return result


def extract_enchantments(dump_path: str, output_path: str) -> List[Dict]:
    """Extract all oil/enchantment entries from a MediaWiki XML dump and write JSON.

    Args:
        dump_path: Absolute path to the MediaWiki XML dump file.
        output_path: Absolute path for the output JSON file.

    Returns:
        List of parsed oil dicts that were written to output_path.
    """
    import json

    oils: List[Dict] = []
    seen_names: set = set()

    for title, wikitext in iterate_pages(dump_path):
        # Try Item Infobox (kind=oil) first
        oil = parse_oil_page(title, wikitext)
        if oil is not None:
            oils.append(oil)
            seen_names.add(title)
            continue

        # Try Equipment/Enchantment Infobox with Type=Oil
        oil = parse_oil_from_equipment_infobox(title, wikitext)
        if oil is not None and title not in seen_names:
            oils.append(oil)
            seen_names.add(title)

    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(oils, fh, indent=2, ensure_ascii=False)

    return oils
