import { NavLink, Outlet, useLocation } from 'react-router-dom'
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
  const { pathname } = useLocation()
  const { meta } = useFilters()
  const total = meta.coverage.reduce((a, c) => a + c.orders, 0)
  const showGlobalFilters = !pathname.startsWith('/dss')

  return (
    <div className="shell">
      <aside className="rail">
        <div className="brand">
          <div className="brand-mark">B</div>
          <div>
            <div className="brand-name">Bibica Retail DSS</div>
          </div>
        </div>
        <nav className="nav" aria-label="Màn hình">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} className={({ isActive }) => (isActive ? 'nav-item on' : 'nav-item')}>
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
