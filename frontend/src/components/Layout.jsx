import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useState } from 'react'
import { LayoutDashboard, TrendingUp, Warehouse, MessageSquareText, FlaskConical } from 'lucide-react'
import FilterBar from './FilterBar.jsx'
import { useFilters } from '../context/FilterContext.jsx'
import { fmtInt, fmtDate } from '../lib/format.js'

const NAV = [
  { to: '/overview', label: 'Executive Overview', icon: LayoutDashboard },
  { to: '/sales', label: 'Sales Performance', icon: TrendingUp },
  { to: '/warehouse', label: 'Warehouse & Fulfillment', icon: Warehouse },
  { to: '/customer', label: 'Customer Experience', icon: MessageSquareText },
  { to: '/dss', label: 'DSS Simulation', icon: FlaskConical },
]

export default function Layout() {
  const [expanded, setExpanded] = useState(false)
  const { pathname } = useLocation()
  const { meta } = useFilters()
  const total = meta.coverage.reduce((a, c) => a + c.orders, 0)
  const showGlobalFilters = !pathname.startsWith('/dss')

  return (
    <div className={`shell ${expanded ? 'rail-expanded' : 'rail-collapsed'}`}>
      <aside className="rail">
        <div className="brand">
          <button className="brand-mark" type="button" onClick={() => setExpanded((v) => !v)} aria-label={expanded ? 'Thu thanh điều hướng' : 'Mở thanh điều hướng'} aria-expanded={expanded}>B</button>
          <div>
            <div className="brand-name">Bibica Retail DSS</div>
          </div>
        </div>
        <nav className="nav" aria-label="Màn hình">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} title={label} aria-label={label} className={({ isActive }) => (isActive ? 'nav-item on' : 'nav-item')}>
              <Icon size={18} strokeWidth={1.75} aria-hidden="true" />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="rail-foot">
          <span className="dot ok" />
          <span>
            Dữ liệu từ DW qua API: {fmtInt(total)} đơn, từ {fmtDate(meta.dateRange.min)} đến {fmtDate(meta.dateRange.max)}.
          </span>
        </div>
      </aside>
      <div className="main-col">
        {showGlobalFilters && <FilterBar />}
        <main className="main"><Outlet /></main>
      </div>
    </div>
  )
}
