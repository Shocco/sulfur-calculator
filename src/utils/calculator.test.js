import { test } from 'node:test'
import assert from 'node:assert/strict'
import { calculateModifiedStats } from './calculator.js'

// Fixtures mirror the shapes in public/data/*.json
const weapon = {
  name: 'Test SMG',
  baseStats: {
    Damage: 60, RPM: 1500, MagazineSize: 40, Spread: 5, Recoil: 3,
    Durability: 3900, MaxDurability: 3900, Weight: 12,
    ProjectileSpeed: 100, MoveSpeed: 1, ProjectileCount: 1
  }
}
const sniperScope = { name: 'Sniper Scope', type: 'sight', modifiers: { ADSCritChance: { value: 0.3, type: 'percent' } } }
const silencer = {
  name: 'Aftermarket Haukland Silencer', type: 'muzzle',
  modifiers: { RPM: { value: -0.15, type: 'percent' }, CritChance: { value: 0.25, type: 'percent' } }
}
const critOil = { name: 'Aimless Oil', modifiers: [{ attribute: 'CritChance', modType: 200, value: 0.3 }] }

const stat = (result, name) => result.find(r => r.stat === name)

test('sight ADS crit bonus is added to ADS crit chance', () => {
  const ads = stat(calculateModifiedStats(weapon, [sniperScope], []), 'ADSCritChance')
  assert.equal(ads.modifiedValue, 0.3)
  assert.equal(ads.change, 0.3)
})

test('muzzle crit bonus is added to crit chance', () => {
  const result = calculateModifiedStats(weapon, [silencer], [])
  assert.equal(stat(result, 'CritChance').modifiedValue, 0.25)
  assert.equal(stat(result, 'ADSCritChance').modifiedValue, 0.25)
})

test('attachment crit stacks additively with oil crit', () => {
  const result = calculateModifiedStats(weapon, [silencer, sniperScope], [critOil])
  assert.equal(stat(result, 'CritChance').modifiedValue, 0.55)
  assert.equal(stat(result, 'ADSCritChance').modifiedValue, 0.85)
})

test('percent attachment modifier on a base stat still scales that stat', () => {
  const result = calculateModifiedStats(weapon, [silencer], [])
  assert.equal(stat(result, 'RPM').modifiedValue, 1275)
})

// --- Stats the weapon has no base value for ---

const reloadOil = (value) => ({ name: `Reload ${value}`, modifiers: [{ attribute: 'ReloadSpeed', modType: 200, value }] })
const bulletDropOil = { name: 'Medicine Ball Oil', modifiers: [{ attribute: 'BulletDrop', modType: 100, value: 30 }] }
const arkanoidOil = {
  name: 'Arkanoid Oil',
  modifiers: [{ attribute: 'BulletSpeed', modType: 200, value: -0.8 }, { attribute: 'BulletBounces', modType: 100, value: 10 }]
}
const laser = { name: 'Laser Sight (Red)', type: 'laser', modifiers: { AccuracyWhileMoving: { value: 0.5, type: 'percent' } } }
const moveAccuracyOil = { name: 'Steady Oil', modifiers: [{ attribute: 'MoveAccuracy', modType: 200, value: 0.2 }] }
const toxicLobotomy = {
  name: 'Scroll of Toxic Lobotomy',
  modifiers: [{ attribute: 'HeadshotDamage', modType: 200, value: 3 }],
  specialEffects: { ConvertWpn: 'Railgun' }
}

test('percent oil on a stat with no base reports the net relative change', () => {
  const reload = stat(calculateModifiedStats(weapon, [], [reloadOil(0.8)]), 'ReloadSpeed')
  assert.equal(reload.modifiedValue, 0.8)
  assert.equal(reload.change, 0.8)
  assert.equal(reload.isRelative, true)
})

test('percent oils on a stat with no base add together', () => {
  const reload = stat(calculateModifiedStats(weapon, [], [reloadOil(0.5), reloadOil(0.3)]), 'ReloadSpeed')
  assert.equal(reload.modifiedValue, 0.8)
})

