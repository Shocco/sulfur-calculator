import React from 'react'
import { formatChange } from '../utils/format'
import { totalDamage, formatTotalDamage, formatDamage } from '../utils/damage'

// What the Total Damage figure is made of, for the caption under it
function totalDamageCaption(hasBonus, shotsPerTrigger) {
  return `${hasBonus ? '(Damage + Bonus Damage)' : 'Damage'} × Projectile Count` +
    (shotsPerTrigger ? ' × Shells per Trigger Pull' : '')
}

// Format stat names for display (convert camelCase to Title Case)
function formatStatName(stat) {
  const statNameMap = {
    'CritChance': 'Crit Chance',
    'ADSCritChance': 'ADS Crit Chance',
    'ProjectileCount': 'Projectile Count',
    'MagazineSize': 'Magazine Size',
    'ReloadTime': 'Reload Time',
    'MaxDurability': 'Max Durability',
    'ProjectileSpeed': 'Projectile Speed',
    'ReloadSpeed': 'Reload Speed',
    'BulletSpeed': 'Bullet Speed',
    'AmmoConsumeChance': 'Ammo Consume Chance',
    'BulletDrop': 'Bullet Drop',
    'BulletBounces': 'Bullet Bounces',
    'BulletPenetrations': 'Bullet Penetrations',
    'BulletSize': 'Bullet Size',
    'JumpPower': 'Jump Power',
    'LootChance': 'Loot Chance',
    'MoveSpeed': 'Move Speed',
    'MoveAccuracy': 'Move Accuracy',
    'BulletBounciness': 'Bullet Bounciness',
    'HeadshotDamage': 'Headshot Damage',
    'BonusDamage': 'Bonus Damage (per projectile)'
  }

  return statNameMap[stat] || stat
}

