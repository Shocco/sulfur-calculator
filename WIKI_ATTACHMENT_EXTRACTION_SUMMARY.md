# SULFUR Wiki Weapon Attachment Extraction Summary

## Overview

This document summarizes the extraction of weapon attachment compatibility data from the SULFUR wiki dump dated 2025-12-24.

## Extraction Results

### Statistics

- **Wiki Dump Source**: `/mnt/z/Claude/sulfurdump/sulfur.wiki.gg-20251224-wikidump/sulfur.wiki.gg-20251224-history-fixed.xml`
- **Total Weapon Pages Found**: 40
- **Weapons with Attachment Data**: 39
- **Total Weapons in weapons.json**: 45
- **Weapons Found in Both**: 39

### Output Files

- **Primary Output**: `/mnt/z/Claude/Sulfur_Data/sulfur-calculator-github/weapon_attachments_from_wiki.json`
- **Extraction Script**: `/mnt/z/Claude/Sulfur_Data/sulfur-calculator-github/parse_wiki_weapon_attachments.py`

## Data Format

The output JSON file maps weapon names to lists of compatible attachment categories:

```json
{
  "Weapon Name": [
    "Attachment Category 1",
    "Attachment Category 2",
    ...
  ]
}
```

### Example

```json
{
  "Beck 8": [
    "Attachments",
    "Muzzle Attachments",
    "Sight",
    "Laser Sights",
    "Gun Crank",
    "Chamber Chisel"
  ]
}
```

## Attachment Categories Found

The following attachment categories were extracted from the wiki:

1. **Attachments** (generic category - appears on some weapons)
2. **Chamber Chisel** / **Chamber Chisels** (caliber conversion)
3. **Gun Crank** (rate of fire modifier)
4. **Laser Sights** (laser targeting)
5. **Muzzle** / **Muzzle Attachments** (muzzle devices)
6. **Priming Bolt** (rifle attachment)
7. **Sight** / **Sights** (optics)

## Weapons with Attachment Data

### Complete List (39 weapons)

1. 1889 Mario - 6 attachments
2. Arbiter 2 - 5 attachments
3. Augusta - 4 attachments
4. Beck 8 - 6 attachments
5. Breacher 8 - 4 attachments
6. Catacoil Rapid X - 2 attachments ⚠️
7. Corpsemaker - 5 attachments
8. Deathstar PG - 6 attachments
9. Dolphin 99 - 5 attachments
10. Drifter 9 - 6 attachments
11. Duhar - 6 attachments
12. Farsight - 6 attachments
13. Ferryman - 5 attachments
14. Flock 76 - 5 attachments
15. Gravekeeper - 6 attachments
16. Hell 'N' Back - 6 attachments
17. Impala Gravita - 4 attachments
18. Knop .22 - 5 attachments
19. Longboy - 5 attachments
20. M11A2 Fisk - 5 attachments
21. M182 Pierre-Fusil - 5 attachments
22. M3 Termite - 6 attachments
23. Majordome - 6 attachments
24. Mossman - 5 attachments
25. Neuraxis F22 - 4 attachments
26. P38 Dirk - 6 attachments
27. Palehorse Topclipper - 6 attachments
28. Ploika Compact - 6 attachments
29. Rektor 100rd - 6 attachments
30. Rokua .308 - 5 attachments
31. Snut .38 - 6 attachments
32. Socom 9 - 6 attachments
33. Star & Witness - 6 attachments
34. Type 80 Typhoon - 5 attachments
35. Unknown - 3 attachments
36. Valet - 6 attachments
37. Vrede - 6 attachments
38. Wingman - 5 attachments
39. Wyatt PULSAR - 3 attachments

## Missing or Incomplete Data

### Weapons in weapons.json but NOT Found in Wiki (6 weapons)

These weapons exist in the game data but don't have an "Available Attachments" section in their wiki pages:

1. **.357 Balthazar** - Has Weapon Infobox but no attachments section
2. **Bronco 89** - No weapon infobox on wiki page
3. **D4RT** - No weapon infobox on wiki page
4. **Flicker** - No weapon infobox on wiki page
5. **Salamander** - No weapon infobox on wiki page
6. **Tailor Marksman MKII** - No weapon infobox on wiki page

**Possible Reasons**:
- Pages may be stubs or incomplete
- Weapons may be recently added to the game
- Wiki content may not be fully up-to-date
- Some weapons may use redirects to parent pages

### Weapons with Unusually Few Attachments

**Catacoil Rapid X** - Only 2 attachment categories (Sight, Laser Sights)
- This may be accurate for this specific weapon
- It's a unique weapon type that may have limited customization

## Data Quality Notes

### Consistent Patterns

Most weapons follow these typical patterns:

**Pistols** (6 attachments):
- Muzzle Attachments
- Sight
- Laser Sights
- Gun Crank
- Chamber Chisel
- (Sometimes generic "Attachments")

**Rifles** (5-6 attachments):
- Muzzle Attachments
- Sight
- Laser Sights
- Priming Bolt (rifles only)
- Chamber Chisel

**SMGs/PDWs** (similar to pistols):
- Muzzle Attachments
- Sight
- Laser Sights
- Gun Crank
- Chamber Chisel

### Extraction Methodology

The script parses MediaWiki XML format and:

1. Identifies weapon pages by looking for `{{Weapon Infobox}}` or `{{Item Infobox}}` with `| kind = weapon`
2. Extracts the `==Available Attachments==` section from the wikitext
3. Parses wikilinks `[[Attachment Category]]` from bullet lists
4. Handles various bullet point styles (*, •, ·, -)
5. Filters out non-attachment links (categories, files, etc.)

## Recommendations

### For Wiki Content

1. **Add "Available Attachments" sections** to the 6 weapons that are missing this information:
   - .357 Balthazar
   - Bronco 89
   - D4RT
   - Flicker
   - Salamander
   - Tailor Marksman MKII

2. **Standardize attachment category names**:
   - Use either "Muzzle" or "Muzzle Attachments" consistently
   - Use either "Sight" or "Sights" consistently
   - Remove generic "Attachments" in favor of specific categories

3. **Verify Catacoil Rapid X** attachments - confirm if only 2 categories is correct

### For Data Integration

1. **Map category names to specific attachments**: The current data shows attachment *categories* (e.g., "Muzzle Attachments"). You may want to cross-reference with the specific attachment JSON files to get exact attachment names.

2. **Handle missing weapons**: The 6 weapons without wiki data should either:
   - Have their wiki pages updated
   - Use default attachment rules based on weapon type
   - Be flagged for manual data entry

3. **Normalize attachment names**: Create a mapping between wiki category names and the attachment category slugs used in the calculator (e.g., "Muzzle Attachments" → "muzzle")

## Cross-Reference with Existing Data

The weapons.json file in the calculator already has `allowedAttachments` arrays with categories like:
- `"chamber"`
- `"chisel"`
- `"laser"`
- `"muzzle"`
- `"sight"`

The wiki data provides human-readable names for these categories:
- Chamber Chisel → chisel
- Laser Sights → laser
- Muzzle/Muzzle Attachments → muzzle
- Sight/Sights → sight

Some weapons also have `specificAttachments` arrays listing exact attachment names (e.g., "Holographic Sight", "M87 'Albatross' Silencer").

## Conclusion

The extraction successfully captured attachment compatibility data for 39 out of 45 weapons (87%). The data is consistent and follows predictable patterns based on weapon types. The 6 missing weapons should be investigated, but the extraction provides a solid foundation for weapon-attachment compatibility mapping.
