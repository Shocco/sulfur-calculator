import { useState, useEffect, useRef } from 'react'

const ATTACHMENT_TYPES = [
  { key: 'muzzle', label: 'Muzzle' },
  { key: 'sight', label: 'Sight' },
  { key: 'laser', label: 'Laser' },
  { key: 'chamber', label: 'Chamber' },
  { key: 'chisel', label: 'Chisel' },
  { key: 'insurance', label: 'Insurance' }
]

function formatModifiers(attachment) {
  const lines = []

  // Format regular modifiers
  if (attachment.modifiers && Object.keys(attachment.modifiers).length > 0) {
    Object.entries(attachment.modifiers).forEach(([stat, value]) => {
      // Support both simple values and objects with {value, type}
      if (typeof value === 'object' && value !== null && 'value' in value) {
        const sign = value.value > 0 ? '+' : ''
        const displayValue = value.type === 'percent'
          ? `${sign}${(value.value * 100).toFixed(0)}%`
          : `${sign}${value.value}`
        lines.push(`${stat}: ${displayValue}`)
      } else {
        const sign = value > 0 ? '+' : ''
        // Format CritChance and ADSCritChance as percentage
        const displayValue = (stat === 'CritChance' || stat === 'ADSCritChance') ? `${sign}${Math.round(value * 100)}%` : `${sign}${value}`
        lines.push(`${stat}: ${displayValue}`)
      }
    })
  }

  // Format special effects
  if (attachment.specialEffects) {
    if (attachment.specialEffects.caliberConversion) {
      lines.push(`Caliber: ${attachment.specialEffects.caliberConversion}`)
    }
    if (attachment.specialEffects.firingMode) {
      lines.push(`Mode: ${attachment.specialEffects.firingMode}`)
    }
    if (attachment.specialEffects.protection) {
      lines.push(`Protection: ${attachment.specialEffects.protection}`)
    }
  }

  return lines
}

export default function AttachmentSelector({
  attachmentsByType,
  selectedAttachments,
  selectedWeapon,
  onSelectAttachment,
  onRemoveAttachment,
  onRemoveAll
}) {
  const [openSlot, setOpenSlot] = useState(null)
  const containerRef = useRef(null)

  const handleToggleSlot = (slotType) => {
    setOpenSlot(openSlot === slotType ? null : slotType)
  }

  // Get allowed attachment types for the selected weapon
  const allowedTypes = selectedWeapon?.allowedAttachments || ['muzzle', 'sight', 'laser', 'chamber', 'chisel', 'insurance']

  // Filter attachment types to only show allowed ones
  const availableAttachmentTypes = ATTACHMENT_TYPES.filter(({ key }) => allowedTypes.includes(key))

  // Filter attachments by specific weapon compatibility
  const getFilteredAttachments = (type) => {
    const attachments = attachmentsByType[type] || []

    // If weapon has specific attachment restrictions, use them
    if (selectedWeapon?.specificAttachments && selectedWeapon.specificAttachments.length > 0) {
      return attachments.filter(attachment =>
        selectedWeapon.specificAttachments.includes(attachment.name)
      )
    }

    // Otherwise, show all attachments of this type (fallback)
    return attachments
  }

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setOpenSlot(null)
      }
    }

    if (openSlot !== null) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [openSlot])

  return (
    <div ref={containerRef} className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold text-red-500">Attachments</h2>
        {Object.values(selectedAttachments).some(a => a) && (
          <button
            onClick={onRemoveAll}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded transition-colors text-sm"
          >
            Remove All Attachments
          </button>
        )}
      </div>

      {!selectedWeapon ? (
        <p className="text-gray-400 text-center py-4">Select a weapon to see available attachments</p>
      ) : availableAttachmentTypes.length === 0 ? (
        <p className="text-gray-400 text-center py-4">No attachments available for this weapon</p>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {availableAttachmentTypes.map(({ key, label }) => (
            <AttachmentSlot
              key={key}
              type={key}
              label={label}
              attachments={getFilteredAttachments(key)}
              selected={selectedAttachments[key]}
              isOpen={openSlot === key}
              onToggle={() => handleToggleSlot(key)}
              onSelect={(attachment) => {
                onSelectAttachment(key, attachment)
                setOpenSlot(null) // Close dropdown after selection
              }}
              onRemove={() => onRemoveAttachment(key)}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function AttachmentSlot({ type, label, attachments, selected, isOpen, onToggle, onSelect, onRemove }) {
  return (
    <div className="bg-gray-700 rounded p-3">
      <div className="text-sm font-semibold text-gray-300 mb-2">{label}</div>

      {selected ? (
        <div className="space-y-2">
          <div className="flex items-start gap-2">
            <img
              src={`${import.meta.env.BASE_URL}${selected.image.startsWith('/') ? selected.image.slice(1) : selected.image}`}
              alt={selected.name}
              className="w-12 h-12 object-contain bg-gray-600 rounded flex-shrink-0"
            />
            <div className="flex-1 min-w-0">
              <div className="text-xs text-white font-semibold mb-1">{selected.name}</div>
              {formatModifiers(selected).map((line, i) => (
                <div key={i} className="text-xs text-green-400">
                  {line}
                </div>
              ))}
            </div>
          </div>
          <button
            onClick={onRemove}
            className="w-full px-2 py-1 bg-red-600 hover:bg-red-700 text-white text-xs rounded"
          >
            Remove
          </button>
        </div>
      ) : (
        <div className="relative">
          <button
            onClick={onToggle}
            className="w-full px-3 py-2 bg-gray-600 hover:bg-gray-500 text-white text-sm rounded"
          >
            Select {label}
          </button>

          {isOpen && (
            <div className="absolute z-10 mt-1 w-80 max-h-96 overflow-y-auto bg-gray-800 border border-gray-600 rounded shadow-lg">
              {attachments.map((attachment) => (
                <button
                  key={attachment.name}
                  onClick={() => onSelect(attachment)}
                  className="w-full px-3 py-2 text-left hover:bg-gray-700 text-sm text-white flex items-start gap-2 border-b border-gray-700 last:border-b-0"
                >
                  <img
                    src={`${import.meta.env.BASE_URL}${attachment.image.startsWith('/') ? attachment.image.slice(1) : attachment.image}`}
                    alt={attachment.name}
                    className="w-10 h-10 object-contain flex-shrink-0"
                  />
                  <div className="flex-1 min-w-0">
                    <div className="font-semibold mb-1">{attachment.name}</div>
                    {formatModifiers(attachment).map((line, i) => (
                      <div key={i} className="text-xs text-green-400">
                        {line}
                      </div>
                    ))}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
