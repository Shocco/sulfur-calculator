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

function applyCaliberConversion(weaponStats, caliber, caliberModifiers, weapon) {
  if (!caliber || !caliberModifiers.calibers || !caliberModifiers.calibers[caliber]) {
    return weaponStats
  }

  const newCaliberStats = caliberModifiers.calibers[caliber]
  const baseAmmoDamage = caliberModifiers.baseAmmoDamage

  // Calculate weapon's damage multiplier from current ammo type
  const currentAmmoType = weapon.ammoType
  const currentBaseDamage = baseAmmoDamage[currentAmmoType]
  const weaponMultiplier = currentBaseDamage ? weaponStats.Damage / currentBaseDamage : 1

  // Apply multiplier to new ammo type's base damage
  const newBaseDamage = baseAmmoDamage[caliber]
  const newDamage = newBaseDamage * weaponMultiplier

  return {
    ...weaponStats,
    Damage: newDamage,
    ProjectileCount: newCaliberStats.ProjectileCount,
    Spread: newCaliberStats.Spread,
    Recoil: newCaliberStats.Recoil
  }
}

function applyModifier(currentValue, baseValue, mod, statName) {
  const modType = mod.modType || mod.mod_type || mod.mod_type_id
  const value = mod.value

  // Special case: CritChance and ADSCritChance are always additive, even for PercentAdd/PercentMult types
  if (statName === 'CritChance' || statName === 'ADSCritChance') {
    return currentValue + value
  }

  if (modType === 'Flat' || modType === 100) {
    return currentValue + value
  } else if (modType === 'PercentAdd' || modType === 200) {
    return currentValue + (baseValue * value)
  } else if (modType === 'PercentMult' || modType === 300) {
    return currentValue * (1 + value)
  }
  return currentValue
}

