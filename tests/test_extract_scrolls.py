"""Tests for scripts/extract_scrolls.py."""

import json
import os
import tempfile
import xml.etree.ElementTree as ET

import pytest

from scripts.extract_scrolls import extract_scrolls, parse_scroll_page


# ---------------------------------------------------------------------------
# Helpers for building minimal MediaWiki XML dumps used in integration tests
# ---------------------------------------------------------------------------

_MW_NS = "http://www.mediawiki.org/xml/export-0.11/"


def _build_dump(pages: list[tuple[str, str]]) -> str:
    """Return a minimal MediaWiki XML dump string containing the given pages.

    Args:
        pages: List of (title, wikitext) tuples.

    Returns:
        XML string suitable for passing to extract_scrolls().
    """
    root = ET.Element(f"{{{_MW_NS}}}mediawiki")
    for title, wikitext in pages:
        page_elem = ET.SubElement(root, f"{{{_MW_NS}}}page")
        title_elem = ET.SubElement(page_elem, f"{{{_MW_NS}}}title")
        title_elem.text = title
        rev_elem = ET.SubElement(page_elem, f"{{{_MW_NS}}}revision")
        text_elem = ET.SubElement(rev_elem, f"{{{_MW_NS}}}text")
        text_elem.text = wikitext
    return ET.tostring(root, encoding="unicode")


# ---------------------------------------------------------------------------
# Unit tests for parse_scroll_page
# ---------------------------------------------------------------------------


class TestParseScrollPageBasic:
    """Basic scroll with Proc and StunArea special effects and no modifiers."""

    WIKITEXT = """\
{{Item Infobox
| kind = scroll
| Proc = 25%
| StunArea = 3m
| SellVal = 1200
}}

==Description==
* Bullets have a 25% chance to stun nearby enemies
* Stun radius 3m
"""

    def test_returns_dict_not_none(self):
        result = parse_scroll_page("Scroll of Stun", self.WIKITEXT)
        assert result is not None

    def test_id_replaces_spaces(self):
        result = parse_scroll_page("Scroll of Stun", self.WIKITEXT)
        assert result["id"] == "Scroll_of_Stun"

    def test_name_preserved(self):
        result = parse_scroll_page("Scroll of Stun", self.WIKITEXT)
        assert result["name"] == "Scroll of Stun"

    def test_no_modifiers(self):
        result = parse_scroll_page("Scroll of Stun", self.WIKITEXT)
        assert result["modifiers"] == []

    def test_special_effects_proc(self):
        result = parse_scroll_page("Scroll of Stun", self.WIKITEXT)
        assert result["specialEffects"]["Proc"] == "25%"

    def test_special_effects_stun_area(self):
        result = parse_scroll_page("Scroll of Stun", self.WIKITEXT)
        assert result["specialEffects"]["StunArea"] == "3m"

    def test_effects_from_description(self):
        result = parse_scroll_page("Scroll of Stun", self.WIKITEXT)
        assert len(result["effects"]) == 2
        assert "25% chance to stun nearby enemies" in result["effects"][0]
        assert "Stun radius 3m" in result["effects"][1]


class TestParseScrollPageConvert:
    """Scroll that converts weapon type with multiple modifiers."""

    WIKITEXT = """\
{{Item Infobox
| kind = scroll
| ConvertWpn = Flamethrower
| Dmg = -86%
| Spread = +150%
| BltSpeed = -70%
| SellVal = 2500
}}
"""

    def test_returns_dict(self):
        result = parse_scroll_page("Scroll of Flame", self.WIKITEXT)
        assert result is not None

    def test_convert_wpn_in_special_effects(self):
        result = parse_scroll_page("Scroll of Flame", self.WIKITEXT)
        assert result["specialEffects"]["ConvertWpn"] == "Flamethrower"

    def test_dmg_modifier(self):
        result = parse_scroll_page("Scroll of Flame", self.WIKITEXT)
        dmg_mod = next(m for m in result["modifiers"] if m["attribute"] == "Damage")
        assert dmg_mod["modType"] == 200
        assert abs(dmg_mod["value"] - (-0.86)) < 1e-9

    def test_spread_modifier(self):
        result = parse_scroll_page("Scroll of Flame", self.WIKITEXT)
        spread_mod = next(m for m in result["modifiers"] if m["attribute"] == "Spread")
        assert spread_mod["modType"] == 200
        assert abs(spread_mod["value"] - 1.5) < 1e-9

    def test_blt_speed_modifier(self):
        result = parse_scroll_page("Scroll of Flame", self.WIKITEXT)
        spd_mod = next(m for m in result["modifiers"] if m["attribute"] == "BulletSpeed")
        assert spd_mod["modType"] == 200
        assert abs(spd_mod["value"] - (-0.70)) < 1e-9

    def test_empty_effects_when_no_description(self):
        result = parse_scroll_page("Scroll of Flame", self.WIKITEXT)
        assert result["effects"] == []


