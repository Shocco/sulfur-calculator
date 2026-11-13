"""Tests for scripts/extract_weapons.py."""

import pytest
from scripts.extract_weapons import parse_weapon_page


REVOLVER_WIKITEXT = """{{Item Infobox
| kind = weapon
| SubType = [[Revolvers|Revolver]]
| Ammo = [[357 Magnum]]
| Damage = 75
| RPM = 180
| Mag = 6
| Spread = 2.5
| Recoil = 4.0
| Durability = 1800
| Weight = 10
| image = Revolver.png
}}

==Available Attachments==
===Sight===
* [[Red Dot Sight]]
* [[Holographic Sight]]
===Muzzle Attachments===
* [[Suppressor]]
"""

SHOTGUN_WIKITEXT = """{{Item Infobox
| kind = weapon
| SubType = [[Shotguns|Shotgun]]
| Ammo = [[12 Gauge]]
| Damage = 40×8
| RPM = 60
| Mag = 5
| Spread = 8.0
| Recoil = 6.5
| Durability = 2000
| Weight = 18
}}

==Available Attachments==
===Muzzle Attachments===
* [[Choke]]
===Chamber Attachments===
* [[Spring Loaded Chamber]]
"""

WEAPON_WITH_GUN_CRANK_WIKITEXT = """{{Item Infobox
| kind = weapon
| SubType = [[SMGs|SMG]]
| Ammo = [[9mm]]
| Damage = 30
| RPM = 900
| Mag = 30
| Spread = 3.5
| Recoil = 2.5
| Durability = 2500
| Weight = 7
| image = SMG_Custom.png
}}

==Available Attachments==
===Sight===
* [[Iron Sight]]
===Gun Crank===
* [[Gun Crank]]
===Insurance===
* [[Insurance]]
"""

NON_WEAPON_WIKITEXT = """{{Item Infobox
| kind = attachment
| SubType = [[Muzzle Attachments|Muzzle attachment]]
| Spread = -0.75
| SellVal = 240
}}

Some description here.
"""

OIL_WIKITEXT = """{{Item Infobox
| kind = oil
| image = Action Oil.png
| GridSize = 1x1
| Recoil = +100%
| SellVal = 350
}}"""


class TestBasicWeaponParsing:
    """Tests for a standard revolver weapon page."""

    def setup_method(self):
        self.result = parse_weapon_page("Revolver", REVOLVER_WIKITEXT)

    def test_returns_dict(self):
        assert self.result is not None
        assert isinstance(self.result, dict)

    def test_id(self):
        assert self.result["id"] == "Weapon_Revolver"

    def test_name(self):
        assert self.result["name"] == "Revolver"

    def test_type_from_subtype_wikilink(self):
        assert self.result["type"] == "Revolver"

    def test_ammo_type(self):
        assert self.result["ammoType"] == "357 Magnum"

    def test_image(self):
        assert self.result["image"] == "Revolver.png"

    def test_base_damage(self):
        assert self.result["baseStats"]["Damage"] == 75.0

    def test_rpm(self):
        assert self.result["baseStats"]["RPM"] == 180.0

    def test_magazine_size(self):
        assert self.result["baseStats"]["MagazineSize"] == 6.0

    def test_spread(self):
        assert self.result["baseStats"]["Spread"] == 2.5

    def test_recoil(self):
        assert self.result["baseStats"]["Recoil"] == 4.0

    def test_durability(self):
        assert self.result["baseStats"]["Durability"] == 1800.0

    def test_max_durability_equals_durability(self):
        assert self.result["baseStats"]["MaxDurability"] == self.result["baseStats"]["Durability"]

    def test_weight(self):
        assert self.result["baseStats"]["Weight"] == 10.0

    def test_projectile_count_default(self):
        assert self.result["baseStats"]["ProjectileCount"] == 1.0

    def test_projectile_speed_default(self):
        assert self.result["baseStats"]["ProjectileSpeed"] == 100.0

    def test_move_speed_default(self):
        assert self.result["baseStats"]["MoveSpeed"] == 1.0


class TestShotgunMultiProjectile:
    """Tests for a shotgun with 40×8 damage notation."""

    def setup_method(self):
        self.result = parse_weapon_page("Pump Shotgun", SHOTGUN_WIKITEXT)

    def test_returns_dict(self):
        assert self.result is not None

    def test_id_with_spaces_replaced(self):
        assert self.result["id"] == "Weapon_Pump_Shotgun"

    def test_damage_is_per_projectile(self):
        assert self.result["baseStats"]["Damage"] == 40.0

    def test_projectile_count_is_eight(self):
        assert self.result["baseStats"]["ProjectileCount"] == 8.0

    def test_image_fallback_uses_title(self):
        # No image in infobox, so should fall back to title-based name
        assert self.result["image"] == "Pump_Shotgun.png"

    def test_ammo_type(self):
        assert self.result["ammoType"] == "12 Gauge"


