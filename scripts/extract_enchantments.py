"""Extract oil/enchantment data from a MediaWiki XML dump for the SULFUR calculator."""

from typing import Dict, List, Optional, Tuple

from scripts.wiki_parser import iterate_pages, parse_infobox, parse_modifier_value


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
            attribute = PARAM_TO_ATTRIBUTE[param_key]
            mod_type, value = parse_modifier_value(raw_value)
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

    for title, wikitext in iterate_pages(dump_path):
        oil = parse_oil_page(title, wikitext)
        if oil is not None:
            oils.append(oil)

    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(oils, fh, indent=2, ensure_ascii=False)

    return oils