class TestParseScrollPageDarkDamage:
    """Scroll with DarkDmg: bypasses percentages and uses flat damage modifier."""

    WIKITEXT = """\
{{Item Infobox
| kind = scroll
| DarkDmg = 1
| BltSize = +100%
| Dmg = +50
| SellVal = 3000
}}
"""

    def test_bypass_percentages_set(self):
        result = parse_scroll_page("Scroll of Darkness", self.WIKITEXT)
        assert result["specialEffects"]["bypassPercentages"] is True

    def test_per_bullet_damage(self):
        result = parse_scroll_page("Scroll of Darkness", self.WIKITEXT)
        assert result["specialEffects"]["perBulletDamage"] == 50

    def test_dmg_modifier_is_flat_100(self):
        result = parse_scroll_page("Scroll of Darkness", self.WIKITEXT)
        dmg_mod = next(m for m in result["modifiers"] if m["attribute"] == "Damage")
        assert dmg_mod["modType"] == 100
        assert dmg_mod["value"] == 100.0

    def test_blt_size_in_special_effects(self):
        result = parse_scroll_page("Scroll of Darkness", self.WIKITEXT)
        assert result["specialEffects"]["BltSize"] == "+100%"

    def test_blt_size_in_modifiers(self):
        result = parse_scroll_page("Scroll of Darkness", self.WIKITEXT)
        size_mod = next(m for m in result["modifiers"] if m["attribute"] == "BulletSize")
        assert size_mod["modType"] == 200
        assert abs(size_mod["value"] - 1.0) < 1e-9


class TestParseScrollPageEffects:
    """Effects extracted from Description section bullet points."""

    WIKITEXT = """\
{{Item Infobox
| kind = scroll
| RPM = +20%
}}

==Description==
* Increases fire rate by 20%
* '''Bold effect''' description
* Third effect

==Lore==
Some lore text here.
"""

    def test_effects_count(self):
        result = parse_scroll_page("Scroll of Speed", self.WIKITEXT)
        assert len(result["effects"]) == 3

    def test_bold_markup_stripped(self):
        result = parse_scroll_page("Scroll of Speed", self.WIKITEXT)
        assert "Bold effect" in result["effects"][1]
        assert "'''" not in result["effects"][1]

    def test_lore_section_not_included(self):
        result = parse_scroll_page("Scroll of Speed", self.WIKITEXT)
        for effect in result["effects"]:
            assert "lore" not in effect.lower()


class TestParseScrollPageNonScroll:
    """Non-scroll pages must return None."""

    def test_oil_page_returns_none(self):
        wikitext = """\
{{Item Infobox
| kind = oil
| Recoil = +100%
| SellVal = 350
}}
"""
        result = parse_scroll_page("Action Oil", wikitext)
        assert result is None

    def test_weapon_page_returns_none(self):
        wikitext = """\
{{Item Infobox
| kind = weapon
| Damage = 60
| RPM = 800
}}
"""
        result = parse_scroll_page("Some Pistol", wikitext)
        assert result is None

    def test_no_infobox_returns_none(self):
        wikitext = "Just some plain text with no infobox."
        result = parse_scroll_page("Random Page", wikitext)
        assert result is None


# ---------------------------------------------------------------------------
# Integration test for extract_scrolls (uses temp XML dump + output file)
# ---------------------------------------------------------------------------


class TestExtractScrolls:
    """Integration tests for extract_scrolls() reading a real XML dump."""

    SCROLL_WIKITEXT = """\
{{Item Infobox
| kind = scroll
| Proc = 10%
| Dmg = +20%
| SellVal = 800
}}

==Description==
* Bullets deal bonus damage
"""

    OIL_WIKITEXT = """\
{{Item Infobox
| kind = oil
| Recoil = +50%
}}
"""

    def test_only_scrolls_extracted(self, tmp_path):
        dump_content = _build_dump([
            ("Scroll of Power", self.SCROLL_WIKITEXT),
            ("Some Oil", self.OIL_WIKITEXT),
        ])
        dump_path = tmp_path / "dump.xml"
        dump_path.write_text(dump_content, encoding="utf-8")
        output_path = tmp_path / "scrolls.json"

        result = extract_scrolls(str(dump_path), str(output_path))

        assert len(result) == 1
        assert result[0]["name"] == "Scroll of Power"

    def test_output_json_valid(self, tmp_path):
        dump_content = _build_dump([
            ("Scroll of Power", self.SCROLL_WIKITEXT),
        ])
        dump_path = tmp_path / "dump.xml"
        dump_path.write_text(dump_content, encoding="utf-8")
        output_path = tmp_path / "scrolls.json"

        extract_scrolls(str(dump_path), str(output_path))

        with open(output_path, encoding="utf-8") as fh:
            data = json.load(fh)

        assert isinstance(data, list)
        assert data[0]["id"] == "Scroll_of_Power"
        assert any(m["attribute"] == "Damage" for m in data[0]["modifiers"])


# ---------------------------------------------------------------------------
# Modifier params that scrolls share with oils (infoboxes copied from the wiki)
# ---------------------------------------------------------------------------

