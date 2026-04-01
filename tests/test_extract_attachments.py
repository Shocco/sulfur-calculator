"""Tests for scripts/extract_attachments.py.

Covers all major parsing paths: muzzle, sight, laser, chamber attachments,
Insurance special case, chisels, and pages that should return None.
"""

import pytest
from scripts.extract_attachments import parse_attachment_page, parse_chisel_page


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_attachment_wikitext(
    subtype_wikilink: str,
    *,
    spread: str = "",
    speed: str = "",
    crit_ads: str = "",
    move_accuracy: str = "",
    dmg: str = "",
    sil_fire: str = "",
    mode_change: str = "",
    extra_params: str = "",
    description_section: str = "",
) -> str:
    """Build minimal attachment wikitext for testing."""
    lines = [
        "{{Item Infobox",
        "| kind = attachment",
        f"| SubType = {subtype_wikilink}",
    ]
    if spread:
        lines.append(f"| Spread = {spread}")
    if speed:
        lines.append(f"| Speed = {speed}")
    if crit_ads:
        lines.append(f"| CritADS = {crit_ads}")
    if move_accuracy:
        lines.append(f"| MoveAccuracy = {move_accuracy}")
    if dmg:
        lines.append(f"| Dmg = {dmg}")
    if sil_fire:
        lines.append(f"| SilFire = {sil_fire}")
    if mode_change:
        lines.append(f"| ModeChange = {mode_change}")
    if extra_params:
        lines.append(extra_params)
    lines.append("}}")
    if description_section:
        lines.append(f"\n==Description==\n{description_section}")
    return "\n".join(lines)


def _make_chisel_wikitext(chamber_ammo: str) -> str:
    """Build minimal chisel wikitext for testing."""
    return "\n".join([
        "{{Item Infobox",
        "| kind = chisel",
        f"| ChamberAmmo = {chamber_ammo}",
        "| SellVal = 1700",
        "}}",
    ])


# ---------------------------------------------------------------------------
# Muzzle attachment: Spread modifier
# ---------------------------------------------------------------------------

class TestMuzzleAttachment:
    """Muzzle attachments use SubType=Muzzle Attachment/Attachments wikilink."""

    def test_spread_modifier_flat(self):
        """Muzzle attachment with flat Spread modifier maps to modifiers['Spread']."""
        wikitext = _make_attachment_wikitext(
            "[[Muzzle Attachments|Muzzle attachment]]",
            spread="-0.75",
        )
        result = parse_attachment_page("Haukland Silencer", wikitext)

        assert result is not None
        assert result["type"] == "muzzle"
        assert result["name"] == "Haukland Silencer"
        assert result["modifiers"]["Spread"] == -0.75

    def test_muzzle_type_from_plural_subtype(self):
        """'Muzzle attachments' (plural) also resolves to slot 'muzzle'."""
        wikitext = _make_attachment_wikitext(
            "[[Muzzle Attachments|Muzzle attachments]]",
            spread="-1.0",
        )
        result = parse_attachment_page("A12C Muzzle Brake", wikitext)

        assert result is not None
        assert result["type"] == "muzzle"

    def test_rarity_present(self):
        """Known rarity is looked up from KNOWN_RARITIES."""
        wikitext = _make_attachment_wikitext(
            "[[Muzzle Attachments|Muzzle attachment]]",
            spread="-0.75",
        )
        result = parse_attachment_page("Haukland Silencer", wikitext)

        assert result is not None
        assert result["rarity"] == "Uncommon"

    def test_image_path_format(self):
        """Image path follows /images/attachments/{name_with_underscores}.png."""
        wikitext = _make_attachment_wikitext(
            "[[Muzzle Attachments|Muzzle attachment]]",
        )
        result = parse_attachment_page("Haukland Flash Hider", wikitext)

        assert result is not None
        assert result["image"] == "/images/attachments/Haukland_Flash_Hider.png"

    def test_silences_fire_special_effect(self):
        """SilFire param sets specialEffects.silencesFire = True."""
        wikitext = _make_attachment_wikitext(
            "[[Muzzle Attachments|Muzzle attachment]]",
            sil_fire="1",
        )
        result = parse_attachment_page("SR-P3 Silencer", wikitext)

        assert result is not None
        assert result["specialEffects"].get("silencesFire") is True


# ---------------------------------------------------------------------------
# Sight: CritADS -> ADSCritChance
# ---------------------------------------------------------------------------

