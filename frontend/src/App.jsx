import { Navigate, Route, Routes } from 'react-router-dom'
import { FilterProvider } from './context/FilterContext.jsx'
import Layout from './components/Layout.jsx'
import ExecutiveOverview from './pages/ExecutiveOverview.jsx'
import SalesPerformance from './pages/SalesPerformance.jsx'
import Warehouse from './pages/Warehouse.jsx'
import Customer from './pages/Customer.jsx'
import Dss from './pages/Dss.jsx'

export default function App() {
  return (
    <FilterProvider>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Navigate to="/overview" replace />} />
          <Route path="/overview" element={<ExecutiveOverview />} />
          <Route path="/sales" element={<SalesPerformance />} />
          <Route path="/warehouse" element={<Warehouse />} />
          <Route path="/customer" element={<Customer />} />
          <Route path="/dss" element={<Dss />} />
          <Route path="*" element={<Navigate to="/overview" replace />} />
        </Route>
      </Routes>
    </FilterProvider>
  )
}
