import { productIdentity } from '../lib/productIdentity.js'
import ViewTabs, { ViewPanel } from '../components/ViewTabs.jsx'
import { useState } from 'react'
import ChartTable from '../components/ChartTable.jsx'
import { CATEGORY_COLORS } from '../components/LinkedChart.jsx'
import { monthSelection } from '../lib/overview.js'
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useFilters } from '../context/FilterContext.jsx'
import { useReport } from '../hooks/useReport.js'
import { getAllBreakdown, getAllProducts, getBreakdown, getKpis, getMonthlyBySource } from '../api/client.js'
import { Page, Section } from '../components/Page.jsx'
import { KpiRow } from '../components/KpiStrip.jsx'
import ShareBars from '../components/ShareBars.jsx'
import DataTable from '../components/DataTable.jsx'
import { storeColor, INK } from '../lib/colors.js'
import { axisTick, AXIS_LINE, GRID, tipStyle } from '../lib/chart.js'
import { fmtAxis, fmtInt, fmtPct, fmtPeriod, fmtVND } from '../lib/format.js'
import { standardKpis, STATUS_LABELS } from '../lib/kpis.js'
import { categoryLabel, shareItems, storeLabel } from '../lib/shape.js'

const METRICS = [['revenue', 'Giá trị đơn hoàn thành'], ['orders', 'Đơn đặt'], ['canceled', 'Đơn hủy']]
const NOTE = {
  revenue: 'Thanh toán của đơn hoàn thành, theo tháng đặt hàng',
  orders: 'Tổng đơn đặt (gồm đơn hủy và chưa hoàn thành)',
  canceled: 'Số đơn bị hủy theo tháng đặt hàng',
}
const CHANNEL_COLOR = { TikTok: '#17908f', Shopee: '#e4572e' }
const num = { align: 'right' }
const money = (i) => `${fmtVND(i.getValue())} ₫`
const cnt = (i) => (i.getValue() == null ? '—' : fmtInt(i.getValue()))

const storeColumns = [
  { accessorKey: 'name', header: 'Cửa hàng' },
  { accessorKey: 'orders', header: 'Đơn đặt', cell: cnt, meta: num },
  { accessorKey: 'revenue', header: 'Giá trị đơn hoàn thành', cell: money, meta: num },
  { accessorKey: 'canceled', header: 'Đơn hủy', cell: cnt, meta: num },
  { accessorKey: 'cancelRate', header: 'Tỷ lệ hủy', cell: (i) => fmtPct(i.getValue()), meta: num },
]
const itemColumns = (label) => [
  { accessorKey: 'name', header: label },
  { accessorKey: 'units', header: 'SL hoàn thành', cell: cnt, meta: num },
  { accessorKey: 'value', header: 'Giá trị dòng hàng', cell: money, meta: num },
  { accessorKey: 'orders', header: 'Đơn có mặt', cell: cnt, meta: num },
]

const itemRow = (name) => (r) => ({ key: r.group_value, name: name(r.group_value), units: r.completed_units, value: r.completed_observed_item_payable, orders: r.orders })

function headline(d) {
  const k = d.kpis
  return `${fmtInt(k.orders)} đơn đặt, ${fmtInt(k.completedUnits)} sản phẩm bán ra từ đơn hoàn thành, tỷ lệ hủy ${fmtPct(k.cancellationRate)}.`
}

