# Search Functionality for Weapons, Oils, and Scrolls

**Date:** 2025-12-27
**Status:** Approved Design
**Purpose:** Add search capability to filter weapons, oils, and scrolls by name and modifiers

## Requirements

- Search across item name and stat modifiers
- Partial match, case-insensitive search
- Separate search input above each selector (weapons, oils, scrolls)
- Show filtered results in scrollable list when searching
- Different behavior for single-select (weapons/scrolls) vs multi-select (oils)

## Architecture

### Component Changes

Three components will be modified:
- `WeaponSelector.jsx` - Add weapon search
- `EnchantmentSelector.jsx` - Add oil search (multi-select) and scroll search (single-select)

Each component will gain:
1. Search input field above existing dropdown
2. Search state using React useState
3. Filtered results list (scrollable, with images and details)
4. Smart visibility: show dropdown when empty, show filtered list when typing

### Non-Breaking Changes

- Existing dropdowns remain functional when not searching
- Search is optional - users can still use dropdowns directly
- Progressive enhancement approach

## Search Filtering Logic

### Filter Function

```javascript
const searchItems = (items, query) => {
  if (!query.trim()) return items

  const lowerQuery = query.toLowerCase()

  return items.filter(item => {
    // Search in name
    if (item.name.toLowerCase().includes(lowerQuery)) {
      return true
    }

    // Search in modifiers (for oils/scrolls)
    if (item.modifiers && item.modifiers.length > 0) {
      const modText = item.modifiers.map(mod =>
        `${mod.attribute} ${mod.value}`
      ).join(' ').toLowerCase()

      if (modText.includes(lowerQuery)) {
        return true
      }
    }

    // Search in special effects
    if (item.specialEffects) {
      const effectText = Object.values(item.specialEffects)
        .join(' ')
        .toLowerCase()

      if (effectText.includes(lowerQuery)) {
        return true
      }
    }

    return false
  })
}
```

### Searchable Fields

For each item type, search looks in:
- **Name** - Item name (e.g., "Damage Oil", "Beck 8", "Scroll of Damage")
- **Modifier attributes** - Stat names (e.g., "Damage", "RPM", "Spread")
- **Modifier values** - Numbers (e.g., "15", "0.5")
- **Special effects** - Effect descriptions (e.g., "automatic", "9mm")

### Example Searches

- `"damage"` → Finds "Damage Oil", items with Damage modifiers, "Scroll of Damage"
- `"15"` → Finds all items with +15% or +15 modifiers
- `"spread"` → Finds items that modify Spread stat
- `"auto"` → Finds items with "automatic" firing mode

## UI Design

### Search Input

Text input above each dropdown:

```jsx
<input
  type="text"
  placeholder="Search by name or stat..."
  value={searchQuery}
  onChange={(e) => setSearchQuery(e.target.value)}
  className="w-full bg-gray-700 border border-gray-600 rounded px-4 py-2 text-white mb-2"
/>
```

### Filtered Results List

Scrollable list showing:
- Item image (existing images)
- Item name (bold)
- Modifier summary (same format as dropdowns: "Damage: +15%, RPM: +10")
- Click to select

### Visual Layout

```
┌─────────────────────────────┐
│ [Search: "damage"_______  ] │ ← Search input
├─────────────────────────────┤
│ 📷 Damage Oil               │ ← Filtered results
│    Damage: +15%             │   (scrollable)
├─────────────────────────────┤
│ 📷 Add Damage Oil           │
│    Damage: +10              │
├─────────────────────────────┤
│ 📷 Scroll of Damage         │
│    Damage: +50%             │
└─────────────────────────────┘
```

### Conditional Display

- **Search empty** → Show normal `<select>` dropdown
- **Search has text** → Hide dropdown, show filtered results list
- **No results** → Show "No items found for '{query}'" message

### Styling

- Max height: 400px with scroll for long lists
- Same styling as existing components (gray-700 backgrounds, cyan/purple/red accents)
- Hover effects on result items

## Selection Behavior

### Weapons (Single-Select)

```javascript
const handleWeaponSelect = (weapon) => {
  onSelectWeapon(weapon)
  setSearchQuery('')  // Clear search
  // Filtered list disappears, dropdown returns
}
```

**Behavior:**
- Click weapon → Select it
- Search clears automatically
- Returns to normal dropdown view

### Scrolls (Single-Select)

```javascript
const handleScrollSelect = (scroll) => {
  onSelectScroll(scroll)
  setSearchQuery('')  // Clear search
  // Filtered list disappears, dropdown returns
}
```

**Behavior:**
- Same as weapons
- One scroll maximum
- Search clears on selection

### Oils (Multi-Select)

```javascript
const handleOilSelect = (oil) => {
  if (canAddOil) {
    onSelectOils([...selectedOils, oil])
    // Keep searchQuery as-is - DON'T clear
    // User can continue searching and adding oils
  }
}
```

**Behavior:**
- Click oil → Add to selection
- Search stays active with current query
- Can immediately search and add another oil
- User manually clears search when done

**Visual Feedback:**
- Already-selected oils appear disabled/grayed in results
- Show count: "Oils (3/5)" to indicate capacity
- Disable clicking already-selected items

## Edge Cases & Polish

### No Results Found

```jsx
{filteredItems.length === 0 && searchQuery && (
  <div className="text-gray-400 text-center py-4">
    No items found for "{searchQuery}"
  </div>
)}
```

### Already Selected Items

**For oils (multi-select):**
- Show already-selected oils in search results but grayed out
- Add checkmark icon to indicate selection
- Prevent clicking them again
- Keep them visible for reference

**For weapons/scrolls (single-select):**
- Search works even if item already selected
- Can search to change selection

### Clear Search

- Add "X" button in search input to clear quickly
- ESC key clears search
- Clicking outside search area doesn't clear (allows scrolling)

### Performance

- Search filters client-side (no API calls)
- No debouncing needed (instant filtering)
- Handles 200+ items without lag

### Accessibility

- Search input has proper placeholder text
- Results list is keyboard navigable (arrow keys)
- Enter key selects highlighted item
- Proper ARIA labels

### Mobile Considerations

- Search input triggers phone keyboard
- Results list touch-friendly (larger tap targets)
- Scrollable results work with touch gestures
- Responsive layout

## Implementation Notes

### State Management

Each component needs:
```javascript
const [searchQuery, setSearchQuery] = useState('')
```

### Filtered Data

```javascript
const filteredItems = searchItems(items, searchQuery)
```

### Conditional Rendering

```javascript
{searchQuery ? (
  // Show filtered results list
  <FilteredResultsList items={filteredItems} onSelect={handleSelect} />
) : (
  // Show normal dropdown
  <select>...</select>
)}
```

## Files to Modify

1. **src/components/WeaponSelector.jsx**
   - Add search state
   - Add search input
   - Add filtered results list
   - Implement weapon selection with search clear

2. **src/components/EnchantmentSelector.jsx**
   - Add search state for oils
   - Add search state for scrolls
   - Add search inputs for both
   - Add filtered results lists
   - Implement different selection behavior (oils keep search, scrolls clear)

## Testing Considerations

- Test search with various queries
- Test selection behavior for each item type
- Test "no results" state
- Test with already-selected items
- Test keyboard navigation
- Test on mobile devices
- Verify performance with 200+ oils

## Success Criteria

- User can type "damage" and see all relevant items
- Search is fast and responsive
- Single-select items (weapons/scrolls) clear search on selection
- Multi-select items (oils) keep search active
- UI is consistent with existing design
- No breaking changes to existing functionality
