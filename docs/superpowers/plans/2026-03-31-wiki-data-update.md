# Wiki Data Update Pipeline — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Download a fresh SULFUR wiki dump via wikiteam3 and regenerate all `public/data/*.json` files from it.

**Architecture:** A suite of standalone Python scripts each parse the MediaWiki XML dump, extract one data category using `xml.etree.ElementTree` iterparse, and write the output JSON in the exact schema the React app already consumes. A runner script calls them all in sequence. A diff script compares old vs new JSON.

**Tech Stack:** Python 3 (stdlib: `xml.etree.ElementTree`, `json`, `re`, `os`, `sys`, `pathlib`), wikiteam3 (user-installed), Node.js (for final build validation)

---

## File Structure

| File | Responsibility |
|------|---------------|
| `scripts/wiki_parser.py` | Shared XML iterparse helper + infobox field parser used by all extractors |
| `scripts/extract_weapons.py` | Parse `kind=weapon` pages → `public/data/weapons.json` |
| `scripts/extract_enchantments.py` | Parse `kind=oil` pages → `public/data/enchantments.json` |
| `scripts/extract_scrolls.py` | Parse `kind=scroll` pages → `public/data/scrolls.json` |
| `scripts/extract_attachments.py` | Parse `kind=attachment` pages → all `public/data/attachments-*.json` |
| `scripts/extract_calibers.py` | Parse ammo pages → `public/data/caliber-modifiers.json` |
| `scripts/update_all.py` | Run all extractors in order, print summary |
| `scripts/diff_data.py` | Compare two sets of JSON files and print human-readable changes |
| `tests/test_wiki_parser.py` | Tests for shared parser |
| `tests/test_extract_weapons.py` | Tests for weapon extractor |
| `tests/test_extract_enchantments.py` | Tests for enchantment extractor |
| `tests/test_extract_scrolls.py` | Tests for scroll extractor |
| `tests/test_extract_attachments.py` | Tests for attachment extractor |
| `tests/test_extract_calibers.py` | Tests for caliber extractor |
| `tests/test_diff_data.py` | Tests for diff tool |

---

## Infobox → JSON Schema Mappings

These mappings were derived by inspecting the Dec 2024 wiki dump and comparing against the existing `public/data/` files.

### Weapons

Wiki infobox (`kind=weapon`):

| Infobox param | JSON field | Notes |
|--------------|-----------|-------|
| (page title) | `name` | |
| (derived) | `id` | `"Weapon_" + name.replace(" ", "_")` |
| `Damage` | `baseStats.Damage` | Parse `40×8` as damage=40, projectileCount=8 |
| `RPM` | `baseStats.RPM` | |
| `Mag` | `baseStats.MagazineSize` | |
| `Spread` | `baseStats.Spread` | |
| `Recoil` | `baseStats.Recoil` | |
| `Durability` | `baseStats.Durability` and `baseStats.MaxDurability` | Same value for both |
| `Weight` | `baseStats.Weight` | |
| (missing from infobox) | `baseStats.ProjectileCount` | Default 1.0 unless `Damage` has `×N` |
| (missing from infobox) | `baseStats.ProjectileSpeed` | Default 100.0 (not in wiki) |
| (missing from infobox) | `baseStats.MoveSpeed` | Default 1.0 (not in wiki) |
| `image` | `image` | Fallback: `name.replace(" ", "_") + ".png"` |
| `SubType` | `type` | Extract link text: `[[Shotguns\|Shotgun]]` → `"Shotgun"` |
| `Ammo` | `ammoType` | Extract link text: `[[7.62mm]]` → `"7.62mm"` |
| (Available Attachments section) | `allowedAttachments` | Map category names to slot IDs |
| (Available Attachments section) | `specificAttachments` | List individual attachment names |

**Attachment category → slot ID mapping:**

```python
ATTACHMENT_CATEGORY_TO_SLOT = {
    "Muzzle Attachments": "muzzle",
    "Sight": "sight",
    "Sights": "sight",
    "Laser Sights": "laser",
    "Laser Sight": "laser",
    "Chamber Attachments": "chamber",
    "Chamber Attachment": "chamber",
    "Chamber Chisel": "chisel",
    "Chamber Chisels": "chisel",
    "Gun Crank": "chamber",          # individual attachment, slot=chamber
    "Priming Bolt": "chamber",        # individual attachment, slot=chamber
    "Insurance": "insurance",
}
```

### Oils (Enchantments)

Wiki infobox (`kind=oil`):

| Infobox param | JSON attribute | modType |
|--------------|---------------|---------|
| `Dmg` | `Damage` | Parse sign: `+15` → Flat(100), `+30%` → PercentAdd(200) |
| `Spread` | `Spread` | Same parsing |
| `Recoil` | `Recoil` | Same parsing |
| `RPM` | `RPM` | Same parsing |
| `RldSpeed` | `ReloadSpeed` | Same parsing |
| `BltSpeed` | `BulletSpeed` | Same parsing |
| `BltBounces` | `BulletBounces` | Same parsing |
| `BltBounciness` | `BulletBounciness` | Same parsing |
| `BltDrop` | `BulletDrop` | Same parsing |
| `BltSize` | `BulletSize` | Same parsing |
| `BltPen` | `BulletPenetrations` | Same parsing |
| `Speed` | `MoveSpeed` | Same parsing |
| `CritChance` | `CritChance` | Same parsing |
| `LootChance` | `LootChance` | Same parsing |
| `ProjecAmnt` | `ProjectileCount` | Same parsing |
| `JumpPwr` | `JumpPower` | Same parsing |
| `MaxDrb` | `MaxDurability` | Same parsing |
| `AmmoConsume` | `AmmoConsumeChance` | Same parsing |
| `MoveAccuracy` | `MoveAccuracy` | Same parsing |

**Modifier value parsing:**
- `+15` or `-15` → modType 100 (Flat), value = 15.0 or -15.0
- `+30%` or `-30%` → modType 200 (PercentAdd), value = 0.3 or -0.3

**Special boolean effects (go in `specialEffects` and `effects`):**
- `AimDisabled` → `{"disablesAiming": true}`, effect `"Disables aiming"`
- `NoDrb` → `{"noDurability": true}`, effect `"No durability loss"`
- `NoMoney` → `{"noMoney": true}`, effect `"No money drops"`
- `NoOrgans` → `{"noOrgans": true}`, effect `"No organ drops"`

### Scrolls

Wiki infobox (`kind=scroll`). Same modifier params as oils, plus special effect params:

| Infobox param | specialEffects key | Notes |
|--------------|-------------------|-------|
| `ConvertWpn` | `ConvertWpn` | Weapon conversion name |
| `Proc` | `Proc` | Proc chance string |
| `Fire` | `Fire` | |
| `Frost` | `Frost` | |
| `Poison` | `Poison` | |
| `Electrocution` | `Electrocution` | |
| `Stun` | `Stun` | |
| `StunArea` | `StunArea` | |
| `Fear` | `Fear` | |
| `Root` | `Root` | |
| `ShareDmg` | `ShareDmg` | |
| `CrpsExpl` | `CrpsExpl` | |
| `DrbConsume` | `DrbConsume` | |
| `WpnAreaDmg` | `WpnAreaDmg` | |
| `LinkBlt` | `LinkBlt` | |
| `PsnCloud` | `PsnCloud` | |
| `PsnPuddle` | `PsnPuddle` | |
| `LessForceSpd` | `LessForceSpd` | |
| `MoreDmgOnHit` | `MoreDmgOnHit` | |
| `PenDmgMult` | `PenDmgMult` | |
| `BltSize` | `BltSize` | Only goes to specialEffects if it's a display value like `+100%` |
| `HSDmg` | `HSDmg` | Headshot damage display |
| `AlwaysOrgans` | `AlwaysOrgans` | |
| `Drag` | `Drag` | |

**Scroll `effects` array:** Built from the Description section bullet points (`* '''text'''`).

**Scroll modifier parsing for `bypassPercentages` and `perBulletDamage`:**
- If `DarkDmg` param exists, set `specialEffects.bypassPercentages = true` and `specialEffects.perBulletDamage = <value>`
- `Dmg` param on scrolls with `DarkDmg` becomes a Flat(100) modifier

### Attachments

Wiki infobox (`kind=attachment`):

| Infobox param | JSON field | Notes |
|--------------|-----------|-------|
| (page title) | `name` | |
| `SubType` | `type` | Map: `Muzzle attachment`→`muzzle`, `Sights`/`Sight`→`sight`, `Laser Sights`/`Laser Sight`→`laser`, `Chamber Attachment`→`chamber` |
| `Spread` | `modifiers.Spread` | Parse as float |
| `Speed` | `modifiers.MoveSpeed` | Parse as float |
| `Dmg` | `modifiers.Damage` | Parse; if has `%`, use `{"value": X, "type": "percent"}` |
| `CritADS` | `modifiers.ADSCritChance` | Parse as float |
| `MoveAccuracy` | `modifiers.AccuracyWhileMoving` | Parse as float |
| `SilFire` | `specialEffects.silencesFire` | Boolean true |
| `ModeChange` | `specialEffects.firingMode` | Extract text: `Automatic`, `Semiautomatic` |
| (category) | `rarity` | Inferred from existing data — not in infobox. Preserve existing values where names match. |
| (description section) | `description` | First sentence of Description section |
| `image` | `image` | Path: `/images/attachments/{name_underscored}.png` |

**Output files by type:**
- `muzzle` → `attachments-muzzle.json`
- `sight` → `attachments-sights.json`
- `laser` → `attachments-lasers.json`
- `chamber` → `attachments-chamber.json`

### Chisels

Wiki infobox (`kind=chisel`):

| Infobox param | JSON field |
|--------------|-----------|
| (page title) | `name` |
| `ChamberAmmo` | `specialEffects.caliberConversion` — extract link text |

Output: `attachments-chisels.json`, type = `chisel`. Rarity preserved from existing data.

