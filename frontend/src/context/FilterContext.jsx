import { createContext, useCallback, useContext, useMemo, useState, useEffect } from 'react'
import { getMeta } from '../api/client.js'
import { addDays } from '../lib/dates.js'

const Ctx = createContext(null)
export const useFilters = () => useContext(Ctx)

// Số ngày cuối của dữ liệu mà đơn thường chưa chuyển sang "Hoàn thành" (quan sát từ DW: tháng gần nhất chỉ vài % đơn hoàn thành)
export const MATURITY_DAYS = 30

// Mặc định: 90 ngày kết thúc cách ngày dữ liệu mới nhất MATURITY_DAYS ngày
const defaultsFor = (m) => {
  const to = addDays(m.dateRange.max, -MATURITY_DAYS)
  return { from: addDays(to, -89), to, store: 'all', channel: 'all', warehouse: 'all', region: 'all', category: 'all', province: 'all', status: 'all', product: null }
}

export function FilterProvider({ children }) {
  const [meta, setMeta] = useState(null)
  const [filters, setFilters] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    getMeta().then((m) => { setMeta(m); setFilters(defaultsFor(m)) })
      .catch((e) => setError(e.message || 'Không tải được danh mục bộ lọc'))
  }, [])

  const update = useCallback((patch) => setFilters((f) => {
    const next = { ...f, ...patch }
    if ('channel' in patch && patch.channel !== f.channel) {
      next.store = 'all'; next.warehouse = 'all'; next.product = null
    }
    if ('store' in patch && patch.store !== f.store) { next.warehouse = 'all'; next.product = null }
    if ('region' in patch && patch.region !== f.region) next.warehouse = 'all'
    return next
  }), [])
  const reset = useCallback(() => meta && setFilters(defaultsFor(meta)), [meta])
  const maturityEnd = meta ? addDays(meta.dateRange.max, -MATURITY_DAYS) : null
  const value = useMemo(() => ({ meta, filters, update, reset, maturityEnd }), [meta, filters, update, reset, maturityEnd])

  if (error) return <div className="boot err">Không tải được dữ liệu: {error}</div>
  if (!filters) return <div className="boot">Đang tải…</div>
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}
