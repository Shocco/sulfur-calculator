# SULFUR Weapon Attachments Extraction Report v2

**Date:** 2025-12-28
**Script:** `extract_weapon_attachments_v2.py`
**Output:** `weapon_attachments_from_wiki_v2.json`

## Summary

Successfully extracted weapon attachment compatibility data for **ALL 45 weapons** from the SULFUR wiki dump.

### Key Statistics

- **Total weapons in weapons.json:** 45
- **Weapons found in wiki:** 45 (100%)
- **Weapons with attachment data:** 44 (97.8%)
- **Weapons missing attachment data:** 1 (D4RT - no attachments section in wiki)
- **Missing weapons:** 0

## Previously Missed Weapons (NOW FOUND)

All 6 previously missed weapons have been successfully extracted:

### 1. .357 Balthazar
- Muzzle Attachments
- Sight
- Laser Sights
- Gun Crank
- Chamber Chisel

### 2. Bronco 89
- Muzzle Attachments
- Sight
- Laser Sights
- Gun Crank
- Chamber Chisel

### 3. D4RT
- **No attachments section found in wiki**
- This weapon may not support attachments

### 4. Flicker
- Muzzle Attachments
- Sight
- Laser Sights
- Gun Crank
- Chamber Chisel

### 5. Salamander
- Muzzle Attachments
- Sight
- Laser Sights
- Gun Crank
- Chamber Chisel

### 6. Tailor Marksman MKII
- Muzzle Attachments
- Sight
- Laser Sights
- Gun Crank
- Chamber Chisel

## Attachment Type Analysis

### Unique Attachment Types Found

| Attachment Type | Number of Weapons |
|----------------|------------------|
| Sight | 44 |
| Laser Sights | 44 |
| Chamber Chisel | 39 |
| Muzzle Attachments | 38 |
| Gun Crank | 26 |
| Priming Bolt | 13 |
| Muzzle | 1 (Impala Gravita) |

### Distribution by Attachment Count

| Attachment Count | Number of Weapons |
|-----------------|------------------|
| 0 attachments | 1 (D4RT) |
| 2 attachments | 3 (Catacoil Rapid X, Unknown, Wyatt PULSAR) |
| 3 attachments | 2 (Augusta, Neuraxis F22) |
| 4 attachments | 2 (Breacher 8, Impala Gravita) |
| 5 attachments | 37 (majority) |

## Improvements in v2

### Enhanced Parsing Capabilities

1. **Case-insensitive section matching:** Handles variations like `==Available Attachments==` and `== Available Attachments ==`

2. **Robust wikilink extraction:** Properly extracts targets from both:
   - Simple links: `[[Muzzle Attachments]]` → `Muzzle Attachments`
   - Piped links: `[[Sight|Sights]]` → `Sight`
   - Complex links: `[[Chamber Chisel|Chamber Chisels]]` → `Chamber Chisel`

3. **Multi-line content handling:** Correctly parses sections that span multiple lines

4. **Bullet point support:** Handles various bullet formats:
   - Unicode bullet: `•`
   - Asterisk: `*`
   - Hyphen: `-`

5. **Memory-efficient XML parsing:** Uses `iterparse` for large XML files

### Parsing Strategy

The script:
1. Loads all weapon names from `weapons.json`
2. Iterates through the wiki XML dump
3. For each weapon page found:
   - Locates the "Available Attachments" section
   - Extracts all wikilinks in that section
   - Filters out generic terms like "Attachments"
   - Stores the attachment type names
4. Reports on found/missing weapons
5. Outputs structured JSON with metadata

## Data Quality Notes

### Note on "Muzzle" vs "Muzzle Attachments"

One weapon (Impala Gravita) uses just "Muzzle" instead of "Muzzle Attachments". This may be:
- A wiki inconsistency
- A different attachment type
- A shortened version of the same thing

Recommend verifying in-game whether these are the same attachment type.

### D4RT Missing Attachments

The D4RT weapon page in the wiki does not have an "Available Attachments" section. This could mean:
- The weapon genuinely doesn't support attachments
- The wiki page is incomplete
- The section uses different formatting

Recommend checking the wiki page manually or in-game to verify.

## Output File Structure

```json
{
  "metadata": {
    "total_weapons": 45,
    "weapons_found": 45,
    "weapons_with_attachments": 44,
    "missing_weapons": []
  },
  "weapons": {
    "Weapon Name": ["Attachment1", "Attachment2", ...],
    ...
  }
}
```

## Files

- **Script:** `/mnt/z/Claude/Sulfur_Data/extract_weapon_attachments_v2.py`
- **Output:** `/mnt/z/Claude/Sulfur_Data/sulfur-calculator-github/weapon_attachments_from_wiki_v2.json`
- **Report:** `/mnt/z/Claude/Sulfur_Data/sulfur-calculator-github/WEAPON_ATTACHMENTS_EXTRACTION_REPORT.md`

## Next Steps

Consider:
1. Verifying D4RT's attachment support in-game
2. Normalizing "Muzzle" vs "Muzzle Attachments"
3. Extracting attachment stat modifiers from the wiki
4. Cross-referencing with in-game data extraction