class TestSightAttachment:
    """Sight attachments use SubType=Sights/Sight wikilink."""

    def test_crit_ads_maps_to_ads_crit_chance(self):
        """CritADS infobox param is stored as modifiers['ADSCritChance']."""
        wikitext = _make_attachment_wikitext(
            "[[Sights|Sights]]",
            crit_ads="0.15",
        )
        result = parse_attachment_page("Assault Scope", wikitext)

        assert result is not None
        assert result["type"] == "sight"
        assert result["modifiers"]["ADSCritChance"] == pytest.approx(0.15)

    def test_singular_sight_subtype(self):
        """'Sight' (singular) also resolves to slot 'sight'."""
        wikitext = _make_attachment_wikitext(
            "[[Sights|Sight]]",
            crit_ads="0.1",
        )
        result = parse_attachment_page("Reflex Sight", wikitext)

        assert result is not None
        assert result["type"] == "sight"


# ---------------------------------------------------------------------------
# Chamber attachment: ModeChange -> firingMode (Gun Crank)
# ---------------------------------------------------------------------------

class TestGunCrankChamberAttachment:
    """Gun Crank is a chamber attachment that changes firing mode."""

    def test_mode_change_becomes_firing_mode(self):
        """ModeChange param is cleaned and stored as specialEffects.firingMode."""
        wikitext = _make_attachment_wikitext(
            "[[Chamber Attachments|Chamber attachment]]",
            mode_change="Automatic",
        )
        result = parse_attachment_page("Gun Crank", wikitext)

        assert result is not None
        assert result["type"] == "chamber"
        assert result["specialEffects"]["firingMode"] == "automatic"

    def test_mode_change_html_stripped(self):
        """HTML tags are stripped from ModeChange value."""
        wikitext = _make_attachment_wikitext(
            "[[Chamber Attachments|Chamber attachment]]",
            mode_change="<b>Automatic</b>",
        )
        result = parse_attachment_page("Gun Crank", wikitext)

        assert result is not None
        assert result["specialEffects"]["firingMode"] == "automatic"

    def test_gun_crank_rarity(self):
        """Gun Crank has Uncommon rarity per KNOWN_RARITIES."""
        wikitext = _make_attachment_wikitext(
            "[[Chamber Attachments|Chamber attachment]]",
            mode_change="Automatic",
        )
        result = parse_attachment_page("Gun Crank", wikitext)

        assert result is not None
        assert result["rarity"] == "Uncommon"


# ---------------------------------------------------------------------------
# Chamber attachment: Spread flat + Dmg percent (Priming Bolt)
# ---------------------------------------------------------------------------

class TestPrimingBoltChamberAttachment:
    """Priming Bolt is a chamber attachment with flat Spread and percent Dmg."""

    def test_spread_flat_modifier(self):
        """Priming Bolt flat Spread maps to modifiers['Spread'] as float."""
        wikitext = _make_attachment_wikitext(
            "[[Chamber Attachments|Chamber attachments]]",
            spread="-1.5",
            dmg="+25%",
        )
        result = parse_attachment_page("Priming Bolt", wikitext)

        assert result is not None
        assert result["type"] == "chamber"
        assert result["modifiers"]["Spread"] == pytest.approx(-1.5)

    def test_dmg_percent_is_dict(self):
        """Percent Dmg field becomes {'value': float, 'type': 'percent'}."""
        wikitext = _make_attachment_wikitext(
            "[[Chamber Attachments|Chamber attachments]]",
            dmg="+25%",
        )
        result = parse_attachment_page("Priming Bolt", wikitext)

        assert result is not None
        dmg = result["modifiers"]["Dmg"]
        assert isinstance(dmg, dict)
        assert dmg["type"] == "percent"
        assert dmg["value"] == pytest.approx(25.0)

    def test_dmg_flat_is_float(self):
        """Flat Dmg field (no %) becomes plain float."""
        wikitext = _make_attachment_wikitext(
            "[[Chamber Attachments|Chamber attachments]]",
            dmg="10",
        )
        result = parse_attachment_page("Priming Bolt", wikitext)

        assert result is not None
        dmg = result["modifiers"]["Dmg"]
        assert isinstance(dmg, float)
        assert dmg == pytest.approx(10.0)

    def test_priming_bolt_rarity(self):
        """Priming Bolt has Rare rarity per KNOWN_RARITIES."""
        wikitext = _make_attachment_wikitext(
            "[[Chamber Attachments|Chamber attachments]]",
        )
        result = parse_attachment_page("Priming Bolt", wikitext)

        assert result is not None
        assert result["rarity"] == "Rare"


# ---------------------------------------------------------------------------
# Laser attachment: MoveAccuracy -> AccuracyWhileMoving
# ---------------------------------------------------------------------------

