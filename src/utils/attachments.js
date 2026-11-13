/**
 * Which attachments a weapon can take.
 *
 * weapon.allowedAttachments lists the slots the weapon has. weapon.specificAttachments
 * names individual items; when some of those belong to a slot, that slot only
 * accepts them (e.g. a chamber slot that only takes Priming Bolt).
 */

// Attachments of one slot type that the weapon accepts
export function getCompatibleAttachments(weapon, type, attachments = []) {
  const specific = weapon?.specificAttachments
  if (specific && specific.length > 0) {
    const typeSpecific = attachments.filter(attachment => specific.includes(attachment.name))
    // Only restrict if some specificAttachments actually belong to this slot type
    if (typeSpecific.length > 0) return typeSpecific
  }
  return attachments
}

// Selected attachments with everything the weapon can't take set to null.
// Returns the same object when nothing needs dropping.
export function pruneIncompatibleAttachments(weapon, selectedAttachments, attachmentsByType = {}) {
  if (!weapon) return selectedAttachments

  const allowedTypes = weapon.allowedAttachments
  let pruned = selectedAttachments

  Object.entries(selectedAttachments).forEach(([type, attachment]) => {
    if (!attachment) return

    let compatible = !allowedTypes || allowedTypes.includes(type)
    // The per-item check needs the attachment data; until it has loaded, keep the item
    const available = attachmentsByType[type] || []
    if (compatible && available.length > 0) {
      compatible = getCompatibleAttachments(weapon, type, available)
        .some(candidate => candidate.name === attachment.name)
    }

    if (!compatible) {
      if (pruned === selectedAttachments) pruned = { ...selectedAttachments }
      pruned[type] = null
    }
  })

  return pruned
}
