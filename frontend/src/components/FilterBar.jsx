import { RotateCcw } from 'lucide-react'
import { useFilters } from '../context/FilterContext.jsx'
import { addDays } from '../lib/dates.js'
import ProductPicker from './ProductPicker.jsx'

function Select({ label, value, onChange, children }) {
  return (
    <label className="field">
      <span>{label}</span>
      <select value={value} onChange={(e) => onChange(e.target.value)}>{children}</select>
    </label>
  )
}

export default function FilterBar() {
  const { meta, filters, update, reset, maturityEnd } = useFilters()
  const byChannel = (ch) => meta.stores.filter((s) => s.channel === ch)
  const presets = [
    ['30 ngày', addDays(maturityEnd, -29), maturityEnd],
    ['90 ngày', addDays(maturityEnd, -89), maturityEnd],
    ['Năm gần nhất', addDays(maturityEnd, -364), maturityEnd],
    ['Toàn bộ', meta.dateRange.min, meta.dateRange.max],
  ]
  const on = (a, b) => filters.from === a && filters.to === b
  const regions = [...new Set(meta.warehouses.map((w) => w.region))]

  return (
    <div className="filterbar" role="search" aria-label="Bộ lọc dữ liệu">
      <label className="field">
        <span>Từ ngày</span>
        <input type="date" value={filters.from} min={meta.dateRange.min} max={filters.to}
          onChange={(e) => e.target.value && update({ from: e.target.value })} />
      </label>
      <label className="field">
        <span>Đến ngày</span>
        <input type="date" value={filters.to} min={filters.from} max={meta.dateRange.max}
          onChange={(e) => e.target.value && update({ to: e.target.value })} />
      </label>
      <div className="presets" role="group" aria-label="Khoảng thời gian nhanh">
        {presets.map(([l, a, b]) => (
          <button key={l} type="button" className={on(a, b) ? 'on' : ''} onClick={() => update({ from: a, to: b })}>{l}</button>
        ))}
      </div>
      <Select label="Kênh / cửa hàng" value={filters.store} onChange={(v) => update({ store: v })}>
        <option value="all">Tất cả</option>
        {['TikTok', 'Shopee'].map((ch) => (
          <optgroup key={ch} label={ch}>
            {byChannel(ch).map((s) => <option key={s.code} value={s.code}>{s.label}</option>)}
          </optgroup>
        ))}
      </Select>
      <Select label="Kho" value={filters.region} onChange={(v) => update({ region: v })}>
        <option value="all">Tất cả</option>
        {regions.map((r) => <option key={r} value={r}>Kho {r}</option>)}
      </Select>
      <Select label="Danh mục" value={filters.category} onChange={(v) => update({ category: v })}>
        <option value="all">Tất cả</option>
        {meta.categories.map((c) => <option key={c} value={c}>{c}</option>)}
      </Select>
      <ProductPicker label="Sản phẩm" value={filters.product} onChange={(p) => update({ product: p })} baseFilters={filters} />
      <button className="reset" onClick={reset}><RotateCcw size={15} aria-hidden="true" /> Đặt lại</button>
    </div>
  )
}
