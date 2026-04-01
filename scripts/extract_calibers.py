"""Extract caliber/ammo data from a MediaWiki XML dump for the SULFUR calculator."""

import json
import re
import sys
from typing import Dict, Optional, Tuple

from scripts.wiki_parser import (
    extract_section,
    extract_wikilink_text,
    iterate_pages,
    parse_infobox,
)

# ---------------------------------------------------------------------------
# Caliber name normalization
# ---------------------------------------------------------------------------

_CALIBER_ALIASES: Dict[str, str] = {
    "12ga": "12Ga",
    "12Ga": "12Ga",
    "50 BMG": ".50 BMG",
    ".50 BMG": ".50 BMG",
}


def _normalize_caliber(raw: str) -> str:
    """Normalize a raw caliber name to its canonical form.

    Args:
        raw: Raw caliber string extracted from wiki markup.

    Returns:
        Canonical caliber name (e.g. ``"12Ga"``, ``".50 BMG"``).
    """
    stripped = raw.strip()
    return _CALIBER_ALIASES.get(stripped, stripped)


# ---------------------------------------------------------------------------
# Ammo page parser
# ---------------------------------------------------------------------------


def parse_ammo_page(title: str, wikitext: str) -> Optional[Tuple[str, int]]:
    """Parse an ammo wiki page and return ``(caliber_name, base_damage)``.

    Args:
        title: Page title from the XML dump. Used as the caliber name.
        wikitext: Raw wikitext content of the page.

    Returns:
        A tuple of ``(caliber_name, base_damage)`` when the page has
        ``kind=ammo`` and a parseable ``Base Damage`` field, otherwise
        ``None``.
    """
    infobox = parse_infobox(wikitext)
    if infobox.get("kind", "").strip().lower() != "ammo":
        return None

    raw_damage = infobox.get("Base Damage", "").strip()
    if not raw_damage:
        return None

    try:
        base_damage = int(raw_damage)
    except ValueError:
        return None

    caliber_name = _normalize_caliber(title)
    return caliber_name, base_damage


# ---------------------------------------------------------------------------
# Caliber modding table parser
# ---------------------------------------------------------------------------


def parse_caliber_table(table_text: str) -> Dict[str, Dict]:
    """Parse a wiki caliber modding table into a dict of caliber stats.

    The expected table format is::

        !Caliber!!Damage!!Projectiles!!Spread!!Recoil
        |-
        |style="text-align: left;|[[12ga]]||40||×8||4||10
        |-
        |style="text-align: left;|[[9mm]]||120||×1||1||1

    Args:
        table_text: Raw wikitext of the wikitable (the full ``{| ... |}``
            block, or just the inner rows).

    Returns:
        Dict mapping caliber name to a stats dict with keys
        ``"Spread"``, ``"Recoil"``, and ``"ProjectileCount"``.
    """
    result: Dict[str, Dict] = {}

    # Split on row separators; each row after a `|-` is a data row.
    rows = table_text.split("|-")

    for row in rows:
        row = row.strip()
        if not row:
            continue

        # Skip header rows (lines that start with !)
        lines = [ln.strip() for ln in row.splitlines() if ln.strip()]
        if not lines:
            continue
        # A data row starts with | (not !) after stripping.
        first_line = lines[0]
        if first_line.startswith("!"):
            continue

        # Join everything and split on ||
        combined = "".join(lines)
        # Remove leading | if present
        if combined.startswith("|"):
            combined = combined[1:]

        cells = combined.split("||")
        if len(cells) < 5:
            continue

        # Cell 0: caliber (may have style prefix like `style="text-align: left;|[[9mm]]`)
        raw_caliber_cell = cells[0].strip()
        # Strip any style prefix ending with `|`
        pipe_idx = raw_caliber_cell.rfind("|")
        if pipe_idx != -1:
            raw_caliber_cell = raw_caliber_cell[pipe_idx + 1:].strip()

        caliber_raw = extract_wikilink_text(raw_caliber_cell)
        caliber = _normalize_caliber(caliber_raw)
        if not caliber:
            continue

        # Cell 2: Projectiles (format ×N)
        raw_proj = cells[2].strip()
        proj_match = re.match(r"[×x\u00d7](\d+)", raw_proj)
        projectile_count = int(proj_match.group(1)) if proj_match else 1

        # Cell 3: Spread
        try:
            spread = float(cells[3].strip())
        except ValueError:
            spread = 0.0

        # Cell 4: Recoil (strip trailing table-close marker `|}` if present)
        raw_recoil = cells[4].strip().rstrip("|}")
        try:
            recoil = float(raw_recoil.strip())
        except ValueError:
            recoil = 0.0

        result[caliber] = {
            "Spread": spread,
            "Recoil": recoil,
            "ProjectileCount": projectile_count,
        }

    return result


# ---------------------------------------------------------------------------
# Top-level extraction
# ---------------------------------------------------------------------------


def extract_calibers(dump_path: str, output_path: str) -> Dict:
    """Extract caliber data from a MediaWiki XML dump and write to JSON.

    Two data sources are combined:

    * **Ammo pages** (``kind=ammo``) supply ``baseAmmoDamage`` via the
      ``Base Damage`` infobox field. The page title is the caliber name.
    * **Weapon pages** that contain a ``== Caliber Modding ==`` section with a
      wikitable listing at least 3 caliber entries supply ``calibers`` stats
      (Spread, Recoil, ProjectileCount per caliber).

    Only the *first* qualifying weapon page is used for the caliber table.

    Args:
        dump_path: Path to the MediaWiki XML dump file.
        output_path: Path where the output JSON will be written.

    Returns:
        The output dict that was written (with keys ``baseAmmoDamage`` and
        ``calibers``).
    """
    base_ammo_damage: Dict[str, int] = {}
    calibers: Dict[str, Dict] = {}
    caliber_table_found = False

    for title, wikitext in iterate_pages(dump_path):
        # --- Ammo pages ---
        ammo_result = parse_ammo_page(title, wikitext)
        if ammo_result is not None:
            caliber_name, base_damage = ammo_result
            base_ammo_damage[caliber_name] = base_damage
            continue

        # --- Weapon pages: look for caliber modding table ---
        if caliber_table_found:
            continue

        section = extract_section(wikitext, "Caliber Modding")
        if section is None:
            continue

        # Find a wikitable within the section
        table_match = re.search(r"\{\|.*?\|\}", section, re.DOTALL)
        if table_match is None:
            continue

        table_text = table_match.group(0)
        parsed = parse_caliber_table(table_text)
        if len(parsed) >= 3:
            calibers = parsed
            caliber_table_found = True

    output = {
        "baseAmmoDamage": base_ammo_damage,
        "calibers": calibers,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Extracted {len(base_ammo_damage)} ammo entries and "
          f"{len(calibers)} caliber stats -> {output_path}")
    return output


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 -m scripts.extract_calibers <dump_path> [output_path]")
        sys.exit(1)

    dump = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "calibers.json"
    extract_calibers(dump, out)
