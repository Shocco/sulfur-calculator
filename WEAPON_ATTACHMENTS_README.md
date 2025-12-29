# Weapon Attachments Compatibility Data

This document describes the weapon attachment compatibility data extracted from the SULFUR wiki.

## Overview

The `weapon_attachments_compatibility.json` file contains a mapping of weapons to their compatible attachment types, extracted from the SULFUR wiki XML dump dated 2025-12-24.

## Data Source

- **Source File**: `/mnt/z/Claude/sulfurdump/sulfur.wiki.gg-20251224-wikidump/sulfur.wiki.gg-20251224-history.xml`
- **Extraction Script**: `parse_weapon_attachments.py`
- **Output File**: `weapon_attachments_compatibility.json`

## Extraction Method

The script parses the MediaWiki XML dump and:

1. Iterates through all wiki pages (2,857 total pages)
2. For each page, finds the most recent revision that contains an "Available Attachments" section
3. Parses the attachment types listed in that section
4. Maps wiki terminology to standardized attachment type IDs

## Attachment Types

The following attachment types are extracted:

- **muzzle**: Muzzle attachments (silencers, compensators, etc.)
- **sight**: Optical sights and scopes
- **laser**: Laser sights
- **chamber**: Chamber attachments (gun crank)
- **chisel**: Chamber chisels (caliber conversion)
- **insurance**: Gun insurance (not found in any weapons in current data)

## Statistics

- **Total weapons found**: 45 weapons
- **Weapons with muzzle**: 38 weapons (84%)
- **Weapons with sight**: 44 weapons (98%)
- **Weapons with laser**: 44 weapons (98%)
- **Weapons with chamber**: 34 weapons (76%)
- **Weapons with chisel**: 39 weapons (87%)
- **Weapons with insurance**: 0 weapons (0%)

## Weapon List

### Full Compatibility (all 5 types)

Most weapons support all attachment types except insurance:

- .357 Balthazar
- 1889 Mario
- Arbiter 2
- Beck 8
- Bronco 89
- Corpsemaker
- Deathstar PG
- Dolphin 99
- Drifter 9
- Duhar
- Flicker
- Flock 76
- Gravekeeper
- Hell 'N' Back
- Knop .22
- Longboy
- M11A2 Fisk
- M182 Pierre-Fusil
- M3 Termite
- Majordome
- Mossman
- P38 Dirk
- Palehorse Topclipper
- Ploika Compact
- Rektor 100rd
- Rokua .308
- Salamander
- Snut .38
- Socom 9
- Tailor Marksman MKII
- Type 80 Typhoon
- Vrede

### Limited Compatibility

Some weapons only support a subset of attachments:

- **Augusta**: chamber, laser, sight (no muzzle, chisel)
- **Breacher 8**: chisel, laser, muzzle, sight (no chamber)
- **Catacoil Rapid X**: laser, sight only
- **D4RT**: laser, sight only
- **Farsight**: chisel, laser, muzzle, sight (no chamber)
- **Ferryman**: chisel, laser, muzzle, sight (no chamber)
- **Impala Gravita**: chisel, muzzle, sight (no chamber, laser)
- **Neuraxis F22**: laser, sight only
- **Star & Witness**: chamber, chisel, laser (no muzzle, sight)
- **Unknown**: laser, sight only
- **Valet**: chisel, laser, muzzle, sight (no chamber)
- **Wingman**: chisel, laser, muzzle, sight (no chamber)
- **Wyatt PULSAR**: laser, sight only

## JSON Format

```json
{
  "Weapon Name": ["attachment_type1", "attachment_type2", ...],
  ...
}
```

Example:

```json
{
  "Beck 8": ["chamber", "chisel", "laser", "muzzle", "sight"],
  "Neuraxis F22": ["laser", "sight"]
}
```

## Notes

1. **Insurance Attachment**: While "insurance" is defined as an attachment type in the game code, no weapons in the wiki currently list it as available. This may be a future feature or removed content.

2. **Revision History**: The script searches backwards through page revisions to find the most recent version that contains attachment data. Some weapons had the "Available Attachments" section removed in later revisions.

3. **Wiki Terminology Mapping**: The script handles multiple wiki naming conventions:
   - "Muzzle Attachments" → muzzle
   - "Sight" or "Sights" → sight
   - "Laser Sights" → laser
   - "Gun Crank" or "Chamber Attachments" → chamber
   - "Chamber Chisel" or "Chamber Chisels" → chisel

4. **Unknown Weapon**: There's an entry for "Unknown" which appears to be a placeholder or test weapon in the wiki.

## Usage

To use this data in your application:

```javascript
// Load the JSON file
const weaponAttachments = require('./weapon_attachments_compatibility.json');

// Check if a weapon can accept a specific attachment
function canUseAttachment(weaponName, attachmentType) {
  return weaponAttachments[weaponName]?.includes(attachmentType) ?? false;
}

// Example
console.log(canUseAttachment('Beck 8', 'muzzle')); // true
console.log(canUseAttachment('Neuraxis F22', 'muzzle')); // false
```

## Re-running Extraction

To update the data with a newer wiki dump:

```bash
python3 parse_weapon_attachments.py
```

Make sure the input path in the script points to the latest wiki XML dump.
