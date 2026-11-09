import { fmtVND, fmtPct, fmtInt } from '../lib/format.js'

// Thanh tỷ trọng. items: { name, revenue, share, change? } từ backend.
// onSelect(item): bấm vào một dòng để lọc (drill-down). item.key là mã lọc nếu khác tên hiển thị.
export default function ShareBars({ items, colorFor, onSelect, countMode }) {
  const max = Math.max(...items.map((i) => i.revenue), 1)
  return (
    <ul className="bars">
      {items.map((i) => {
        const inner = (
          <>
            <div className="bars-row">
              <span className="bars-name">{i.name}</span>
              <span className="bars-val">
                {countMode ? fmtInt(i.revenue) : `${fmtVND(i.revenue)} ₫`}
                <em>{fmtPct(i.share, 0)}</em>
              </span>
            </div>
            <div className="bars-track">
              <div className="bars-fill" style={{ width: `${(i.revenue / max) * 100}%`, background: colorFor(i.name) }} />
            </div>
          </>
        )
        return (
          <li key={i.key ?? i.name}>
            {onSelect ? (
              <button type="button" className="bars-btn" onClick={() => onSelect(i)}
                title="Bấm để lọc theo mục này">{inner}</button>
            ) : inner}
          </li>
        )
      })}
    </ul>
  )
}