class TestAllowedAttachmentsSlotExtraction:
    """Tests for allowedAttachments slot parsing."""

    def setup_method(self):
        self.revolver = parse_weapon_page("Revolver", REVOLVER_WIKITEXT)
        self.shotgun = parse_weapon_page("Pump Shotgun", SHOTGUN_WIKITEXT)

    def test_revolver_has_sight_slot(self):
        assert "sight" in self.revolver["allowedAttachments"]

    def test_revolver_has_muzzle_slot(self):
        assert "muzzle" in self.revolver["allowedAttachments"]

    def test_revolver_no_duplicate_slots(self):
        slots = self.revolver["allowedAttachments"]
        assert len(slots) == len(set(slots))

    def test_shotgun_has_muzzle_slot(self):
        assert "muzzle" in self.shotgun["allowedAttachments"]

    def test_shotgun_has_chamber_slot(self):
        assert "chamber" in self.shotgun["allowedAttachments"]

    def test_revolver_specific_attachments_empty(self):
        assert self.revolver["specificAttachments"] == []


class TestSpecificAttachments:
    """Tests for specificAttachments (individual named attachments)."""

    def setup_method(self):
        self.result = parse_weapon_page("Custom SMG", WEAPON_WITH_GUN_CRANK_WIKITEXT)

    def test_returns_dict(self):
        assert self.result is not None

    def test_gun_crank_in_specific_attachments(self):
        assert "Gun Crank" in self.result["specificAttachments"]

    def test_insurance_in_specific_attachments(self):
        assert "Insurance" in self.result["specificAttachments"]

    def test_sight_category_still_produces_slot(self):
        # Individual attachments (Gun Crank, Insurance) sit alongside ordinary
        # categories; the sight category must still produce its slot
        assert "sight" in self.result["allowedAttachments"]

    def test_specific_attachments_no_duplicates(self):
        specifics = self.result["specificAttachments"]
        assert len(specifics) == len(set(specifics))


class TestNonWeaponReturnsNone:
    """Tests that non-weapon pages return None."""

    def test_attachment_page_returns_none(self):
        result = parse_weapon_page("Suppressor", NON_WEAPON_WIKITEXT)
        assert result is None

    def test_oil_page_returns_none(self):
        result = parse_weapon_page("Action Oil", OIL_WIKITEXT)
        assert result is None

    def test_empty_page_returns_none(self):
        result = parse_weapon_page("Empty Page", "No infobox here at all.")
        assert result is None

    def test_page_without_kind_returns_none(self):
        wikitext = "{{Item Infobox\n| Damage = 50\n}}"
        result = parse_weapon_page("Unknown", wikitext)
        assert result is None


class TestIndividualChamberAttachmentAddsSlot:
    """Gun Crank / Priming Bolt must open the chamber slot.

    The UI only renders slots listed in allowedAttachments; specificAttachments
    then narrows that slot to the named item. Without the slot the item can
    never be equipped.
    """

    def test_old_format_gun_crank_heading_adds_chamber_slot(self):
        result = parse_weapon_page("Custom SMG", WEAPON_WITH_GUN_CRANK_WIKITEXT)
        assert "chamber" in result["allowedAttachments"]
        assert "Gun Crank" in result["specificAttachments"]

    def test_weapon_without_chamber_listing_has_no_chamber_slot(self):
        result = parse_weapon_page("Revolver", REVOLVER_WIKITEXT)
        assert "chamber" not in result["allowedAttachments"]

    def test_no_duplicate_slots(self):
        result = parse_weapon_page("Custom SMG", WEAPON_WITH_GUN_CRANK_WIKITEXT)
        slots = result["allowedAttachments"]
        assert len(slots) == len(set(slots))


class TestAttachmentsHeadingWithSpaces:
    """The wiki writes the heading both as ==X== and == X ==."""

    WIKITEXT = REVOLVER_WIKITEXT.split("==Available Attachments==")[0] + """
== Available Attachments ==
The weapon can accept the following [[Attachments|attachment]] types:

• [[Muzzle Attachments]]

• [[Sight|Sights]]

• [[Gun Crank]]

== Trivia ==
* [[Laser Sights]] are mentioned here but are not an attachment listing.
"""

    def setup_method(self):
        self.result = parse_weapon_page("Spaced Heading Gun", self.WIKITEXT)

    def test_slots_parsed(self):
        assert self.result["allowedAttachments"] == ["muzzle", "sight", "chamber", "insurance"]

    def test_specific_parsed(self):
        assert self.result["specificAttachments"] == ["Gun Crank"]


class TestShotsPerTrigger:
    """Arbiter 2 style weapons: Damage = 40x8x3 means three shells per trigger pull."""

    def test_third_damage_factor_is_recorded(self):
        wikitext = SHOTGUN_WIKITEXT.replace("| Damage = 40×8", "| Damage = 40&times;8&times;3")
        assert "40&times;8&times;3" in wikitext
        result = parse_weapon_page("Triple Gun", wikitext)
        assert result["shotsPerTrigger"] == 3
        assert result["baseStats"]["Damage"] == 40.0
        assert result["baseStats"]["ProjectileCount"] == 8.0

    def test_ordinary_weapon_has_no_field(self):
        result = parse_weapon_page("Revolver", REVOLVER_WIKITEXT)
        assert "shotsPerTrigger" not in result