class TestLaserAttachment:
    """Laser sights use SubType=Laser Sights/Laser Sight wikilink."""

    def test_move_accuracy_maps_to_accuracy_while_moving(self):
        """MoveAccuracy infobox param is stored as modifiers['AccuracyWhileMoving']."""
        wikitext = _make_attachment_wikitext(
            "[[Laser Sights|Laser sight]]",
            move_accuracy="0.3",
        )
        result = parse_attachment_page("Laser Sight (Red)", wikitext)

        assert result is not None
        assert result["type"] == "laser"
        assert result["modifiers"]["AccuracyWhileMoving"] == pytest.approx(0.3)

    def test_laser_sight_plural_subtype(self):
        """'Laser sights' (plural) also resolves to slot 'laser'."""
        wikitext = _make_attachment_wikitext(
            "[[Laser Sights|Laser sights]]",
            move_accuracy="0.2",
        )
        result = parse_attachment_page("Laser Sight (Green)", wikitext)

        assert result is not None
        assert result["type"] == "laser"

    def test_speed_maps_to_move_speed(self):
        """Speed infobox param is stored as modifiers['MoveSpeed']."""
        wikitext = _make_attachment_wikitext(
            "[[Laser Sights|Laser sight]]",
            speed="0.05",
        )
        result = parse_attachment_page("Laser Sight (Yellow)", wikitext)

        assert result is not None
        assert result["modifiers"]["MoveSpeed"] == pytest.approx(0.05)


# ---------------------------------------------------------------------------
# Insurance special case
# ---------------------------------------------------------------------------

class TestInsuranceAttachment:
    """Insurance is a special attachment that maps to slot 'insurance'."""

    def test_insurance_detection_by_title(self):
        """Title 'Insurance' forces slot to 'insurance' regardless of SubType."""
        # SubType wikilink display text "attachment" also maps to insurance
        wikitext = _make_attachment_wikitext(
            "[[Insurance|attachment]]",
        )
        result = parse_attachment_page("Insurance", wikitext)

        assert result is not None
        assert result["type"] == "insurance"

    def test_insurance_protection_special_effect(self):
        """Insurance has specialEffects.protection describing its effect."""
        wikitext = _make_attachment_wikitext(
            "[[Insurance|attachment]]",
        )
        result = parse_attachment_page("Insurance", wikitext)

        assert result is not None
        assert "protection" in result["specialEffects"]
        assert "Collection Box" in result["specialEffects"]["protection"]

    def test_insurance_rarity_legendary(self):
        """Insurance has Legendary rarity per KNOWN_RARITIES."""
        wikitext = _make_attachment_wikitext(
            "[[Insurance|attachment]]",
        )
        result = parse_attachment_page("Insurance", wikitext)

        assert result is not None
        assert result["rarity"] == "Legendary"

    def test_insurance_subtype_display_attachment(self):
        """SubType display text 'attachment' (generic) maps to insurance slot."""
        wikitext = _make_attachment_wikitext(
            "[[SomeLink|attachment]]",
        )
        # Any title with this subtype gets slot "insurance"
        result = parse_attachment_page("Insurance", wikitext)

        assert result is not None
        assert result["type"] == "insurance"


# ---------------------------------------------------------------------------
# Chisel parsing
# ---------------------------------------------------------------------------

class TestChiselParsing:
    """Chamber chisels have kind=chisel and ChamberAmmo wikilink."""

    def test_9mm_chisel(self):
        """Chamber Chisel (9mm) parses ChamberAmmo wikilink to caliberConversion."""
        wikitext = _make_chisel_wikitext("[[9mm]]")
        result = parse_chisel_page("Chamber Chisel (9mm)", wikitext)

        assert result is not None
        assert result["type"] == "chisel"
        assert result["specialEffects"]["caliberConversion"] == "9mm"
        assert result["modifiers"] == {}

    def test_50_bmg_normalization(self):
        """'50 BMG' (without leading dot) is normalized to '.50 BMG'."""
        wikitext = _make_chisel_wikitext("[[50 BMG]]")
        result = parse_chisel_page("Chamber Chisel (.50 BMG)", wikitext)

        assert result is not None
        assert result["specialEffects"]["caliberConversion"] == ".50 BMG"

    def test_50_bmg_description(self):
        """Normalized .50 BMG caliber uses the correct description."""
        wikitext = _make_chisel_wikitext("[[50 BMG]]")
        result = parse_chisel_page("Chamber Chisel (.50 BMG)", wikitext)

        assert result is not None
        assert ".50 BMG" in result["description"]
        assert "extreme damage" in result["description"]

    def test_556_chisel(self):
        """Chamber Chisel (5.56mm) caliber conversion and description."""
        wikitext = _make_chisel_wikitext("[[5.56mm]]")
        result = parse_chisel_page("Chamber Chisel (5.56mm)", wikitext)

        assert result is not None
        assert result["specialEffects"]["caliberConversion"] == "5.56mm"
        assert "balanced" in result["description"]

    def test_762_chisel_rarity(self):
        """Chamber Chisel (7.62mm) has Rare rarity."""
        wikitext = _make_chisel_wikitext("[[7.62mm]]")
        result = parse_chisel_page("Chamber Chisel (7.62mm)", wikitext)

        assert result is not None
        assert result["rarity"] == "Rare"

    def test_12ga_chisel(self):
        """Chamber Chisel (12Ga) parses correctly."""
        wikitext = _make_chisel_wikitext("[[12Ga]]")
        result = parse_chisel_page("Chamber Chisel (12Ga)", wikitext)

        assert result is not None
        assert result["specialEffects"]["caliberConversion"] == "12Ga"
        assert "shotgun" in result["description"].lower()

    def test_legendary_bmg_rarity(self):
        """Chamber Chisel (.50 BMG) has Legendary rarity."""
        wikitext = _make_chisel_wikitext("[[50 BMG]]")
        result = parse_chisel_page("Chamber Chisel (.50 BMG)", wikitext)

        assert result is not None
        assert result["rarity"] == "Legendary"

    def test_chisel_image_path(self):
        """Chisel image path uses title with underscores."""
        wikitext = _make_chisel_wikitext("[[9mm]]")
        result = parse_chisel_page("Chamber Chisel (9mm)", wikitext)

        assert result is not None
        assert result["image"] == "/images/attachments/Chamber_Chisel_(9mm).png"

    def test_piped_wikilink_uses_display_text(self):
        """Piped wikilink [[50 BMG|.50 BMG]] uses the display text directly."""
        wikitext = _make_chisel_wikitext("[[50 BMG|.50 BMG]]")
        result = parse_chisel_page("Chamber Chisel (.50 BMG)", wikitext)

        assert result is not None
        # Display text ".50 BMG" passes through normalize unchanged
        assert result["specialEffects"]["caliberConversion"] == ".50 BMG"