### Insurance

Single item. Detected by `title == "Insurance"` and `kind=attachment`. Output: `attachments-insurance.json`.

### Calibers

Wiki infobox (`kind=ammo`):

| Infobox param | JSON field |
|--------------|-----------|
| (page title or `Ammo` in title) | caliber key |
| `Base Damage` | `baseAmmoDamage[key]` |

The `calibers` sub-object (Spread, Recoil, ProjectileCount per caliber) is NOT in ammo infoboxes — it comes from the "Caliber Modding" tables on weapon pages. Extract from the first weapon page that has a `{| class="wikitable"` with caliber columns.

---

## Task 1: Shared Wiki Parser Module

**Files:**
- Create: `scripts/__init__.py`
- Create: `scripts/wiki_parser.py`
- Create: `tests/__init__.py`
- Create: `tests/test_wiki_parser.py`

- [ ] **Step 1: Write tests for infobox field parser**

```python
# tests/test_wiki_parser.py
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
|GridSize = 1×2
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
        damage, projectile_count = parse_damage_field('40×8')
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /opt/sulfur-calculator && python3 -m pytest tests/test_wiki_parser.py -v
```

Expected: ModuleNotFoundError — `scripts.wiki_parser` doesn't exist yet.

- [ ] **Step 3: Implement wiki_parser.py**

```python
# scripts/__init__.py
# (empty)

# scripts/wiki_parser.py
"""Shared helpers for parsing MediaWiki XML dumps from sulfur.wiki.gg."""

import re
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple


def iterate_pages(dump_path: str, namespace: str = 'http://www.mediawiki.org/xml/export-0.11/'):
    """
    Yield (title, wikitext) for each page in the XML dump.

    Uses iterparse to keep memory low. Only yields the most recent revision
    for each page. Skips namespace pages (those with ':' in the title).
    """
    ns_prefix = f'{{{namespace}}}'
    context = ET.iterparse(dump_path, events=('end',))

    for event, elem in context:
        if elem.tag != f'{ns_prefix}page':
            continue

        ns_map = {'mw': namespace}
        title_elem = elem.find('mw:title', ns_map)
        if title_elem is None or not title_elem.text or ':' in title_elem.text:
            elem.clear()
            continue

        title = title_elem.text

        # Get the first (most recent) revision
        revision = elem.find('mw:revision', ns_map)
        if revision is None:
            elem.clear()
            continue

        text_elem = revision.find('mw:text', ns_map)
        if text_elem is None or not text_elem.text:
            elem.clear()
            continue

        yield title, text_elem.text
        elem.clear()


def parse_infobox(wikitext: str) -> Dict[str, str]:
    """
    Extract key-value pairs from a {{Item Infobox ...}} template.

    Returns dict of param_name → raw_value (strings, not yet parsed).
    """
    match = re.search(r'\{\{Item Infobox(.*?)\}\}', wikitext, re.DOTALL)
    if not match:
        return {}

    body = match.group(1)
    result = {}

    for param_match in re.finditer(r'\|\s*([\w\s]+?)\s*=\s*(.*?)(?=\n\s*\||$)', body, re.DOTALL):
        key = param_match.group(1).strip()
        value = param_match.group(2).strip()
        if value:
            result[key] = value

    return result


def parse_modifier_value(raw: str) -> Tuple[int, float]:
    """
    Parse a modifier value string from the wiki into (modType, value).

    - "+30%" or "-30%" → (200, 0.3) or (200, -0.3)  [PercentAdd]
    - "+15" or "-15" or "0.3" or "-0.75" → (100, value)  [Flat]
    """
    raw = raw.strip()

    if raw.endswith('%'):
        # PercentAdd
        num_str = raw[:-1].strip()
        value = float(num_str) / 100.0
        return (200, value)
    else:
        # Flat
        value = float(raw.lstrip('+'))
        return (100, value)


def parse_damage_field(raw: str) -> Tuple[float, int]:
    """
    Parse a Damage field which may contain projectile count.

    "60" → (60.0, 1)
    "40×8" or "40&times;8" → (40.0, 8)
    """
    raw = raw.replace('&times;', '×')
    if '×' in raw:
        parts = raw.split('×')
        return (float(parts[0].strip()), int(parts[1].strip()))
    return (float(raw.strip()), 1)


def extract_wikilink_text(raw: str) -> str:
    """
    Extract display text from a wikilink.

    "[[9mm]]" → "9mm"
    "[[Pistols|Pistol]]" → "Pistol"
    "Shotgun" → "Shotgun"
    """
    match = re.match(r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]', raw.strip())
    if match:
        return match.group(2) or match.group(1)
    return raw.strip()


def extract_wikilinks(text: str) -> List[str]:
    """Extract all wikilink targets from text. Returns the link part (before |)."""
    return [m.group(1) for m in re.finditer(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', text)]


def extract_section(wikitext: str, heading: str) -> Optional[str]:
    """
    Extract the content of a wiki section by heading name.

    Returns text from after ==heading== until the next == or end of text.
    """
    pattern = rf'=={re.escape(heading)}==\s*(.*?)(?:\n==|$)'
    match = re.search(pattern, wikitext, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def extract_bullet_points(text: str) -> List[str]:
    """Extract bullet point text from wiki markup, stripping formatting."""
    points = []
    for line in text.split('\n'):
        line = line.strip()
        if line.startswith(('*', '•', '·', '-')):
            content = line.lstrip('*•·- ').strip()
            # Remove bold/italic markup
            content = re.sub(r"'''|''", '', content)
            if content:
                points.append(content)
    return points
```

- [ ] **Step 4: Create tests/__init__.py**

```python
# tests/__init__.py
# (empty)
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd /opt/sulfur-calculator && python3 -m pytest tests/test_wiki_parser.py -v
```

Expected: All tests PASS.

- [ ] **Step 6: Commit**

```bash
cd /opt/sulfur-calculator
git add scripts/ tests/
git commit -m "feat: add shared wiki parser module with tests"
```

---

## Task 2: Weapon Extractor

**Files:**
- Create: `scripts/extract_weapons.py`
- Create: `tests/test_extract_weapons.py`

- [ ] **Step 1: Write tests for weapon extraction**

```python
# tests/test_extract_weapons.py
import pytest
import json
from scripts.extract_weapons import parse_weapon_page, ATTACHMENT_CATEGORY_TO_SLOT

SAMPLE_WEAPON_TEXT = """{{Item Infobox
| kind = weapon
| GridSize = 3&times;2
| SubType = [[Revolvers|Revolver]]
| Ammo = [[7.62mm]]
| Mode = Double Action
| Mag = 4
| Weight = 5
| Damage = 160
| RPM = 80
| Spread = 2
| Recoil = 20
| Durability = 1000
| SellVal = 1600
| image = .357_Balthazar.png
}}
Some description text.
==Available Attachments==
The gun can accept:
• [[Muzzle Attachments]]
• [[Sight|Sights]]
• [[Laser Sights]]
• [[Gun Crank]]
• [[Chamber Chisel|Chamber Chisels]]
[[Category:Items]][[Category:Weapons]][[Category:Revolvers]][[Category:7.62mm]]"""

SAMPLE_SHOTGUN_TEXT = """{{Item Infobox
| kind = weapon
| GridSize = 5&times;2
| SubType = [[Shotguns|Shotgun]]
| Ammo = [[12Ga]]
| Mode = Break Action
| Mag = 2
| Weight = 16
| Damage = 40&times;8
| RPM = 500
| Spread = 4
| Recoil = 10
| Durability = 2000
| SellVal = 600
}}
Shotgun description.
==Available Attachments==
• [[Muzzle Attachments]]
• [[Sight|Sights]]
• [[Laser Sights]]
• [[Gun Crank]]
• [[Chamber Chisel|Chamber Chisels]]
[[Category:Items]][[Category:Weapons]][[Category:Shotguns]][[Category:12Ga]]"""


class TestParseWeaponPage:
    def test_basic_weapon(self):
        result = parse_weapon_page('.357 Balthazar', SAMPLE_WEAPON_TEXT)
        assert result is not None
        assert result['name'] == '.357 Balthazar'
        assert result['id'] == 'Weapon_.357_Balthazar'
        assert result['baseStats']['Damage'] == 160.0
        assert result['baseStats']['RPM'] == 80.0
        assert result['baseStats']['MagazineSize'] == 4.0
        assert result['baseStats']['Spread'] == 2.0
        assert result['baseStats']['Recoil'] == 20.0
        assert result['baseStats']['Durability'] == 1000.0
        assert result['baseStats']['MaxDurability'] == 1000.0
        assert result['baseStats']['Weight'] == 5.0
        assert result['baseStats']['ProjectileCount'] == 1.0
        assert result['baseStats']['ProjectileSpeed'] == 100.0
        assert result['baseStats']['MoveSpeed'] == 1.0
        assert result['type'] == 'Revolver'
        assert result['ammoType'] == '7.62mm'
        assert result['image'] == '.357_Balthazar.png'

    def test_shotgun_multi_projectile(self):
        result = parse_weapon_page('1889 Mario', SAMPLE_SHOTGUN_TEXT)
        assert result is not None
        assert result['baseStats']['Damage'] == 40.0
        assert result['baseStats']['ProjectileCount'] == 8.0
        assert result['ammoType'] == '12Ga'
        assert result['type'] == 'Shotgun'

    def test_allowed_attachments(self):
        result = parse_weapon_page('.357 Balthazar', SAMPLE_WEAPON_TEXT)
        assert 'muzzle' in result['allowedAttachments']
        assert 'sight' in result['allowedAttachments']
        assert 'laser' in result['allowedAttachments']
        assert 'chamber' in result['allowedAttachments']
        assert 'chisel' in result['allowedAttachments']

    def test_specific_attachments_includes_categories(self):
        result = parse_weapon_page('.357 Balthazar', SAMPLE_WEAPON_TEXT)
        assert 'Gun Crank' in result['specificAttachments']

    def test_non_weapon_returns_none(self):
        text = """{{Item Infobox
| kind = oil
| Dmg = +15
}}"""
        result = parse_weapon_page('Some Oil', text)
        assert result is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /opt/sulfur-calculator && python3 -m pytest tests/test_extract_weapons.py -v
```

