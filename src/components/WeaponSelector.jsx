import React, { useState } from 'react'

export default function WeaponSelector({ weapons, selectedWeapon, onSelectWeapon }) {
  const [searchQuery, setSearchQuery] = useState('')

  // Search filter function
  const searchWeapons = (weapons, query) => {
    if (!query.trim()) return weapons

    const lowerQuery = query.toLowerCase()

    return weapons.filter(weapon => {
      // Search in name
      if (weapon.name.toLowerCase().includes(lowerQuery)) {
        return true
      }

      // Search in type
      if (weapon.type && weapon.type.toLowerCase().includes(lowerQuery)) {
        return true
      }

      // Search in ammo type
      if (weapon.ammoType && weapon.ammoType.toLowerCase().includes(lowerQuery)) {
        return true
      }

      // Search in base stats
      if (weapon.baseStats || weapon.base_stats) {
        const stats = weapon.baseStats || weapon.base_stats
        const statText = Object.entries(stats)
          .map(([key, value]) => `${key} ${value}`)
          .join(' ')
          .toLowerCase()

        if (statText.includes(lowerQuery)) {
          return true
        }
      }

      return false
    })
  }

  const filteredWeapons = searchWeapons(weapons, searchQuery)

  const handleWeaponSelect = (weapon) => {
    onSelectWeapon(weapon)
    setSearchQuery('') // Clear search on selection
  }

  const clearSearch = () => {
    setSearchQuery('')
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <h2 className="text-2xl font-bold mb-4 text-red-400">Select Weapon</h2>

      {weapons.length === 0 ? (
        <p className="text-gray-400">Loading weapons...</p>
      ) : (
        <>
          {/* Search Input */}
          <div className="relative mb-2">
            <input
              type="text"
              placeholder="Search by name, type, or stat..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Escape') {
                  clearSearch()
                }
              }}
              className="w-full bg-gray-700 border border-gray-600 rounded px-4 py-2 text-white pr-10"
            />
            {searchQuery && (
              <button
                onClick={clearSearch}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
                aria-label="Clear search"
              >
                ✕
              </button>
            )}
          </div>

          {/* Show filtered results list when searching, otherwise show dropdown */}
          {searchQuery ? (
            <div className="bg-gray-700 border border-gray-600 rounded max-h-96 overflow-y-auto">
              {filteredWeapons.length === 0 ? (
                <div className="text-gray-400 text-center py-4">
                  No weapons found for "{searchQuery}"
                </div>
              ) : (
                <div>
                  {filteredWeapons.map(weapon => (
                    <div
                      key={weapon.id}
                      onClick={() => handleWeaponSelect(weapon)}
                      className="flex items-start gap-3 p-3 hover:bg-gray-600 cursor-pointer border-b border-gray-600 last:border-b-0"
                    >
                      {weapon.image && (
                        <img
                          src={`${import.meta.env.BASE_URL}images/weapons/${weapon.image}`}
                          alt={weapon.name}
                          className="w-12 h-12 object-contain bg-gray-800 rounded border border-gray-600 flex-shrink-0"
                          onError={(e) => { e.target.style.display = 'none' }}
                        />
                      )}
                      <div className="flex-1 min-w-0">
                        <p className="font-bold text-sm truncate">{weapon.name}</p>
                        <p className="text-xs text-gray-400">
                          {weapon.type || 'Unknown'} • {weapon.ammoType || 'Unknown Ammo'}
                        </p>
                        {(weapon.baseStats || weapon.base_stats) && (
                          <p className="text-xs text-red-300 mt-1 truncate">
                            {Object.entries(weapon.baseStats || weapon.base_stats)
                              .slice(0, 3)
                              .map(([stat, value]) => `${stat}: ${value}`)
                              .join(', ')}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <select
              className="w-full bg-gray-700 border border-gray-600 rounded px-4 py-2 text-white"
              value={selectedWeapon?.id || ''}
              onChange={(e) => {
                const weapon = weapons.find(w => w.id == e.target.value)
                onSelectWeapon(weapon)
              }}
            >
              <option value="">-- Select a Weapon --</option>
              {weapons.map(weapon => (
                <option key={weapon.id} value={weapon.id}>
                  {weapon.name} {weapon.type ? `(${weapon.type})` : ''}
                </option>
              ))}
            </select>
          )}
        </>
      )}

      {selectedWeapon && (
        <div className="mt-4 p-4 bg-gray-700 rounded">
          <div className="flex items-start gap-4 mb-3">
            {selectedWeapon.image && (
              <div className="flex-shrink-0">
                <img
                  src={`${import.meta.env.BASE_URL}images/weapons/${selectedWeapon.image}`}
                  alt={selectedWeapon.name}
                  className="w-24 h-24 object-contain bg-gray-800 rounded border border-gray-600"
                  onError={(e) => {
                    e.target.style.display = 'none'
                  }}
                />
              </div>
            )}
            <div className="flex-1">
              <h3 className="font-bold text-lg mb-1">{selectedWeapon.name}</h3>
              <p className="text-sm text-gray-400">
                {selectedWeapon.type || 'Unknown'} • {selectedWeapon.ammoType || 'Unknown Ammo'}
              </p>
            </div>
          </div>
          {(selectedWeapon.baseStats || selectedWeapon.base_stats) && Object.keys(selectedWeapon.baseStats || selectedWeapon.base_stats).length > 0 && (
            <div>
              <p className="text-sm font-semibold mb-1">Base Stats:</p>
              <ul className="text-sm space-y-1">
                {Object.entries(selectedWeapon.baseStats || selectedWeapon.base_stats).slice(0, 10).map(([stat, value]) => (
                  <li key={stat} className="text-gray-300">
                    {stat}: <span className="text-green-400">{value}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
