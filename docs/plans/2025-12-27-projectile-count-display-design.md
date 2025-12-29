# ProjectileCount Display Design

**Date:** 2025-12-27
**Status:** Approved

## Overview

Add ProjectileCount as a visible stat in the weapon calculator UI. Currently it's hidden and only shown inline with damage (e.g., "40x8") and in total damage calculations.

## Current State

**Existing Behavior:**
- ProjectileCount exists in weapon data
- Filtered out from stats display (lines 101, 145 in StatsDisplay.jsx)
- Only visible inline with damage display
- Used in Total Damage calculation (Damage × ProjectileCount)
- Can be modified by chamber chisels and enchantments

## Proposed Changes

**New Behavior:**
- ProjectileCount appears as its own stat row
- Displayed as integer: "8" not "8.0"
- Shows change indicators when modified
- Keep existing inline damage display AND total damage box

## Display Format

### Base Stats Section
- ProjectileCount appears in stat list
- Format: Integer using `Math.round()`
- Example: "ProjectileCount" → "8"

### After Modifications Section
- Shows when ProjectileCount changes
- Change indicator with color coding
- Example: "8 → 1 (-7)" in red

### Example Display

**12Ga Shotgun (Base):**
```
Damage: 40x8
ProjectileCount: 8
RPM: 500
Total Damage: 320
```

**After 9mm Chamber Chisel:**
```
Damage: 60x1 (was 40x8)
ProjectileCount: 1 (was 8, -7)
RPM: 500
Total Damage: 60
```

## Implementation

### File Changes

**`src/components/StatsDisplay.jsx`:**

1. Remove line 101 filter:
   ```javascript
   .filter(([stat]) => stat !== 'ProjectileCount')
   ```

2. Remove line 145 filter:
   ```javascript
   .filter(({ stat }) => stat !== 'ProjectileCount')
   ```

3. Add integer formatting for ProjectileCount in both display sections

### Testing Checklist

- [ ] ProjectileCount visible for all weapons
- [ ] Shows as integer without decimals
- [ ] Changes correctly with chamber chisel
- [ ] Inline damage format still works
- [ ] Total Damage calculation correct
- [ ] Change indicators display properly

## No Breaking Changes

- Calculator logic unchanged
- Data files unchanged
- Only UI display changes