Expected: ImportError — `scripts.extract_weapons` doesn't exist yet.

- [ ] **Step 3: Implement extract_weapons.py**

```python
# scripts/extract_weapons.py
"""Extract weapon data from SULFUR wiki dump → public/data/weapons.json."""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional

from scripts.wiki_parser import (
    iterate_pages, parse_infobox, parse_damage_field,
    extract_wikilink_text, extract_wikilinks, extract_section,
)

ATTACHMENT_CATEGORY_TO_SLOT = {
    "Muzzle Attachments": "muzzle",
    "Sight": "sight",
    "Sights": "sight",
    "Laser Sights": "laser",
    "Laser Sight": "laser",
    "Chamber Attachments": "chamber",
    "Chamber Attachment": "chamber",
    "Chamber Chisel": "chisel",
    "Chamber Chisels": "chisel",
    "Gun Crank": "chamber",
    "Priming Bolt": "chamber",
    "Insurance": "insurance",
}

# Individual attachments that appear as direct links in Available Attachments
INDIVIDUAL_ATTACHMENTS = {"Gun Crank", "Priming Bolt", "Insurance"}


def parse_weapon_page(title: str, wikitext: str) -> Optional[Dict]:
    """Parse a single weapon page into the weapons.json schema."""
    infobox = parse_infobox(wikitext)
    if infobox.get('kind', '').lower() != 'weapon':
        return None

    # Parse damage (may include projectile count like "40×8")
    damage_raw = infobox.get('Damage', '0')
    damage, projectile_count = parse_damage_field(damage_raw)

    # Build base stats
    base_stats = {
        'Damage': damage,
        'RPM': float(infobox.get('RPM', 0)),
        'MagazineSize': float(infobox.get('Mag', 0)),
        'Spread': float(infobox.get('Spread', 0)),
        'Recoil': float(infobox.get('Recoil', 0)),
        'Durability': float(infobox.get('Durability', 0)),
        'MaxDurability': float(infobox.get('Durability', 0)),
        'Weight': float(infobox.get('Weight', 0)),
        'ProjectileCount': float(projectile_count),
        'ProjectileSpeed': 100.0,
        'MoveSpeed': 1.0,
    }

    # Weapon type from SubType link
    weapon_type = extract_wikilink_text(infobox.get('SubType', ''))

    # Ammo type from Ammo link
    ammo_type = extract_wikilink_text(infobox.get('Ammo', ''))

    # Image
    image = infobox.get('image', title.replace(' ', '_') + '.png')

    # Parse Available Attachments section
    allowed_slots = set()
    specific_attachments = []

    attachments_section = extract_section(wikitext, 'Available Attachments')
    if attachments_section:
        links = extract_wikilinks(attachments_section)
        for link in links:
            if link == 'Attachments' or link == 'attachment':
                continue

            # Map to slot ID
            slot = ATTACHMENT_CATEGORY_TO_SLOT.get(link)
            if slot:
                allowed_slots.add(slot)

            # Track individual attachments
            if link in INDIVIDUAL_ATTACHMENTS:
                specific_attachments.append(link)

    # Always add insurance if not explicitly excluded
    # (most weapons accept insurance)

    return {
        'id': f"Weapon_{title.replace(' ', '_')}",
        'name': title,
        'baseStats': base_stats,
        'image': image,
        'type': weapon_type,
        'ammoType': ammo_type,
        'allowedAttachments': sorted(list(allowed_slots)),
        'specificAttachments': sorted(specific_attachments),
    }


def extract_weapons(dump_path: str, output_path: str, attachment_data: Optional[Dict[str, List[str]]] = None):
    """
    Extract all weapons from the wiki dump and write weapons.json.

    If attachment_data is provided (slot_type → [attachment_names]),
    populates specificAttachments for each weapon based on its allowedAttachments slots.
    """
    weapons = []

    for title, wikitext in iterate_pages(dump_path):
        weapon = parse_weapon_page(title, wikitext)
        if weapon:
            # Populate specific attachments from attachment_data if available
            if attachment_data:
                specific = set(weapon['specificAttachments'])
                for slot in weapon['allowedAttachments']:
                    if slot in attachment_data:
                        specific.update(attachment_data[slot])
                weapon['specificAttachments'] = sorted(list(specific))
            weapons.append(weapon)

    # Sort by name for stable output
    weapons.sort(key=lambda w: w['name'])

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(weapons, f, indent=2, ensure_ascii=False)

    print(f"Extracted {len(weapons)} weapons → {output_path}")
    return weapons


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.extract_weapons <dump_path> [output_path]")
        sys.exit(1)

    dump_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else 'public/data/weapons.json'
    extract_weapons(dump_path, output_path)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /opt/sulfur-calculator && python3 -m pytest tests/test_extract_weapons.py -v
```

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
cd /opt/sulfur-calculator
git add scripts/extract_weapons.py tests/test_extract_weapons.py
git commit -m "feat: add weapon extractor with tests"
```

---

## Task 3: Enchantment (Oil) Extractor

**Files:**
- Create: `scripts/extract_enchantments.py`
- Create: `tests/test_extract_enchantments.py`

- [ ] **Step 1: Write tests for oil extraction**

```python
# tests/test_extract_enchantments.py
import pytest
from scripts.extract_enchantments import parse_oil_page

SAMPLE_OIL_BASIC = """{{Item Infobox
| kind = oil
| image = Action Oil.png
| GridSize = 1x1
| Recoil = +100%
| RldSpeed = +40%
| SellVal = 350
| SoldBy = [[Scholar|Kevin]]
}}
== Description ==
'''Enchantment'''
''Drag this onto a weapon with an empty enchantment slot to enchant it.''
* '''Recoil: +100%'''
* '''Reload speed: +40%'''
[[Category:Items]][[Category:Enchantments]][[Category:Oils]]"""

SAMPLE_OIL_FLAT_DMG = """{{Item Infobox
| kind = oil
| image = Add Damage Oil.png
| GridSize = 1x1
| Dmg = +15
| SellVal = 200
}}
== Description ==
'''Enchantment'''
* '''Damage: +15'''
[[Category:Oils]]"""

SAMPLE_OIL_WITH_EFFECTS = """{{Item Infobox
| kind = oil
| image = Aimless Oil.png
| GridSize = 1x1
| CritChance = +30%
| AimDisabled = yes
| SellVal = 300
}}
== Description ==
'''Enchantment'''
* '''Crit Chance: +30%'''
* '''Disables aiming'''
[[Category:Oils]]"""


class TestParseOilPage:
    def test_basic_oil(self):
        result = parse_oil_page('Action Oil', SAMPLE_OIL_BASIC)
        assert result is not None
        assert result['name'] == 'Action Oil'
        assert result['id'] == 'Action_Oil'
        assert len(result['modifiers']) == 2

        recoil_mod = next(m for m in result['modifiers'] if m['attribute'] == 'Recoil')
        assert recoil_mod['modType'] == 200
        assert recoil_mod['value'] == 1.0

        reload_mod = next(m for m in result['modifiers'] if m['attribute'] == 'ReloadSpeed')
        assert reload_mod['modType'] == 200
        assert reload_mod['value'] == 0.4

    def test_flat_damage_oil(self):
        result = parse_oil_page('Add Damage Oil', SAMPLE_OIL_FLAT_DMG)
        assert result is not None
        dmg_mod = result['modifiers'][0]
        assert dmg_mod['attribute'] == 'Damage'
        assert dmg_mod['modType'] == 100
        assert dmg_mod['value'] == 15.0

    def test_oil_with_special_effects(self):
        result = parse_oil_page('Aimless Oil', SAMPLE_OIL_WITH_EFFECTS)
        assert result is not None
        assert result['specialEffects']['disablesAiming'] is True
        assert 'Disables aiming' in result['effects']

        crit_mod = next(m for m in result['modifiers'] if m['attribute'] == 'CritChance')
        assert crit_mod['modType'] == 200
        assert crit_mod['value'] == 0.3

    def test_non_oil_returns_none(self):
        text = """{{Item Infobox
| kind = weapon
| Damage = 60
}}"""
        assert parse_oil_page('Some Weapon', text) is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /opt/sulfur-calculator && python3 -m pytest tests/test_extract_enchantments.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement extract_enchantments.py**

