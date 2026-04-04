"""Tests for new wiki format parsers added in the April 2026 dump update.

Covers:
- Weapon attachment parsing with • (U+2022) bullet format (flat, no sub-headings)
- Enchantment parsing from Equipment/Enchantment Infobox templates
- Scroll parsing from Equipment/Enchantment Infobox templates
- Merge logic in update_all._merge_array_data
"""

import pytest

from scripts.extract_weapons import parse_weapon_page
from scripts.extract_enchantments import (
    parse_oil_from_equipment_infobox,
    _parse_description_modifiers,
)
from scripts.extract_scrolls import parse_scroll_from_equipment_infobox
from scripts.update_all import _merge_array_data


# ---------------------------------------------------------------------------
# Weapon attachments: • bullet flat format
# ---------------------------------------------------------------------------

WEAPON_BULLET_DOT_FLAT = """\
{{Item Infobox
| kind = weapon
| SubType = [[Rifles|Rifle]]
| Ammo = [[5.56mm]]
| Damage = 80
| RPM = 450
| Mag = 15
| Spread = 2.0
| Recoil = 1.5
| Durability = 2000
| Weight = 8
}}

==Available Attachments==
The weapon can accept the following [[Attachments|attachment]] types:

\u2022 [[Muzzle Attachments]]

\u2022 [[Sight|Sights]]

\u2022 [[Laser Sights]]

\u2022 [[Gun Crank]]

\u2022 [[Chamber Chisel|Chamber Chisels]]
"""

WEAPON_BULLET_DOT_MIXED = """\
{{Item Infobox
| kind = weapon
| SubType = [[Snipers|Sniper]]
| Ammo = [[7.62mm]]
| Damage = 400
| RPM = 100
| Mag = 6
| Spread = 1.0
| Recoil = 8.0
| Durability = 700
| Weight = 25
}}

==Available Attachments==

\u2022 [[Muzzle Attachments]]

\u2022 [[Sight|Sights]]

\u2022 [[Laser Sights]]

\u2022 [[Chamber Chisel|Chamber Chisels]]

\u2022 [[Priming Bolt]]
"""


class TestWeaponBulletDotFlatFormat:
    """Weapon pages using • bullets with flat category list (no sub-headings)."""

    def setup_method(self):
        self.result = parse_weapon_page("Test Rifle", WEAPON_BULLET_DOT_FLAT)

    def test_returns_dict(self):
        assert self.result is not None

    def test_muzzle_slot(self):
        assert "muzzle" in self.result["allowedAttachments"]

    def test_sight_slot(self):
        assert "sight" in self.result["allowedAttachments"]

    def test_laser_slot(self):
        assert "laser" in self.result["allowedAttachments"]

    def test_chisel_slot(self):
        assert "chisel" in self.result["allowedAttachments"]

    def test_gun_crank_specific(self):
        assert "Gun Crank" in self.result["specificAttachments"]

    def test_no_duplicate_slots(self):
        slots = self.result["allowedAttachments"]
        assert len(slots) == len(set(slots))


class TestWeaponBulletDotWithPrimingBolt:
    """Weapon with Priming Bolt (individual attachment in flat • format)."""

    def setup_method(self):
        self.result = parse_weapon_page("Test Sniper", WEAPON_BULLET_DOT_MIXED)

    def test_priming_bolt_in_specific(self):
        assert "Priming Bolt" in self.result["specificAttachments"]

    def test_has_muzzle_slot(self):
        assert "muzzle" in self.result["allowedAttachments"]

    def test_has_chisel_slot(self):
        assert "chisel" in self.result["allowedAttachments"]


class TestWeaponOldFormatStillWorks:
    """Ensure the old asterisk-based sub-heading format still works."""

    WIKITEXT = """\
{{Item Infobox
| kind = weapon
| SubType = [[Pistols|Pistol]]
| Ammo = [[9mm]]
| Damage = 60
| RPM = 400
| Mag = 12
| Spread = 2.0
| Recoil = 2.0
| Durability = 1500
| Weight = 5
}}

==Available Attachments==
===Muzzle Attachments===
* [[Suppressor]]
===Sight===
* [[Red Dot]]
===Gun Crank===
* [[Gun Crank]]
"""

    def test_muzzle_in_allowed(self):
        result = parse_weapon_page("Old Pistol", self.WIKITEXT)
        assert "muzzle" in result["allowedAttachments"]

    def test_sight_in_allowed(self):
        result = parse_weapon_page("Old Pistol", self.WIKITEXT)
        assert "sight" in result["allowedAttachments"]

    def test_gun_crank_in_specific(self):
        result = parse_weapon_page("Old Pistol", self.WIKITEXT)
        assert "Gun Crank" in result["specificAttachments"]