test('negative percent oil on a stat with no base reports a negative change', () => {
  const reload = stat(calculateModifiedStats(weapon, [], [reloadOil(-0.4)]), 'ReloadSpeed')
  assert.equal(reload.modifiedValue, -0.4)
})

test('flat modifier on a stat with no base stays an absolute value', () => {
  const drop = stat(calculateModifiedStats(weapon, [], [bulletDropOil]), 'BulletDrop')
  assert.equal(drop.modifiedValue, 30)
  assert.ok(!drop.isRelative)
})

test('crit chance stays an absolute value, not a relative change', () => {
  const crit = stat(calculateModifiedStats(weapon, [], [critOil]), 'CritChance')
  assert.equal(crit.modifiedValue, 0.3)
  assert.ok(!crit.isRelative)
})

test('oil bullet speed applies to the weapon projectile speed', () => {
  const result = calculateModifiedStats(weapon, [], [arkanoidOil])
  assert.equal(stat(result, 'ProjectileSpeed').modifiedValue, 20)
  assert.equal(stat(result, 'BulletSpeed'), undefined)
})

test('laser move accuracy is reported as a relative change', () => {
  const result = calculateModifiedStats(weapon, [laser], [])
  assert.equal(stat(result, 'MoveAccuracy').modifiedValue, 0.5)
  assert.equal(stat(result, 'AccuracyWhileMoving'), undefined)
})

test('laser and oil move accuracy land on a single stat', () => {
  const result = calculateModifiedStats(weapon, [laser], [moveAccuracyOil])
  assert.equal(result.filter(r => r.stat === 'MoveAccuracy').length, 1)
  assert.equal(stat(result, 'AccuracyWhileMoving'), undefined)
  assert.ok(stat(result, 'MoveAccuracy').modifiedValue > 0.5)
})

test('scroll headshot damage percent is reported as a relative change', () => {
  const hs = stat(calculateModifiedStats(weapon, [], [toxicLobotomy]), 'HeadshotDamage')
  assert.equal(hs.modifiedValue, 3)
  assert.equal(hs.isRelative, true)
})

// --- Base stats whose value is 0 (energy weapons have Recoil 0) ---

const energyWeapon = { name: 'Test Energy Gun', baseStats: { ...weapon.baseStats, Recoil: 0 } }
const flatRecoilOil = { name: 'Dead Center Oil', modifiers: [{ attribute: 'Recoil', modType: 100, value: 1 }] }
const percentRecoilOil = { name: 'Action Oil', modifiers: [{ attribute: 'Recoil', modType: 200, value: 1 }] }

test('flat oil on a zero base stat produces a single row', () => {
  const rows = calculateModifiedStats(energyWeapon, [], [flatRecoilOil]).filter(r => r.stat === 'Recoil')
  assert.equal(rows.length, 1)
  assert.equal(rows[0].baseValue, 0)
  assert.equal(rows[0].modifiedValue, 1)
})

test('percent oil on a zero base stat leaves it at zero in a single row', () => {
  const rows = calculateModifiedStats(energyWeapon, [], [percentRecoilOil]).filter(r => r.stat === 'Recoil')
  assert.equal(rows.length, 1)
  assert.equal(rows[0].modifiedValue, 0)
  assert.ok(!rows[0].isRelative)
})

// --- Ammo consume chance is a chance: percentage points that add up ---

const megaSoaker = {
  name: 'Scroll of Mega Soaker',
  modifiers: [{ attribute: 'AmmoConsumeChance', modType: 200, value: -2 }],
  specialEffects: { ConvertWpn: 'Mega Soaker' }
}
const bulkOil = { name: 'Bulk Oil', modifiers: [{ attribute: 'AmmoConsumeChance', modType: 200, value: -0.4 }] }

test('scroll and oil ammo consume chance add together', () => {
  const ammo = stat(calculateModifiedStats(weapon, [], [bulkOil, megaSoaker]), 'AmmoConsumeChance')
  assert.equal(ammo.modifiedValue, -2.4)
  assert.equal(ammo.isRelative, true)
})

// --- Crit chance cannot exceed 100% ---

const bigCritOil = (value) => ({ name: `Crit ${value}`, modifiers: [{ attribute: 'CritChance', modType: 200, value }] })

