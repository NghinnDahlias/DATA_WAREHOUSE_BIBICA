import { STORES } from '../api/client.js'

// Chuyển hàng breakdown của API thành mục cho ShareBars: { key, name, revenue, share }
export function shareItems(rows, valueKey, labeler) {
  const total = rows.reduce((a, r) => a + (r[valueKey] ?? 0), 0)
  return rows.map((r) => ({ key: r.group_value, name: labeler(r.group_value), revenue: r[valueKey] ?? 0, share: total ? (r[valueKey] ?? 0) / total : 0, raw: r }))
    .sort((a, b) => b.revenue - a.revenue)
}
export const storeLabel = (code) => STORES[code]?.label ?? String(code)
export const categoryLabel = (c) => c ?? 'Chưa phân loại'