```python
# scripts/extract_enchantments.py
"""Extract oil/enchantment data from SULFUR wiki dump → public/data/enchantments.json."""

import json
import sys
import os
from typing import Dict, List, Optional

from scripts.wiki_parser import (
    iterate_pages, parse_infobox, parse_modifier_value,
    extract_section, extract_bullet_points,
)

# Map wiki infobox param names → JSON attribute names
OIL_PARAM_MAP = {
    'Dmg': 'Damage',
    'Spread': 'Spread',
    'Recoil': 'Recoil',
    'RPM': 'RPM',
    'RldSpeed': 'ReloadSpeed',
    'BltSpeed': 'BulletSpeed',
    'BltBounces': 'BulletBounces',
    'BltBounciness': 'BulletBounciness',
    'BltDrop': 'BulletDrop',
    'BltSize': 'BulletSize',
    'BltPen': 'BulletPenetrations',
    'Speed': 'MoveSpeed',
    'CritChance': 'CritChance',
    'LootChance': 'LootChance',
    'ProjecAmnt': 'ProjectileCount',
    'JumpPwr': 'JumpPower',
    'MaxDrb': 'MaxDurability',
    'AmmoConsume': 'AmmoConsumeChance',
    'AmmoExConsume': 'AmmoConsumeChance',
    'MoveAccuracy': 'MoveAccuracy',
}

# Boolean special effect params
OIL_SPECIAL_EFFECTS = {
    'AimDisabled': ('disablesAiming', 'Disables aiming'),
    'NoDrb': ('noDurability', 'No durability loss'),
    'NoMoney': ('noMoney', 'No money drops'),
    'NoOrgans': ('noOrgans', 'No organ drops'),
}


def parse_oil_page(title: str, wikitext: str) -> Optional[Dict]:
    """Parse a single oil page into the enchantments.json schema."""
    infobox = parse_infobox(wikitext)
    if infobox.get('kind', '').lower() != 'oil':
        return None

    modifiers = []
    special_effects = {}
    effects = []

    # Parse stat modifiers
    for wiki_param, json_attr in OIL_PARAM_MAP.items():
        if wiki_param in infobox:
            raw = infobox[wiki_param]
            try:
                mod_type, value = parse_modifier_value(raw)
                modifiers.append({
                    'attribute': json_attr,
                    'modType': mod_type,
                    'value': value,
                })
            except (ValueError, IndexError):
                pass

    # Parse special boolean effects
    for wiki_param, (effect_key, effect_text) in OIL_SPECIAL_EFFECTS.items():
        if wiki_param in infobox:
            special_effects[effect_key] = True
            effects.append(effect_text)

    # Build description effects from bullet points if present
    desc_section = extract_section(wikitext, 'Description')
    if desc_section:
        bullets = extract_bullet_points(desc_section)
        # Only use bullet points for effects if we detected special effects
        # (to avoid duplicating modifier descriptions as effects)
        if special_effects and not effects:
            effects = bullets

    result = {
        'id': title.replace(' ', '_'),
        'name': title,
        'modifiers': modifiers,
    }

    if special_effects:
        result['specialEffects'] = special_effects
    if effects:
        result['effects'] = effects

    return result


def extract_enchantments(dump_path: str, output_path: str):
    """Extract all oils from the wiki dump and write enchantments.json."""
    oils = []

    for title, wikitext in iterate_pages(dump_path):
        oil = parse_oil_page(title, wikitext)
        if oil:
            oils.append(oil)

    oils.sort(key=lambda o: o['name'])

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(oils, f, indent=2, ensure_ascii=False)

    print(f"Extracted {len(oils)} enchantments → {output_path}")
    return oils


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.extract_enchantments <dump_path> [output_path]")
        sys.exit(1)

    dump_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else 'public/data/enchantments.json'
    extract_enchantments(dump_path, output_path)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /opt/sulfur-calculator && python3 -m pytest tests/test_extract_enchantments.py -v
```

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
cd /opt/sulfur-calculator
git add scripts/extract_enchantments.py tests/test_extract_enchantments.py
git commit -m "feat: add enchantment (oil) extractor with tests"
```

---

## Task 4: Scroll Extractor

**Files:**
- Create: `scripts/extract_scrolls.py`
- Create: `tests/test_extract_scrolls.py`

- [ ] **Step 1: Write tests for scroll extraction**

```python
# tests/test_extract_scrolls.py
import pytest
from scripts.extract_scrolls import parse_scroll_page

SAMPLE_SCROLL_BASIC = """{{Item Infobox
| kind = scroll
| GridSize = 1×2
| StunArea = &#128771;
| Proc = 10%
| SellVal = 2500
}}
== Description ==
'''Elemental enchantment'''
'''Drag this onto a weapon with an empty enchantment slot to enchant it.'''
'''Adds chance to shock the area on hit, stunning nearby units.'''
[[Category:Scrolls]]"""

SAMPLE_SCROLL_CONVERT = """{{Item Infobox
|kind = scroll
|GridSize = 1×2
| ConvertWpn   = Flamethrower
| LifeTime     = 0.8 seconds
| LessForceSpd = &#128770;
| Dmg           = -86%
| Spread        = +150%
| BltSpeed      = -70%
| Drag          = 8
| BltBounces    = +1
| BltBounciness = 0.2
| SellVal = 2500
}}
== Description ==
'''Elemental enchantment'''
'''Drag this onto a weapon with an empty enchantment slot to enchant it.'''
'''Increases damage on target for every bullet hit.'''
* '''Spread +150%'''
* '''Bullet speed -70%'''
* '''More drag'''
* '''Less force speed'''
* '''Damage -86%'''
* '''Converts into Flamethrower'''
* '''More life time'''
* '''Bullets bounce +1'''
[[Category:Scrolls]]"""

SAMPLE_SCROLL_DARK_DMG = """{{Item Infobox
| kind = scroll
| GridSize = 1×2
| BltSize = +100%
| Dmg = +50
| DarkDmg = yes
| Stun = ✓
| Swap = yes
| SellVal = 2500
}}
== Description ==
'''Elemental enchantment'''
* '''Dark Damage +50'''
* '''Chance to increase dark damage up to 800%'''
* '''Chance to stun target'''
* '''Swap places with target'''
* '''Bigger Bullets'''
[[Category:Scrolls]]"""


class TestParseScrollPage:
    def test_basic_scroll(self):
        result = parse_scroll_page('Scroll of Aftershock', SAMPLE_SCROLL_BASIC)
        assert result is not None
        assert result['name'] == 'Scroll of Aftershock'
        assert result['id'] == 'Scroll_of_Aftershock'
        assert result['specialEffects']['StunArea'] == '🟃'
        assert result['specialEffects']['Proc'] == '10%'
        assert result['modifiers'] == []

    def test_convert_scroll(self):
        result = parse_scroll_page('Scroll of Flame Thrower', SAMPLE_SCROLL_CONVERT)
        assert result is not None
        assert result['specialEffects']['ConvertWpn'] == 'Flamethrower'
        assert result['specialEffects']['LessForceSpd'] == '🟂'
        assert result['specialEffects']['Drag'] == '8'

        dmg_mod = next(m for m in result['modifiers'] if m['attribute'] == 'Damage')
        assert dmg_mod['modType'] == 200
        assert dmg_mod['value'] == -0.86

        spread_mod = next(m for m in result['modifiers'] if m['attribute'] == 'Spread')
        assert spread_mod['modType'] == 200
        assert spread_mod['value'] == 1.5

    def test_dark_damage_scroll(self):
        result = parse_scroll_page('Scroll of Chaos Strike', SAMPLE_SCROLL_DARK_DMG)
        assert result is not None
        assert result['specialEffects']['bypassPercentages'] is True
        assert result['specialEffects']['perBulletDamage'] == 50

        # BltSize goes to specialEffects as display value
        assert result['specialEffects']['BltSize'] == '+100%'

        # Dmg becomes flat modifier
        dmg_mod = next(m for m in result['modifiers'] if m['attribute'] == 'Damage')
        assert dmg_mod['modType'] == 100
        assert dmg_mod['value'] == 50.0

        # BulletSize also gets a modifier
        blt_mod = next(m for m in result['modifiers'] if m['attribute'] == 'BulletSize')
        assert blt_mod['modType'] == 200
        assert blt_mod['value'] == 1.0

    def test_effects_from_bullets(self):
        result = parse_scroll_page('Scroll of Flame Thrower', SAMPLE_SCROLL_CONVERT)
        assert result is not None
        assert len(result.get('effects', [])) > 0

    def test_non_scroll_returns_none(self):
        text = """{{Item Infobox
| kind = oil
| Dmg = +15
}}"""
        assert parse_scroll_page('Some Oil', text) is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /opt/sulfur-calculator && python3 -m pytest tests/test_extract_scrolls.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement extract_scrolls.py**

