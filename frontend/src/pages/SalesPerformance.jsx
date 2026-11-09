import { useState } from 'react'
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
        category: (label[r.group_value]?.historical_categories ?? []).filter(Boolean).join(', ') || 'Chưa phân loại',
        units: r.completed_units, value: r.completed_observed_item_payable, orders: r.orders }))
        .sort((a, b) => (b.units ?? 0) - (a.units ?? 0))
      setState({ phase: 'done', rows: data })
    } catch (e) { setState({ phase: 'error', message: e.message }) }
  }
  const cols = [{ accessorKey: 'name', header: 'Sản phẩm' }, { accessorKey: 'category', header: 'Danh mục' },
    ...itemColumns('').slice(1)]
  return (
    <Section title="Sản phẩm bán chạy" note="Xếp hạng theo số lượng sản phẩm hoàn thành">
      {state.phase === 'idle' && <button className="primary" onClick={load}>Tải xếp hạng sản phẩm</button>}
      {state.phase === 'loading' && <p className="muted">Đang tải {state.total ? `${fmtInt(state.done)}/${fmtInt(state.total)} sản phẩm` : ''}…</p>}
      {state.phase === 'error' && <p className="muted">Không tải được: {state.message} <button className="reset" onClick={load}>Thử lại</button></p>}
      {state.phase === 'done' && (
        <DataTable columns={cols} data={state.rows.slice(0, 30)} onRowClick={(r) => update({ product: { key: r.key, label: r.name } })}
          initialSort={[{ id: 'units', desc: true }]} />
      )}
      {state.phase === 'done' && <p className="fine">Hiển thị 30 sản phẩm đầu trong {fmtInt(state.rows.length)}. Bấm một dòng để lọc theo sản phẩm. Mỗi mã sản phẩm thuộc một cửa hàng.</p>}
    </Section>
  )
}

export default function SalesPerformance() {
  const { filters, update } = useFilters()
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
    <Page title="Sales Performance" headline={headline} state={state}>
      {(d) => (
        <div className="sales-performance">
          <div className="sales-kpi-block">
            <div className="sales-block-heading">
              <span className="sales-eyebrow">SALES SNAPSHOT</span>
              <span className="sales-context">Theo bộ lọc hiện tại</span>
            </div>
            <KpiRow items={standardKpis(d.kpis)} />
          </div>

          <div className="sales-trend-card">
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
                    <LineChart data={d.monthly[metric]} margin={{ top: 12, right: 28, left: 8, bottom: 4 }}>
                      <CartesianGrid stroke={GRID} vertical={false} />
                      <XAxis dataKey="period" tickFormatter={fmtPeriod} tick={axisTick} tickLine={false} axisLine={AXIS_LINE} minTickGap={24} />
                      <YAxis tickFormatter={fmtAxis} tick={axisTick} tickLine={false} axisLine={false} width={64} />
                      <Tooltip formatter={(v, n) => [metric === 'revenue' ? fmtVND(v) + ' ₫' : fmtInt(v), n]} labelFormatter={fmtPeriod} contentStyle={tipStyle} />
                      <Legend iconType="plainline" wrapperStyle={{ fontSize: 13, paddingTop: 8 }} />
                      {d.monthly.names.map((n) => <Line key={n} type="monotone" dataKey={n} stroke={groupBy === 'channel' ? (CHANNEL_COLOR[n] ?? '#7a6b73') : storeColor(n)} strokeWidth={2.5} dot={{ r: 4, strokeWidth: 2, fill: '#ffffff' }} activeDot={{ r: 6, strokeWidth: 2 }} />)}
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
              <p className="fine sales-chart-note">Dữ liệu được tổng hợp theo tháng. Tháng đầu và tháng cuối của kỳ có thể chưa đầy đủ.</p>
            </Section>
          </div>

          <div className="sales-analysis-grid">
            <div className="sales-analysis-card">
              <div className="sales-card-index">01 / CHANNEL PERFORMANCE</div>
              <Section title="Theo cửa hàng" note="Bấm một dòng để lọc">
                <div className="sales-store-table">
                  <DataTable
                    columns={storeColumns} data={d.stores} onRowClick={(r) => update({ store: r.key })} initialSort={[{ id: 'revenue', desc: true }]}
                  />
                </div>
              </Section>
            </div>
            <div className="sales-analysis-card">
              <div className="sales-card-index">02 / ORDER STATUS</div>
              <Section title="Đơn theo trạng thái" note="Số đơn đặt, trạng thái hiện tại của đơn">
                <ShareBars items={d.status.map((s) => ({ ...s, revenue: s.revenue }))} colorFor={() => INK} countMode />
              </Section>
            </div>
            <div className="sales-analysis-card">
              <div className="sales-card-index">03 / CATEGORY MIX</div>
              <Section title="Theo danh mục" note="Danh mục được phân loại dựa trên tên sản phẩm trong dữ liệu lịch sử. Một đơn có thể thuộc nhiều danh mục nên không cộng tổng các dòng.">
                <DataTable columns={itemColumns('Danh mục')} data={d.categories} onRowClick={(r) => r.key && update({ category: r.key })} initialSort={[{ id: 'units', desc: true }]} />
              </Section>
            </div>
            <div className="sales-analysis-card">
              <div className="sales-card-index">04 / WAREHOUSE REGION</div>
              <Section title="Theo vùng kho" note="Phân bổ số lượng và giá trị theo vùng kho xuất hàng.">
                <DataTable columns={itemColumns('Vùng kho')} data={d.regions} initialSort={[{ id: 'units', desc: true }]} />
              </Section>
            </div>
          </div>

          <div className="sales-detail-card">
            <div className="sales-card-index">05 / DELIVERY GEOGRAPHY</div>
            <Section title="12 tỉnh/thành nhận nhiều đơn nhất" note="Xếp hạng theo số đơn có thông tin tỉnh/thành nhận hàng.">
              <DataTable columns={itemColumns('Tỉnh / thành')} data={d.provinces} initialSort={[{ id: 'orders', desc: true }]} />
            </Section>
          </div>

          <div className="sales-detail-card sales-product-card">
            <div className="sales-card-index">06 / PRODUCT RANKING</div>
            <ProductRanking key={JSON.stringify(filters)} filters={filters} update={update} />
          </div>

          <p className="footnote sales-footnote">
            Giá trị dòng hàng khác với "Giá trị đơn hoàn thành" nên không cộng hai chỉ tiêu này. Một số chỉ tiêu chi tiết chưa được hỗ trợ bởi dữ liệu hiện tại.
          </p>
        </div>
      )}
    </Page>
  )
}
