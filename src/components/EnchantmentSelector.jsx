import React from 'react'

export default function EnchantmentSelector({ oils, scrolls, selectedOils, selectedScroll, onSelectOils, onSelectScroll }) {
  const validOils = oils.filter(o => o.modifiers && o.modifiers.length > 0)
  // Include all scrolls, even those without stat modifiers (they may have special effects)
  const validScrolls = scrolls

  const maxOils = selectedScroll ? 4 : 5
  const canAddOil = selectedOils.length < maxOils
  const canAddScroll = !selectedScroll && selectedOils.length < 5

  const addOil = (oilId) => {
    const oil = validOils.find(o => o.id === oilId)
    if (oil && canAddOil) {
      onSelectOils([...selectedOils, oil])
    }
  }

  const removeOil = (index) => {
    const newOils = selectedOils.filter((_, i) => i !== index)
    onSelectOils(newOils)
  }

  const setScroll = (scrollId) => {
    if (scrollId === '') {
      onSelectScroll(null)
    } else {
      const scroll = validScrolls.find(s => s.id === scrollId)
      if (scroll && canAddScroll) {
        onSelectScroll(scroll)
      }
    }
  }

  const clearAllEnchantments = () => {
    onSelectOils([])
    onSelectScroll(null)
  }

  const clearAllOils = () => {
    onSelectOils([])
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold text-purple-400">Select Enchantments</h2>
        <div className="flex gap-2">
          {selectedOils.length > 0 && (
            <button
              onClick={clearAllOils}
              className="px-3 py-1 bg-orange-600 hover:bg-orange-700 text-white text-sm rounded transition-colors"
            >
              Clear Oils
            </button>
          )}
          {(selectedOils.length > 0 || selectedScroll) && (
            <button
              onClick={clearAllEnchantments}
              className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white text-sm rounded transition-colors"
            >
              Clear All Enchantments
            </button>
          )}
        </div>
      </div>

      {/* Oils Section */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-2 text-purple-300">
          Oils ({selectedOils.length}/{maxOils})
        </h3>

        {canAddOil && (
          <select
            className="w-full bg-gray-700 border border-gray-600 rounded px-4 py-2 text-white mb-3"
            value=""
            onChange={(e) => {
              if (e.target.value) {
                addOil(e.target.value)
                e.target.value = ''
              }
            }}
          >
            <option value="">-- Add Oil --</option>
            {validOils
              .filter(oil => !selectedOils.find(s => s.id === oil.id))
              .map(oil => {
                // Create effect summary for dropdown
                const effects = oil.modifiers.map(mod => {
                  const sign = mod.value > 0 ? '+' : ''
                  const displayValue = mod.modType === 200
                    ? `${sign}${(mod.value * 100).toFixed(0)}%`
                    : `${sign}${mod.value}`
                  return `${mod.attribute} ${displayValue}`
                }).join(', ')

                return (
                  <option key={oil.id} value={oil.id}>
                    {oil.name} — {effects}
                  </option>
                )
              })}
          </select>
        )}

        {selectedOils.length > 0 && (
          <div className="space-y-2">
            {selectedOils.map((oil, idx) => {
              const imageUrl = `https://sulfur.wiki.gg/wiki/Special:FilePath/${encodeURIComponent(oil.name)}.png`

              return (
                <div key={idx} className="flex items-start justify-between bg-gray-700 rounded p-3">
                  <div className="flex items-start gap-3 flex-1">
                    <img
                      src={imageUrl}
                      alt={oil.name}
                      className="w-12 h-12 object-contain bg-gray-800 rounded border border-gray-600 flex-shrink-0"
                      onError={(e) => { e.target.style.display = 'none' }}
                    />
                    <div className="flex-1">
                      <p className="font-semibold text-sm">{oil.name}</p>
                      <ul className="text-xs text-purple-300 mt-1">
                        {oil.modifiers.map((mod, midx) => {
                          const sign = mod.value > 0 ? '+' : ''
                          const displayValue = mod.modType === 200
                            ? `${sign}${(mod.value * 100).toFixed(0)}%`
                            : `${sign}${mod.value}`
                          return (
                            <li key={midx}>
                              {mod.attribute}: {displayValue}
                            </li>
                          )
                        })}
                      </ul>
                    </div>
                  </div>
                  <button
                    onClick={() => removeOil(idx)}
                    className="ml-2 text-red-400 hover:text-red-300 text-sm font-bold"
                  >
                    ✕
                  </button>
                </div>
              )
            })}
          </div>
        )}

        {!canAddOil && (
          <p className="text-xs text-yellow-500">
            Maximum oils selected {selectedScroll ? '(4 oils + 1 scroll limit)' : '(5 oils max)'}
          </p>
        )}
      </div>

      {/* Scrolls Section */}
      <div>
        <h3 className="text-lg font-semibold mb-2 text-blue-300">
          Scroll {selectedScroll ? '(1/1)' : '(0/1)'}
        </h3>

        {canAddScroll && !selectedScroll && (
          <select
            className="w-full bg-gray-700 border border-gray-600 rounded px-4 py-2 text-white"
            value={selectedScroll?.id || ''}
            onChange={(e) => setScroll(e.target.value)}
          >
            <option value="">-- Select Scroll (Optional) --</option>
            {validScrolls.map(scroll => {
              // Create effect summary for dropdown
              let effects = []

              if (scroll.modifiers && scroll.modifiers.length > 0) {
                effects = scroll.modifiers.map(mod => {
                  const sign = mod.value > 0 ? '+' : ''
                  const displayValue = mod.modType === 200
                    ? `${sign}${(mod.value * 100).toFixed(0)}%`
                    : `${sign}${mod.value}`
                  return `${mod.attribute} ${displayValue}`
                })
              }

              if (scroll.specialEffects && Object.keys(scroll.specialEffects).length > 0) {
                Object.entries(scroll.specialEffects).forEach(([key, value]) => {
                  effects.push(`${key}: ${value}`)
                })
              }

              if (scroll.effects && scroll.effects.length > 0) {
                effects.push(...scroll.effects)
              }

              const effectText = effects.length > 0 ? effects.join(', ') : 'Special Effect'

              return (
                <option key={scroll.id} value={scroll.id}>
                  {scroll.name} — {effectText}
                </option>
              )
            })}
          </select>
        )}

        {selectedScroll && (
          <div className="bg-gray-700 rounded p-3">
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-3 flex-1">
                <img
                  src={`https://sulfur.wiki.gg/wiki/Special:FilePath/${encodeURIComponent(selectedScroll.name)}.png`}
                  alt={selectedScroll.name}
                  className="w-12 h-12 object-contain bg-gray-800 rounded border border-gray-600 flex-shrink-0"
                  onError={(e) => { e.target.style.display = 'none' }}
                />
                <div className="flex-1">
                  <p className="font-semibold text-sm">{selectedScroll.name}</p>
                  {selectedScroll.modifiers && selectedScroll.modifiers.length > 0 && (
                    <ul className="text-xs text-blue-300 mt-1">
                      {selectedScroll.modifiers.map((mod, idx) => {
                        const sign = mod.value > 0 ? '+' : ''
                        const displayValue = mod.modType === 200
                          ? `${sign}${(mod.value * 100).toFixed(0)}%`
                          : `${sign}${mod.value}`
                        return (
                          <li key={idx}>
                            {mod.attribute}: {displayValue}
                          </li>
                        )
                      })}
                    </ul>
                  )}
                  {selectedScroll.specialEffects && Object.keys(selectedScroll.specialEffects).length > 0 && (
                    <ul className="text-xs text-blue-300 mt-1">
                      {Object.entries(selectedScroll.specialEffects).map(([key, value], idx) => (
                        <li key={idx}>
                          {key}: {value}
                        </li>
                      ))}
                    </ul>
                  )}
                  {selectedScroll.effects && selectedScroll.effects.length > 0 && (
                    <ul className="text-xs text-blue-300 mt-1">
                      {selectedScroll.effects.map((effect, idx) => (
                        <li key={idx}>• {effect}</li>
                      ))}
                    </ul>
                  )}
                  {selectedScroll.description && !selectedScroll.effects && (
                    <p className="text-xs text-gray-400 mt-1 italic">{selectedScroll.description}</p>
                  )}
                </div>
              </div>
              <button
                onClick={() => onSelectScroll(null)}
                className="ml-2 text-red-400 hover:text-red-300 text-sm font-bold"
              >
                ✕
              </button>
            </div>
          </div>
        )}

        {!canAddScroll && selectedOils.length === 5 && (
          <p className="text-xs text-yellow-500">
            Remove an oil to add a scroll (5 oils max, or 4 oils + 1 scroll)
          </p>
        )}
      </div>

      <p className="text-xs text-gray-500 mt-4">
        {validOils.length} oils, {validScrolls.length} scrolls available
      </p>
    </div>
  )
}