export default function StatsDisplay({ weapon, selectedOils, selectedScroll, selectedAttachments, modifiedStats }) {
  const hasEnchantments = selectedOils.length > 0 || selectedScroll
  const hasAttachments = selectedAttachments && Object.values(selectedAttachments).some(a => a)

  if (!weapon) {
    return (
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 text-center">
        <p className="text-gray-400">Select a weapon to see its stats</p>
      </div>
    )
  }

  const enchantmentNames = [
    ...selectedOils.map(o => o.name),
    ...(selectedScroll ? [selectedScroll.name] : [])
  ]

  // Use local image
  const imageUrl = weapon.image
    ? `${import.meta.env.BASE_URL}images/weapons/${weapon.image}`
    : null

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-start gap-6 mb-4">
        {imageUrl && (
          <div className="flex-shrink-0">
            <img
              src={imageUrl}
              alt={weapon.name}
              className="w-32 h-32 object-contain bg-gray-700 rounded border border-gray-600"
              onError={(e) => {
                // Fallback if image doesn't load
                e.target.style.display = 'none'
              }}
            />
          </div>
        )}
        <div className="flex-1">
          <h2 className="text-2xl font-bold mb-2 text-cyan-400">
            {weapon.name}
          </h2>
          <p className="text-sm text-gray-500 mb-2">
            {weapon.type} • {weapon.ammoType}
          </p>
          {(selectedOils.length > 0 || selectedScroll) && (
            <div>
              <p className="text-sm text-gray-400">With Enchantments:</p>
              <div className="flex flex-wrap gap-2 mt-1">
                {selectedOils.map((oil, idx) => (
                  <span key={idx} className="text-xs bg-purple-900 text-purple-200 px-2 py-1 rounded">
                    {oil.name}
                  </span>
                ))}
                {selectedScroll && (
                  <span className="text-xs bg-blue-900 text-blue-200 px-2 py-1 rounded">
                    {selectedScroll.name}
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Attachment Summary */}
      {weapon && hasAttachments && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-300 mb-3">Active Attachments</h3>
          <div className="flex gap-2 flex-wrap">
            {Object.entries(selectedAttachments || {}).map(([type, attachment]) => (
              attachment ? (
                <div
                  key={type}
                  className="relative group"
                  title={`${attachment.name}${attachment.modifiers ? '\n' + Object.entries(attachment.modifiers).map(([k, v]) => `${k}: ${v > 0 ? '+' : ''}${v}`).join('\n') : ''}`}
                >
                  <img
                    src={`${import.meta.env.BASE_URL}${attachment.image.startsWith('/') ? attachment.image.slice(1) : attachment.image}`}
                    alt={attachment.name}
                    className="w-16 h-16 object-contain bg-gray-700 rounded border-2 border-gray-600 hover:border-red-500 transition-colors"
                  />
                  <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 hidden group-hover:block bg-gray-900 text-white text-xs rounded py-1 px-2 whitespace-nowrap z-10">
                    {attachment.name}
                  </div>
                </div>
              ) : null
            ))}
          </div>
        </div>
      )}

      <div className={`grid grid-cols-1 ${(hasEnchantments || hasAttachments) && modifiedStats ? 'md:grid-cols-2' : ''} gap-6`}>
        {/* Base Stats */}
        <div>
          <h3 className="font-bold text-lg mb-3 text-gray-300">Base Stats</h3>
          <div className="space-y-2">
            {Object.entries(weapon.baseStats || weapon.base_stats || {})
              .filter(([stat]) => {
                // Hide these stats in base stats (only show if modified)
                const hiddenStats = [
                  'CritChance', 'ADSCritChance', 'ProjectileSpeed', 'MoveSpeed',
                  'AmmoConsumeChance', 'BulletDrop', 'BulletBounces',
                  'BulletPenetrations', 'BulletSize', 'JumpPower',
                  'LootChance', 'MoveAccuracy', 'BulletBounciness'
                ]
                return !hiddenStats.includes(stat)
              })
              .sort(([statA], [statB]) => {
                // Define base stats order
                const baseStatsOrder = {
                  'Damage': 1,
                  'ProjectileCount': 2,
                  'RPM': 3,
                  'MagazineSize': 4,
                  'Spread': 5,
                  'Recoil': 6,
                  'Durability': 7,
                  'MaxDurability': 8,
                  'Weight': 9,
                  'ProjectileSpeed': 10,
                  'MoveSpeed': 11
                }
                const orderA = baseStatsOrder[statA] || 999
                const orderB = baseStatsOrder[statB] || 999

                if (orderA !== orderB) return orderA - orderB
                return statA.localeCompare(statB)
              })
              .map(([stat, value]) => {
                // Format Damage with projectile count
                let displayValue = value
                if (stat === 'Damage') {
                  const projectiles = (weapon.baseStats || weapon.base_stats || {}).ProjectileCount || 1
                  displayValue = formatDamage(value, projectiles, weapon.shotsPerTrigger)
                }
                // Format ProjectileCount as integer
                if (stat === 'ProjectileCount') {
                  displayValue = Math.round(value)
                }

                return (
                  <div key={stat} className="flex justify-between p-2 bg-gray-700 rounded">
                    <span className="text-gray-300">{formatStatName(stat)}</span>
                    <span className="font-mono text-green-400">{displayValue}</span>
                  </div>
                )
              })}
          </div>

          {/* Total Damage */}
          <div className="mt-4 p-3 bg-gray-900 rounded border border-cyan-600">
            <div className="flex justify-between items-center">
              <span className="text-cyan-300 font-semibold">Total Damage</span>
              <span className="font-mono text-cyan-400 text-lg font-bold">
                {(() => {
                  const damage = (weapon.baseStats || weapon.base_stats || {}).Damage || 0
                  const projectiles = (weapon.baseStats || weapon.base_stats || {}).ProjectileCount || 1
                  return formatTotalDamage(totalDamage({ damage, projectiles, shotsPerTrigger: weapon.shotsPerTrigger }))
                })()}
              </span>
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {totalDamageCaption(false, weapon.shotsPerTrigger)}
            </div>
          </div>
        </div>

        {/* Modified Stats - Show if enchantments or attachments are selected */}
        {(hasEnchantments || hasAttachments) && modifiedStats && (
          <div>
            <h3 className="font-bold text-lg mb-3 text-cyan-300">After Modifications</h3>
            <div className="space-y-2">
              {modifiedStats
                .filter(({ stat, change }) => {
                  // Only show these stats if they've been modified
                  const conditionalStats = [
                    'CritChance', 'ADSCritChance', 'ProjectileSpeed',
                    'AmmoConsumeChance', 'BulletDrop', 'BulletBounces',
                    'BulletPenetrations', 'BulletSize', 'JumpPower',
                    'LootChance', 'MoveSpeed', 'MoveAccuracy', 'BulletBounciness'
                  ]

                  // If it's a conditional stat, only show if changed
                  if (conditionalStats.includes(stat)) {
                    return change !== 0
                  }

                  // Show all other stats
                  return true
                })
                .sort((a, b) => {
                  // Define stat order: CritChance and ADSCritChance between Damage and ProjectileCount
                  const statOrder = {
                    'Damage': 1,
                    'BonusDamage': 1.5,
                    'CritChance': 2,
                    'ADSCritChance': 3,
                    'ProjectileCount': 4,
                    'RPM': 5,
                    'MagazineSize': 6,
                    'Spread': 7,
                    'Recoil': 8,
                    'Durability': 9,
                    'MaxDurability': 10,
                    'Weight': 11,
                    // Conditional stats (only show if modified)
                    'ProjectileSpeed': 12,
                    'ReloadTime': 13,
                    'Range': 14,
                    'ReloadSpeed': 15,
                    'BulletSpeed': 16,
                    'AmmoConsumeChance': 17,
                    'BulletDrop': 18,
                    'BulletBounces': 19,
                    'BulletPenetrations': 20,
                    'BulletSize': 21,
                    'JumpPower': 22,
                    'LootChance': 23,
                    'MoveSpeed': 24,
                    'MoveAccuracy': 25,
                    'BulletBounciness': 26
                  }

                  const orderA = statOrder[a.stat] || 999
                  const orderB = statOrder[b.stat] || 999

                  if (orderA !== orderB) return orderA - orderB
                  return a.stat.localeCompare(b.stat)
                })
                .map(({ stat, baseValue, modifiedValue, change, modifier, isRelative }) => {
                  // Format Damage with projectile count
                  let displayModified = modifiedValue
                  let displayBase = baseValue

                  if (stat === 'Damage') {
                    const projectileStat = modifiedStats.find(s => s.stat === 'ProjectileCount')
                    const projectiles = projectileStat ? projectileStat.modifiedValue : (weapon.baseStats || weapon.base_stats || {}).ProjectileCount || 1
                    const baseProjectiles = (weapon.baseStats || weapon.base_stats || {}).ProjectileCount || 1
                    displayModified = formatDamage(modifiedValue, projectiles, weapon.shotsPerTrigger)
                    displayBase = formatDamage(baseValue, baseProjectiles, weapon.shotsPerTrigger)
                  }
                  // Format ProjectileCount as integer
                  if (stat === 'ProjectileCount') {
                    displayModified = Math.round(modifiedValue)
                    displayBase = Math.round(baseValue)
                  }
                  // Format CritChance as percentage
                  if (stat === 'CritChance' || stat === 'ADSCritChance') {
                    displayModified = `${Math.round(modifiedValue * 100)}%`
                    displayBase = `${Math.round(baseValue * 100)}%`
                  }
                  // Stats with no weapon base value are a net relative change (0.8 = +80%)
                  if (isRelative) {
                    displayModified = `${modifiedValue > 0 ? '+' : ''}${Math.round(modifiedValue * 100)}%`
                  }

                  return (
                    <div key={stat} className="p-2 bg-gray-700 rounded">
                      <div className="flex justify-between items-center">
                        <span className="text-gray-300">{formatStatName(stat)}</span>
                        <span className={`font-mono ${change !== 0 ? 'text-cyan-400 font-bold' : 'text-gray-400'}`}>
                          {displayModified}
                        </span>
                      </div>
                      {change !== 0 && !isRelative && (
                        <div className="text-xs text-gray-500 mt-1">
                          {displayBase} → {displayModified}
                          <span className={change > 0 ? 'text-green-400' : 'text-red-400'}>
                            {' '}({formatChange(change, stat === 'CritChance' || stat === 'ADSCritChance')})
                          </span>
                        </div>
                      )}
                    </div>
                  )
                })}
            </div>

            {/* Total Damage - Modified */}
            <div className="mt-4 p-3 bg-gray-900 rounded border border-cyan-600">
              <div className="flex justify-between items-center">
                <span className="text-cyan-300 font-semibold">Total Damage</span>
                <span className="font-mono text-cyan-400 text-lg font-bold">
                  {(() => {
                    const damageStat = modifiedStats.find(s => s.stat === 'Damage')
                    const projectileStat = modifiedStats.find(s => s.stat === 'ProjectileCount')
                    const damage = damageStat ? damageStat.modifiedValue : (weapon.baseStats || weapon.base_stats || {}).Damage || 0
                    const projectiles = projectileStat ? projectileStat.modifiedValue : (weapon.baseStats || weapon.base_stats || {}).ProjectileCount || 1
                    const bonusStat = modifiedStats.find(s => s.stat === 'BonusDamage')
                    return formatTotalDamage(totalDamage({
                      damage,
                      projectiles,
                      bonus: bonusStat ? bonusStat.modifiedValue : 0,
                      shotsPerTrigger: weapon.shotsPerTrigger
                    }))
                  })()}
                </span>
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {totalDamageCaption(modifiedStats.some(s => s.stat === 'BonusDamage'), weapon.shotsPerTrigger)}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