```python
# scripts/extract_scrolls.py
"""Extract scroll data from SULFUR wiki dump → public/data/scrolls.json."""

import html
import json
import sys
import os
from typing import Dict, List, Optional

from scripts.wiki_parser import (
    iterate_pages, parse_infobox, parse_modifier_value,
    extract_section, extract_bullet_points,
)

# Modifier params shared with oils
SCROLL_MODIFIER_PARAMS = {
    'Dmg': 'Damage',
    'Spread': 'Spread',
    'RPM': 'RPM',
    'BltSpeed': 'BulletSpeed',
    'BltBounces': 'BulletBounces',
    'BltBounciness': 'BulletBounciness',
    'BltDrop': 'BulletDrop',
    'HSDmg': 'HeadshotDamage',
}

# Params that go directly into specialEffects as-is (string values)
SCROLL_SPECIAL_PARAMS = {
    'ConvertWpn', 'Proc', 'Fire', 'Frost', 'Poison', 'Electrocution',
    'Stun', 'StunArea', 'Fear', 'Root', 'ShareDmg', 'CrpsExpl',
    'DrbConsume', 'WpnAreaDmg', 'LinkBlt', 'PsnCloud', 'PsnPuddle',
    'LessForceSpd', 'MoreDmgOnHit', 'PenDmgMult', 'AlwaysOrgans',
    'Drag', 'Wet', 'Blind', 'AreaBlind', 'SelfBlind', 'SelfDmg',
    'Charm', 'Petrify', 'Homing', 'Lava', 'OilPuddle', 'Oily',
    'FrostPuddle', 'ElecArea', 'Explosion', 'RocketBlt', 'Fear',
    'LifeTime', 'Swap',
}

# BltSize goes to BOTH specialEffects (display) and modifiers
BLTSIZE_PARAM = 'BltSize'


def parse_scroll_page(title: str, wikitext: str) -> Optional[Dict]:
    """Parse a single scroll page into the scrolls.json schema."""
    infobox = parse_infobox(wikitext)
    if infobox.get('kind', '').lower() != 'scroll':
        return None

    modifiers = []
    special_effects = {}
    effects = []

    has_dark_dmg = 'DarkDmg' in infobox

    # Parse stat modifiers
    for wiki_param, json_attr in SCROLL_MODIFIER_PARAMS.items():
        if wiki_param not in infobox:
            continue
        raw = infobox[wiki_param]

        # Special case: if DarkDmg is present, Dmg is flat per-bullet damage
        if wiki_param == 'Dmg' and has_dark_dmg:
            try:
                value = float(raw.lstrip('+').rstrip('%'))
                modifiers.append({
                    'attribute': json_attr,
                    'modType': 100,
                    'value': value,
                })
            except ValueError:
                pass
            continue

        try:
            mod_type, value = parse_modifier_value(raw)
            modifiers.append({
                'attribute': json_attr,
                'modType': mod_type,
                'value': value,
            })
        except (ValueError, IndexError):
            pass

    # Handle BltSize — goes to both specialEffects and modifiers
    if BLTSIZE_PARAM in infobox:
        raw = infobox[BLTSIZE_PARAM]
        special_effects[BLTSIZE_PARAM] = raw
        try:
            mod_type, value = parse_modifier_value(raw)
            modifiers.append({
                'attribute': 'BulletSize',
                'modType': mod_type,
                'value': value,
            })
        except (ValueError, IndexError):
            pass

    # Handle DarkDmg → bypassPercentages + perBulletDamage
    if has_dark_dmg:
        special_effects['bypassPercentages'] = True
        if 'Dmg' in infobox:
            try:
                val = float(infobox['Dmg'].lstrip('+').rstrip('%'))
                special_effects['perBulletDamage'] = int(val)
            except ValueError:
                pass

    # Parse special effect params
    for param in SCROLL_SPECIAL_PARAMS:
        if param in infobox:
            raw = infobox[param]
            # Decode HTML entities
            decoded = html.unescape(raw)
            special_effects[param] = decoded

    # Extract effects from Description bullet points
    desc_section = extract_section(wikitext, 'Description')
    if desc_section:
        effects = extract_bullet_points(desc_section)

    result = {
        'id': title.replace(' ', '_'),
        'name': title,
        'modifiers': modifiers,
    }

    if special_effects:
        result['specialEffects'] = special_effects
    if effects:
        result['effects'] = effects

    return result


def extract_scrolls(dump_path: str, output_path: str):
    """Extract all scrolls from the wiki dump and write scrolls.json."""
    scrolls = []

    for title, wikitext in iterate_pages(dump_path):
        scroll = parse_scroll_page(title, wikitext)
        if scroll:
            scrolls.append(scroll)

    scrolls.sort(key=lambda s: s['name'])

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(scrolls, f, indent=2, ensure_ascii=False)

    print(f"Extracted {len(scrolls)} scrolls → {output_path}")
    return scrolls


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.extract_scrolls <dump_path> [output_path]")
        sys.exit(1)

    dump_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else 'public/data/scrolls.json'
    extract_scrolls(dump_path, output_path)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /opt/sulfur-calculator && python3 -m pytest tests/test_extract_scrolls.py -v
```

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
cd /opt/sulfur-calculator
git add scripts/extract_scrolls.py tests/test_extract_scrolls.py
git commit -m "feat: add scroll extractor with tests"
```

---

## Task 5: Attachment Extractor

**Files:**
- Create: `scripts/extract_attachments.py`
- Create: `tests/test_extract_attachments.py`

- [ ] **Step 1: Write tests for attachment extraction**

```python
# tests/test_extract_attachments.py
import pytest
from scripts.extract_attachments import parse_attachment_page, parse_chisel_page

SAMPLE_MUZZLE = """{{Item Infobox
| kind = attachment
| Grid Size = 1x1
| SellVal = 240
| BuyVal  = 480
| SoldBy  = [[Ralphie]]
| SubType = [[Muzzle Attachments|Muzzle attachment]]
| Spread = -0.75
}}
== Description ==
''A muzzle device designed to lower the spread of guns. Compatible with most barrels.''
[[Category:Items]]
[[Category:Attachments]]
[[Category:Muzzle Attachments]]"""

SAMPLE_SIGHT = """{{Item Infobox
| kind = attachment
| SubType = [[Sight|Sights]]
| CritADS = 0.2
| SellVal = 300
}}
== Description ==
''Assault rifle optic for improved accuracy''
[[Category:Sights]]"""

SAMPLE_CHAMBER = """{{Item Infobox
|kind=attachment
|image=Gun Crank.png
|GridSize=1×1
|SubType=[[Chamber Attachment]]
|ModeChange=<br>Automatic
|SellVal=340
|SoldBy=[[Ralphie]]
}}
== Description ==
''A mechanical device that can turn any semi-automatic gun fully automatic.''
[[Category:Chamber Attachments]]"""

SAMPLE_PRIMING_BOLT = """{{Item Infobox
|kind=attachment
|image=Priming_Bolt.png
|GridSize=1×1
|SubType=[[Chamber Attachment]]
|ModeChange=<br>Semiautomatic
|Spread=-0.1
|Dmg=+10%
|SellVal=500
}}
== Description ==
''Makes weapon semiautomatic with improved damage and accuracy''
[[Category:Chamber Attachments]]"""

SAMPLE_CHISEL = """{{Item Infobox
|kind=chisel
|GridSize=4×2
|ChamberAmmo=[[50 BMG]]
|SellVal=1700
|SoldBy=[[Ralphie]]
}}
== Description ==
A toolkit for reboreing a firearm barrel to .50 BMG.
[[Category:Chamber Chisels]]"""

SAMPLE_LASER = """{{Item Infobox
| kind = attachment
| SubType = [[Laser Sights|Laser Sight]]
| MoveAccuracy = 50
| SellVal = 200
}}
== Description ==
''Tactical device allowing for more accurate hip fire''
[[Category:Laser Sights]]"""

SAMPLE_INSURANCE = """{{Item Infobox
| kind = attachment
| Grid Size = 1x1
| SubType = [[Attachments|Attachment]]
| SellVal = 5000
| BuyVal  = 10000
}}
== Description ==
''When you lose a weapon this is attached to, it will drop out of the church collection box. One use only!''
[[Category:Attachments]]"""


class TestParseAttachmentPage:
    def test_muzzle(self):
        result = parse_attachment_page('A12C Muzzle Brake', SAMPLE_MUZZLE)
        assert result is not None
        assert result['name'] == 'A12C Muzzle Brake'
        assert result['type'] == 'muzzle'
        assert result['modifiers']['Spread'] == -0.75

    def test_sight(self):
        result = parse_attachment_page('Assault Scope', SAMPLE_SIGHT)
        assert result is not None
        assert result['type'] == 'sight'
        assert result['modifiers']['ADSCritChance'] == 0.2

    def test_chamber_gun_crank(self):
        result = parse_attachment_page('Gun Crank', SAMPLE_CHAMBER)
        assert result is not None
        assert result['type'] == 'chamber'
        assert result['specialEffects']['firingMode'] == 'automatic'
        assert result['modifiers'] == {}

    def test_chamber_priming_bolt(self):
        result = parse_attachment_page('Priming Bolt', SAMPLE_PRIMING_BOLT)
        assert result is not None
        assert result['type'] == 'chamber'
        assert result['modifiers']['Spread'] == -0.1
        assert result['modifiers']['Damage'] == {'value': 0.1, 'type': 'percent'}
        assert result['specialEffects']['firingMode'] == 'semiautomatic'

    def test_laser(self):
        result = parse_attachment_page('Laser Sight (Red)', SAMPLE_LASER)
        assert result is not None
        assert result['type'] == 'laser'
        assert result['modifiers']['AccuracyWhileMoving'] == 50

    def test_insurance(self):
        result = parse_attachment_page('Insurance', SAMPLE_INSURANCE)
        assert result is not None
        assert result['type'] == 'insurance'
        assert result['specialEffects']['protection'] == 'Returns weapon to Collection Box on death'


class TestParseChiselPage:
    def test_chisel(self):
        result = parse_chisel_page('Chamber Chisel (.50 BMG)', SAMPLE_CHISEL)
        assert result is not None
        assert result['name'] == 'Chamber Chisel (.50 BMG)'
        assert result['type'] == 'chisel'
        assert result['specialEffects']['caliberConversion'] == '50 BMG'
        assert result['modifiers'] == {}

    def test_non_chisel_returns_none(self):
        text = """{{Item Infobox
| kind = oil
}}"""
        assert parse_chisel_page('Some Oil', text) is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /opt/sulfur-calculator && python3 -m pytest tests/test_extract_attachments.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement extract_attachments.py**