test('crit chance is capped at 100%', () => {
  const crit = stat(calculateModifiedStats(weapon, [], [bigCritOil(0.6), bigCritOil(0.45)]), 'CritChance')
  assert.equal(crit.modifiedValue, 1)
  assert.equal(crit.change, 1)
})

test('ADS crit chance is capped at 100% and its change is what the scope actually adds', () => {
  const ads = stat(calculateModifiedStats(weapon, [sniperScope], [bigCritOil(0.9)]), 'ADSCritChance')
  assert.equal(ads.baseValue, 0.9)
  assert.equal(ads.modifiedValue, 1)
  assert.equal(ads.change, 0.1)
})

// --- Dark damage scrolls (Chaos Strike): flat damage per projectile, after percentages ---

const chaosStrike = {
  name: 'Scroll of Chaos Strike',
  modifiers: [{ attribute: 'BulletSize', modType: 200, value: 1 }],
  specialEffects: { bypassPercentages: true, perBulletDamage: 50, DarkDmg: '+50–200' }
}
const damageOil = { name: 'Glass Cannon Oil', modifiers: [{ attribute: 'Damage', modType: 200, value: 0.5 }] }
const shotgun = { name: 'Test Shotgun', baseStats: { ...weapon.baseStats, Damage: 40, ProjectileCount: 8 } }

test('dark damage scroll still applies its ordinary modifiers', () => {
  const size = stat(calculateModifiedStats(weapon, [], [chaosStrike]), 'BulletSize')
  assert.equal(size.modifiedValue, 1)
  assert.equal(size.isRelative, true)
})

test('dark damage is a separate bonus row and leaves listed damage alone', () => {
  const result = calculateModifiedStats(weapon, [], [damageOil, chaosStrike])
  assert.equal(stat(result, 'Damage').modifiedValue, 60 * 1.5)
  const bonus = stat(result, 'BonusDamage')
  assert.equal(bonus.baseValue, 0)
  assert.equal(bonus.modifiedValue, 50)
  assert.equal(bonus.change, 50)
})

test('bonus damage is per projectile and does not scale with projectile count', () => {
  const result = calculateModifiedStats(shotgun, [], [chaosStrike])
  assert.equal(stat(result, 'Damage').modifiedValue, 40)
  assert.equal(stat(result, 'BonusDamage').modifiedValue, 50)
})

test('bonus damage is divided by 8 on a 12Ga weapon', () => {
  const result = calculateModifiedStats({ ...shotgun, ammoType: '12Ga' }, [], [chaosStrike])
  assert.equal(stat(result, 'BonusDamage').modifiedValue, 6.25)
})

test('a bonus damage scroll with its own flat damage modifier does not change listed damage', () => {
  const oldFormat = {
    ...chaosStrike,
    modifiers: [...chaosStrike.modifiers, { attribute: 'Damage', modType: 100, value: 100 }]
  }
  const result = calculateModifiedStats(weapon, [], [oldFormat])
  assert.equal(stat(result, 'Damage').modifiedValue, 60)
  assert.equal(stat(result, 'BonusDamage').modifiedValue, 50)
})

test('explosive bonus damage is not scaled by percent oils', () => {
  const explosions = { name: 'Scroll of Explosions', modifiers: [], specialEffects: { Explosion: '¤', bypassPercentages: true, perBulletDamage: 25 } }
  const result = calculateModifiedStats(weapon, [], [damageOil, explosions])
  assert.equal(stat(result, 'Damage').modifiedValue, 90)
  assert.equal(stat(result, 'BonusDamage').modifiedValue, 25)
})

test('no bonus damage row without a bonus damage scroll', () => {
  assert.equal(stat(calculateModifiedStats(weapon, [], [damageOil]), 'BonusDamage'), undefined)
})

// --- Weapon stats cannot go below zero ---

const percentDamageOil = (value) => ({ name: `Damage ${value}`, modifiers: [{ attribute: 'Damage', modType: 200, value }] })
const flatSpreadOil = (value) => ({ name: `Spread ${value}`, modifiers: [{ attribute: 'Spread', modType: 100, value }] })

