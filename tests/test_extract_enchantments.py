"""Tests for scripts/extract_enchantments.py."""

import pytest

from scripts.extract_enchantments import parse_oil_page


class TestParseOilPage:
    """Tests for parse_oil_page covering the main parsing paths."""

    def test_percent_modifiers(self):
        """Oil with percent-based modifiers produces modType=200 entries."""
        wikitext = """{{Item Infobox
| kind = oil
| image = Action Oil.png
| GridSize = 1x1
| Recoil = +100%
| RldSpeed = +40%
| SellVal = 350
}}"""
        result = parse_oil_page("Action Oil", wikitext)

        assert result is not None
        assert result["id"] == "Action_Oil"
        assert result["name"] == "Action Oil"

        modifiers = result["modifiers"]
        recoil = next(m for m in modifiers if m["attribute"] == "Recoil")
        assert recoil["modType"] == 200
        assert recoil["value"] == pytest.approx(1.0)

        reload_speed = next(m for m in modifiers if m["attribute"] == "ReloadSpeed")
        assert reload_speed["modType"] == 200
        assert reload_speed["value"] == pytest.approx(0.4)

        # No special effects keys present when there are none.
        assert "specialEffects" not in result
        assert "effects" not in result

    def test_flat_damage_modifier(self):
        """Oil with a flat damage modifier produces modType=100 entries."""
        wikitext = """{{Item Infobox
| kind = oil
| image = Damage Oil.png
| GridSize = 1x1
| Dmg = +15
| SellVal = 500
}}"""
        result = parse_oil_page("Damage Oil", wikitext)

        assert result is not None
        assert result["id"] == "Damage_Oil"

        modifiers = result["modifiers"]
        damage = next(m for m in modifiers if m["attribute"] == "Damage")
        assert damage["modType"] == 100
        assert damage["value"] == pytest.approx(15.0)

    def test_special_effects(self):
        """Oil with AimDisabled and a percent modifier includes specialEffects and effects."""
        wikitext = """{{Item Infobox
| kind = oil
| image = Ghost Oil.png
| GridSize = 1x1
| AimDisabled = 1
| CritChance = +30%
| SellVal = 800
}}"""
        result = parse_oil_page("Ghost Oil", wikitext)

        assert result is not None

        # CritChance modifier
        modifiers = result["modifiers"]
        crit = next(m for m in modifiers if m["attribute"] == "CritChance")
        assert crit["modType"] == 200
        assert crit["value"] == pytest.approx(0.3)

        # Special effect present in both dicts
        assert result["specialEffects"] == {"disablesAiming": True}
        assert "Disables aiming" in result["effects"]

    def test_non_oil_returns_none(self):
        """Pages whose infobox kind is not 'oil' return None."""
        weapon_wikitext = """{{Item Infobox
| kind = weapon
| Damage = 60
| RPM = 800
| Mag = 26
}}"""
        assert parse_oil_page("Some Pistol", weapon_wikitext) is None

    def test_no_infobox_returns_none(self):
        """Pages with no infobox at all return None."""
        assert parse_oil_page("Random Page", "Just some plain text.") is None

    def test_multiple_special_effects(self):
        """Oil with multiple special effects adds all of them."""
        wikitext = """{{Item Infobox
| kind = oil
| image = Mystery Oil.png
| NoDrb = 1
| NoMoney = 1
| NoOrgans = 1
| SellVal = 1200
}}"""
        result = parse_oil_page("Mystery Oil", wikitext)

        assert result is not None
        assert result["specialEffects"]["noDurability"] is True
        assert result["specialEffects"]["noMoney"] is True
        assert result["specialEffects"]["noOrgans"] is True
        assert "No durability loss" in result["effects"]
        assert "No money drops" in result["effects"]
        assert "No organ drops" in result["effects"]

    def test_id_spaces_replaced_with_underscores(self):
        """The id field replaces spaces in the title with underscores."""
        wikitext = """{{Item Infobox
| kind = oil
| Recoil = +50%
}}"""
        result = parse_oil_page("Multi Word Oil Name", wikitext)
        assert result is not None
        assert result["id"] == "Multi_Word_Oil_Name"
        assert result["name"] == "Multi Word Oil Name"

    def test_negative_percent_modifier(self):
        """Negative percent modifiers parse correctly."""
        wikitext = """{{Item Infobox
| kind = oil
| BltDrop = -50%
}}"""
        result = parse_oil_page("Drop Oil", wikitext)
        assert result is not None
        drop = next(m for m in result["modifiers"] if m["attribute"] == "BulletDrop")
        assert drop["modType"] == 200
        assert drop["value"] == pytest.approx(-0.5)