```python
# scripts/extract_attachments.py
"""Extract attachment data from SULFUR wiki dump → public/data/attachments-*.json."""

import json
import re
import sys
import os
from typing import Dict, List, Optional

from scripts.wiki_parser import (
    iterate_pages, parse_infobox, extract_wikilink_text,
    extract_section,
)

# Existing rarity data — not available in wiki infobox, preserved from current files
KNOWN_RARITIES = {
    'A12C Muzzle Brake': 'Uncommon',
    'Aftermarket Haukland Silencer': 'Rare',
    'Barrel Extension 2"': 'Common',
    'Barrel Extension 4"': 'Uncommon',
    'Barrel Extension 6"': 'Rare',
    'Breznik BMD': 'Uncommon',
    'Breznik BMD (Tactical)': 'Rare',
    'Haukland Flash Hider': 'Common',
    'Haukland Silencer': 'Uncommon',
    'Improvised Barrel Extension': 'Common',
    'M87 "Albatross" Silencer': 'Rare',
    'SR-P3 Silencer': 'Rare',
    'Shrouded Barrel Extension': 'Uncommon',
    'Warmage Compensator': 'Rare',
    'Assault Scope': 'Uncommon',
    'Compact Sight': 'Common',
    'Holographic Sight': 'Uncommon',
    'Hunting Scope': 'Rare',
    'Recon Scope': 'Uncommon',
    'Reflex Sight': 'Uncommon',
    'Sniper Scope': 'Rare',
    'Laser Sight (Red)': 'Common',
    'Laser Sight (Green)': 'Uncommon',
    'Laser Sight (Yellow)': 'Rare',
    'Gun Crank': 'Uncommon',
    'Priming Bolt': 'Rare',
    'Chamber Chisel (9mm)': 'Uncommon',
    'Chamber Chisel (5.56mm)': 'Uncommon',
    'Chamber Chisel (7.62mm)': 'Rare',
    'Chamber Chisel (.50 BMG)': 'Legendary',
    'Chamber Chisel (12Ga)': 'Rare',
    'Insurance': 'Legendary',
}

SUBTYPE_TO_SLOT = {
    'muzzle attachment': 'muzzle',
    'muzzle attachments': 'muzzle',
    'sights': 'sight',
    'sight': 'sight',
    'laser sights': 'laser',
    'laser sight': 'laser',
    'chamber attachment': 'chamber',
    'chamber attachments': 'chamber',
    'attachment': 'insurance',  # Generic "Attachment" is used for Insurance
}

SLOT_TO_FILENAME = {
    'muzzle': 'attachments-muzzle.json',
    'sight': 'attachments-sights.json',
    'laser': 'attachments-lasers.json',
    'chamber': 'attachments-chamber.json',
    'chisel': 'attachments-chisels.json',
    'insurance': 'attachments-insurance.json',
}

CHISEL_DESCRIPTIONS = {
    '9mm': 'Converts weapon to 9mm caliber - provides reduced recoil but lower damage',
    '5.56mm': 'Converts weapon to 5.56mm caliber - balanced damage and recoil',
    '7.62mm': 'Converts weapon to 7.62mm caliber - high damage with increased recoil',
    '.50 BMG': 'Converts weapon to .50 BMG caliber - extreme damage with very high recoil',
    '50 BMG': 'Converts weapon to .50 BMG caliber - extreme damage with very high recoil',
    '12Ga': 'Converts weapon to 12 Gauge shotgun shells - multiple pellets with spread',
}


def parse_attachment_page(title: str, wikitext: str) -> Optional[Dict]:
    """Parse a single attachment page into its JSON schema."""
    infobox = parse_infobox(wikitext)
    if infobox.get('kind', '').lower() != 'attachment':
        return None

    # Determine slot type from SubType
    sub_type_raw = infobox.get('SubType', '')
    sub_type_text = extract_wikilink_text(sub_type_raw).lower()

    # Special case: Insurance
    if title == 'Insurance':
        slot = 'insurance'
    else:
        slot = SUBTYPE_TO_SLOT.get(sub_type_text)
        if not slot:
            return None

    modifiers = {}
    special_effects = {}

    # Parse modifier fields
    if 'Spread' in infobox:
        try:
            modifiers['Spread'] = float(infobox['Spread'])
        except ValueError:
            pass

    if 'Speed' in infobox:
        try:
            modifiers['MoveSpeed'] = float(infobox['Speed'])
        except ValueError:
            pass

    if 'CritADS' in infobox:
        try:
            modifiers['ADSCritChance'] = float(infobox['CritADS'])
        except ValueError:
            pass

    if 'MoveAccuracy' in infobox:
        try:
            modifiers['AccuracyWhileMoving'] = float(infobox['MoveAccuracy'])
        except ValueError:
            pass

    if 'Dmg' in infobox:
        raw = infobox['Dmg']
        if '%' in raw:
            try:
                val = float(raw.replace('%', '').lstrip('+')) / 100.0
                modifiers['Damage'] = {'value': val, 'type': 'percent'}
            except ValueError:
                pass
        else:
            try:
                modifiers['Damage'] = float(raw.lstrip('+'))
            except ValueError:
                pass

    if 'SilFire' in infobox:
        special_effects['silencesFire'] = True

    if 'ModeChange' in infobox:
        mode_raw = infobox['ModeChange']
        # Strip HTML like <br>
        mode_clean = re.sub(r'<[^>]+>', '', mode_raw).strip().lower()
        if mode_clean:
            special_effects['firingMode'] = mode_clean

    if title == 'Insurance':
        special_effects['protection'] = 'Returns weapon to Collection Box on death'

    # Description
    desc_section = extract_section(wikitext, 'Description')
    description = ''
    if desc_section:
        # Take first non-empty line, strip wiki markup
        for line in desc_section.split('\n'):
            line = line.strip().strip("'").strip("''").strip("'''")
            line = re.sub(r"'''|''", '', line)
            if line and not line.startswith(('*', '#', '{')):
                description = line
                break

    rarity = KNOWN_RARITIES.get(title, 'Common')

    result = {
        'name': title,
        'type': slot,
        'rarity': rarity,
        'description': description,
        'image': f'/images/attachments/{title.replace(" ", "_")}.png',
        'modifiers': modifiers,
    }

    if special_effects:
        result['specialEffects'] = special_effects

    return result


def parse_chisel_page(title: str, wikitext: str) -> Optional[Dict]:
    """Parse a chamber chisel page into its JSON schema."""
    infobox = parse_infobox(wikitext)
    if infobox.get('kind', '').lower() != 'chisel':
        return None

    # Extract caliber from ChamberAmmo
    chamber_ammo_raw = infobox.get('ChamberAmmo', '')
    caliber = extract_wikilink_text(chamber_ammo_raw)

    # Normalize caliber display for .50 BMG
    caliber_display = caliber
    if caliber == '50 BMG':
        caliber_display = '.50 BMG'

    desc = CHISEL_DESCRIPTIONS.get(caliber, CHISEL_DESCRIPTIONS.get(caliber_display, f'Converts weapon to {caliber_display} caliber'))
    rarity = KNOWN_RARITIES.get(title, 'Common')

    return {
        'name': title,
        'type': 'chisel',
        'rarity': rarity,
        'description': desc,
        'image': f'/images/attachments/{title.replace(" ", "_")}.png',
        'modifiers': {},
        'specialEffects': {
            'caliberConversion': caliber_display,
        },
    }


def extract_attachments(dump_path: str, output_dir: str):
    """
    Extract all attachments from the wiki dump and write per-type JSON files.

    Returns dict of slot_type → [attachment_names] for use by weapon extractor.
    """
    attachments_by_slot = {
        'muzzle': [],
        'sight': [],
        'laser': [],
        'chamber': [],
        'chisel': [],
        'insurance': [],
    }

    for title, wikitext in iterate_pages(dump_path):
        # Try as regular attachment
        attach = parse_attachment_page(title, wikitext)
        if attach:
            attachments_by_slot[attach['type']].append(attach)
            continue

        # Try as chisel
        chisel = parse_chisel_page(title, wikitext)
        if chisel:
            attachments_by_slot['chisel'].append(chisel)

    # Sort each group by name and write to files
    slot_names = {}
    for slot, items in attachments_by_slot.items():
        items.sort(key=lambda x: x['name'])
        filename = SLOT_TO_FILENAME[slot]
        filepath = os.path.join(output_dir, filename)
        os.makedirs(output_dir, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
        print(f"  {slot}: {len(items)} attachments → {filepath}")
        slot_names[slot] = [item['name'] for item in items]

    total = sum(len(v) for v in attachments_by_slot.values())
    print(f"Extracted {total} total attachments")
    return slot_names


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.extract_attachments <dump_path> [output_dir]")
        sys.exit(1)

    dump_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else 'public/data'
    extract_attachments(dump_path, output_dir)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /opt/sulfur-calculator && python3 -m pytest tests/test_extract_attachments.py -v
```

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
cd /opt/sulfur-calculator
git add scripts/extract_attachments.py tests/test_extract_attachments.py
git commit -m "feat: add attachment extractor with tests"
```

---

## Task 6: Caliber Extractor

**Files:**
- Create: `scripts/extract_calibers.py`
- Create: `tests/test_extract_calibers.py`

- [ ] **Step 1: Write tests for caliber extraction**

```python
# tests/test_extract_calibers.py
import pytest
from scripts.extract_calibers import parse_ammo_page, parse_caliber_table

SAMPLE_AMMO = """{{Item Infobox
| kind  = ammo
| title = 5.56mm Ammo Box
| image = Ammo_5.56mm.png
| GridSize = 2x1
| Base Damage = 80
| Ammo Count  = 30
| BuyVal = 100
}}
==Description==
30 rounds.
[[Category:Ammo]]"""

SAMPLE_CALIBER_TABLE = """{| class="wikitable" style="text-align: center"
!Caliber!!Damage!!Projectiles!!Spread!!Recoil
|-
|style="text-align: left;|[[12ga]]||40||×8||4||10
|-
|style="text-align: left;|[[9mm]]||120||×1||1||1
|-
|style="text-align: left;|[[5.56mm]]||160||×1||1||2
|-
|style="text-align: left;|[[7.62mm]]||200||×1||1||4
|-
|style="text-align: left;|[[50 BMG]]||400||×1||1||10
|}"""


class TestParseAmmoPage:
    def test_basic_ammo(self):
        name, base_damage = parse_ammo_page('5.56mm', SAMPLE_AMMO)
        assert name == '5.56mm'
        assert base_damage == 80

    def test_non_ammo_returns_none(self):
        text = """{{Item Infobox
| kind = weapon
}}"""
        assert parse_ammo_page('Weapon', text) is None


class TestParseCaliberTable:
    def test_parse_table(self):
        result = parse_caliber_table(SAMPLE_CALIBER_TABLE)
        assert '9mm' in result
        assert result['9mm']['Spread'] == 1
        assert result['9mm']['Recoil'] == 1
        assert result['9mm']['ProjectileCount'] == 1

        assert '12Ga' in result or '12ga' in result
        twelve_ga = result.get('12Ga', result.get('12ga'))
        assert twelve_ga['ProjectileCount'] == 8
        assert twelve_ga['Spread'] == 4

        assert '5.56mm' in result
        assert result['5.56mm']['Recoil'] == 2

        bmg = result.get('.50 BMG', result.get('50 BMG'))
        assert bmg is not None
        assert bmg['Recoil'] == 10
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /opt/sulfur-calculator && python3 -m pytest tests/test_extract_calibers.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement extract_calibers.py**

