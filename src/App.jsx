import { useState, useEffect } from 'react'
import './App.css'
import WeaponSelector from './components/WeaponSelector'
import EnchantmentSelector from './components/EnchantmentSelector'
import StatsDisplay from './components/StatsDisplay'
import SavedConfigs from './components/SavedConfigs'
import { calculateModifiedStats } from './utils/calculator'

const STORAGE_KEY = 'sulfur_saved_configs'

function App() {
  const [weapons, setWeapons] = useState([])
  const [oils, setOils] = useState([])
  const [scrolls, setScrolls] = useState([])
  const [selectedWeapon, setSelectedWeapon] = useState(null)
  const [selectedOils, setSelectedOils] = useState([])
  const [selectedScroll, setSelectedScroll] = useState(null)
  const [modifiedStats, setModifiedStats] = useState(null)
  const [savedConfigs, setSavedConfigs] = useState([])

  // Load data on mount
  useEffect(() => {
    const baseUrl = import.meta.env.BASE_URL
    Promise.all([
      fetch(`${baseUrl}data/weapons.json`).then(r => r.json()),
      fetch(`${baseUrl}data/enchantments.json`).then(r => r.json()),
      fetch(`${baseUrl}data/scrolls.json`).then(r => r.json())
    ]).then(([weaponData, oilsData, scrollsData]) => {
      setWeapons(Array.isArray(weaponData) ? weaponData : weaponData.weapons || [])
      setOils(Array.isArray(oilsData) ? oilsData : oilsData.enchantments || [])
      setScrolls(Array.isArray(scrollsData) ? scrollsData : scrollsData.scrolls || [])
    }).catch(err => {
      console.error('Error loading data:', err)
    })

    // Load saved configs from localStorage
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved) {
        setSavedConfigs(JSON.parse(saved))
      }
    } catch (err) {
      console.error('Error loading saved configs:', err)
    }
  }, [])

  // Calculate modified stats when weapon or enchantments change
  useEffect(() => {
    if (selectedWeapon && (selectedOils.length > 0 || selectedScroll)) {
      const allEnchantments = [...selectedOils]
      if (selectedScroll) {
        allEnchantments.push(selectedScroll)
      }
      const modified = calculateModifiedStats(selectedWeapon, allEnchantments)
      setModifiedStats(modified)
    } else {
      setModifiedStats(null)
    }
  }, [selectedWeapon, selectedOils, selectedScroll])

  const resetAll = () => {
    setSelectedWeapon(null)
    setSelectedOils([])
    setSelectedScroll(null)
  }

  const saveConfig = (name) => {
    const newConfig = {
      name,
      weapon: selectedWeapon,
      oils: selectedOils,
      scroll: selectedScroll,
      timestamp: Date.now()
    }

    const updated = [...savedConfigs, newConfig]
    setSavedConfigs(updated)

    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
    } catch (err) {
      console.error('Error saving config:', err)
      alert('Failed to save configuration')
    }
  }

  const loadConfig = (config) => {
    setSelectedWeapon(config.weapon)
    setSelectedOils(config.oils || [])
    setSelectedScroll(config.scroll || null)
  }

  const deleteConfig = (index) => {
    if (confirm('Are you sure you want to delete this build?')) {
      const updated = savedConfigs.filter((_, i) => i !== index)
      setSavedConfigs(updated)

      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
      } catch (err) {
        console.error('Error deleting config:', err)
      }
    }
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <header className="bg-gray-800 border-b border-gray-700 p-6">
        <h1 className="text-4xl font-bold text-center text-red-500">
          SULFUR Weapon Calculator
        </h1>
        <p className="text-center text-gray-400 mt-2">
          Calculate weapon stats with oils and scrolls (up to 5 oils OR 4 oils + 1 scroll)
        </p>
      </header>

      <main className="container mx-auto p-6 max-w-[1800px]">
        {(selectedWeapon || selectedOils.length > 0 || selectedScroll) && (
          <div className="mb-6 flex justify-center">
            <button
              onClick={resetAll}
              className="px-6 py-2 bg-red-600 hover:bg-red-700 text-white font-semibold rounded-lg transition-colors shadow-lg"
            >
              Reset All
            </button>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mb-8">
          {/* Saved Configs - Left Column */}
          <div className="lg:col-span-3">
            <SavedConfigs
              savedConfigs={savedConfigs}
              onLoadConfig={loadConfig}
              onDeleteConfig={deleteConfig}
              onSaveConfig={saveConfig}
              currentConfig={{
                weapon: selectedWeapon,
                oils: selectedOils,
                scroll: selectedScroll
              }}
            />
          </div>

          {/* Weapon and Enchantment Selectors - Middle Columns */}
          <div className="lg:col-span-9 grid grid-cols-1 md:grid-cols-2 gap-6">
            <WeaponSelector
              weapons={weapons}
              selectedWeapon={selectedWeapon}
              onSelectWeapon={setSelectedWeapon}
            />
            <EnchantmentSelector
              oils={oils}
              scrolls={scrolls}
              selectedOils={selectedOils}
              selectedScroll={selectedScroll}
              onSelectOils={setSelectedOils}
              onSelectScroll={setSelectedScroll}
            />
          </div>
        </div>

        <StatsDisplay
          weapon={selectedWeapon}
          selectedOils={selectedOils}
          selectedScroll={selectedScroll}
          modifiedStats={modifiedStats}
        />
      </main>

      <footer className="bg-gray-800 border-t border-gray-700 p-4 mt-12">
        <p className="text-center text-gray-500 text-sm">
          SULFUR Weapon Calculator | Data extracted from game files
        </p>
      </footer>
    </div>
  )
}

export default App
