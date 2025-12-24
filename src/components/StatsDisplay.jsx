import React from 'react'

export default function StatsDisplay({ weapon, selectedOils, selectedScroll, modifiedStats }) {
  const hasEnchantments = selectedOils.length > 0 || selectedScroll

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

  // Construct wiki image URL using Special:FilePath
  const imageUrl = weapon.image
    ? `https://sulfur.wiki.gg/wiki/Special:FilePath/${encodeURIComponent(weapon.image)}`
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

      <div className={`grid grid-cols-1 ${hasEnchantments && modifiedStats ? 'md:grid-cols-2' : ''} gap-6`}>
        {/* Base Stats */}
        <div>
          <h3 className="font-bold text-lg mb-3 text-gray-300">Base Stats</h3>
          <div className="space-y-2">
            {Object.entries(weapon.baseStats || weapon.base_stats || {})
              .filter(([stat]) => stat !== 'ProjectileCount') // Don't show ProjectileCount separately
              .map(([stat, value]) => {
                // Format Damage with projectile count
                let displayValue = value
                if (stat === 'Damage') {
                  const projectiles = (weapon.baseStats || weapon.base_stats || {}).ProjectileCount || 1
                  if (projectiles > 1) {
                    displayValue = `${value}x${Math.round(projectiles)}`
                  }
                }

                return (
                  <div key={stat} className="flex justify-between p-2 bg-gray-700 rounded">
                    <span className="text-gray-300">{stat}</span>
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
                  return Math.round(damage * projectiles * 100) / 100
                })()}
              </span>
            </div>
            <div className="text-xs text-gray-500 mt-1">
              Damage × Projectile Count
            </div>
          </div>
        </div>

        {/* Modified Stats - Only show if enchantments are selected */}
        {hasEnchantments && modifiedStats && (
          <div>
            <h3 className="font-bold text-lg mb-3 text-cyan-300">After Enchantments</h3>
            <div className="space-y-2">
              {modifiedStats
                .filter(({ stat }) => stat !== 'ProjectileCount') // Don't show ProjectileCount separately
                .map(({ stat, baseValue, modifiedValue, change, modifier }) => {
                  // Format Damage with projectile count
                  let displayModified = modifiedValue
                  let displayBase = baseValue

                  if (stat === 'Damage') {
                    const projectileStat = modifiedStats.find(s => s.stat === 'ProjectileCount')
                    const projectiles = projectileStat ? projectileStat.modifiedValue : (weapon.baseStats || weapon.base_stats || {}).ProjectileCount || 1
                    if (projectiles > 1) {
                      displayModified = `${modifiedValue}x${Math.round(projectiles)}`
                      const baseProjectiles = (weapon.baseStats || weapon.base_stats || {}).ProjectileCount || 1
                      if (baseProjectiles > 1) {
                        displayBase = `${baseValue}x${Math.round(baseProjectiles)}`
                      }
                    }
                  }

                  return (
                    <div key={stat} className="p-2 bg-gray-700 rounded">
                      <div className="flex justify-between items-center">
                        <span className="text-gray-300">{stat}</span>
                        <span className={`font-mono ${change !== 0 ? 'text-cyan-400 font-bold' : 'text-gray-400'}`}>
                          {displayModified}
                        </span>
                      </div>
                      {change !== 0 && (
                        <div className="text-xs text-gray-500 mt-1">
                          {displayBase} → {displayModified}
                          <span className={change > 0 ? 'text-green-400' : 'text-red-400'}>
                            {' '}({change > 0 ? '+' : ''}{change})
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
                    return Math.round(damage * projectiles * 100) / 100
                  })()}
                </span>
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Damage × Projectile Count
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
