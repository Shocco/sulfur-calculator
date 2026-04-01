"""Tests for scripts/extract_calibers.py."""

import pytest

from scripts.extract_calibers import parse_ammo_page, parse_caliber_table


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ammo_wikitext(base_damage: int, kind: str = "ammo") -> str:
    return f"""{{{{Item Infobox
| kind = {kind}
| title = Test Ammo Box
| Base Damage = {base_damage}
| Ammo Count  = 30
}}}}"""


MULTI_ROW_TABLE = """{| class="wikitable"
!Caliber!!Damage!!Projectiles!!Spread!!Recoil
|-
|style="text-align: left;|[[12ga]]||40||×8||4||10
|-
|style="text-align: left;|[[9mm]]||120||×1||1||1
|-
|style="text-align: left;|[[5.56mm]]||80||×1||2||3
|-
|style="text-align: left;|[[7.62mm]]||100||×1||3||5
|-
|style="text-align: left;|[[50 BMG]]||200||×1||5||8
|}"""


# ---------------------------------------------------------------------------
# parse_ammo_page
# ---------------------------------------------------------------------------


class TestParseAmmoPage:
    def test_basic_ammo_returns_caliber_and_damage(self):
        """A page with kind=ammo and Base Damage returns the correct tuple."""
        wikitext = _make_ammo_wikitext(60)
        result = parse_ammo_page("9mm", wikitext)
        assert result is not None
        caliber, damage = result
        assert caliber == "9mm"
        assert damage == 60

    def test_ammo_title_used_as_caliber_name(self):
        """The page title is the caliber name."""
        wikitext = _make_ammo_wikitext(80)
        result = parse_ammo_page("5.56mm", wikitext)
        assert result is not None
        assert result[0] == "5.56mm"

    def test_returns_none_for_non_ammo_kind(self):
        """Pages with kind != ammo return None."""
        wikitext = _make_ammo_wikitext(60, kind="weapon")
        assert parse_ammo_page("9mm", wikitext) is None

    def test_returns_none_for_missing_base_damage(self):
        """Pages with no Base Damage field return None."""
        wikitext = """{{Item Infobox
| kind = ammo
| Ammo Count = 30
}}"""
        assert parse_ammo_page("9mm", wikitext) is None

    def test_returns_none_for_no_infobox(self):
        """Pages without an infobox return None."""
        assert parse_ammo_page("9mm", "Just some text without an infobox.") is None


# ---------------------------------------------------------------------------
# parse_caliber_table
# ---------------------------------------------------------------------------


class TestParseCalibrTable:
    def test_multi_row_table_returns_all_calibers(self):
        """All five caliber rows are parsed from the multi-row table."""
        result = parse_caliber_table(MULTI_ROW_TABLE)
        assert len(result) == 5

    def test_12ga_projectile_count(self):
        """12ga row has ProjectileCount=8 (×8 format)."""
        result = parse_caliber_table(MULTI_ROW_TABLE)
        assert "12Ga" in result
        assert result["12Ga"]["ProjectileCount"] == 8

    def test_12ga_stats(self):
        """12ga row has the correct Spread and Recoil values."""
        result = parse_caliber_table(MULTI_ROW_TABLE)
        assert result["12Ga"]["Spread"] == pytest.approx(4.0)
        assert result["12Ga"]["Recoil"] == pytest.approx(10.0)

    def test_9mm_single_projectile(self):
        """9mm row has ProjectileCount=1."""
        result = parse_caliber_table(MULTI_ROW_TABLE)
        assert "9mm" in result
        assert result["9mm"]["ProjectileCount"] == 1
        assert result["9mm"]["Spread"] == pytest.approx(1.0)
        assert result["9mm"]["Recoil"] == pytest.approx(1.0)

    def test_556mm_stats(self):
        """5.56mm row is parsed correctly."""
        result = parse_caliber_table(MULTI_ROW_TABLE)
        assert "5.56mm" in result
        assert result["5.56mm"]["Spread"] == pytest.approx(2.0)
        assert result["5.56mm"]["Recoil"] == pytest.approx(3.0)

    def test_762mm_stats(self):
        """7.62mm row is parsed correctly."""
        result = parse_caliber_table(MULTI_ROW_TABLE)
        assert "7.62mm" in result
        assert result["7.62mm"]["Spread"] == pytest.approx(3.0)
        assert result["7.62mm"]["Recoil"] == pytest.approx(5.0)

    def test_50bmg_normalized(self):
        """'50 BMG' in the table is normalized to '.50 BMG'."""
        result = parse_caliber_table(MULTI_ROW_TABLE)
        assert ".50 BMG" in result
        assert "50 BMG" not in result

    def test_50bmg_stats(self):
        """.50 BMG has the correct stats."""
        result = parse_caliber_table(MULTI_ROW_TABLE)
        assert result[".50 BMG"]["Spread"] == pytest.approx(5.0)
        assert result[".50 BMG"]["Recoil"] == pytest.approx(8.0)
        assert result[".50 BMG"]["ProjectileCount"] == 1

    def test_empty_table_returns_empty_dict(self):
        """A table with no data rows returns an empty dict."""
        table = """{| class="wikitable"
!Caliber!!Damage!!Projectiles!!Spread!!Recoil
|}"""
        assert parse_caliber_table(table) == {}


# ---------------------------------------------------------------------------
# Caliber normalization (via parse_ammo_page and parse_caliber_table)
# ---------------------------------------------------------------------------


class TestCaliberNormalization:
    def test_12ga_lowercase_normalized_via_ammo_page(self):
        """'12ga' page title is normalized to '12Ga'."""
        wikitext = _make_ammo_wikitext(40)
        result = parse_ammo_page("12ga", wikitext)
        assert result is not None
        assert result[0] == "12Ga"

    def test_12Ga_titlecase_normalized_via_ammo_page(self):
        """'12Ga' page title stays '12Ga'."""
        wikitext = _make_ammo_wikitext(40)
        result = parse_ammo_page("12Ga", wikitext)
        assert result is not None
        assert result[0] == "12Ga"

    def test_50_bmg_no_dot_normalized_via_ammo_page(self):
        """'50 BMG' page title is normalized to '.50 BMG'."""
        wikitext = _make_ammo_wikitext(200)
        result = parse_ammo_page("50 BMG", wikitext)
        assert result is not None
        assert result[0] == ".50 BMG"

    def test_dot_50_bmg_stays_normalized_via_ammo_page(self):
        """'.50 BMG' page title stays '.50 BMG'."""
        wikitext = _make_ammo_wikitext(200)
        result = parse_ammo_page(".50 BMG", wikitext)
        assert result is not None
        assert result[0] == ".50 BMG"

    def test_standard_calibers_unchanged(self):
        """'9mm', '5.56mm', '7.62mm' pass through unchanged."""
        for caliber in ("9mm", "5.56mm", "7.62mm"):
            wikitext = _make_ammo_wikitext(60)
            result = parse_ammo_page(caliber, wikitext)
            assert result is not None
            assert result[0] == caliber

    def test_12ga_in_table_normalized_to_12Ga(self):
        """[[12ga]] wikilink in a table row normalizes to '12Ga'."""
        result = parse_caliber_table(MULTI_ROW_TABLE)
        assert "12Ga" in result
        assert "12ga" not in result