class TestWeaponNoAttachmentSection:
    """Weapon with no Available Attachments section at all."""

    WIKITEXT = """\
{{Item Infobox
| kind = weapon
| SubType = [[Pistols|Pistol]]
| Ammo = [[9mm]]
| Damage = 50
| RPM = 600
| Mag = 10
| Spread = 3.0
| Recoil = 2.0
| Durability = 1200
| Weight = 4
}}
"""

    def test_empty_allowed_attachments(self):
        result = parse_weapon_page("Bare Pistol", self.WIKITEXT)
        assert result["allowedAttachments"] == []

    def test_empty_specific_attachments(self):
        result = parse_weapon_page("Bare Pistol", self.WIKITEXT)
        assert result["specificAttachments"] == []


# ---------------------------------------------------------------------------
# Enchantments: Equipment Infobox / Enchantment Infobox
# ---------------------------------------------------------------------------


class TestParseDescriptionModifiers:
    """Test _parse_description_modifiers for various bullet formats."""

    def test_flat_damage_modifier(self):
        wikitext = """== Description ==
* '''Damage: +25'''
"""
        mods = _parse_description_modifiers(wikitext)
        assert len(mods) == 1
        assert mods[0]["attribute"] == "Damage"
        assert mods[0]["modType"] == 100
        assert mods[0]["value"] == pytest.approx(25.0)

    def test_percent_modifier(self):
        wikitext = """== Description ==
* '''Bullet speed: -80%'''
"""
        mods = _parse_description_modifiers(wikitext)
        assert len(mods) == 1
        assert mods[0]["attribute"] == "BulletSpeed"
        assert mods[0]["modType"] == 200
        assert mods[0]["value"] == pytest.approx(-0.8)

    def test_multiple_modifiers(self):
        wikitext = """== Description ==
* '''Damage: +15'''
* '''Spread: -20%'''
* '''Recoil: +30%'''
"""
        mods = _parse_description_modifiers(wikitext)
        assert len(mods) == 3
        attrs = {m["attribute"] for m in mods}
        assert attrs == {"Damage", "Spread", "Recoil"}

    def test_no_description_section(self):
        mods = _parse_description_modifiers("Just some text, no section.")
        assert mods == []

    def test_non_modifier_lines_ignored(self):
        wikitext = """== Description ==
'''Elemental enchantment'''
''Adds a chance of spawning a bolt.''
"""
        mods = _parse_description_modifiers(wikitext)
        assert mods == []

    def test_unicode_bullet_markers(self):
        wikitext = """== Description ==
\u2022 '''Damage: +10'''
"""
        mods = _parse_description_modifiers(wikitext)
        assert len(mods) == 1
        assert mods[0]["attribute"] == "Damage"


class TestParseOilFromEquipmentInfobox:
    """Test parsing oils from Equipment/Enchantment Infobox templates."""

    def test_basic_equipment_infobox_oil(self):
        wikitext = """\
{{Equipment Infobox
|Grid Size=1x1
|Value= 250
|Type=[[Oil]]
}}
== Description ==
* '''Damage: +25'''
"""
        result = parse_oil_from_equipment_infobox("Add Damage Oil", wikitext)
        assert result is not None
        assert result["name"] == "Add Damage Oil"
        assert result["id"] == "Add_Damage_Oil"
        assert len(result["modifiers"]) == 1
        assert result["modifiers"][0]["attribute"] == "Damage"

    def test_enchantment_infobox_oil(self):
        wikitext = """\
{{Enchantment Infobox
|Grid Size=1x1
|Value= 500
|Type=[[Oil]]
}}
== Description ==
* '''Recoil: -15%'''
"""
        result = parse_oil_from_equipment_infobox("Steady Oil", wikitext)
        assert result is not None
        assert len(result["modifiers"]) == 1
        assert result["modifiers"][0]["attribute"] == "Recoil"
        assert result["modifiers"][0]["modType"] == 200

    def test_non_oil_type_returns_none(self):
        wikitext = """\
{{Equipment Infobox
|Type=[[Scroll Enchantment]]
}}
"""
        result = parse_oil_from_equipment_infobox("Scroll of X", wikitext)
        assert result is None

    def test_no_infobox_returns_none(self):
        result = parse_oil_from_equipment_infobox("Random", "No infobox here.")
        assert result is None

    def test_oil_with_no_modifiers(self):
        wikitext = """\
{{Equipment Infobox
|Grid Size=1x1
|Type=[[Oil]]
}}
== Description ==
'''Special effect oil'''
''Does something unique.''
"""
        result = parse_oil_from_equipment_infobox("Mystery Oil", wikitext)
        assert result is not None
        assert result["modifiers"] == []


# ---------------------------------------------------------------------------
# Scrolls: Equipment Infobox / Enchantment Infobox
# ---------------------------------------------------------------------------


