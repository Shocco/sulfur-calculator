/**
 * Calculate modified weapon stats when oils/scrolls are applied
 *
 * StatModType values:
 * - 100: Flat (additive)
 * - 200: PercentAdd (additive percentage)
 * - 300: PercentMult (multiplicative percentage)
 *
 * Special handling: Scrolls with ConvertWpn (like Scroll of Light) have their
 * modifiers applied first, then oil modifiers are calculated based on those values
 */

function applyModifier(currentValue, baseValue, mod) {
  const modType = mod.modType || mod.mod_type || mod.mod_type_id
  const value = mod.value

  if (modType === 'Flat' || modType === 100) {
    return currentValue + value
  } else if (modType === 'PercentAdd' || modType === 200) {
    return currentValue + (baseValue * value)
  } else if (modType === 'PercentMult' || modType === 300) {
    return currentValue * (1 + value)
  }
  return currentValue
}

export function calculateModifiedStats(weapon, enchantments) {
  if (!weapon || !enchantments) {
    return null
  }

  // Handle both single enchantment and array of enchantments
  const enchantmentList = Array.isArray(enchantments) ? enchantments : [enchantments]

  if (enchantmentList.length === 0) {
    return null
  }

  const baseStats = weapon.baseStats || weapon.base_stats || {}

  // Separate scrolls with ConvertWpn from other enchantments
  const convertScrolls = enchantmentList.filter(ench =>
    ench && ench.specialEffects && ench.specialEffects.ConvertWpn
  )
  const otherEnchantments = enchantmentList.filter(ench =>
    !ench || !ench.specialEffects || !ench.specialEffects.ConvertWpn
  )

  // Collect modifiers from convert scrolls (applied first)
  const convertScrollMods = {}
  convertScrolls.forEach(ench => {
    if (ench && ench.modifiers) {
      ench.modifiers.forEach(mod => {
        const attr = mod.attribute
        if (!convertScrollMods[attr]) {
          convertScrollMods[attr] = []
        }
        convertScrollMods[attr].push(mod)
      })
    }
  })

  // Collect modifiers from other enchantments (oils and non-convert scrolls)
  const otherMods = {}
  otherEnchantments.forEach(ench => {
    if (ench && ench.modifiers) {
      ench.modifiers.forEach(mod => {
        const attr = mod.attribute
        if (!otherMods[attr]) {
          otherMods[attr] = []
        }
        otherMods[attr].push(mod)
      })
    }
  })

  const result = []

  // Calculate modified values for each stat
  Object.entries(baseStats).forEach(([stat, originalBase]) => {
    let currentValue = originalBase
    let intermediateValue = originalBase

    // Step 1: Apply convert scroll modifiers first (e.g., Scroll of Light)
    if (convertScrollMods[stat]) {
      convertScrollMods[stat].forEach(mod => {
        currentValue = applyModifier(currentValue, originalBase, mod)
      })
      intermediateValue = currentValue
    }

    // Step 2: Apply other modifiers (oils) using the scroll-modified value as base
    if (otherMods[stat]) {
      otherMods[stat].forEach(mod => {
        currentValue = applyModifier(currentValue, intermediateValue, mod)
      })
    }

    result.push({
      stat,
      baseValue: originalBase,
      modifiedValue: Math.round(currentValue * 100) / 100,
      change: Math.round((currentValue - originalBase) * 100) / 100,
      modifier: null
    })
  })

  // Add any stats that are only in modifiers (not in base stats)
  const allModStats = new Set([...Object.keys(convertScrollMods), ...Object.keys(otherMods)])
  allModStats.forEach(stat => {
    if (!baseStats[stat]) {
      let value = 0
      if (convertScrollMods[stat]) {
        convertScrollMods[stat].forEach(mod => {
          value = applyModifier(value, 0, mod)
        })
      }
      if (otherMods[stat]) {
        otherMods[stat].forEach(mod => {
          value = applyModifier(value, value, mod)
        })
      }

      result.push({
        stat,
        baseValue: 0,
        modifiedValue: Math.round(value * 100) / 100,
        change: Math.round(value * 100) / 100,
        modifier: null
      })
    }
  })

  return result
}