test('stacked percentage penalties bottom out at 1% of the stat', () => {
  const damage = stat(calculateModifiedStats(weapon, [], [percentDamageOil(-0.8), percentDamageOil(-0.5)]), 'Damage')
  assert.equal(damage.modifiedValue, 0.6)
  assert.equal(damage.change, -59.4)
})

test('stacked percentage bonuses top out at 10 times the stat', () => {
  const beam = { name: 'Scroll of Beam', modifiers: [{ attribute: 'RPM', modType: 200, value: 9 }], specialEffects: { ConvertWpn: 'Beam Gun' } }
  const rpmOil = { name: 'Zero Fucks Oil', modifiers: [{ attribute: 'RPM', modType: 200, value: 0.5 }] }
  assert.equal(stat(calculateModifiedStats(weapon, [], [beam]), 'RPM').modifiedValue, 15000)
  assert.equal(stat(calculateModifiedStats(weapon, [], [rpmOil, beam]), 'RPM').modifiedValue, 15000)
})

test('percentages inside the limits are not changed by them', () => {
  assert.equal(stat(calculateModifiedStats(weapon, [], [percentDamageOil(-0.8)]), 'Damage').modifiedValue, 12)
  assert.equal(stat(calculateModifiedStats(weapon, [], [percentDamageOil(3)]), 'Damage').modifiedValue, 240)
})

test('flat spread reductions bottom out at zero', () => {
  const spread = stat(calculateModifiedStats(weapon, [], [flatSpreadOil(-2), flatSpreadOil(-2), flatSpreadOil(-2)]), 'Spread')
  assert.equal(spread.modifiedValue, 0)
  assert.equal(spread.change, -5)
})

test('a relative stat can still be negative', () => {
  const reload = stat(calculateModifiedStats(weapon, [], [reloadOil(-0.4)]), 'ReloadSpeed')
  assert.equal(reload.modifiedValue, -0.4)
})

// --- 12Ga: flat damage modifiers are divided by 8 (wiki Enchantments page, game 1.0) ---

const shotgun12 = { name: 'Test 12Ga', ammoType: '12Ga', baseStats: { ...weapon.baseStats, Damage: 40, ProjectileCount: 8 } }
const rifle = {
  name: 'Test Rifle', ammoType: '7.62mm', baseStats: { ...weapon.baseStats, Damage: 200 },
  caliberModding: { '12Ga': { Damage: 40, Spread: 5, Recoil: 25, ProjectileCount: 8 } }
}
const chisel12 = { name: 'Chamber Chisel (12Ga)', type: 'chisel', modifiers: {}, specialEffects: { caliberConversion: '12Ga' } }
const flatDamageOil = (value) => ({ name: `Flat ${value}`, modifiers: [{ attribute: 'Damage', modType: 100, value }] })

test('flat damage on a 12Ga weapon is divided by 8', () => {
  assert.equal(stat(calculateModifiedStats(shotgun12, [], [flatDamageOil(16)]), 'Damage').modifiedValue, 42)
})

test('negative flat damage on a 12Ga weapon is divided by 8 too', () => {
  assert.equal(stat(calculateModifiedStats(shotgun12, [], [flatDamageOil(-16)]), 'Damage').modifiedValue, 38)
})

test('percent damage on a 12Ga weapon applies to the base plus the divided flat amount', () => {
  const damage = stat(calculateModifiedStats(shotgun12, [], [flatDamageOil(16), damageOil]), 'Damage')
  assert.equal(damage.modifiedValue, (40 + 2) * 1.5)
})

test('flat damage on other calibers is not divided', () => {
  assert.equal(stat(calculateModifiedStats({ ...weapon, ammoType: '9mm' }, [], [flatDamageOil(16)]), 'Damage').modifiedValue, 76)
})

test('a weapon chiselled to 12Ga divides flat damage by 8', () => {
  assert.equal(stat(calculateModifiedStats(rifle, [chisel12], [flatDamageOil(16)]), 'Damage').modifiedValue, 42)
})

test('other flat modifiers on a 12Ga weapon are not divided', () => {
  const spread = stat(calculateModifiedStats(shotgun12, [], [{ name: 'Spread', modifiers: [{ attribute: 'Spread', modType: 100, value: 1 }] }]), 'Spread')
  assert.equal(spread.modifiedValue, 6)
})