# ---------------------------------------------------------------------------
# Non-attachment/chisel pages return None
# ---------------------------------------------------------------------------

class TestNonAttachmentReturnsNone:
    """Pages that are not attachments or chisels should return None."""

    def test_weapon_page_returns_none_for_attachment_parser(self):
        """A weapon infobox is not an attachment; parse_attachment_page -> None."""
        wikitext = """\
{{Item Infobox
| kind = weapon
| Damage = 60
| RPM = 800
| SubType = [[Pistols|Pistol]]
}}"""
        assert parse_attachment_page("Beck 8", wikitext) is None

    def test_oil_page_returns_none_for_attachment_parser(self):
        """An oil infobox is not an attachment; parse_attachment_page -> None."""
        wikitext = """\
{{Item Infobox
| kind = oil
| Recoil = +100%
}}"""
        assert parse_attachment_page("Action Oil", wikitext) is None

    def test_no_infobox_returns_none(self):
        """Page with no Item Infobox returns None."""
        wikitext = "This page has no infobox at all."
        assert parse_attachment_page("Empty Page", wikitext) is None
        assert parse_chisel_page("Empty Page", wikitext) is None

    def test_weapon_page_returns_none_for_chisel_parser(self):
        """A weapon infobox is not a chisel; parse_chisel_page -> None."""
        wikitext = """\
{{Item Infobox
| kind = weapon
| Damage = 60
}}"""
        assert parse_chisel_page("Some Weapon", wikitext) is None

    def test_attachment_page_returns_none_for_chisel_parser(self):
        """An attachment infobox is not a chisel; parse_chisel_page -> None."""
        wikitext = """\
{{Item Infobox
| kind = attachment
| SubType = [[Muzzle Attachments|Muzzle attachment]]
}}"""
        assert parse_chisel_page("Haukland Silencer", wikitext) is None

    def test_unknown_subtype_returns_none(self):
        """Attachment with unrecognised SubType display text returns None."""
        wikitext = """\
{{Item Infobox
| kind = attachment
| SubType = [[Unknown Category|mystery slot]]
}}"""
        assert parse_attachment_page("Mystery Item", wikitext) is None


# ---------------------------------------------------------------------------
# Description extraction
# ---------------------------------------------------------------------------

class TestDescriptionExtraction:
    """Description is taken from the first plain-text line of ==Description==."""

    def test_description_extracted(self):
        """Description section content appears in the result."""
        wikitext = _make_attachment_wikitext(
            "[[Muzzle Attachments|Muzzle attachment]]",
            description_section="A compact silencer for urban engagements.",
        )
        result = parse_attachment_page("Haukland Silencer", wikitext)

        assert result is not None
        assert result["description"] == "A compact silencer for urban engagements."

    def test_no_description_section_gives_empty_string(self):
        """Missing Description section results in empty description string."""
        wikitext = _make_attachment_wikitext(
            "[[Muzzle Attachments|Muzzle attachment]]",
        )
        result = parse_attachment_page("Haukland Silencer", wikitext)

        assert result is not None
        assert result["description"] == ""
