import { useState, useEffect } from 'react'
import './App.css'
import WeaponSelector from './components/WeaponSelector'
import EnchantmentSelector from './components/EnchantmentSelector'
import AttachmentSelector from './components/AttachmentSelector'
import StatsDisplay from './components/StatsDisplay'
import SavedConfigs from './components/SavedConfigs'
import { calculateModifiedStats } from './utils/calculator'

const STORAGE_KEY = 'sulfur_saved_configs'
const CURRENT_BUILD_KEY = 'sulfur_current_build'

function App() {
  const [weapons, setWeapons] = useState([])
  const [oils, setOils] = useState([])
  const [scrolls, setScrolls] = useState([])
  const [selectedWeapon, setSelectedWeapon] = useState(null)
  const [selectedOils, setSelectedOils] = useState([])
  const [selectedScroll, setSelectedScroll] = useState(null)
  const [modifiedStats, setModifiedStats] = useState(null)
  const [savedConfigs, setSavedConfigs] = useState([])
  const [attachmentsByType, setAttachmentsByType] = useState({
    muzzle: [],
    sight: [],
    laser: [],
    chamber: [],
    chisel: [],
    insurance: []
  })
  const [selectedAttachments, setSelectedAttachments] = useState({
    muzzle: null,
    sight: null,
    laser: null,
    chamber: null,
    chisel: null,
    insurance: null
  })
  const [caliberModifiers, setCaliberModifiers] = useState({})

  // Load data on mount
  useEffect(() => {
    const baseUrl = import.meta.env.BASE_URL
    Promise.all([
      fetch(`${baseUrl}data/weapons.json`).then(r => r.json()),
      fetch(`${baseUrl}data/enchantments.json`).then(r => r.json()),
      fetch(`${baseUrl}data/scrolls.json`).then(r => r.json()),
      fetch(`${baseUrl}data/attachments-muzzle.json`).then(r => r.json()),
      fetch(`${baseUrl}data/attachments-sights.json`).then(r => r.json()),
      fetch(`${baseUrl}data/attachments-lasers.json`).then(r => r.json()),
      fetch(`${baseUrl}data/attachments-chamber.json`).then(r => r.json()),
      fetch(`${baseUrl}data/attachments-chisels.json`).then(r => r.json()),
      fetch(`${baseUrl}data/attachments-insurance.json`).then(r => r.json()),
      fetch(`${baseUrl}data/caliber-modifiers.json`).then(r => r.json())
    ]).then(([
      weaponData,
      oilsData,
      scrollsData,
      muzzleData,
      sightData,
      laserData,
      chamberData,
      chiselData,
      insuranceData,
      caliberData
    ]) => {
      setWeapons(Array.isArray(weaponData) ? weaponData : weaponData.weapons || [])
      setOils(Array.isArray(oilsData) ? oilsData : oilsData.enchantments || [])
      setScrolls(Array.isArray(scrollsData) ? scrollsData : scrollsData.scrolls || [])
      setAttachmentsByType({
        muzzle: Array.isArray(muzzleData) ? muzzleData : [],
        sight: Array.isArray(sightData) ? sightData : [],
        laser: Array.isArray(laserData) ? laserData : [],
        chamber: Array.isArray(chamberData) ? chamberData : [],
        chisel: Array.isArray(chiselData) ? chiselData : [],
        insurance: Array.isArray(insuranceData) ? insuranceData : []
      })
      setCaliberModifiers(caliberData || {})
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

    // Load current build from localStorage
    try {
      const currentBuild = localStorage.getItem(CURRENT_BUILD_KEY)
      if (currentBuild) {
        const build = JSON.parse(currentBuild)
        if (build.weapon) setSelectedWeapon(build.weapon)
        if (build.attachments) setSelectedAttachments(build.attachments)
        if (build.oils) setSelectedOils(build.oils)
        if (build.scroll) setSelectedScroll(build.scroll)
      }
    } catch (err) {
      console.error('Error loading current build:', err)
    }
  }, [])

  // Calculate modified stats when weapon, attachments, or enchantments change
  useEffect(() => {
    const hasAttachments = Object.values(selectedAttachments).some(a => a !== null)

    if (selectedWeapon && (selectedOils.length > 0 || selectedScroll || hasAttachments)) {
      const allEnchantments = [...selectedOils]
      if (selectedScroll) {
        allEnchantments.push(selectedScroll)
      }

      const attachmentsList = Object.values(selectedAttachments).filter(a => a !== null)
      const modified = calculateModifiedStats(
        selectedWeapon,
        attachmentsList,
        allEnchantments,
        caliberModifiers
      )
      setModifiedStats(modified)
    } else {
      setModifiedStats(null)
    }
  }, [selectedWeapon, selectedAttachments, selectedOils, selectedScroll, caliberModifiers])

  // Auto-save current build to localStorage
  useEffect(() => {
    if (selectedWeapon) {
      const currentBuild = {
        weapon: selectedWeapon,
        attachments: selectedAttachments,
        oils: selectedOils,
        scroll: selectedScroll
      }
      try {
        localStorage.setItem(CURRENT_BUILD_KEY, JSON.stringify(currentBuild))
      } catch (err) {
        console.error('Error saving current build:', err)
      }
    }
  }, [selectedWeapon, selectedAttachments, selectedOils, selectedScroll])

  const resetAll = () => {
    setSelectedWeapon(null)
    setSelectedOils([])
    setSelectedScroll(null)
    setSelectedAttachments({
      muzzle: null,
      sight: null,
      laser: null,
      chamber: null,
      chisel: null,
      insurance: null
    })
    // Clear current build from localStorage
    try {
      localStorage.removeItem(CURRENT_BUILD_KEY)
    } catch (err) {
      console.error('Error clearing current build:', err)
    }
  }

  const handleSelectAttachment = (type, attachment) => {
    setSelectedAttachments(prev => ({
      ...prev,
      [type]: attachment
    }))
  }

  const handleRemoveAttachment = (type) => {
    setSelectedAttachments(prev => ({
      ...prev,
      [type]: null
    }))
  }

  const handleRemoveAllAttachments = () => {
    setSelectedAttachments({
      muzzle: null,
      sight: null,
      laser: null,
      chamber: null,
      chisel: null,
      insurance: null
    })
  }

  const saveConfig = (name) => {
    const newConfig = {
      name,
      weapon: selectedWeapon,
      attachments: selectedAttachments,
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
    setSelectedAttachments(config.attachments || {
      muzzle: null,
      sight: null,
      laser: null,
      chamber: null,
      chisel: null,
      insurance: null
    })
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
          Calculate weapon stats with attachments, oils and scrolls (6 attachment slots + up to 5 oils OR 4 oils + 1 scroll)
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

        {/* Attachment Selector */}
        <div className="mb-8">
          <AttachmentSelector
            attachmentsByType={attachmentsByType}
            selectedAttachments={selectedAttachments}
            onSelectAttachment={handleSelectAttachment}
            onRemoveAttachment={handleRemoveAttachment}
            onRemoveAll={handleRemoveAllAttachments}
          />
        </div>

        <StatsDisplay
          weapon={selectedWeapon}
          selectedOils={selectedOils}
          selectedScroll={selectedScroll}
          selectedAttachments={selectedAttachments}
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
