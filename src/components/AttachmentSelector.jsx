import { useState } from 'react'

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
      const sign = value > 0 ? '+' : ''
      lines.push(`${stat}: ${sign}${value}`)
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
  onSelectAttachment,
  onRemoveAttachment,
  onRemoveAll
}) {
  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
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

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {ATTACHMENT_TYPES.map(({ key, label }) => (
          <AttachmentSlot
            key={key}
            type={key}
            label={label}
            attachments={attachmentsByType[key] || []}
            selected={selectedAttachments[key]}
            onSelect={(attachment) => onSelectAttachment(key, attachment)}
            onRemove={() => onRemoveAttachment(key)}
          />
        ))}
      </div>
    </div>
  )
}

function AttachmentSlot({ type, label, attachments, selected, onSelect, onRemove }) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="bg-gray-700 rounded p-3">
      <div className="text-sm font-semibold text-gray-300 mb-2">{label}</div>

      {selected ? (
        <div className="space-y-2">
          <div className="flex items-start gap-2">
            <img
              src={selected.image}
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
            onClick={() => setIsOpen(!isOpen)}
            className="w-full px-3 py-2 bg-gray-600 hover:bg-gray-500 text-white text-sm rounded"
          >
            Select {label}
          </button>

          {isOpen && (
            <div className="absolute z-10 mt-1 w-80 max-h-96 overflow-y-auto bg-gray-800 border border-gray-600 rounded shadow-lg">
              {attachments.map((attachment) => (
                <button
                  key={attachment.name}
                  onClick={() => {
                    onSelect(attachment)
                    setIsOpen(false)
                  }}
                  className="w-full px-3 py-2 text-left hover:bg-gray-700 text-sm text-white flex items-start gap-2 border-b border-gray-700 last:border-b-0"
                >
                  <img
                    src={attachment.image}
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
