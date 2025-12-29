import React, { useState } from 'react'

export default function EnchantmentSelector({ oils, scrolls, selectedOils, selectedScroll, onSelectOils, onSelectScroll }) {
  const [oilSearchQuery, setOilSearchQuery] = useState('')
  const [scrollSearchQuery, setScrollSearchQuery] = useState('')

  const validOils = oils.filter(o => o.modifiers && o.modifiers.length > 0)
  // Include all scrolls, even those without stat modifiers (they may have special effects)
  const validScrolls = scrolls

  const maxOils = selectedScroll ? 4 : 5
  const canAddOil = selectedOils.length < maxOils
  const canAddScroll = !selectedScroll && selectedOils.length < 5

  // Search filter function for enchantments (oils/scrolls)
  const searchItems = (items, query) => {
    if (!query.trim()) return items

    const lowerQuery = query.toLowerCase()

    return items.filter(item => {
      // Search in name
      if (item.name.toLowerCase().includes(lowerQuery)) {
        return true
      }

      // Search in modifiers
      if (item.modifiers && item.modifiers.length > 0) {
        const modText = item.modifiers.map(mod =>
          `${mod.attribute} ${mod.value}`
        ).join(' ').toLowerCase()

        if (modText.includes(lowerQuery)) {
          return true
        }
      }

      // Search in special effects
      if (item.specialEffects && Object.keys(item.specialEffects).length > 0) {
        const effectText = Object.entries(item.specialEffects)
          .map(([key, value]) => `${key} ${value}`)
          .join(' ')
          .toLowerCase()

        if (effectText.includes(lowerQuery)) {
          return true
        }
      }

      // Search in effects array
      if (item.effects && item.effects.length > 0) {
        const effectsText = item.effects.join(' ').toLowerCase()
        if (effectsText.includes(lowerQuery)) {
          return true
        }
      }

      // Search in description
      if (item.description && item.description.toLowerCase().includes(lowerQuery)) {
        return true
      }

      return false
    })
  }

  const filteredOils = searchItems(validOils, oilSearchQuery)
  const filteredScrolls = searchItems(validScrolls, scrollSearchQuery)

  const addOil = (oilId) => {
    const oil = validOils.find(o => o.id === oilId)
    if (oil && canAddOil) {
      onSelectOils([...selectedOils, oil])
      // Don't clear search for oils - allow continued searching
    }
  }

  const handleOilClickFromSearch = (oil) => {
    if (!selectedOils.find(s => s.id === oil.id) && canAddOil) {
      onSelectOils([...selectedOils, oil])
      // Keep search active for multi-select
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

  const handleScrollClickFromSearch = (scroll) => {
    if (canAddScroll) {
      onSelectScroll(scroll)
      setScrollSearchQuery('') // Clear search on scroll selection
    }
  }

  const clearAllEnchantments = () => {
    onSelectOils([])
    onSelectScroll(null)
  }

  const clearAllOils = () => {
    onSelectOils([])
  }

  const clearOilSearch = () => {
    setOilSearchQuery('')
  }

  const clearScrollSearch = () => {
    setScrollSearchQuery('')
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
          <>
            {/* Oil Search Input */}
            <div className="relative mb-2">
              <input
                type="text"
                placeholder="Search oils by name or stat..."
                value={oilSearchQuery}
                onChange={(e) => setOilSearchQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Escape') {
                    clearOilSearch()
                  }
                }}
                className="w-full bg-gray-700 border border-gray-600 rounded px-4 py-2 text-white pr-10"
              />
              {oilSearchQuery && (
                <button
                  onClick={clearOilSearch}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
                  aria-label="Clear search"
                >
                  ✕
                </button>
              )}
            </div>

            {/* Show filtered results list when searching, otherwise show dropdown */}
            {oilSearchQuery ? (
              <div className="bg-gray-700 border border-gray-600 rounded max-h-96 overflow-y-auto mb-3">
                {filteredOils.length === 0 ? (
                  <div className="text-gray-400 text-center py-4">
                    No oils found for "{oilSearchQuery}"
                  </div>
                ) : (
                  <div>
                    {filteredOils.map(oil => {
                      const isSelected = selectedOils.find(s => s.id === oil.id)
                      const imageUrl = `${import.meta.env.BASE_URL}images/oils/${oil.name}.png`

                      return (
                        <div
                          key={oil.id}
                          onClick={() => handleOilClickFromSearch(oil)}
                          className={`flex items-start gap-3 p-3 border-b border-gray-600 last:border-b-0 ${
                            isSelected
                              ? 'bg-gray-600 opacity-60 cursor-not-allowed'
                              : 'hover:bg-gray-600 cursor-pointer'
                          }`}
                        >
                          <img
                            src={imageUrl}
                            alt={oil.name}
                            className="w-12 h-12 object-contain bg-gray-800 rounded border border-gray-600 flex-shrink-0"
                            onError={(e) => { e.target.style.display = 'none' }}
                          />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <p className="font-bold text-sm truncate">{oil.name}</p>
                              {isSelected && <span className="text-green-400 text-sm">✓</span>}
                            </div>
                            <ul className="text-xs text-purple-300 mt-1">
                              {oil.modifiers.map((mod, midx) => {
                                const sign = mod.value > 0 ? '+' : ''
                                const displayValue = mod.modType === 200
                                  ? `${sign}${(mod.value * 100).toFixed(0)}%`
                                  : `${sign}${mod.value}`
                                return (
                                  <li key={midx} className="truncate">
                                    {mod.attribute}: {displayValue}
                                  </li>
                                )
                              })}
                              {oil.effects && oil.effects.map((effect, idx) => (
                                <li key={`effect-${idx}`} className="truncate text-yellow-300">
                                  • {effect}
                                </li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            ) : (
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
                    const modifierEffects = oil.modifiers.map(mod => {
                      const sign = mod.value > 0 ? '+' : ''
                      const displayValue = mod.modType === 200
                        ? `${sign}${(mod.value * 100).toFixed(0)}%`
                        : `${sign}${mod.value}`
                      return `${mod.attribute} ${displayValue}`
                    })

                    const specialEffects = oil.effects || []
                    const allEffects = [...modifierEffects, ...specialEffects].join(', ')

                    return (
                      <option key={oil.id} value={oil.id}>
                        {oil.name} — {allEffects}
                      </option>
                    )
                  })}
              </select>
            )}
          </>
        )}

        {selectedOils.length > 0 && (
          <div className="space-y-2">
            {selectedOils.map((oil, idx) => {
              const imageUrl = `${import.meta.env.BASE_URL}images/oils/${oil.name}.png`

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
                        {oil.effects && oil.effects.map((effect, idx) => (
                          <li key={`effect-${idx}`} className="text-yellow-300">
                            • {effect}
                          </li>
                        ))}
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
          <>
            {/* Scroll Search Input */}
            <div className="relative mb-2">
              <input
                type="text"
                placeholder="Search scrolls by name or effect..."
                value={scrollSearchQuery}
                onChange={(e) => setScrollSearchQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Escape') {
                    clearScrollSearch()
                  }
                }}
                className="w-full bg-gray-700 border border-gray-600 rounded px-4 py-2 text-white pr-10"
              />
              {scrollSearchQuery && (
                <button
                  onClick={clearScrollSearch}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
                  aria-label="Clear search"
                >
                  ✕
                </button>
              )}
            </div>

            {/* Show filtered results list when searching, otherwise show dropdown */}
            {scrollSearchQuery ? (
              <div className="bg-gray-700 border border-gray-600 rounded max-h-96 overflow-y-auto">
                {filteredScrolls.length === 0 ? (
                  <div className="text-gray-400 text-center py-4">
                    No scrolls found for "{scrollSearchQuery}"
                  </div>
                ) : (
                  <div>
                    {filteredScrolls.map(scroll => {
                      const imageUrl = `${import.meta.env.BASE_URL}images/scrolls/${scroll.name}.png`

                      return (
                        <div
                          key={scroll.id}
                          onClick={() => handleScrollClickFromSearch(scroll)}
                          className="flex items-start gap-3 p-3 hover:bg-gray-600 cursor-pointer border-b border-gray-600 last:border-b-0"
                        >
                          <img
                            src={imageUrl}
                            alt={scroll.name}
                            className="w-12 h-12 object-contain bg-gray-800 rounded border border-gray-600 flex-shrink-0"
                            onError={(e) => { e.target.style.display = 'none' }}
                          />
                          <div className="flex-1 min-w-0">
                            <p className="font-bold text-sm truncate">{scroll.name}</p>
                            {scroll.modifiers && scroll.modifiers.length > 0 && (
                              <ul className="text-xs text-blue-300 mt-1">
                                {scroll.modifiers.map((mod, idx) => {
                                  const sign = mod.value > 0 ? '+' : ''
                                  const displayValue = mod.modType === 200
                                    ? `${sign}${(mod.value * 100).toFixed(0)}%`
                                    : `${sign}${mod.value}`
                                  return (
                                    <li key={idx} className="truncate">
                                      {mod.attribute}: {displayValue}
                                    </li>
                                  )
                                })}
                              </ul>
                            )}
                            {scroll.specialEffects && Object.keys(scroll.specialEffects).length > 0 && (
                              <ul className="text-xs text-blue-300 mt-1">
                                {Object.entries(scroll.specialEffects).map(([key, value], idx) => (
                                  <li key={idx} className="truncate">
                                    {key}: {value}
                                  </li>
                                ))}
                              </ul>
                            )}
                            {scroll.effects && scroll.effects.length > 0 && (
                              <ul className="text-xs text-blue-300 mt-1">
                                {scroll.effects.slice(0, 2).map((effect, idx) => (
                                  <li key={idx} className="truncate">• {effect}</li>
                                ))}
                              </ul>
                            )}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            ) : (
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
          </>
        )}

        {selectedScroll && (
          <div className="bg-gray-700 rounded p-3">
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-3 flex-1">
                <img
                  src={`${import.meta.env.BASE_URL}images/scrolls/${selectedScroll.name}.png`}
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
