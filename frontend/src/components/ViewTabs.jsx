import { useId } from 'react'

export default function ViewTabs({ items, value, onChange, label = 'Nội dung phân tích' }) {
  const id = useId()
  return <div className="view-tabs" role="tablist" aria-label={label}>
    {items.map(([key, title], i) => <button key={key} id={`${id}-${key}`} type="button" role="tab" aria-selected={key === value}
      tabIndex={key === value ? 0 : -1} onClick={() => onChange(key)}
      onKeyDown={(e) => {
        const next = e.key === 'ArrowRight' ? (i + 1) % items.length : e.key === 'ArrowLeft' ? (i + items.length - 1) % items.length : e.key === 'Home' ? 0 : e.key === 'End' ? items.length - 1 : null
        if (next !== null) { e.preventDefault(); onChange(items[next][0]); e.currentTarget.parentElement.children[next].focus() }
      }}>{title}</button>)}
  </div>
}

export function ViewPanel({ active, name, children }) {
  return active ? <div className="view-panel" role="tabpanel" aria-label={name}>{children}</div> : null
}