function ProductRanking({ filters, update }) {
  const [state, setState] = useState({ phase: 'idle' })
  const load = async () => {
    setState({ phase: 'loading', done: 0, total: 0 })
    try {
      const [rows, names] = await Promise.all([
        getAllBreakdown('product', filters, (done, total) => setState({ phase: 'loading', done, total })),
        getAllProducts(filters)])
      const label = Object.fromEntries(names.map((p) => [p.product_key, p]))
      const data = rows.map((r) => ({ key: r.group_value, name: label[r.group_value]?.product_name ?? `Sản phẩm #${r.group_value}`,
        store: label[r.group_value]?.storefront_code, sku: label[r.group_value]?.native_sku_id, variation: label[r.group_value]?.variation_name,
        category: (label[r.group_value]?.historical_categories ?? []).filter(Boolean).join(', ') || 'Chưa phân loại',
        units: r.completed_units, value: r.completed_observed_item_payable, orders: r.orders }))
        .sort((a, b) => (b.units ?? 0) - (a.units ?? 0))
      setState({ phase: 'done', rows: data })
    } catch (e) { setState({ phase: 'error', message: e.message }) }
  }
  const cols = [{ accessorKey: 'name', header: 'Sản phẩm / SKU', cell: (c) => <span className="product-cell" title={`${c.getValue()} — ${productIdentity(c.row.original)}`}><span>{c.getValue()}</span></span> }, { accessorKey: 'category', header: 'Danh mục' },
    ...itemColumns('').slice(1)]
  return (
    <Section title="Sản phẩm bán chạy" note="Xếp hạng theo số lượng sản phẩm hoàn thành">
      {state.phase === 'idle' && <button className="primary" onClick={load}>Tải xếp hạng sản phẩm</button>}
      {state.phase === 'loading' && <p className="muted">Đang tải {state.total ? `${fmtInt(state.done)}/${fmtInt(state.total)} sản phẩm` : ''}…</p>}
      {state.phase === 'error' && <p className="muted">Không tải được: {state.message} <button className="reset" onClick={load}>Thử lại</button></p>}
      {state.phase === 'done' && (
        <ChartTable columns={cols} rows={state.rows.slice(0,30)} valueKey="units" label="SKU theo sản lượng" onSelect={r=>update({product:{key:r.key,label:r.name,store:r.store,sku:r.sku,variation:r.variation}})}/>
      )}
      {state.phase === 'done' && <p className="fine">Hiển thị 30 sản phẩm đầu trong {fmtInt(state.rows.length)}. Bấm một dòng để lọc theo sản phẩm. Mỗi mã sản phẩm thuộc một cửa hàng.</p>}
    </Section>
  )
}