```python
# scripts/extract_calibers.py
"""Extract caliber/ammo data from SULFUR wiki dump → public/data/caliber-modifiers.json."""

import json
import re
import sys
import os
from typing import Dict, Optional, Tuple

from scripts.wiki_parser import iterate_pages, parse_infobox, extract_wikilink_text

# Normalize caliber names to match existing schema
CALIBER_NORMALIZE = {
    '12ga': '12Ga',
    '12Ga': '12Ga',
    '50 BMG': '.50 BMG',
    '.50 BMG': '.50 BMG',
    '9mm': '9mm',
    '5.56mm': '5.56mm',
    '7.62mm': '7.62mm',
}


def normalize_caliber(raw: str) -> str:
    """Normalize a caliber name to match the existing JSON schema."""
    stripped = raw.strip()
    return CALIBER_NORMALIZE.get(stripped, stripped)


def parse_ammo_page(title: str, wikitext: str) -> Optional[Tuple[str, int]]:
    """Parse an ammo page to get (caliber_name, base_damage)."""
    infobox = parse_infobox(wikitext)
    if infobox.get('kind', '').lower() != 'ammo':
        return None

    base_damage_raw = infobox.get('Base Damage', '0')
    try:
        base_damage = int(base_damage_raw)
    except ValueError:
        base_damage = 0

    return (title, base_damage)


def parse_caliber_table(table_text: str) -> Dict[str, Dict]:
    """
    Parse a wiki caliber modding table to extract per-caliber stats.

    Expected format:
    !Caliber!!Damage!!Projectiles!!Spread!!Recoil
    |-
    |[[9mm]]||120||×1||1||1
    """
    result = {}

    # Find rows between |- markers
    rows = re.split(r'\|-', table_text)
    for row in rows:
        # Look for data cells (||)
        cells = re.split(r'\|\|', row)
        if len(cells) < 5:
            continue

        # First cell is caliber (may have style prefix and wikilink)
        caliber_cell = cells[0].strip()
        # Remove table style prefix like |style="text-align: left;|
        caliber_cell = re.sub(r'^[^|]*\|', '', caliber_cell).strip()
        # Handle remaining | prefix
        caliber_cell = caliber_cell.lstrip('|').strip()

        # Extract wikilink
        link_match = re.search(r'\[\[([^\]|]+)', caliber_cell)
        if not link_match:
            continue
        caliber_raw = link_match.group(1).strip()
        caliber = normalize_caliber(caliber_raw)

        try:
            # Damage is cells[1], Projectiles is cells[2], Spread is cells[3], Recoil is cells[4]
            proj_raw = cells[2].strip().lstrip('×x').strip()
            projectile_count = int(proj_raw) if proj_raw else 1
            spread = float(cells[3].strip())
            recoil = float(cells[4].strip().rstrip('|}'))
        except (ValueError, IndexError):
            continue

        result[caliber] = {
            'Spread': spread,
            'Recoil': recoil,
            'ProjectileCount': projectile_count,
        }

    return result


def extract_calibers(dump_path: str, output_path: str):
    """Extract caliber data from the wiki dump and write caliber-modifiers.json."""
    base_ammo_damage = {}
    caliber_stats = None

    for title, wikitext in iterate_pages(dump_path):
        # Look for ammo pages
        ammo_result = parse_ammo_page(title, wikitext)
        if ammo_result:
            cal_name = normalize_caliber(ammo_result[0])
            base_ammo_damage[cal_name] = ammo_result[1]

        # Look for a caliber modding table on weapon pages
        if caliber_stats is None and '== Caliber Modding ==' in wikitext:
            table_match = re.search(r'(\{\|.*?class="wikitable".*?\|\})', wikitext, re.DOTALL)
            if table_match:
                parsed = parse_caliber_table(table_match.group(1))
                if len(parsed) >= 3:
                    caliber_stats = parsed

    # Build output
    output = {
        'baseAmmoDamage': base_ammo_damage,
        'calibers': caliber_stats or {},
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Extracted {len(base_ammo_damage)} ammo types, {len(caliber_stats or {})} caliber stat sets → {output_path}")
    return output


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.extract_calibers <dump_path> [output_path]")
        sys.exit(1)

    dump_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else 'public/data/caliber-modifiers.json'
    extract_calibers(dump_path, output_path)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /opt/sulfur-calculator && python3 -m pytest tests/test_extract_calibers.py -v
```

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
cd /opt/sulfur-calculator
git add scripts/extract_calibers.py tests/test_extract_calibers.py
git commit -m "feat: add caliber extractor with tests"
```

---

## Task 7: Diff Tool

**Files:**
- Create: `scripts/diff_data.py`
- Create: `tests/test_diff_data.py`

- [ ] **Step 1: Write tests for diff tool**

```python
# tests/test_diff_data.py
import pytest
import json
import os
import tempfile
from scripts.diff_data import diff_json_files, diff_json_arrays, diff_json_objects

class TestDiffJsonArrays:
    def test_added_items(self):
        old = [{"name": "A"}, {"name": "B"}]
        new = [{"name": "A"}, {"name": "B"}, {"name": "C"}]
        added, removed, changed = diff_json_arrays(old, new, key='name')
        assert added == ['C']
        assert removed == []
        assert changed == []

    def test_removed_items(self):
        old = [{"name": "A"}, {"name": "B"}]
        new = [{"name": "A"}]
        added, removed, changed = diff_json_arrays(old, new, key='name')
        assert added == []
        assert removed == ['B']

    def test_changed_items(self):
        old = [{"name": "A", "val": 1}]
        new = [{"name": "A", "val": 2}]
        added, removed, changed = diff_json_arrays(old, new, key='name')
        assert added == []
        assert removed == []
        assert len(changed) == 1
        assert changed[0][0] == 'A'

class TestDiffJsonObjects:
    def test_added_keys(self):
        old = {"a": 1}
        new = {"a": 1, "b": 2}
        added, removed, changed = diff_json_objects(old, new)
        assert added == ['b']
        assert removed == []

    def test_changed_values(self):
        old = {"a": 1}
        new = {"a": 2}
        added, removed, changed = diff_json_objects(old, new)
        assert len(changed) == 1
        assert changed[0] == ('a', 1, 2)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /opt/sulfur-calculator && python3 -m pytest tests/test_diff_data.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement diff_data.py**

```python
# scripts/diff_data.py
"""Compare old vs new JSON data files and print human-readable diff."""

import json
import sys
import os
from typing import Any, Dict, List, Tuple


def diff_json_arrays(old: List[Dict], new: List[Dict], key: str = 'name') -> Tuple[List[str], List[str], List[Tuple[str, Dict]]]:
    """
    Compare two lists of dicts by a key field.

    Returns: (added_names, removed_names, changed_items)
    changed_items is list of (name, {field: (old_val, new_val)})
    """
    old_by_key = {item[key]: item for item in old}
    new_by_key = {item[key]: item for item in new}

    old_keys = set(old_by_key.keys())
    new_keys = set(new_by_key.keys())

    added = sorted(new_keys - old_keys)
    removed = sorted(old_keys - new_keys)

    changed = []
    for name in sorted(old_keys & new_keys):
        old_item = old_by_key[name]
        new_item = new_by_key[name]
        if old_item != new_item:
            diffs = {}
            all_fields = set(list(old_item.keys()) + list(new_item.keys()))
            for field in all_fields:
                old_val = old_item.get(field)
                new_val = new_item.get(field)
                if old_val != new_val:
                    diffs[field] = (old_val, new_val)
            changed.append((name, diffs))

    return added, removed, changed


def diff_json_objects(old: Dict, new: Dict) -> Tuple[List[str], List[str], List[Tuple[str, Any, Any]]]:
    """
    Compare two flat dicts.

    Returns: (added_keys, removed_keys, changed_tuples)
    changed_tuples is list of (key, old_val, new_val)
    """
    old_keys = set(old.keys())
    new_keys = set(new.keys())

    added = sorted(new_keys - old_keys)
    removed = sorted(old_keys - new_keys)

    changed = []
    for key in sorted(old_keys & new_keys):
        if old[key] != new[key]:
            changed.append((key, old[key], new[key]))

    return added, removed, changed


def diff_json_files(old_dir: str, new_dir: str):
    """Compare all JSON files in old_dir vs new_dir and print report."""
    files_to_compare = [
        ('weapons.json', 'name'),
        ('enchantments.json', 'name'),
        ('scrolls.json', 'name'),
        ('attachments-muzzle.json', 'name'),
        ('attachments-sights.json', 'name'),
        ('attachments-lasers.json', 'name'),
        ('attachments-chamber.json', 'name'),
        ('attachments-chisels.json', 'name'),
        ('attachments-insurance.json', 'name'),
    ]

    for filename, key_field in files_to_compare:
        old_path = os.path.join(old_dir, filename)
        new_path = os.path.join(new_dir, filename)

        if not os.path.exists(old_path):
            print(f"\n--- {filename}: OLD FILE MISSING ---")
            continue
        if not os.path.exists(new_path):
            print(f"\n--- {filename}: NEW FILE MISSING ---")
            continue

        with open(old_path) as f:
            old_data = json.load(f)
        with open(new_path) as f:
            new_data = json.load(f)

        if isinstance(old_data, list):
            added, removed, changed = diff_json_arrays(old_data, new_data, key=key_field)
        else:
            # caliber-modifiers.json is an object
            added, removed, changed_tuples = diff_json_objects(old_data, new_data)
            changed = [(k, {'value': (o, n)}) for k, o, n in changed_tuples]

        if not added and not removed and not changed:
            print(f"\n--- {filename}: NO CHANGES ---")
            continue

        print(f"\n--- {filename} ---")
        if added:
            print(f"  ADDED ({len(added)}):")
            for name in added:
                print(f"    + {name}")
        if removed:
            print(f"  REMOVED ({len(removed)}):")
            for name in removed:
                print(f"    - {name}")
        if changed:
            print(f"  CHANGED ({len(changed)}):")
            for name, diffs in changed:
                print(f"    ~ {name}:")
                if isinstance(diffs, dict):
                    for field, (old_val, new_val) in diffs.items():
                        print(f"        {field}: {old_val} → {new_val}")

    # Handle caliber-modifiers.json separately (object, not array)
    cal_old = os.path.join(old_dir, 'caliber-modifiers.json')
    cal_new = os.path.join(new_dir, 'caliber-modifiers.json')
    if os.path.exists(cal_old) and os.path.exists(cal_new):
        with open(cal_old) as f:
            old_cal = json.load(f)
        with open(cal_new) as f:
            new_cal = json.load(f)

        if old_cal != new_cal:
            print(f"\n--- caliber-modifiers.json ---")
            for section in ['baseAmmoDamage', 'calibers']:
                if old_cal.get(section) != new_cal.get(section):
                    print(f"  {section} changed")
                    added, removed, changed = diff_json_objects(
                        old_cal.get(section, {}),
                        new_cal.get(section, {})
                    )
                    for k in added:
                        print(f"    + {k}: {new_cal[section][k]}")
                    for k in removed:
                        print(f"    - {k}")
                    for k, o, n in changed:
                        print(f"    ~ {k}: {o} → {n}")
        else:
            print(f"\n--- caliber-modifiers.json: NO CHANGES ---")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python -m scripts.diff_data <old_dir> <new_dir>")
        print("Example: python -m scripts.diff_data public/data.bak public/data")
        sys.exit(1)

    diff_json_files(sys.argv[1], sys.argv[2])
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /opt/sulfur-calculator && python3 -m pytest tests/test_diff_data.py -v
```

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
cd /opt/sulfur-calculator
git add scripts/diff_data.py tests/test_diff_data.py
git commit -m "feat: add JSON diff tool with tests"
```

---

## Task 8: Update Runner + Path Updates

**Files:**
- Create: `scripts/update_all.py`
- Modify: `parse_wiki_weapon_attachments.py:18-20`
- Modify: `extract_specific_attachments.py:17-18`

- [ ] **Step 1: Implement update_all.py**

```python
# scripts/update_all.py
"""
Master runner: extract all data from a SULFUR wiki dump.

Usage:
    python -m scripts.update_all <dump_xml_path> [--output-dir public/data] [--backup]

Steps:
1. Back up existing data (if --backup)
2. Extract attachments (needed by weapon extractor for specificAttachments)
3. Extract weapons (uses attachment names)
4. Extract enchantments
5. Extract scrolls
6. Extract calibers
7. Print summary
"""

