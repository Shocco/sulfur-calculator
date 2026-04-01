"""Extract scroll data from a MediaWiki XML dump for the SULFUR calculator."""

import html
import json
from typing import Dict, List, Optional

from scripts.wiki_parser import (
    extract_bullet_points,
    extract_section,
    iterate_pages,
    parse_infobox,
    parse_modifier_value,
)


# Mapping from wiki infobox param names to JSON attribute names (modifier params).
PARAM_TO_ATTRIBUTE: Dict[str, str] = {
    "Dmg": "Damage",
    "Spread": "Spread",
    "RPM": "RPM",
    "BltSpeed": "BulletSpeed",
    "BltBounces": "BulletBounces",
    "BltBounciness": "BulletBounciness",
    "BltDrop": "BulletDrop",
    "HSDmg": "HeadshotDamage",
}

# Special effect param names whose raw string values are stored directly in specialEffects.
SPECIAL_EFFECT_PARAMS = {
    "ConvertWpn",
    "Proc",
    "Fire",
    "Frost",
    "Poison",
    "Electrocution",
    "Stun",
    "StunArea",
    "Fear",
    "Root",
    "ShareDmg",
    "CrpsExpl",
    "DrbConsume",
    "WpnAreaDmg",
    "LinkBlt",
    "PsnCloud",
    "PsnPuddle",
    "LessForceSpd",
    "MoreDmgOnHit",
    "PenDmgMult",
    "AlwaysOrgans",
    "Drag",
    "Wet",
    "Blind",
    "AreaBlind",
    "SelfBlind",
    "SelfDmg",
    "Charm",
    "Petrify",
    "Homing",
    "Lava",
    "OilPuddle",
    "Oily",
    "FrostPuddle",
    "ElecArea",
    "Explosion",
    "RocketBlt",
    "LifeTime",
    "Swap",
}


def parse_scroll_page(title: str, wikitext: str) -> Optional[Dict]:
    """Parse a wiki page and return a scroll JSON object if applicable.

    Args:
        title: The page title from the MediaWiki dump.
        wikitext: The raw wikitext content of the page.

    Returns:
        A dict representing the scroll item, or None if the page is not a scroll.

    Example output::

        {
            "id": "Scroll_of_X",
            "name": "Scroll of X",
            "modifiers": [
                {"attribute": "Damage", "modType": 200, "value": -0.86},
                {"attribute": "Spread", "modType": 200, "value": 1.5}
            ],
            "specialEffects": {"ConvertWpn": "Flamethrower"},
            "effects": ["Converts weapon to Flamethrower"]
        }
    """
    params = parse_infobox(wikitext)
    if params.get("kind") != "scroll":
        return None

    has_dark_dmg = "DarkDmg" in params

    modifiers: List[Dict] = []
    special_effects: Dict = {}

    for param_key, raw_value in params.items():
        # --- BltSize: goes to both specialEffects and modifiers ---
        if param_key == "BltSize":
            unescaped = html.unescape(raw_value)
            special_effects["BltSize"] = unescaped
            mod_type, value = parse_modifier_value(raw_value)
            modifiers.append({"attribute": "BulletSize", "modType": mod_type, "value": value})
            continue

        # --- DarkDmg special handling ---
        if param_key == "DarkDmg":
            special_effects["bypassPercentages"] = True
            continue

        # --- Dmg: behaviour changes when DarkDmg is present ---
        if param_key == "Dmg":
            if has_dark_dmg:
                # perBulletDamage = int of the raw Dmg value; modifier becomes Flat(100)
                try:
                    per_bullet = int(float(raw_value.lstrip("+")))
                except ValueError:
                    per_bullet = 0
                special_effects["perBulletDamage"] = per_bullet
                modifiers.append({"attribute": "Damage", "modType": 100, "value": 100.0})
            else:
                mod_type, value = parse_modifier_value(raw_value)
                modifiers.append({"attribute": "Damage", "modType": mod_type, "value": value})
            continue

        # --- Regular modifier params ---
        if param_key in PARAM_TO_ATTRIBUTE:
            attribute = PARAM_TO_ATTRIBUTE[param_key]
            mod_type, value = parse_modifier_value(raw_value)
            modifiers.append({"attribute": attribute, "modType": mod_type, "value": value})
            continue

        # --- Special effect string params ---
        if param_key in SPECIAL_EFFECT_PARAMS:
            special_effects[param_key] = html.unescape(raw_value)
            continue

    # Extract effects from the Description section bullet points.
    effects: List[str] = []
    description_section = extract_section(wikitext, "Description")
    if description_section:
        effects = extract_bullet_points(description_section)

    result: Dict = {
        "id": title.replace(" ", "_"),
        "name": title,
        "modifiers": modifiers,
        "specialEffects": special_effects,
        "effects": effects,
    }

    return result


def extract_scrolls(dump_path: str, output_path: str) -> List[Dict]:
    """Extract all scroll entries from a MediaWiki XML dump and write JSON.

    Args:
        dump_path: Absolute path to the MediaWiki XML dump file.
        output_path: Absolute path for the output JSON file.

    Returns:
        List of parsed scroll dicts that were written to output_path.
    """
    scrolls: List[Dict] = []

    for title, wikitext in iterate_pages(dump_path):
        scroll = parse_scroll_page(title, wikitext)
        if scroll is not None:
            scrolls.append(scroll)

    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(scrolls, fh, indent=2, ensure_ascii=False)

    return scrolls
