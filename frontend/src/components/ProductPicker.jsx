
import { useEffect, useRef, useState } from 'react'
import { Search, X } from 'lucide-react'
import { searchProducts } from '../api/client.js'

// Ô tìm sản phẩm: tìm theo tên, loại bỏ kết quả trùng product_key.
export default function ProductPicker({
  value,
  onChange,
  baseFilters,
  placeholder = 'Tìm sản phẩm…',
  label,
}) {
  const [text, setText] = useState('')
  const [open, setOpen] = useState(false)
  const [items, setItems] = useState([])
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState(null)
  const box = useRef(null)

  useEffect(() => {
    if (!open) return

    const t = setTimeout(() => {
      setBusy(true)
      setErr(null)

      searchProducts(
        { ...baseFilters, product: null },
        text.trim()
      )
        .then((rows) => {
          // Chỉ loại bỏ các dòng trùng mã sản phẩm.
          // Hai sản phẩm khác mã nhưng cùng tên vẫn được giữ lại.
          const unique = new Map()

          rows.forEach((p) => {
            const key = Number(p.key)

            if (!unique.has(key)) {
              unique.set(key, p)
            }
          })

          setItems([...unique.values()])
        })
        .catch((e) => setErr(e.message))
        .finally(() => setBusy(false))
    }, 250)

    return () => clearTimeout(t)
  }, [
    text,
    open,
    baseFilters.from,
    baseFilters.to,
    baseFilters.store,
    baseFilters.region,
    baseFilters.category,
  ]) // eslint-disable-line

  useEffect(() => {
    const close = (e) => {
      if (box.current && !box.current.contains(e.target)) {
        setOpen(false)
      }
    }

    document.addEventListener('mousedown', close)
    return () => document.removeEventListener('mousedown', close)
  }, [])

  return (
    <div className="picker" ref={box}>
      {label && <span className="picker-label">{label}</span>}

      {value ? (
        <div className="picker-chip" title={value.label}>
          <span>
            {value.label.length > 34
              ? value.label.slice(0, 33) + '…'
              : value.label}
          </span>

          <button
            type="button"
            onClick={() => onChange(null)}
            aria-label="Bỏ chọn sản phẩm"
          >
            <X size={14} />
          </button>
        </div>
      ) : (
        <div className="picker-input">
          <Search size={14} aria-hidden="true" />

          <input
            value={text}
            placeholder={placeholder}
            aria-label={label || 'Tìm sản phẩm'}
            onFocus={() => setOpen(true)}
            onChange={(e) => {
              setText(e.target.value)
              setOpen(true)
            }}
          />
        </div>
      )}

      {open && !value && (
        <ul className="picker-list" role="listbox">
          {busy && <li className="muted">Đang tìm…</li>}

          {err && <li className="muted">{err}</li>}

          {!busy && !err && items.length === 0 && (
            <li className="muted">Không có sản phẩm khớp</li>
          )}

          {!busy && !err && items.map((p) => (
            <li key={p.key}>
              <button
                type="button"
                onClick={() => {
                  onChange({
                    key: p.key,
                    label: p.label,
                    categories: p.categories,
                  })
                  setOpen(false)
                  setText('')
                }}
              >
                {p.label}

                <small>
                  Mã SP: {p.key} · {
                    (p.categories || []).filter(Boolean).join(', ')
                    || 'Chưa phân loại'
                  }
                </small>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