test('eighths from the 12Ga division are kept exactly', () => {
  const explosions = { name: 'Scroll of Explosions', modifiers: [], specialEffects: { bypassPercentages: true, perBulletDamage: 25 } }
  const result = calculateModifiedStats(shotgun12, [], [flatDamageOil(15), explosions])
  assert.equal(stat(result, 'Damage').modifiedValue, 41.875)
  assert.equal(stat(result, 'Damage').change, 1.875)
  assert.equal(stat(result, 'BonusDamage').modifiedValue, 3.125)
})

// --- Flat modifiers apply before a converting scroll's percentage ---
// (base + flat) x scroll, not base x scroll + flat

const bigGun = { name: 'Test Cannon', baseStats: { ...weapon.baseStats, Damage: 500 } }
const flameThrower = {
  name: 'Scroll of Flame Thrower',
  modifiers: [{ attribute: 'Damage', modType: 200, value: -0.86 }, { attribute: 'Spread', modType: 200, value: 1.5 }],
  specialEffects: { ConvertWpn: 'Flamethrower' }
}
const steam = {
  name: 'Scroll of Steam',
  modifiers: [{ attribute: 'Damage', modType: 200, value: -1 }],
  specialEffects: { ConvertWpn: 'Steam Sprayer' }
}

test('wiki example: converting scroll then percent oil (500 -> 70 -> 105)', () => {
  assert.equal(stat(calculateModifiedStats(bigGun, [], [flameThrower]), 'Damage').modifiedValue, 70)
  assert.equal(stat(calculateModifiedStats(bigGun, [], [damageOil, flameThrower]), 'Damage').modifiedValue, 105)
})

test('flat oil damage is added before a converting scroll percentage', () => {
  const damage = stat(calculateModifiedStats(weapon, [], [flatDamageOil(15), flameThrower]), 'Damage')
  assert.equal(damage.modifiedValue, 10.5)
})

test('a -100% converting scroll leaves 1% of base plus flat damage', () => {
  assert.equal(stat(calculateModifiedStats(weapon, [], [flatDamageOil(15), steam]), 'Damage').modifiedValue, 0.75)
})

test('flat, scroll percent and oil percent combine as (base + flat) x scroll x oils', () => {
  const damage = stat(calculateModifiedStats(bigGun, [], [flatDamageOil(20), damageOil, flameThrower]), 'Damage')
  assert.equal(damage.modifiedValue, 109.2)
})

test('flat spread is added before a converting scroll percentage', () => {
  const spread = stat(calculateModifiedStats(weapon, [], [flatSpreadOil(1), flameThrower]), 'Spread')
  assert.equal(spread.modifiedValue, 15)
})

// --- Attachment percentages pool with oil percentages ---

const albatross = { name: 'M87 "Albatross" Silencer', type: 'muzzle', modifiers: { Damage: { value: 0.15, type: 'percent' } } }
const primingBoltAtt = { name: 'Priming Bolt', type: 'chamber', modifiers: { Damage: { value: 0.1, type: 'percent' }, Spread: -0.1 } }

test('two attachment percentages on one stat add together', () => {
  const damage = stat(calculateModifiedStats(weapon, [albatross, primingBoltAtt], []), 'Damage')
  assert.equal(damage.modifiedValue, 75)
})

test('attachment and oil percentages on one stat add together', () => {
  const damage = stat(calculateModifiedStats(weapon, [albatross], [damageOil]), 'Damage')
  assert.equal(damage.modifiedValue, 99)
})

test('a converting scroll stays a separate factor from pooled attachment and oil percentages', () => {
  const damage = stat(calculateModifiedStats(bigGun, [albatross], [damageOil, flameThrower]), 'Damage')
  assert.equal(damage.modifiedValue, 115.5)
})

test('attachment flat changes still apply before percentages', () => {
  const spread = stat(calculateModifiedStats(weapon, [primingBoltAtt], [{ name: 'Spread %', modifiers: [{ attribute: 'Spread', modType: 200, value: 1 }] }]), 'Spread')
  assert.equal(spread.modifiedValue, 9.8)
})
