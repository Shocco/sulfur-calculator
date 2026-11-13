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

function applyCaliberConversion(weaponStats, caliber, weapon) {
  const caliberData = weapon.caliberModding?.[caliber]
  if (!caliber || !caliberData) {
    return weaponStats
  }

  return {
    ...weaponStats,
    Damage: caliberData.Damage,
    ProjectileCount: caliberData.ProjectileCount,
    Spread: caliberData.Spread,
    Recoil: caliberData.Recoil,
  }
}

function applyModifier(currentValue, baseValue, mod, statName) {
  const modType = mod.modType || mod.mod_type || mod.mod_type_id
  const value = mod.value

  // Special case: chances are percentage points, so they are always additive, even for
  // PercentAdd/PercentMult types and across scrolls and oils
  if (isCritStat(statName) || statName === 'AmmoConsumeChance') {
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

// The data uses two names for the same game stat (wiki params BltSpeed and
// MoveAccuracy): oils and attachments must land on one stat to combine.
const STAT_ALIASES = {
  BulletSpeed: 'ProjectileSpeed',
  AccuracyWhileMoving: 'MoveAccuracy'
}
const canonicalStat = (stat) => STAT_ALIASES[stat] || stat

const isCritStat = (stat) => stat === 'CritChance' || stat === 'ADSCritChance'
const isFlatMod = (mod) => (mod.modType || mod.mod_type) === 100 || (mod.modType || mod.mod_type) === 'Flat'
const round2 = (value) => Math.round(value * 100) / 100
// Weapon stats keep three decimals so the 12Ga division by 8 stays exact (41.875)
const round3 = (value) => Math.round(value * 1000) / 1000

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
      weapon
    )
  }

  // The caliber the weapon is chambered in, after any chisel that applies to it
  const convertedCaliber = chisel?.specialEffects.caliberConversion
  const caliber = convertedCaliber && weapon.caliberModding?.[convertedCaliber]
    ? convertedCaliber
    : weapon.ammoType
  const is12Ga = String(caliber || '').toLowerCase() === '12ga'
  // As of game 1.0, flat damage modifiers from enchantments are divided by 8 on
  // weapons chambered in 12Ga, negatives included, whatever the projectile count
  const scaleFor12Ga = (attr, mod) =>
    is12Ga && attr === 'Damage' && isFlatMod(mod) ? { ...mod, value: mod.value / 8 } : mod

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
        const attr = canonicalStat(mod.attribute)
        if (!convertScrollMods[attr]) {
          convertScrollMods[attr] = []
        }
        convertScrollMods[attr].push(scaleFor12Ga(attr, mod))
      })
    }
  })

  // Collect modifiers from other attachments (excluding chisel which was already applied)
  const otherAttachments = attachmentList.filter(a => !a?.specialEffects?.caliberConversion)
  const attachmentMods = {}
  otherAttachments.forEach(attachment => {
    if (attachment && attachment.modifiers) {
      Object.entries(attachment.modifiers).forEach(([rawStat, value]) => {
        const stat = canonicalStat(rawStat)
        if (!attachmentMods[stat]) {
          attachmentMods[stat] = []
        }
        // CritChance and ADSCritChance are percentage points, so they are always
        // additive (same rule as applyModifier), even when the data marks them 'percent'
        const isCrit = isCritStat(stat)
        // Support both simple values (flat) and objects with {value, type}
        if (typeof value === 'object' && value !== null && 'value' in value) {
          attachmentMods[stat].push({ value: value.value, type: isCrit ? 'flat' : (value.type || 'flat') })
        } else {
          attachmentMods[stat].push({ value, type: 'flat' })
        }
      })
    }
  })

  // Collect modifiers from other enchantments (oils and non-convert scrolls).
  // Dark damage scrolls contribute their ordinary modifiers here too, but not
  // Damage: theirs is added per projectile after percentages, further down.
  const otherMods = {}
  const isBypassScroll = (ench) => bypassPercentageScrolls.includes(ench)
  ;[...otherEnchantments, ...bypassPercentageScrolls].forEach(ench => {
    if (ench && ench.modifiers) {
      ench.modifiers.forEach(mod => {
        const attr = canonicalStat(mod.attribute)
        if (attr === 'Damage' && isBypassScroll(ench)) return
        if (!otherMods[attr]) {
          otherMods[attr] = []
        }
        otherMods[attr].push(scaleFor12Ga(attr, mod))
      })
    }
  })

  const result = []

  // Run every collected modifier for one stat, starting from startValue.
  // Flat changes from every source come first, then percentages:
  //   (base + flats) x converting scroll x (1 + sum of attachment and oil percentages)
  // A converting scroll's percentage is its own factor (wiki: "applies separately
  // from Oils"), and it applies to the value including flat oil bonuses.
  // With applyLimits, the combined effect of all percentages is held between 1%
  // and 10 times the value after flats, as the game does for weapon stats.
  const typeIs = (mod, id, name) => (mod.modType || mod.mod_type) === id || (mod.modType || mod.mod_type) === name
  const applyAllModifiers = (stat, startValue, applyLimits = false) => {
    const scrollMods = convertScrollMods[stat] || []
    const attachMods = attachmentMods[stat] || []
    const oilMods = otherMods[stat] || []
    let currentValue = startValue

    // Step 1: flat modifiers from scroll, attachments and oils
    scrollMods.filter(m => typeIs(m, 100, 'Flat')).forEach(mod => {
      currentValue = applyModifier(currentValue, currentValue, mod, stat)
    })
    attachMods.filter(m => m.type !== 'percent').forEach(mod => {
      currentValue += mod.value
    })
    oilMods.filter(m => typeIs(m, 100, 'Flat')).forEach(mod => {
      currentValue = applyModifier(currentValue, currentValue, mod, stat)
    })

    const afterFlats = currentValue

    // Step 2: converting scroll percentages (PercentAdd, then PercentMult)
    let phaseBase = currentValue
    scrollMods.filter(m => typeIs(m, 200, 'PercentAdd')).forEach(mod => {
      currentValue = applyModifier(currentValue, phaseBase, mod, stat)
    })
    phaseBase = currentValue
    scrollMods.filter(m => typeIs(m, 300, 'PercentMult')).forEach(mod => {
      currentValue = applyModifier(currentValue, phaseBase, mod, stat)
    })

    // Step 3: attachment and oil percentages share one pool and add together
    // (PercentAdd), then PercentMult
    phaseBase = currentValue
    attachMods.filter(m => m.type === 'percent').forEach(mod => {
      currentValue += phaseBase * mod.value
    })
    oilMods.filter(m => typeIs(m, 200, 'PercentAdd')).forEach(mod => {
      currentValue = applyModifier(currentValue, phaseBase, mod, stat)
    })
    phaseBase = currentValue
    oilMods.filter(m => typeIs(m, 300, 'PercentMult')).forEach(mod => {
      currentValue = applyModifier(currentValue, phaseBase, mod, stat)
    })

    if (applyLimits && afterFlats > 0) {
      currentValue = Math.min(Math.max(currentValue, afterFlats * 0.01), afterFlats * 10)
    }

    return currentValue
  }

  // Calculate modified values for each stat
  Object.entries(baseStats).forEach(([stat, originalBase]) => {
    // Percentages are limited to 1%-10x of the stat; flat penalties can still take
    // a stat to zero, but never below it
    const currentValue = Math.max(applyAllModifiers(stat, originalBase, true), 0)

    result.push({
      stat,
      baseValue: originalBase,
      modifiedValue: round3(currentValue),
      change: round3(currentValue - originalBase),
      modifier: null
    })
  })

  // Dark and explosive damage (Chaos Strike, Explosions) is its own damage source:
  // a fixed amount per projectile that oils, attachments and crits don't change,
  // and that isn't part of the gun's listed damage. Divided by 8 on 12Ga.
  const bonusDamage = bypassPercentageScrolls.reduce(
    (sum, scroll) => sum + (scroll.specialEffects.perBulletDamage || 0), 0
  ) / (is12Ga ? 8 : 1)
  if (bonusDamage > 0) {
    result.push({
      stat: 'BonusDamage',
      baseValue: 0,
      modifiedValue: round3(bonusDamage),
      change: round3(bonusDamage),
      modifier: null
    })
  }

  // Add any stats that are only in modifiers (not in base stats)
  const allModStats = new Set([...Object.keys(convertScrollMods), ...Object.keys(attachmentMods), ...Object.keys(otherMods)])
  allModStats.forEach(stat => {
    // `in`, not truthiness: a base stat of 0 (e.g. energy weapon Recoil) is still a base stat
    if (!(stat in baseStats)) {
      // A percentage of an unknown base can't be shown as an absolute number.
      // When every modifier is a percentage, start from 1 (100%) and report the
      // net relative change (0.8 = +80%). Flat stats (Bullet Drop, Bounces) and
      // crit chance start from 0 and stay absolute.
      const hasFlat =
        [...(convertScrollMods[stat] || []), ...(otherMods[stat] || [])].some(isFlatMod) ||
        (attachmentMods[stat] || []).some(m => m.type !== 'percent')
      const isRelative = !isCritStat(stat) && !hasFlat
      const startValue = isRelative ? 1 : 0
      let value = round2(applyAllModifiers(stat, startValue) - startValue)
      // Crit chance above 100% has no further effect in game
      if (isCritStat(stat)) value = Math.min(value, 1)

      result.push({
        stat,
        baseValue: 0,
        modifiedValue: value,
        change: value,
        modifier: null,
        ...(isRelative && { isRelative: true })
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
    // Total ADS crit = base + ADS bonus, capped at 100%
    const totalADSCrit = Math.min(baseCritChance + adsBonus, 1)

    // Update the ADSCritChance stat to show total
    adsCritChanceStat.baseValue = baseCritChance
    adsCritChanceStat.modifiedValue = round2(totalADSCrit)
    adsCritChanceStat.change = round2(totalADSCrit - baseCritChance)
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
