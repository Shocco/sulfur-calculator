# SULFUR Weapon Specific Attachments Extraction

## Summary

Successfully extracted specific attachment names for each weapon from the SULFUR wiki dump.

### Extraction Results

- **Total weapons found**: 39
- **Total unique attachments**: 32
- **Attachment categories**: 5 (Muzzle, Sights, Laser Sights, Chamber Attachments, Chamber Chisels)

### Files Generated

- `weapon_specific_attachments.json` - Complete mapping of weapons to their compatible attachments
- `extract_specific_attachments.py` - Extraction script

## Attachment Categories

### Muzzle Attachments (14 items)
- A12C Muzzle Brake
- Aftermarket Haukland Silencer
- Barrel Extension 2"
- Barrel Extension 4"
- Barrel Extension 6"
- Breznik BMD
- Breznik BMD (Tactical)
- Haukland Flash Hider
- Haukland Silencer
- Improvised Barrel Extension
- M87 "Albatross" Silencer
- Shrouded Barrel Extension
- SR-P3 Silencer
- Warmage Compensator

### Sights (7 items)
- Assault Scope
- Compact Sight
- Holographic Sight
- Hunting Scope
- Recon Scope
- Reflex Sight
- Sniper Scope

### Laser Sights (3 items)
- Laser Sight (Green)
- Laser Sight (Red)
- Laser Sight (Yellow)

### Chamber Attachments (2 items)
- Gun Crank - Converts semi-auto/single/double action to full-auto
- Priming Bolt - Converts automatic to semi-automatic

### Chamber Chisels (5 items)
- Chamber Chisel (.50 BMG)
- Chamber Chisel (12Ga)
- Chamber Chisel (5.56mm)
- Chamber Chisel (7.62mm)
- Chamber Chisel (9mm)

## Key Findings

### Chamber Attachment Usage Pattern

**Gun Crank** (21 weapons) - Semi-auto weapons that can become full-auto:
- 1889 Mario, Arbiter 2, Augusta, Beck 8, Deathstar PG
- Dolphin 99, Farsight, Gravekeeper, Hell 'N' Back, Knop .22
- Longboy, M182 Pierre-Fusil, M3 Termite, Majordome, Mossman
- P38 Dirk, Palehorse Topclipper, Rokua .308, Snut .38, Socom 9
- Star & Witness

**Priming Bolt** (13 weapons) - Full-auto weapons that can become semi-auto:
- Corpsemaker, Drifter 9, Duhar, Ferryman, Flock 76
- M11A2 Fisk, Neuraxis F22, Ploika Compact, Rektor 100rd
- Type 80 Typhoon, Valet, Vrede, Wingman

**No weapons** can use both Gun Crank and Priming Bolt - this is logical since they serve opposite purposes.

### Attachment Compatibility Patterns

**Full attachment suite (30 attachments)**:
- Most weapons support all muzzle attachments, sights, laser sights, and chamber chisels
- 26 weapons have access to 29-30 attachments

**Limited attachment options (10-16 attachments)**:
- Augusta (11): Sights, Lasers, Gun Crank only
- Catacoil Rapid X (10): Sights and Lasers only
- Unknown (10): Sights and Lasers only
- Wyatt PULSAR (10): Sights and Lasers only
- Neuraxis F22 (11): Sights, Lasers, Priming Bolt only
- Impala Gravita (16): Limited set including Gun Crank

## Data Format

The output JSON follows this structure:

```json
{
  "Weapon Name": [
    "Attachment 1",
    "Attachment 2",
    ...
  ]
}
```

Example:
```json
{
  "Beck 8": [
    "A12C Muzzle Brake",
    "Aftermarket Haukland Silencer",
    "Assault Scope",
    "Barrel Extension 2\"",
    "Compact Sight",
    "Gun Crank",
    "Haukland Flash Hider",
    "Laser Sight (Green)",
    "Laser Sight (Red)",
    "Laser Sight (Yellow)",
    ...
  ]
}
```

## Extraction Method

The script parses the MediaWiki XML dump and:

1. Identifies all attachment items by their category tags
2. Groups attachments into their respective categories
3. Finds weapon pages with "==Available Attachments==" sections
4. Extracts the attachment type references (e.g., "Muzzle Attachments", "Gun Crank")
5. Maps each weapon to specific attachment names by:
   - Expanding category references to individual attachments
   - Including individual attachments directly (like "Gun Crank")

## Notes

- Some weapons like "Unknown" appear to be placeholder/test weapons
- The wiki uses both category-based attachment types and individual attachments
- All attachment names are extracted from the latest revision of each page
- Weapons with fewer attachments are typically energy/special weapons that don't use standard attachments