export default function SalesPerformance() {
  const { filters, update } = useFilters()
  const [view, setView] = useState('trend')
  const [metric, setMetric] = useState('revenue')
  const [groupBy, setGroupBy] = useState('channel')
  const state = useReport(async () => {
    const [kpis, monthly, store, status, category, province, region] = await Promise.all([
      getKpis(filters), getMonthlyBySource(filters, groupBy), getBreakdown('store', filters), getBreakdown('status', filters),
      getBreakdown('category', filters), getBreakdown('province', filters), getBreakdown('warehouse_region', filters)])
    return {
      kpis, monthly,
      stores: store.rows.map((r) => ({ key: r.group_value, name: storeLabel(r.group_value), orders: r.orders, revenue: r.completed_payable,
        canceled: r.canceled_orders, cancelRate: r.orders ? r.canceled_orders / r.orders : 0 })),
      storeShare: shareItems(store.rows, 'completed_payable', storeLabel),
      status: shareItems(status.rows.map((r) => ({ ...r, orders_v: r.orders })), 'orders_v', (s) => STATUS_LABELS[s] ?? s),
      categories: category.rows.map(itemRow(categoryLabel)),
      provinces: province.rows.filter((r) => r.group_value && r.group_value !== 'Unknown').map(itemRow((p) => p))
        .sort((a, b) => b.orders - a.orders).slice(0, 12),
      regions: region.rows.map(itemRow((r) => (r ? `Kho ${r}` : 'Không rõ'))),
    }
  }, [filters, groupBy])

  const toggle = (
    <div className="toggle" role="group" aria-label="Chỉ số">
      {METRICS.map(([k, l]) => <button key={k} className={metric === k ? 'on' : ''} aria-pressed={metric === k} onClick={() => setMetric(k)}>{l}</button>)}
    </div>
  )

  const groupToggle = (
    <div className="toggle" role="group" aria-label="Nhóm theo">
      {[['channel', 'Theo kênh'], ['store', 'Theo cửa hàng']].map(([k, l]) => (
        <button key={k} className={groupBy === k ? 'on' : ''} aria-pressed={groupBy === k} onClick={() => setGroupBy(k)}>{l}</button>
      ))}
    </div>
  )

  return (
    <Page title="Sales Performance" headline={(d) => filters.product ? `${fmtInt(d.kpis.orders)} đơn có SKU đã chọn, ${fmtInt(d.kpis.completedUnits)} đơn vị SKU hoàn thành. Tiền hiển thị là tiền toàn đơn có chứa SKU, không phải doanh thu riêng SKU.` : headline(d)} state={state}>
      {(d) => (
        <div className="sales-performance">
          <div className="sales-kpi-block">
            <div className="sales-block-heading">
              <span className="sales-eyebrow">SALES SNAPSHOT</span>
              <span className="sales-context">Theo bộ lọc hiện tại</span>
            </div>
            <KpiRow items={standardKpis(d.kpis, Boolean(filters.product))} />
          </div>

          <ViewTabs value={view} onChange={setView} items={[["trend", "Xu hướng"], ["stores", "Cửa hàng & trạng thái"], ["mix", "Danh mục & vùng kho"], ["geography", "Tỉnh nhận hàng"], ["products", "Sản phẩm"]]} />
          <ViewPanel active={view === 'trend'} name="Xu hướng"><div className="sales-trend-card">
            <Section title={groupBy === 'channel' ? 'Xu hướng theo kênh' : 'Xu hướng theo cửa hàng'} note={NOTE[metric]}
              aside={<div className="sales-trend-toolbar">
                <div className="sales-trend-control">
                  <span>Phân nhóm</span>
                  {groupToggle}
                </div>
                <div className="sales-trend-control">
                  <span>Chỉ tiêu</span>
                  {toggle}
                </div>
              </div>}>
              <div className="sales-chart-frame">
                <div className="chart hero trend-chart">
                  <ResponsiveContainer>
                    <LineChart data={d.monthly[metric]} onClick={e=>e?.activeLabel&&update(monthSelection(e.activeLabel,filters))} margin={{ top: 12, right: 28, left: 8, bottom: 4 }}>
                      <CartesianGrid stroke={GRID} vertical={false} />
                      <XAxis dataKey="period" tickFormatter={fmtPeriod} tick={axisTick} tickLine={false} axisLine={AXIS_LINE} minTickGap={24} />
                      <YAxis tickFormatter={fmtAxis} tick={axisTick} tickLine={false} axisLine={false} width={64} />
                      <Tooltip formatter={(v, n) => [metric === 'revenue' ? fmtVND(v) + ' ₫' : fmtInt(v), n]} labelFormatter={fmtPeriod} contentStyle={tipStyle} />
                      <Legend iconType="plainline" wrapperStyle={{ fontSize: 13, paddingTop: 8 }} />
                      {d.monthly.names.map((n) => <Line isAnimationActive={false} key={n} type="monotone" dataKey={n} stroke={groupBy === 'channel' ? (CHANNEL_COLOR[n] ?? '#7a6b73') : storeColor(n)} strokeWidth={2.5} dot={{ r: 4, strokeWidth: 2, fill: '#ffffff' }} activeDot={{ r: 6, strokeWidth: 2 }} />)}
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
              <p className="fine sales-chart-note">Dữ liệu được tổng hợp theo tháng. Tháng đầu và tháng cuối của kỳ có thể chưa đầy đủ.</p>
            </Section>
          </div>

          </ViewPanel>
          <ViewPanel active={view === 'stores' || view === 'mix'} name="Phân tích doanh số"><div className="sales-analysis-grid" data-view={view}>
            <div className="sales-analysis-card">
              <div className="sales-card-index">01 / CHANNEL PERFORMANCE</div>
              <Section title="Theo cửa hàng" note="Bấm một dòng để lọc">
                <div className="sales-store-table">
                  <ChartTable columns={storeColumns} rows={[...d.stores].sort((a,b)=>(b.revenue??0)-(a.revenue??0))} valueKey="revenue" format={v=>`${fmtVND(v)} ₫`} color={r=>storeColor(r.name)} label="Tiền hoàn thành theo cửa hàng" onSelect={r=>update({store:r.key})}/>
                </div>
              </Section>
            </div>
            <div className="sales-analysis-card">
              <div className="sales-card-index">02 / ORDER STATUS</div>
              <Section title="Đơn theo trạng thái" note="Số đơn đặt, trạng thái hiện tại của đơn">
                <ChartTable rows={d.status.map(r=>({...r,orders:r.revenue})).sort((a,b)=>b.orders-a.orders)} columns={[{accessorKey:'name',header:'Trạng thái'},{accessorKey:'orders',header:'Đơn',cell:cnt,meta:num}]} valueKey="orders" color={r=>r.key==='CANCELED'?'#d68a39':'#178a80'} label="Đơn theo trạng thái" onSelect={r=>update({status:r.key})}/>
              </Section>
            </div>
            <div className="sales-analysis-card">
              <div className="sales-card-index">03 / CATEGORY MIX</div>
              <Section title="Theo danh mục" note="Danh mục được phân loại dựa trên tên sản phẩm trong dữ liệu lịch sử. Một đơn có thể thuộc nhiều danh mục nên không cộng tổng các dòng.">
                <ChartTable columns={itemColumns('Danh mục')} rows={[...d.categories].sort((a,b)=>(b.units??0)-(a.units??0))} valueKey="units" label="Danh mục theo sản lượng" color={r=>CATEGORY_COLORS[r.name]} onSelect={r=>r.key&&update({category:r.key})}/>
              </Section>
            </div>
            <div className="sales-analysis-card">
              <div className="sales-card-index">04 / WAREHOUSE REGION</div>
              <Section title="Theo vùng kho" note="Phân bổ số lượng và giá trị theo vùng kho xuất hàng.">
                <ChartTable columns={itemColumns('Vùng kho')} rows={[...d.regions].sort((a,b)=>(b.units??0)-(a.units??0))} valueKey="units" label="Vùng kho theo sản lượng" color={r=>r.key==='Hà Nội'?'#5377bb':'#17958a'} onSelect={r=>r.key&&update({region:r.key})}/>
              </Section>
            </div>
          </div>

          </ViewPanel>
          <ViewPanel active={view === 'geography'} name="Tỉnh nhận hàng"><div className="sales-detail-card">
            <div className="sales-card-index">05 / DELIVERY GEOGRAPHY</div>
            <Section title="12 tỉnh/thành nhận nhiều đơn nhất" note="Xếp hạng theo số đơn có thông tin tỉnh/thành nhận hàng.">
              <ChartTable columns={itemColumns('Tỉnh / thành')} rows={d.provinces} valueKey="orders" label="Đơn theo tỉnh khách" onSelect={r=>update({province:r.key})}/>
            </Section>
          </div>

          </ViewPanel>
          <ViewPanel active={view === 'products'} name="Sản phẩm"><div className="sales-detail-card sales-product-card">
            <div className="sales-card-index">06 / PRODUCT RANKING</div>
            <ProductRanking key={JSON.stringify(filters)} filters={filters} update={update} />
          </div>

          </ViewPanel>
          <p className="footnote sales-footnote">
            Giá trị dòng hàng khác với "Giá trị đơn hoàn thành" nên không cộng hai chỉ tiêu này. Một số chỉ tiêu chi tiết chưa được hỗ trợ bởi dữ liệu hiện tại.
          </p>
        </div>
      )}
    </Page>
  )
}
