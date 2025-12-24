import React from 'react'

export default function WeaponSelector({ weapons, selectedWeapon, onSelectWeapon }) {
  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <h2 className="text-2xl font-bold mb-4 text-red-400">Select Weapon</h2>

      {weapons.length === 0 ? (
        <p className="text-gray-400">Loading weapons...</p>
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

      {selectedWeapon && (
        <div className="mt-4 p-4 bg-gray-700 rounded">
          <div className="flex items-start gap-4 mb-3">
            {selectedWeapon.image && (
              <div className="flex-shrink-0">
                <img
                  src={`https://sulfur.wiki.gg/wiki/Special:FilePath/${encodeURIComponent(selectedWeapon.image)}`}
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