import argparse
import json
import os
import shutil
import sys

from scripts.extract_attachments import extract_attachments
from scripts.extract_weapons import extract_weapons
from scripts.extract_enchantments import extract_enchantments
from scripts.extract_scrolls import extract_scrolls
from scripts.extract_calibers import extract_calibers


def main():
    parser = argparse.ArgumentParser(description='Extract all SULFUR data from wiki dump')
    parser.add_argument('dump_path', help='Path to the wiki XML dump file')
    parser.add_argument('--output-dir', default='public/data', help='Output directory for JSON files')
    parser.add_argument('--backup', action='store_true', help='Back up existing data before overwriting')
    args = parser.parse_args()

    dump_path = args.dump_path
    output_dir = args.output_dir

    if not os.path.exists(dump_path):
        print(f"Error: Dump file not found: {dump_path}")
        sys.exit(1)

    # Step 0: Backup
    if args.backup and os.path.exists(output_dir):
        backup_dir = output_dir + '.bak'
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)
        shutil.copytree(output_dir, backup_dir)
        print(f"Backed up {output_dir} → {backup_dir}")

    # Step 1: Extract attachments first (weapon extractor needs the names)
    print("\n=== Extracting Attachments ===")
    attachment_names = extract_attachments(dump_path, output_dir)

    # Step 2: Extract weapons with attachment data
    print("\n=== Extracting Weapons ===")
    weapons_path = os.path.join(output_dir, 'weapons.json')
    extract_weapons(dump_path, weapons_path, attachment_data=attachment_names)

    # Step 3: Extract enchantments
    print("\n=== Extracting Enchantments ===")
    enchantments_path = os.path.join(output_dir, 'enchantments.json')
    extract_enchantments(dump_path, enchantments_path)

    # Step 4: Extract scrolls
    print("\n=== Extracting Scrolls ===")
    scrolls_path = os.path.join(output_dir, 'scrolls.json')
    extract_scrolls(dump_path, scrolls_path)

    # Step 5: Extract calibers
    print("\n=== Extracting Calibers ===")
    calibers_path = os.path.join(output_dir, 'caliber-modifiers.json')
    extract_calibers(dump_path, calibers_path)

    print("\n=== Extraction Complete ===")
    print(f"All data written to {output_dir}/")

    # Summary counts
    for filename in sorted(os.listdir(output_dir)):
        if filename.endswith('.json'):
            filepath = os.path.join(output_dir, filename)
            with open(filepath) as f:
                data = json.load(f)
            count = len(data) if isinstance(data, list) else len(data.keys())
            print(f"  {filename}: {count} entries")


if __name__ == '__main__':
    main()
```

- [ ] **Step 2: Update old script paths**

In `parse_wiki_weapon_attachments.py`, update lines 18-20:

```python
# Old:
WIKI_DUMP_PATH = "/mnt/z/Claude/sulfurdump/sulfur.wiki.gg-20251224-wikidump/sulfur.wiki.gg-20251224-history-fixed.xml"
OUTPUT_PATH = "/mnt/z/Claude/Sulfur_Data/sulfur-calculator-github/weapon_attachments_from_wiki.json"
WEAPONS_JSON_PATH = "/mnt/z/Claude/Sulfur_Data/sulfur-calculator-github/public/data/weapons.json"

# New — use command-line args or env vars with fallback
WIKI_DUMP_PATH = os.environ.get('SULFUR_DUMP_PATH', "/mnt/z/Claude/sulfurdump/sulfur.wiki.gg-20251224-wikidump/sulfur.wiki.gg-20251224-history-fixed.xml")
OUTPUT_PATH = os.environ.get('SULFUR_OUTPUT_PATH', "weapon_attachments_from_wiki.json")
WEAPONS_JSON_PATH = os.environ.get('SULFUR_WEAPONS_JSON', "public/data/weapons.json")
```

In `extract_specific_attachments.py`, update lines 17-18:

```python
# Old:
WIKI_DUMP_PATH = "/mnt/z/Claude/sulfurdump/sulfur.wiki.gg-20251224-wikidump/sulfur.wiki.gg-20251224-history.xml"
OUTPUT_PATH = "/mnt/z/Claude/Sulfur_Data/sulfur-calculator-github/weapon_specific_attachments.json"

# New:
WIKI_DUMP_PATH = os.environ.get('SULFUR_DUMP_PATH', "/mnt/z/Claude/sulfurdump/sulfur.wiki.gg-20251224-wikidump/sulfur.wiki.gg-20251224-history.xml")
OUTPUT_PATH = os.environ.get('SULFUR_OUTPUT_PATH', "weapon_specific_attachments.json")
```

Also add `import os` at the top of `extract_specific_attachments.py` if missing.

- [ ] **Step 3: Run all tests**

```bash
cd /opt/sulfur-calculator && python3 -m pytest tests/ -v
```

Expected: All tests PASS.

- [ ] **Step 4: Commit**

```bash
cd /opt/sulfur-calculator
git add scripts/update_all.py parse_wiki_weapon_attachments.py extract_specific_attachments.py
git commit -m "feat: add update runner and make dump paths configurable"
```

---

## Task 9: Download Fresh Wiki Dump

**This task is manual — the user runs wikiteam3.**

- [ ] **Step 1: Install/verify wikiteam3**

```bash
pip install wikiteam3
```

- [ ] **Step 2: Download the dump**

```bash
cd /mnt/z/Claude/sulfurdump
wikiteam3dumpgenerator --xml --images "https://sulfur.wiki.gg/"
```

This will create a new directory like `sulfur.wiki.gg-20260331-wikidump/` with the XML dump inside.

- [ ] **Step 3: Verify the dump exists**

```bash
ls /mnt/z/Claude/sulfurdump/sulfur.wiki.gg-2026*/*.xml
```

Expected: At least one XML file in the new dump directory.

---

## Task 10: Run Full Extraction Pipeline

- [ ] **Step 1: Back up existing data**

```bash
cd /opt/sulfur-calculator
cp -r public/data public/data.bak
```

- [ ] **Step 2: Run the extraction pipeline**

Replace `<DUMP_PATH>` with the actual path to the new XML file:

```bash
cd /opt/sulfur-calculator
python3 -m scripts.update_all /mnt/z/Claude/sulfurdump/sulfur.wiki.gg-YYYYMMDD-wikidump/sulfur.wiki.gg-YYYYMMDD-history.xml --output-dir public/data
```

Expected: Output showing extraction counts for each category.

- [ ] **Step 3: Run diff report**

```bash
cd /opt/sulfur-calculator
python3 -m scripts.diff_data public/data.bak public/data
```

Expected: Human-readable summary showing what changed between old and new data.

- [ ] **Step 4: Spot-check results**

```bash
cd /opt/sulfur-calculator
python3 -c "
import json
for f in ['weapons', 'enchantments', 'scrolls']:
    with open(f'public/data/{f}.json') as fh:
        data = json.load(fh)
    print(f'{f}: {len(data)} items')
    if data:
        print(f'  First: {data[0][\"name\"]}')
        print(f'  Last: {data[-1][\"name\"]}')
"
```

- [ ] **Step 5: Build the app to verify no breakage**

```bash
cd /opt/sulfur-calculator
npm run build
```

Expected: Build completes without errors.

- [ ] **Step 6: Commit updated data**

```bash
cd /opt/sulfur-calculator
git add public/data/
git commit -m "data: update all game data from 2026-03-31 wiki dump"
```

- [ ] **Step 7: Clean up backup**

```bash
rm -rf /opt/sulfur-calculator/public/data.bak
```
