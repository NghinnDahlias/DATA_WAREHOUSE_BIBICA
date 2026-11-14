
// Hợp đồng KPI của DW đánh dấu M17 "tăng trưởng" là UNAVAILABLE nên không hiển thị % so với kỳ trước.
function Kpi({ label, value, note }) {
  return (
    <div className="kpi" title={note||undefined}>
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{value}</div>
    </div>
  )
}

// Dải KPI: items = [{ label, value, note }]
export function KpiRow({ items }) {
  return (
    <div className={`kpis n${items.length}`} style={{ gridTemplateColumns: `repeat(${items.length}, 1fr)` }}>
      {items.map((i) => <Kpi key={i.label} {...i} />)}
    </div>
  )
}
