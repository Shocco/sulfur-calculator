import pytest
from scripts.wiki_parser import parse_infobox, parse_modifier_value, parse_damage_field, extract_wikilink_text


class TestParseInfobox:
    def test_basic_weapon_infobox(self):
        text = """{{Item Infobox
| kind = weapon
| Damage = 60
| RPM = 800
| Mag = 26
| Spread = 3
| Recoil = 3.5
| Durability = 2250
| Weight = 8
| Ammo = [[9mm]]
| SubType = [[Pistols|Pistol]]
| Mode = Semi-automatic
| SellVal = 1000
| image = Beck_8.png
}}"""
        result = parse_infobox(text)
        assert result['kind'] == 'weapon'
        assert result['Damage'] == '60'
        assert result['RPM'] == '800'
        assert result['Mag'] == '26'
        assert result['Ammo'] == '[[9mm]]'
        assert result['SubType'] == '[[Pistols|Pistol]]'
        assert result['image'] == 'Beck_8.png'

    def test_oil_infobox(self):
        text = """{{Item Infobox
| kind = oil
| image = Action Oil.png
| GridSize = 1x1
| Recoil = +100%
| RldSpeed = +40%
| SellVal = 350
}}"""
        result = parse_infobox(text)
        assert result['kind'] == 'oil'
        assert result['Recoil'] == '+100%'
        assert result['RldSpeed'] == '+40%'

    def test_scroll_with_convert(self):
        text = """{{Item Infobox
|kind = scroll
|GridSize = 1\u00d72
| ConvertWpn = Flamethrower
| Dmg = -86%
| Spread = +150%
| BltSpeed = -70%
| SellVal = 2500
}}"""
        result = parse_infobox(text)
        assert result['kind'] == 'scroll'
        assert result['ConvertWpn'] == 'Flamethrower'
        assert result['Dmg'] == '-86%'

    def test_attachment_infobox(self):
        text = """{{Item Infobox
| kind = attachment
| SubType = [[Muzzle Attachments|Muzzle attachment]]
| Spread = -0.75
| SellVal = 240
}}"""
        result = parse_infobox(text)
        assert result['kind'] == 'attachment'
        assert result['Spread'] == '-0.75'

    def test_chisel_infobox(self):
        text = """{{Item Infobox
|kind=chisel
|ChamberAmmo=[[50 BMG]]
|SellVal=1700
}}"""
        result = parse_infobox(text)
        assert result['kind'] == 'chisel'
        assert result['ChamberAmmo'] == '[[50 BMG]]'

    def test_ammo_infobox(self):
        text = """{{Item Infobox
| kind  = ammo
| title = 5.56mm Ammo Box
| Base Damage = 80
| Ammo Count  = 30
}}"""
        result = parse_infobox(text)
        assert result['kind'] == 'ammo'
        assert result['Base Damage'] == '80'


class TestParseModifierValue:
    # Bullet Drop multipliers are stored as Flat N (no base value to multiply)
    def test_suffix_multiplier(self):
        # Medicine Ball Oil: "BltDrop = +30x"
        assert parse_modifier_value('+30x') == (100, 30.0)

    def test_prefix_multiplier_entity(self):
        # Artillery Oil: "BltDrop = &times;15" (old wiki wrote "+15")
        assert parse_modifier_value('&times;15') == (100, 15.0)

    def test_prefix_multiplier_symbol(self):
        assert parse_modifier_value('×40') == (100, 40.0)

    def test_trailing_wiki_comment_ignored(self):
        raw = '+1\n<!-- | BltBounciness = -->\n<!-- | Drag          = more -->'
        assert parse_modifier_value(raw) == (100, 1.0)

    def test_percent_positive(self):
        mod_type, value = parse_modifier_value('+100%')
        assert mod_type == 200
        assert value == 1.0

    def test_percent_negative(self):
        mod_type, value = parse_modifier_value('-86%')
        assert mod_type == 200
        assert value == -0.86

    def test_flat_positive(self):
        mod_type, value = parse_modifier_value('+15')
        assert mod_type == 100
        assert value == 15.0

    def test_flat_negative(self):
        mod_type, value = parse_modifier_value('-15')
        assert mod_type == 100
        assert value == -15.0

    def test_flat_decimal(self):
        mod_type, value = parse_modifier_value('-0.75')
        assert mod_type == 100
        assert value == -0.75

    def test_bare_number(self):
        mod_type, value = parse_modifier_value('0.3')
        assert mod_type == 100
        assert value == 0.3

    def test_percent_40(self):
        mod_type, value = parse_modifier_value('+40%')
        assert mod_type == 200
        assert value == 0.4


