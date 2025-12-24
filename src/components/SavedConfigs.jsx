import React, { useState } from 'react'

export default function SavedConfigs({ savedConfigs, onLoadConfig, onDeleteConfig, onSaveConfig, currentConfig }) {
  const [isNaming, setIsNaming] = useState(false)
  const [configName, setConfigName] = useState('')

  const handleSave = () => {
    if (!currentConfig.weapon) {
      alert('Please select a weapon first')
      return
    }
    setIsNaming(true)
  }

  const confirmSave = () => {
    if (!configName.trim()) {
      alert('Please enter a name for this configuration')
      return
    }
    onSaveConfig(configName.trim())
    setConfigName('')
    setIsNaming(false)
  }

  const cancelSave = () => {
    setConfigName('')
    setIsNaming(false)
  }

  const getWeaponImageUrl = (weapon) => {
    return weapon.image
      ? `https://sulfur.wiki.gg/wiki/Special:FilePath/${encodeURIComponent(weapon.image)}`
      : null
  }

  const getEnchantmentImageUrl = (enchantment) => {
    // Enchantments use the name with .png extension
    const imageName = `${enchantment.name}.png`
    return `https://sulfur.wiki.gg/wiki/Special:FilePath/${encodeURIComponent(imageName)}`
  }

  const calculateTotalDamage = (weapon) => {
    const damage = weapon.baseStats?.Damage || 0
    const projectiles = weapon.baseStats?.ProjectileCount || 1
    return Math.round(damage * projectiles * 100) / 100
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold text-cyan-400">Saved Builds</h2>
        {!isNaming && (
          <button
            onClick={handleSave}
            disabled={!currentConfig.weapon}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-semibold rounded transition-colors"
          >
            Save Current
          </button>
        )}
      </div>

      {isNaming && (
        <div className="mb-4 p-4 bg-gray-900 rounded border border-cyan-600">
          <h3 className="text-lg font-semibold mb-2 text-cyan-300">Name Your Build</h3>
          <input
            type="text"
            value={configName}
            onChange={(e) => setConfigName(e.target.value)}
            placeholder="Enter build name..."
            className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded text-white mb-3"
            autoFocus
            onKeyPress={(e) => e.key === 'Enter' && confirmSave()}
          />
          <div className="flex gap-2">
            <button
              onClick={confirmSave}
              className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 text-white font-semibold rounded transition-colors"
            >
              Save
            </button>
            <button
              onClick={cancelSave}
              className="flex-1 px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white font-semibold rounded transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {savedConfigs.length === 0 ? (
        <div className="text-center text-gray-500 py-8">
          No saved builds yet. Create your first build!
        </div>
      ) : (
        <div className="space-y-3 max-h-[600px] overflow-y-auto">
          {savedConfigs.map((config, index) => (
            <div
              key={index}
              className="bg-gray-900 rounded-lg p-4 border border-gray-700 hover:border-cyan-600 transition-colors cursor-pointer"
              onClick={() => onLoadConfig(config)}
            >
              <div className="flex justify-between items-start mb-3">
                <h3 className="text-lg font-bold text-cyan-300">{config.name}</h3>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    onDeleteConfig(index)
                  }}
                  className="text-red-400 hover:text-red-300 text-sm"
                >
                  Delete
                </button>
              </div>

              {/* Weapon Info */}
              <div className="flex items-center gap-3 mb-3 pb-3 border-b border-gray-700">
                {getWeaponImageUrl(config.weapon) && (
                  <img
                    src={getWeaponImageUrl(config.weapon)}
                    alt={config.weapon.name}
                    className="w-16 h-16 object-contain bg-gray-800 rounded border border-gray-600"
                    onError={(e) => { e.target.style.display = 'none' }}
                  />
                )}
                <div className="flex-1">
                  <div className="font-semibold text-white">{config.weapon.name}</div>
                  <div className="text-sm text-gray-400">
                    Total Damage: <span className="text-cyan-400 font-mono">{calculateTotalDamage(config.weapon)}</span>
                  </div>
                </div>
              </div>

              {/* Oils */}
              {config.oils && config.oils.length > 0 && (
                <div className="mb-3">
                  <div className="text-xs text-gray-400 mb-2">Oils:</div>
                  <div className="space-y-1">
                    {config.oils.map((oil, idx) => (
                      <div key={idx} className="flex items-center gap-2">
                        <img
                          src={getEnchantmentImageUrl(oil)}
                          alt={oil.name}
                          className="w-8 h-8 object-contain bg-gray-800 rounded border border-gray-600"
                          onError={(e) => { e.target.style.display = 'none' }}
                        />
                        <span className="text-sm text-gray-300">{oil.name}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Scroll */}
              {config.scroll && (
                <div>
                  <div className="text-xs text-gray-400 mb-2">Scroll:</div>
                  <div className="flex items-center gap-2">
                    <img
                      src={getEnchantmentImageUrl(config.scroll)}
                      alt={config.scroll.name}
                      className="w-8 h-8 object-contain bg-gray-800 rounded border border-gray-600"
                      onError={(e) => { e.target.style.display = 'none' }}
                    />
                    <span className="text-sm text-gray-300">{config.scroll.name}</span>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
