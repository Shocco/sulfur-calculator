/**
 * Total damage per trigger pull.
 *
 * damage           listed damage per projectile
 * projectiles      projectiles per shell (shotgun pellets)
 * bonus            extra damage per projectile from its own source (dark, explosive)
 * shotsPerTrigger  shells fired per pull: a number (Arbiter 2 fires 3), or a
 *                  [min, max] range (Breacher 8 fires however many were charged)
 *
 * Returns a number, or [min, max] when shotsPerTrigger is a range.
 */
const round2 = (value) => Math.round(value * 100) / 100

export function totalDamage({ damage = 0, projectiles = 1, bonus = 0, shotsPerTrigger = 1 } = {}) {
  const perShell = (damage + bonus) * projectiles
  if (Array.isArray(shotsPerTrigger)) {
    return shotsPerTrigger.map(shots => round2(perShell * shots))
  }
  return round2(perShell * shotsPerTrigger)
}

export function formatTotalDamage(total) {
  return Array.isArray(total) ? `${total[0]}–${total[1]}` : `${total}`
}

// "60", "40x8", "40x8x3", or "40x8 x1–8" for a variable number of shells
export function formatDamage(damage, projectiles = 1, shotsPerTrigger) {
  const count = Math.round(projectiles)
  if (Array.isArray(shotsPerTrigger)) {
    return `${damage}x${count} x${shotsPerTrigger[0]}–${shotsPerTrigger[1]}`
  }
  if (shotsPerTrigger && shotsPerTrigger !== 1) return `${damage}x${count}x${shotsPerTrigger}`
  return count > 1 ? `${damage}x${count}` : `${damage}`
}
