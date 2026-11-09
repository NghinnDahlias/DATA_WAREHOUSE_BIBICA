const dec = (n, d = 1) =>
  n.toLocaleString('vi-VN', { minimumFractionDigits: d, maximumFractionDigits: d })

export function fmtVND(n) {
  if (n == null) return '—'
  if (n >= 1e9) return dec(n / 1e9, 2) + ' tỷ'
  if (n >= 1e6) return dec(n / 1e6, 1) + ' tr'
  if (n >= 1e3) return dec(n / 1e3, 0) + 'k'
  return dec(n, 0)
}

// Số tiền có dấu: +12,3 tr / −4,5 tr
export function fmtDelta(n) {
  if (n === 0) return '0'
  return (n > 0 ? '+' : '−') + fmtVND(Math.abs(n))
}

// Nhãn trục: gọn, không số lẻ thừa
export function fmtAxis(n) {
  if (n == null) return ''
  if (n >= 1e9) return dec(n / 1e9, 1).replace(',0', '') + ' tỷ'
  if (n >= 1e6) return Math.round(n / 1e6) + ' tr'
  if (n >= 1e3) return Math.round(n / 1e3) + 'k'
  return String(Math.round(n))
}

// 2026-10-12 → 12/10 ; 2026-10 → T10/26
export function fmtPeriod(p) {
  if (!p) return ''
  if (/^\d{4}-Q\d$/.test(p)) return `${p.slice(5)}/${p.slice(2, 4)}`
  if (p.length === 7) return `T${p.slice(5, 7)}/${p.slice(2, 4)}`
  return `${p.slice(8, 10)}/${p.slice(5, 7)}`
}

export const fmtInt = (n) => (n == null ? '—' : Math.round(n).toLocaleString('vi-VN'))
export const fmtPct = (x, d = 1) => (x == null ? '—' : dec(x * 100, d) + '%')

// +12,3% / −4,1%
export function fmtChange(x) {
  if (x === null || x === undefined || !isFinite(x)) return '—'
  return (x > 0 ? '+' : x < 0 ? '−' : '') + fmtPct(Math.abs(x))
}

export const fmtDays = (x) => (x === null || x === undefined ? '—' : dec(x, 1) + ' ngày')
export const fmtStar = (x) => (x === null || x === undefined ? '—' : dec(x, 2))
// 2026-09-18 → 18/09/2026
export const fmtDate = (iso) => (iso ? `${iso.slice(8, 10)}/${iso.slice(5, 7)}/${iso.slice(0, 4)}` : '')