class TestParseDamageField:
    def test_simple_damage(self):
        damage, projectile_count = parse_damage_field('60')
        assert damage == 60.0
        assert projectile_count == 1

    def test_multi_projectile(self):
        damage, projectile_count = parse_damage_field('40\u00d78')
        assert damage == 40.0
        assert projectile_count == 8

    def test_multi_projectile_html(self):
        damage, projectile_count = parse_damage_field('40&times;8')
        assert damage == 40.0
        assert projectile_count == 8


class TestExtractWikilinkText:
    def test_simple_link(self):
        assert extract_wikilink_text('[[9mm]]') == '9mm'

    def test_piped_link(self):
        assert extract_wikilink_text('[[Pistols|Pistol]]') == 'Pistol'

    def test_plain_text(self):
        assert extract_wikilink_text('Shotgun') == 'Shotgun'

    def test_link_with_spaces(self):
        assert extract_wikilink_text('[[Muzzle Attachments|Muzzle attachment]]') == 'Muzzle attachment'


class TestFindRedirects:
    def test_maps_redirect_titles_to_targets(self, tmp_path):
        from scripts.wiki_parser import find_redirects
        xml = tmp_path / 'dump.xml'
        xml.write_text(
            '<mediawiki xmlns="http://www.mediawiki.org/xml/export-0.11/">'
            '<page><title>Arrow Oil</title><revision><text>#REDIRECT [[Time Arrow Oil]]</text></revision></page>'
            '<page><title>Whim Oil</title><revision><text>#redirect [[Fleeting Oil#Top|x]]</text></revision></page>'
            '<page><title>Time Arrow Oil</title><revision><text>{{Item Infobox}}</text></revision></page>'
            '</mediawiki>', encoding='utf-8')
        assert find_redirects(str(xml)) == {'Arrow Oil': 'Time Arrow Oil', 'Whim Oil': 'Fleeting Oil'}


class TestInfoboxComments:
    def test_html_comments_are_removed(self):
        from scripts.wiki_parser import parse_infobox
        text = ("{{Item Infobox\n| kind = scroll\n| ConvertWpn = Steam Sprayer <!-- | LifeTime = more -->\n"
                "| BltBounces = +1\n<!-- | BltBounciness = -->\n| Drag = 8\n}}")
        box = parse_infobox(text)
        assert box['ConvertWpn'] == 'Steam Sprayer'
        assert box['BltBounces'] == '+1'
        assert 'BltBounciness' not in box


class TestParseShotsPerTrigger:
    """Third factor of a weapon's Damage field: shells or cells fired per trigger pull."""

    def test_fixed_count(self):
        from scripts.wiki_parser import parse_shots_per_trigger
        assert parse_shots_per_trigger("40&times;8&times;3") == 3
        assert parse_shots_per_trigger("50&times;3&times;3") == 3
        assert parse_shots_per_trigger("40x8x3") == 3

    def test_variable_count_is_a_range(self):
        from scripts.wiki_parser import parse_shots_per_trigger
        assert parse_shots_per_trigger("40&times;8(&times;1-8)") == [1, 8]

    def test_ordinary_damage_has_none(self):
        from scripts.wiki_parser import parse_shots_per_trigger
        assert parse_shots_per_trigger("60") is None
        assert parse_shots_per_trigger("40&times;8") is None
        assert parse_shots_per_trigger("40x8") is None
        assert parse_shots_per_trigger("100<sup>&dagger;</sup>") is None
        assert parse_shots_per_trigger("") is None
