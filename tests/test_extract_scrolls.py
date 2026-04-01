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
