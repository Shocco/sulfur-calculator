/**
 * Builds are stored in localStorage as whole weapon/oil/scroll/attachment objects,
 * so after a data update they still carry the old stats. These helpers swap each
 * stored item for the current item of the same id (or name).
 *
 * Items that no longer exist in the data (renamed or removed on the wiki) are
 * kept as stored rather than silently dropped from the build. Every helper
 * returns its input unchanged when nothing needs replacing, so React state
 * setters can tell that nothing changed.
 */

export function refreshItem(item, currentItems = []) {
  if (!item) return item
  const current = item.id
    ? currentItems.find(candidate => candidate.id === item.id)
    : currentItems.find(candidate => candidate.name === item.name)
  return current || item
}

export function refreshItems(items, currentItems = []) {
  if (!Array.isArray(items)) return items
  const refreshed = items.map(item => refreshItem(item, currentItems))
  return refreshed.every((item, index) => item === items[index]) ? items : refreshed
}

export function refreshAttachments(attachments, attachmentsByType = {}) {
  if (!attachments) return attachments
  let refreshed = attachments
  Object.entries(attachments).forEach(([type, attachment]) => {
    const current = refreshItem(attachment, attachmentsByType[type])
    if (current !== attachment) {
      if (refreshed === attachments) refreshed = { ...attachments }
      refreshed[type] = current
    }
  })
  return refreshed
}

export function refreshBuild(build, { weapons, oils, scrolls, attachmentsByType }) {
  const weapon = refreshItem(build.weapon, weapons)
  const buildOils = refreshItems(build.oils, oils)
  const scroll = refreshItem(build.scroll, scrolls)
  const attachments = refreshAttachments(build.attachments, attachmentsByType)

  const unchanged = weapon === build.weapon && buildOils === build.oils &&
    scroll === build.scroll && attachments === build.attachments
  return unchanged ? build : { ...build, weapon, oils: buildOils, scroll, attachments }
}
