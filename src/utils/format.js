// A stat change for display: "+750", "-0.1", or "+30%" for percentage-point stats.
// Keeps up to three decimals so small changes (Spread 5 -> 4.9) don't show as 0
// and 12Ga eighths (+1.875) stay exact.
export function formatChange(change, asPercent = false) {
  const sign = change > 0 ? '+' : ''
  if (asPercent) return `${sign}${Math.round(change * 100)}%`
  return `${sign}${Math.round(change * 1000) / 1000}`
}