export function calculateModifiedStats(weapon, attachments = [], enchantments = [], caliberModifiers = {}) {
  // For backward compatibility, handle old signature: calculateModifiedStats(weapon, enchantments)
  let actualAttachments = attachments
  let actualEnchantments = enchantments

  if (!Array.isArray(attachments) && attachments !== null && typeof attachments === 'object') {
    // Old signature detected: second param is enchantments
    actualEnchantments = Array.isArray(attachments) ? attachments : [attachments]
    actualAttachments = []
  }

  if (!weapon) {
    return null
  }

  // Handle both single enchantment and array of enchantments
  const enchantmentList = Array.isArray(actualEnchantments) ? actualEnchantments :
                          (actualEnchantments ? [actualEnchantments] : [])
  const attachmentList = Array.isArray(actualAttachments) ? actualAttachments :
                         (actualAttachments ? [actualAttachments] : [])

  if (enchantmentList.length === 0 && attachmentList.length === 0) {
    return null
  }

  let baseStats = weapon.baseStats || weapon.base_stats || {}

  // Step 0: Apply chamber chisel (caliber conversion) FIRST - this modifies base stats
  const chisel = attachmentList.find(a => a?.specialEffects?.caliberConversion)
  if (chisel) {
    baseStats = applyCaliberConversion(
      baseStats,
      chisel.specialEffects.caliberConversion,
      caliberModifiers,
      weapon
    )
  }

  // Separate special scrolls
  const convertScrolls = enchantmentList.filter(ench =>
    ench && ench.specialEffects && ench.specialEffects.ConvertWpn
  )
  const bypassPercentageScrolls = enchantmentList.filter(ench =>
    ench && ench.specialEffects && ench.specialEffects.bypassPercentages
  )
  const otherEnchantments = enchantmentList.filter(ench =>
    !ench || !ench.specialEffects || (!ench.specialEffects.ConvertWpn && !ench.specialEffects.bypassPercentages)
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

  // Collect modifiers from other attachments (excluding chisel which was already applied)
  const otherAttachments = attachmentList.filter(a => !a?.specialEffects?.caliberConversion)
  const attachmentMods = {}
  otherAttachments.forEach(attachment => {
    if (attachment && attachment.modifiers) {
      Object.entries(attachment.modifiers).forEach(([stat, value]) => {
        if (!attachmentMods[stat]) {
          attachmentMods[stat] = []
        }
        // Support both simple values (flat) and objects with {value, type}
        if (typeof value === 'object' && value !== null && 'value' in value) {
          attachmentMods[stat].push({ value: value.value, type: value.type || 'flat' })
        } else {
          attachmentMods[stat].push({ value, type: 'flat' })
        }
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
    // Order: Flat (100) -> PercentAdd (200) -> PercentMult (300)
    if (convertScrollMods[stat]) {
      let scrollBase = originalBase

      // Apply Flat modifiers first
      convertScrollMods[stat].filter(m => (m.modType || m.mod_type) === 100 || (m.modType || m.mod_type) === 'Flat').forEach(mod => {
        currentValue = applyModifier(currentValue, scrollBase, mod, stat)
      })
      // Update base after flat for percentage calculations
      scrollBase = currentValue

      // Then PercentAdd
      convertScrollMods[stat].filter(m => (m.modType || m.mod_type) === 200 || (m.modType || m.mod_type) === 'PercentAdd').forEach(mod => {
        currentValue = applyModifier(currentValue, scrollBase, mod, stat)
      })
      // Update base after PercentAdd for PercentMult
      scrollBase = currentValue

      // Then PercentMult
      convertScrollMods[stat].filter(m => (m.modType || m.mod_type) === 300 || (m.modType || m.mod_type) === 'PercentMult').forEach(mod => {
        currentValue = applyModifier(currentValue, scrollBase, mod, stat)
      })
      intermediateValue = currentValue
    }

    // Step 2: Apply attachment modifiers (flat first, then percentage)
    if (attachmentMods[stat]) {
      // Apply flat modifiers first
      attachmentMods[stat].filter(m => m.type !== 'percent').forEach(mod => {
        currentValue += mod.value
      })
      // Then percentage modifiers
      attachmentMods[stat].filter(m => m.type === 'percent').forEach(mod => {
        currentValue = currentValue + (currentValue * mod.value)
      })
      intermediateValue = currentValue
    }

    // Step 3: Apply other modifiers (oils) using the scroll/attachment-modified value as base
    // Order: Flat (100) -> PercentAdd (200) -> PercentMult (300)
    if (otherMods[stat]) {
      // Apply Flat modifiers first
      otherMods[stat].filter(m => (m.modType || m.mod_type) === 100 || (m.modType || m.mod_type) === 'Flat').forEach(mod => {
        currentValue = applyModifier(currentValue, intermediateValue, mod, stat)
      })
      // Update intermediate value after flat modifiers so percentages use correct base
      intermediateValue = currentValue

      // Then PercentAdd
      otherMods[stat].filter(m => (m.modType || m.mod_type) === 200 || (m.modType || m.mod_type) === 'PercentAdd').forEach(mod => {
        currentValue = applyModifier(currentValue, intermediateValue, mod, stat)
      })
      // Update intermediate value after PercentAdd for PercentMult
      intermediateValue = currentValue

      // Then PercentMult
      otherMods[stat].filter(m => (m.modType || m.mod_type) === 300 || (m.modType || m.mod_type) === 'PercentMult').forEach(mod => {
        currentValue = applyModifier(currentValue, intermediateValue, mod, stat)
      })
    }

    // Special handling for Damage with bypass-percentage scrolls
    if (stat === 'Damage' && bypassPercentageScrolls.length > 0) {
      // Add per-bullet damage multiplied by projectile count
      const projectileCount = baseStats.ProjectileCount || 1
      bypassPercentageScrolls.forEach(scroll => {
        if (scroll.specialEffects && scroll.specialEffects.perBulletDamage) {
          currentValue += scroll.specialEffects.perBulletDamage * projectileCount
        }
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
  const allModStats = new Set([...Object.keys(convertScrollMods), ...Object.keys(attachmentMods), ...Object.keys(otherMods)])
  allModStats.forEach(stat => {
    if (!baseStats[stat]) {
      let value = 0
      // Apply convert scroll modifiers: Flat -> PercentAdd -> PercentMult
      if (convertScrollMods[stat]) {
        convertScrollMods[stat].filter(m => (m.modType || m.mod_type) === 100 || (m.modType || m.mod_type) === 'Flat').forEach(mod => {
          value = applyModifier(value, 0, mod, stat)
        })
        convertScrollMods[stat].filter(m => (m.modType || m.mod_type) === 200 || (m.modType || m.mod_type) === 'PercentAdd').forEach(mod => {
          value = applyModifier(value, 0, mod, stat)
        })
        convertScrollMods[stat].filter(m => (m.modType || m.mod_type) === 300 || (m.modType || m.mod_type) === 'PercentMult').forEach(mod => {
          value = applyModifier(value, 0, mod, stat)
        })
      }
      // Apply attachment modifiers
      if (attachmentMods[stat]) {
        // Apply flat modifiers first
        attachmentMods[stat].filter(m => m.type !== 'percent').forEach(mod => {
          value += mod.value
        })
        // Then percentage modifiers
        attachmentMods[stat].filter(m => m.type === 'percent').forEach(mod => {
          value = value + (value * mod.value)
        })
      }
      // Apply other modifiers: Flat -> PercentAdd -> PercentMult
      if (otherMods[stat]) {
        otherMods[stat].filter(m => (m.modType || m.mod_type) === 100 || (m.modType || m.mod_type) === 'Flat').forEach(mod => {
          value = applyModifier(value, value, mod, stat)
        })
        otherMods[stat].filter(m => (m.modType || m.mod_type) === 200 || (m.modType || m.mod_type) === 'PercentAdd').forEach(mod => {
          value = applyModifier(value, value, mod, stat)
        })
        otherMods[stat].filter(m => (m.modType || m.mod_type) === 300 || (m.modType || m.mod_type) === 'PercentMult').forEach(mod => {
          value = applyModifier(value, value, mod, stat)
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

  // Calculate ADSCritChance (ADS crit = base crit + scope bonus)
  // Always show ADSCritChance in the results
  const critChanceStat = result.find(r => r.stat === 'CritChance')
  let adsCritChanceStat = result.find(r => r.stat === 'ADSCritChance')

  // Base crit chance from weapon/oils
  const baseCritChance = critChanceStat ? critChanceStat.modifiedValue : (baseStats.CritChance || 0)

  if (adsCritChanceStat) {
    // ADS bonus from scopes exists
    const adsBonus = adsCritChanceStat.modifiedValue
    // Total ADS crit = base + ADS bonus
    const totalADSCrit = baseCritChance + adsBonus

    // Update the ADSCritChance stat to show total
    adsCritChanceStat.baseValue = baseCritChance
    adsCritChanceStat.modifiedValue = Math.round(totalADSCrit * 100) / 100
    adsCritChanceStat.change = Math.round(adsBonus * 100) / 100
  } else {
    // No scope selected, but still show ADSCritChance = base crit chance
    result.push({
      stat: 'ADSCritChance',
      baseValue: baseCritChance,
      modifiedValue: baseCritChance,
      change: 0,
      modifier: null
    })
  }

  return result
}