class TestParseScrollFromEquipmentInfobox:
    """Test parsing scrolls from Equipment/Enchantment Infobox templates."""

    def test_basic_scroll(self):
        wikitext = """\
{{Equipment Infobox
|Grid Size=1x2
|Value= 2000
|Type=[[Scroll Enchantment]]
}}
== Description ==
'''Elemental enchantment'''
''Adds a chance of spawning a bolt that electrocutes and spreads to nearby enemies.''
"""
        result = parse_scroll_from_equipment_infobox("Scroll of Chain Lightning", wikitext)
        assert result is not None
        assert result["name"] == "Scroll of Chain Lightning"
        assert result["id"] == "Scroll_of_Chain_Lightning"
        assert result["modifiers"] == []
        assert result["specialEffects"] == {}
        assert len(result["effects"]) > 0

    def test_enchantment_infobox_scroll(self):
        wikitext = """\
{{Enchantment Infobox
|Grid Size=1x2
|Value= 1500
|Type=[[Scroll Enchantment]]
}}
== Description ==
* Fire effect applied on hit
"""
        result = parse_scroll_from_equipment_infobox("Scroll of Fire", wikitext)
        assert result is not None
        assert "Fire effect" in result["effects"][0]

    def test_non_scroll_type_returns_none(self):
        wikitext = """\
{{Equipment Infobox
|Type=[[Oil]]
}}
"""
        result = parse_scroll_from_equipment_infobox("Some Oil", wikitext)
        assert result is None

    def test_no_infobox_returns_none(self):
        result = parse_scroll_from_equipment_infobox("Random", "No infobox.")
        assert result is None

    def test_scroll_with_bullet_effects(self):
        wikitext = """\
{{Equipment Infobox
|Type=[[Scroll Enchantment]]
}}
== Description ==
* Enemies hit have a 10% chance to freeze
* Frozen enemies take 50% more damage
"""
        result = parse_scroll_from_equipment_infobox("Scroll of Frost", wikitext)
        assert result is not None
        assert len(result["effects"]) == 2


# ---------------------------------------------------------------------------
# Merge logic: _merge_array_data
# ---------------------------------------------------------------------------


class TestMergeArrayData:
    """Test the merge strategy for combining new and old extracted data."""

    def test_keeps_new_items(self):
        new = [{"name": "A", "value": 1}]
        old = [{"name": "A", "value": 2}]
        merged = _merge_array_data(new, old)
        item = next(i for i in merged if i["name"] == "A")
        assert item["value"] == 1

    def test_adds_old_only_items(self):
        new = [{"name": "A", "value": 1}]
        old = [{"name": "A", "value": 1}, {"name": "B", "value": 2}]
        merged = _merge_array_data(new, old)
        assert len(merged) == 2
        names = {i["name"] for i in merged}
        assert names == {"A", "B"}

    def test_fills_empty_lists_from_old(self):
        new = [{"name": "Gun", "allowedAttachments": [], "damage": 50}]
        old = [{"name": "Gun", "allowedAttachments": ["muzzle", "sight"], "damage": 40}]
        merged = _merge_array_data(new, old)
        item = next(i for i in merged if i["name"] == "Gun")
        assert item["allowedAttachments"] == ["muzzle", "sight"]
        assert item["damage"] == 50  # new value kept

    def test_fills_zeroed_base_stats(self):
        new = [{"name": "Gun", "baseStats": {"Damage": 0.0, "RPM": 500.0, "Recoil": 0.0}}]
        old = [{"name": "Gun", "baseStats": {"Damage": 40.0, "RPM": 400.0, "Recoil": 10.0}}]
        merged = _merge_array_data(new, old)
        item = next(i for i in merged if i["name"] == "Gun")
        assert item["baseStats"]["Damage"] == 40.0  # filled from old
        assert item["baseStats"]["RPM"] == 500.0  # kept new (non-zero)
        assert item["baseStats"]["Recoil"] == 10.0  # filled from old

    def test_does_not_fill_intentionally_zero_stats(self):
        """If both old and new have 0.0, it stays 0.0."""
        new = [{"name": "Gun", "baseStats": {"Weight": 0.0}}]
        old = [{"name": "Gun", "baseStats": {"Weight": 0.0}}]
        merged = _merge_array_data(new, old)
        item = next(i for i in merged if i["name"] == "Gun")
        assert item["baseStats"]["Weight"] == 0.0

    def test_preserves_new_only_items(self):
        new = [{"name": "NewGun", "damage": 100}]
        old = [{"name": "OldGun", "damage": 50}]
        merged = _merge_array_data(new, old)
        assert len(merged) == 2

    def test_no_duplicates(self):
        new = [{"name": "A"}, {"name": "B"}]
        old = [{"name": "B"}, {"name": "C"}]
        merged = _merge_array_data(new, old)
        names = [i["name"] for i in merged]
        assert len(names) == len(set(names))

    def test_empty_new_returns_all_old(self):
        old = [{"name": "A"}, {"name": "B"}]
        merged = _merge_array_data([], old)
        assert len(merged) == 2

    def test_empty_old_returns_all_new(self):
        new = [{"name": "A"}, {"name": "B"}]
        merged = _merge_array_data(new, [])
        assert len(merged) == 2

    def test_non_empty_list_not_overwritten(self):
        """If new already has attachment data, don't replace with old."""
        new = [{"name": "Gun", "allowedAttachments": ["muzzle"]}]
        old = [{"name": "Gun", "allowedAttachments": ["muzzle", "sight", "laser"]}]
        merged = _merge_array_data(new, old)
        item = next(i for i in merged if i["name"] == "Gun")
        assert item["allowedAttachments"] == ["muzzle"]  # kept new, not overwritten
