import { useEffect, useId, useRef, useState } from 'react'
import { Search, X } from 'lucide-react'
import { searchProducts } from '../api/client.js'
import { productIdentity } from '../lib/productIdentity.js'
import { fmtInt } from '../lib/format.js'

const PAGE_SIZE = 10

export default function ProductPicker({ value, onChange, baseFilters, placeholder = 'Tìm tên, SKU hoặc biến thể…', label }) {
  const [text, setText] = useState('')
  const [open, setOpen] = useState(false)
  const [items, setItems] = useState([])
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState(null)
  const [page, setPage] = useState(0)
  const box = useRef(null)
  const listId = useId()
  const choose = (p) => { onChange(p); setOpen(false); setText(''); setPage(0) }
  const scope = [baseFilters.from, baseFilters.to, baseFilters.store, baseFilters.region, baseFilters.category, baseFilters.channel, baseFilters.warehouse, baseFilters.province, baseFilters.status]
  useEffect(() => { setPage(0) }, scope) // reset pagination when the cohort changes
  useEffect(() => {
    if (!open) return
    let active = true
    setBusy(true); setErr(null); setItems([])
    const timer = setTimeout(() => {
      searchProducts({ ...baseFilters, product: null }, text.trim(), PAGE_SIZE, page * PAGE_SIZE)
        .then((rows) => {
          if (!active) return
          const unique = new Map(rows.map((p) => [Number(p.key), p]))
          setItems([...unique.values()])
        })
        .catch((e) => active && setErr(e.message))
        .finally(() => active && setBusy(false))
    }, 250)
    return () => { active = false; clearTimeout(timer) }
  }, [text, open, page, ...scope]) // eslint-disable-line
  useEffect(() => {
    const close = (e) => { if (!box.current?.contains(e.target)) setOpen(false) }
    document.addEventListener('mousedown', close)
    return () => document.removeEventListener('mousedown', close)
  }, [])
  const search = (e) => { setText(e.target.value); setPage(0); setOpen(true) }
  const keys = (e) => {
    if (e.key === 'Escape') setOpen(false)
    if (e.key === 'ArrowDown') { e.preventDefault(); setOpen(true); box.current?.querySelector('button[data-product-key]')?.focus() }
  }
  const total = items[0]?.total ?? items.length
  return <div className="picker" ref={box}>
    {label && <span className="picker-label">{label} <span className="sku-tag">SKU</span></span>}
    {value ? <div className="picker-chip" title={[value.label, productIdentity(value)].join(' — ')}>
      <button type="button" className="picker-selection" aria-label="Đổi sản phẩm" aria-expanded={open} onClick={() => { setOpen((v) => !v); setText(''); setPage(0) }}>
        <span>{value.label}</span><small>{productIdentity(value)}</small>
      </button>
      <button type="button" onClick={() => { onChange(null); setOpen(false) }} aria-label="Bỏ chọn sản phẩm"><X size={14} /></button>
    </div> : <div className="picker-input">
      <Search size={14} aria-hidden="true" />
      <input value={text} placeholder={placeholder} aria-label={label || 'Tìm sản phẩm'} aria-controls={open ? listId : undefined}
        onFocus={() => setOpen(true)} onChange={search} onKeyDown={keys} />
    </div>}
    {open && <div className="picker-popover">
      {value && <input className="picker-research" aria-label="Tìm SKU thay thế" value={text} placeholder="Tìm tên, SKU hoặc biến thể…" onChange={search} onKeyDown={keys} />}
      <ul className="picker-list" id={listId} role="listbox" aria-label="Các SKU phù hợp">
        <li className="picker-help">Mỗi lựa chọn là một SKU của một cửa hàng. Cùng tên có thể khác biến thể hoặc mã SKU.</li>
        {busy && <li className="muted">Đang tìm…</li>}
        {err && <li className="muted">{err}</li>}
        {!busy && !err && !items.length && <li className="muted">Không có SKU khớp bộ lọc</li>}
        {!busy && !err && items.map((p) => <li key={p.key}>
          <button type="button" data-product-key={p.key} title={[p.label, productIdentity(p)].join(' — ')} onClick={() => choose(p)}>
            <span className="picker-result-name">{p.label}</span>
            <small>{productIdentity(p)}</small>
            <small>{p.orders == null ? '' : `${fmtInt(p.orders)} đơn có SKU trong kỳ · `}{(p.categories || []).filter(Boolean).join(', ') || 'Chưa phân loại'}</small>
          </button>
        </li>)}
      </ul>
      {!busy && !err && total > 0 && <div className="picker-pagination">
        <button type="button" disabled={!page} onClick={() => setPage((p) => p - 1)}>Trước</button>
        <span>{page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, total)} / {fmtInt(total)} SKU</span>
        <button type="button" disabled={(page + 1) * PAGE_SIZE >= total} onClick={() => setPage((p) => p + 1)}>Sau</button>
      </div>}
    </div>}
  </div>
}