BEAM_WIKITEXT = """{{Item Infobox
| kind = scroll
| GridSize = 1&times;2
| ConvertWpn = Beam Gun
| RPM = +900%
| Dmg = -90%
| Recoil = -70%
| Spread = +100%
| SellVal = 500
}}"""

LIGHT_WIKITEXT = """{{Item Infobox
| kind = scroll
| GridSize = 1&times;2
| ConvertWpn = Railgun
| RPM = -25%
| BltPen = +999
| PenDmgMult = <br>-50%
| SellVal = 500
}}"""

MEGA_SOAKER_WIKITEXT = """{{Item Infobox
| kind = scroll
| ConvertWpn = Mega Soaker
| Dmg = -99%
| AmmoConsume = <br>-200%
| Knockback = +10
| SellVal = 500
}}"""

SACRED_GROUND_WIKITEXT = """{{Item Infobox
| kind = scroll
| GridSize = 1&times;2
| Damage = -50%
| DrbConsume = +1
| SellVal = 500
}}"""


def _modifier(scroll, attribute):
    matches = [m for m in scroll["modifiers"] if m["attribute"] == attribute]
    assert len(matches) == 1, f"expected one {attribute} modifier, got {matches}"
    return matches[0]


class TestParseScrollPageSharedModifierParams:
    """Recoil, BltPen, AmmoConsume and the long-form Damage param are modifiers."""

    def test_recoil_percent(self):
        mod = _modifier(parse_scroll_page("Scroll of Beam", BEAM_WIKITEXT), "Recoil")
        assert (mod["modType"], mod["value"]) == (200, -0.7)

    def test_bullet_penetrations_flat(self):
        mod = _modifier(parse_scroll_page("Scroll of Light", LIGHT_WIKITEXT), "BulletPenetrations")
        assert (mod["modType"], mod["value"]) == (100, 999.0)

    def test_ammo_consume_with_leading_br(self):
        mod = _modifier(parse_scroll_page("Scroll of Mega Soaker", MEGA_SOAKER_WIKITEXT), "AmmoConsumeChance")
        assert (mod["modType"], mod["value"]) == (200, -2.0)

    def test_long_form_damage_param(self):
        mod = _modifier(parse_scroll_page("Scroll of Sacred Ground", SACRED_GROUND_WIKITEXT), "Damage")
        assert (mod["modType"], mod["value"]) == (200, -0.5)

    def test_existing_params_still_parsed(self):
        scroll = parse_scroll_page("Scroll of Beam", BEAM_WIKITEXT)
        assert _modifier(scroll, "RPM")["value"] == 9.0
        assert _modifier(scroll, "Damage")["value"] == -0.9
        assert scroll["specialEffects"]["ConvertWpn"] == "Beam Gun"


class TestParseScrollPageDarkDamageRange:
    """Current wiki format: the amount is on DarkDmg itself, as a range, with no Dmg param."""

    WIKITEXT = """{{Item Infobox
| kind = scroll
| GridSize = 1x2
| Stun = &check;
| DarkDmg = +50&ndash;200
| BltSize = +100%
| SellVal = 1000
}}"""

    def setup_method(self):
        self.result = parse_scroll_page("Scroll of Chaos Strike", self.WIKITEXT)

    def test_bypass_percentages_set(self):
        assert self.result["specialEffects"]["bypassPercentages"] is True

    def test_per_bullet_damage_is_lower_bound_of_range(self):
        assert self.result["specialEffects"]["perBulletDamage"] == 50

    def test_range_text_kept_for_display(self):
        assert self.result["specialEffects"]["DarkDmg"] == "+50–200"

    def test_no_damage_modifier_is_invented(self):
        assert [m for m in self.result["modifiers"] if m["attribute"] == "Damage"] == []

    def test_bullet_size_still_a_modifier(self):
        assert _modifier(self.result, "BulletSize")["value"] == 1.0


class TestParseScrollPageExplosiveDamage:
    """Scroll of Explosions: the flat Dmg is unlisted explosive damage per projectile,
    independent of other enchantments (wiki: Scroll of Explosions, Damage Mechanics)."""

    WIKITEXT = """{{Item Infobox
| kind = scroll
| GridSize = 1&times;2
| Explosion = &#164;
| Dmg = +25
| SellVal = 1000
}}"""

    def setup_method(self):
        self.result = parse_scroll_page("Scroll of Explosions", self.WIKITEXT)

    def test_flat_damage_becomes_per_bullet_bonus(self):
        assert self.result["specialEffects"]["perBulletDamage"] == 25
        assert self.result["specialEffects"]["bypassPercentages"] is True

    def test_no_listed_damage_modifier(self):
        assert [m for m in self.result["modifiers"] if m["attribute"] == "Damage"] == []

    def test_explosion_effect_kept(self):
        assert self.result["specialEffects"]["Explosion"] == "¤"

    def test_percent_damage_on_an_explosive_scroll_stays_a_modifier(self):
        wikitext = self.WIKITEXT.replace("Dmg = +25", "Dmg = -50%")
        result = parse_scroll_page("Scroll of Boom", wikitext)
        assert _modifier(result, "Damage")["value"] == -0.5
        assert "perBulletDamage" not in result["specialEffects"]
