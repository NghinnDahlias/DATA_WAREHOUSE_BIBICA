export function addDays(iso, n) {
  const d = new Date(iso + 'T00:00:00Z')
  d.setUTCDate(d.getUTCDate() + n)
  return d.toISOString().slice(0, 10)
}

export function daysBetween(a, b) {
  return Math.round((new Date(b + 'T00:00:00Z') - new Date(a + 'T00:00:00Z')) / 86400000) + 1
}

// Kỳ liền trước có cùng độ dài
export function previousPeriod(from, to) {
  const n = daysBetween(from, to)
  return { from: addDays(from, -n), to: addDays(from, -1) }
}

export function weekStart(iso) {
  const d = new Date(iso + 'T00:00:00Z')
  const shift = (d.getUTCDay() + 6) % 7 // thứ Hai = 0
  d.setUTCDate(d.getUTCDate() - shift)
  return d.toISOString().slice(0, 10)
}

export function bucketKey(date, granularity) {
  if (granularity === 'day') return date
  if (granularity === 'week') return weekStart(date)
  return date.slice(0, 7)
}
