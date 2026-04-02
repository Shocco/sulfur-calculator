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

        # Get the most recent revision (last in history dumps)
        revisions = elem.findall('mw:revision', ns_map)
        if not revisions:
            elem.clear()
            continue

        revision = revisions[-1]
        text_elem = revision.find('mw:text', ns_map)
        if text_elem is None or not text_elem.text:
            elem.clear()
            continue

        yield title, text_elem.text
        elem.clear()


def _parse_infobox_body(body: str) -> Dict[str, str]:
    """Parse key-value pairs from an infobox body string."""
    result = {}
    # Split body into lines, then reassemble param values
    current_key = None
    current_val_lines: List[str] = []

    for line in body.split('\n'):
        stripped = line.strip()
        # Check if this is a new param: starts with | key =
        m = re.match(r'\|\s*([\w\s]+?)\s*=\s*(.*)', stripped)
        if m:
            # Save previous param
            if current_key is not None:
                val = '\n'.join(current_val_lines).strip()
                if val:
                    result[current_key] = val
            current_key = m.group(1).strip()
            current_val_lines = [m.group(2).strip()]
        elif stripped and not stripped.startswith('}}') and current_key is not None:
            # Continuation of previous value
            current_val_lines.append(stripped)

    # Save last param
    if current_key is not None:
        val = '\n'.join(current_val_lines).strip()
        if val:
            result[current_key] = val

    return result


def parse_infobox(wikitext: str) -> Dict[str, str]:
    """
    Extract key-value pairs from a {{Item Infobox ...}} template.

    Returns dict of param_name -> raw_value (strings, not yet parsed).
    """
    match = re.search(r'\{\{Item Infobox(.*?)\}\}', wikitext, re.DOTALL)
    if not match:
        return {}
    return _parse_infobox_body(match.group(1))


def parse_weapon_infobox(wikitext: str) -> Optional[Dict[str, str]]:
    """
    Extract key-value pairs from a {{Weapon_Infobox ...}} template.

    Returns dict of param_name -> raw_value, or None if not found.
    """
    match = re.search(r'\{\{Weapon[_ ]Infobox(.*?)\}\}', wikitext, re.DOTALL)
    if not match:
        return None
    return _parse_infobox_body(match.group(1))


def parse_modifier_value(raw: str) -> Tuple[int, float]:
    """
    Parse a modifier value string from the wiki into (modType, value).

    - "+30%" or "-30%" -> (200, 0.3) or (200, -0.3)  [PercentAdd]
    - "+15" or "-15" or "0.3" or "-0.75" -> (100, value)  [Flat]
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

    "60" -> (60.0, 1)
    "40x8" or "40&times;8" -> (40.0, 8)
    """
    raw = raw.replace('&times;', '\u00d7')
    if '\u00d7' in raw:
        parts = raw.split('\u00d7')
        count_str = re.match(r'\d+', parts[1].strip())
        return (float(parts[0].strip()), int(count_str.group()) if count_str else 1)
    # Strip trailing non-numeric chars
    num_match = re.match(r'[\d.]+', raw.strip())
    return (float(num_match.group()) if num_match else 0.0, 1)


def extract_wikilink_text(raw: str) -> str:
    """
    Extract display text from a wikilink.

    "[[9mm]]" -> "9mm"
    "[[Pistols|Pistol]]" -> "Pistol"
    "Shotgun" -> "Shotgun"
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
    pattern = rf'==\s*{re.escape(heading)}\s*==\s*(.*?)(?:\n==|$)'
    match = re.search(pattern, wikitext, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def extract_bullet_points(text: str) -> List[str]:
    """Extract bullet point text from wiki markup, stripping formatting."""
    points = []
    for line in text.split('\n'):
        line = line.strip()
        if line.startswith(('*', '\u2022', '\u00b7', '-')):
            content = line.lstrip('*\u2022\u00b7- ').strip()
            # Remove bold/italic markup
            content = re.sub(r"'''|''", '', content)
            if content:
                points.append(content)
    return points
