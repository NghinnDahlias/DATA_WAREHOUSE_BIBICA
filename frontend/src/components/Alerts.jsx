import { TriangleAlert, Info } from 'lucide-react'

export default function Alerts({ items }) {
  if (!items.length) {
    return <p className="muted">Không phát hiện bất thường trong khoảng thời gian này.</p>
  }
  return (
    <ul className="alerts">
      {items.map((a, i) => (
        <li key={i} className={a.level}>
          {a.level === 'warn'
            ? <TriangleAlert size={18} aria-label="Cần chú ý" />
            : <Info size={18} aria-label="Thông tin" />}
          <div>
            <strong>{a.title}</strong>
            <span>{a.detail}</span>
          </div>
        </li>
      ))}
    </ul>
  )
}
