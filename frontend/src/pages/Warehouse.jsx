import ViewTabs, { ViewPanel } from '../components/ViewTabs.jsx'
import { useEffect, useState } from 'react'
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useFilters } from '../context/FilterContext.jsx'
import { useReport } from '../hooks/useReport.js'
import { getBreakdown, getDelivery, getKpis, getRisk, pool, SOURCES, STORES } from '../api/client.js'
import { Page, Section } from '../components/Page.jsx'
import { KpiRow } from '../components/KpiStrip.jsx'
import DataTable from '../components/DataTable.jsx'
import ChartTable from '../components/ChartTable.jsx'
import LinkedChart from '../components/LinkedChart.jsx'
import Alerts from '../components/Alerts.jsx'
import { BURGUNDY, storeColor } from '../lib/colors.js'
import { axisTick, AXIS_LINE, GRID, tipStyle } from '../lib/chart.js'
import { fmtDays, fmtInt, fmtPct } from '../lib/format.js'

const num = { align: 'right' }
const cnt = (i) => (i.getValue() == null ? '—' : fmtInt(i.getValue()))
const pct = (i) => (i.getValue() == null ? '—' : fmtPct(i.getValue()))
const days = (i) => fmtDays(i.getValue())

const whColumns = [
  { accessorKey: 'store', header: 'Cửa hàng' },
  { accessorKey: 'name', header: 'Kho' },
  { accessorKey: 'orders', header: 'Đơn có xuất hàng từ kho', cell: cnt, meta: num },
  { accessorKey: 'cancelRate', header: 'Tỷ lệ hủy', cell: pct, meta: num },
  { accessorKey: 'units', header: 'SL hoàn thành', cell: cnt, meta: num },
  { accessorKey: 'meanDays', header: 'Thời gian TB từ tạo đơn đến ghi nhận giao', cell: days, meta: num },
  { accessorKey: 'samples', header: 'Mẫu giao', cell: cnt, meta: num },
]
const routeColumns = [
  { accessorKey: 'store', header: 'Cửa hàng' },
  { accessorKey: 'warehouse', header: 'Kho' },
  { accessorKey: 'province', header: 'Tỉnh / thành nhận' },
  { accessorKey: 'orders', header: 'Đơn', cell: cnt, meta: num },
  { accessorKey: 'cancelRate', header: 'Hủy / có kết quả', cell: pct, meta: num },
  { accessorKey: 'median', header: 'Trung vị', cell: days, meta: num },
  { accessorKey: 'p90', header: 'P90 (ngày)', cell: days, meta: num },
  { accessorKey: 'samples', header: 'Mẫu giao', cell: cnt, meta: num },
  { accessorKey: 'risk', header: 'Rủi ro', cell: (i) => (i.getValue() == null ? '—' : i.getValue().toFixed(1).replace('.', ',')), meta: num },
  { accessorKey: 'support', header: 'Bằng chứng', cell: (i) => (i.getValue() === 'SUPPORTED' ? 'Đủ mẫu' : 'Mẫu thưa') },
]
const deliveryColumns = [
  { accessorKey: 'name', header: 'Nguồn' },
  { accessorKey: 'orders', header: 'Đơn', cell: cnt, meta: num },
  { accessorKey: 'created_to_recorded_samples', header: 'Số đơn có mốc tạo và giao', cell: cnt, meta: num },
  { accessorKey: 'mean_created_to_recorded_days', header: 'TB từ tạo đơn đến ghi nhận giao', cell: days, meta: num },
  { accessorKey: 'shipped_to_recorded_samples', header: 'Số đơn có mốc gửi và giao', cell: cnt, meta: num },
  { accessorKey: 'mean_shipped_to_recorded_days', header: 'TB từ gửi hàng đến ghi nhận giao', cell: days, meta: num },
]

// Đo thời gian từng lời gọi và in ra console dạng "[perf] Warehouse · tên: 123 ms" để tìm chỗ chậm.
async function timed(label, promise) {
  const t0 = performance.now()
  try { return await promise } finally { console.info(`[perf] Warehouse · ${label}: ${Math.round(performance.now() - t0)} ms`) }
}

// Tên kho chuẩn hóa thường đã chứa vùng ("Kho Hà Nội"): chỉ thêm vùng khi tên chưa có.
const whLabel = (w) => (w.region && !w.name.toLowerCase().includes(w.region.toLowerCase()) ? `${w.name} (${w.region})` : w.name)

function headline(d) {
  const k = d.kpis
  return `${fmtInt(k.orders)} đơn đặt, tỷ lệ hủy ${fmtPct(k.cancellationRate)}. ${k.meanDeliveryDays == null ? 'Chọn một cửa hàng để xem thời gian từ tạo đơn đến ghi nhận giao.' : `Thời gian trung bình từ tạo đơn đến ghi nhận giao là ${fmtDays(k.meanDeliveryDays)}.`}`
}

// Khối tải sau: hiện khung và trạng thái đang tải ngay, phần còn lại của trang không phải chờ.
function Later({ title, note, state, children }) {
  return (
    <Section title={title} note={note}>
      {state.error && <div className="notice err">Không tải được phần này: {state.error}. Các phần khác của trang vẫn dùng được.</div>}
      {!state.data && !state.error && <p className="muted">Đang tải…</p>}
      {state.data && <div className={state.loading ? 'body loading' : 'body'}>{children(state.data)}</div>}
    </Section>
  )
}

export default function Warehouse() {
  const { meta, filters, update } = useFilters()
  const [view, setView] = useState('warehouses')
  const [routePage, setRoutePage] = useState(1)
  const ROUTES_PER_PAGE = 4

  // Khi thay đổi bộ lọc, quay lại trang đầu tiên.
  useEffect(() => {
    setRoutePage(1)
  }, [filters])
  const storeCodes = filters.store === 'all' ? Object.keys(STORES).filter((s) => !filters.channel || filters.channel === 'all' || STORES[s].channel.toUpperCase() === filters.channel) : [filters.store]
  const codeOf = Object.fromEntries(meta.stores.map((s) => [s.key, s.code]))

  // 1) Nhanh: KPI, thời gian giao theo nguồn, vùng kho, tỉnh. Hiện trước.
  const head = useReport(async () => {
    const [kpis, delivery, region, province] = await Promise.all([
      timed('overview/kpis', getKpis(filters)), timed('operations/delivery', getDelivery(filters)),
      timed('analytics/warehouse_region', getBreakdown('warehouse_region', filters)), timed('analytics/province', getBreakdown('province', filters))])
    return {
      kpis, deliveryWarnings: delivery.warnings,
      delivery: delivery.rows.map((r) => ({ ...r, name: SOURCES[r.source_code]?.label ?? r.source_code })),
      regions: region.rows.map((r) => ({ name: r.group_value ? `Kho ${r.group_value}` : 'Không rõ', orders: r.orders, units: r.completed_units })),
      provinces: province.rows.filter((r) => r.group_value && r.group_value !== 'Unknown').map((r) => ({ name: r.group_value, orders: r.orders, units: r.completed_units }))
        .sort((a, b) => b.orders - a.orders).slice(0, 12),
    }
  }, [filters])

  // 2) Hiệu suất từng kho: mỗi kho một lần gọi KPI (tối đa 3 lần cùng lúc). Chạy song song với (1) và (3).
  const perf = useReport(async () => {
    const whs = meta.warehouses.filter((w) => (filters.region === 'all' || w.region === filters.region) && storeCodes.includes(codeOf[w.storeKey]) && (!filters.warehouse || filters.warehouse === 'all' || Number(filters.warehouse) === w.key))
    const res = await pool(whs.map((w) => () => timed(`kpis kho ${w.key}`, getKpis({ ...filters, store: codeOf[w.storeKey], region: 'all' }, { warehouse_key: w.key }))), 3)
    return whs.map((w, i) => ({ key: w.key, store: STORES[codeOf[w.storeKey]].label, storeCode: codeOf[w.storeKey], region: w.region, name: whLabel(w),
      orders: res[i].orders, cancelRate: res[i].cancellationRate, units: res[i].completedUnits, meanDays: res[i].meanDeliveryDays, samples: res[i].deliveryObservedOrders }))
  }, [filters])

  // 3) Tuyến kho → tỉnh (/dss/risk, nhiều trang, nặng nhất). Hiện sau cùng.
  const routes = useReport(async () => {
    // Risk profiles use the commercial route cohort, independent of a specific SKU/category.
    // Never display unfiltered route scores under a product/category filter.
    if (filters.product || filters.category !== 'all' || filters.status && filters.status !== 'all') return []
    const whName = Object.fromEntries(meta.warehouses.map((w) => [w.key, w]))
    const risks = await Promise.all(storeCodes.map((s) => timed(`dss/risk ${s}`, getRisk(s, filters.to, filters.from)).then((r) => ({ s, ...r }))))
    return risks.flatMap((r) => r.rows.map((x) => ({
      store: STORES[r.s].label, warehouse: whName[x.warehouse_key] ? whLabel(whName[x.warehouse_key]) : `Kho #${x.warehouse_key}`, region: whName[x.warehouse_key]?.region,
      warehouseKey: x.warehouse_key, province: x.route_province, orders: x.orders, cancelRate: x.resolved_orders ? x.canceled_orders / x.resolved_orders : null,
      median: x.median_lead_days, p90: x.p90_lead_days, samples: x.timing_samples, risk: x.risk_score, support: x.evidence_support })))
      .filter((r) => (filters.region === 'all' || r.region === filters.region) && (!filters.province || filters.province === 'all' || r.province === filters.province) && (!filters.warehouse || filters.warehouse === 'all' || r.warehouseKey === Number(filters.warehouse)))
  }, [filters])

  return (
    <Page title="Warehouse & Fulfillment" headline={headline} state={head}>
      {(d) => {
        const k = d.kpis
        return (
          <>
            <KpiRow items={[
              { label: 'Đơn đặt', value: fmtInt(k.orders), note: 'Trong phạm vi lọc' },
              { label: 'Tỷ lệ hủy', value: k.cancellationRate == null ? '—' : fmtPct(k.cancellationRate), note: `${fmtInt(k.canceledOrders)} đơn hủy` },
              { label: 'Dòng hàng', value: fmtInt(k.acceptedLines), note: 'Số dòng hàng hợp lệ' },
              { label: 'Số lượng hoàn thành', value: fmtInt(k.completedUnits), note: 'Sản phẩm của đơn hoàn thành' },
              { label: 'Ngày TB tạo → ghi nhận giao', value: fmtDays(k.meanDeliveryDays), note: k.meanDeliveryDays == null ? 'Chọn một cửa hàng để xem chỉ số' : `${fmtInt(k.deliveryObservedOrders)} đơn có thông tin giao hàng` },
            ]} />

            <ViewTabs value={view} onChange={setView} items={[["warehouses", "Hiệu suất kho"], ["delivery", "Thời gian giao"], ["province", "Tỉnh nhận hàng"], ["routes", "Tuyến kho → tỉnh"]]} />
            <ViewPanel active={view === 'warehouses'} name="Hiệu suất kho">
            <Later title="Hiệu suất theo kho" state={perf}
              note="Mỗi kho thuộc một cửa hàng. Một đơn có thể được xuất từ nhiều kho, vì vậy không cộng số đơn giữa các kho.">
              {(whs) => {
                const alerts = whs.filter((w) => w.orders >= 200 && w.cancelRate != null && k.cancellationRate && w.cancelRate > 1.25 * k.cancellationRate)
                  .map((w) => ({ level: 'warn', title: `${w.store} · ${w.name} có tỷ lệ hủy cao`, detail: `${fmtPct(w.cancelRate)} so với ${fmtPct(k.cancellationRate)} toàn bộ phạm vi lọc.` }))
                return (
                  <>
                    {alerts.length > 0 && <Alerts items={alerts} />}
                    <div className="warehouse-visual"><ChartTable columns={whColumns} rows={[...whs].sort((a,b)=>b.orders-a.orders).map(r=>({...r,plotName:`${r.region==='Hà Nội'?'HN':'HCM'} · ${r.storeCode==='bibica_tiktok_shop'?'TikTok':r.storeCode==='bibica_official_store'?'Shopee Bibica':'Quasure'}`}))} valueKey="cancelRate" format={fmtPct} axisFormat={v=>fmtPct(v,0)} color={r=>storeColor(r.store)} label="Tỷ lệ hủy theo kho" onSelect={r=>update({warehouse:String(r.key)})}/></div>
                    <details className="data-notes"><summary>Cách đọc thời gian giao</summary><p className="fine">Lưu ý: Shopee sử dụng thời điểm hoàn thành đơn, còn TikTok sử dụng thời điểm ghi nhận đã giao. Đây là thời gian tham chiếu từ dữ liệu sàn, không phải thời gian vận chuyển thực tế đã được xác minh. Chọn một dòng để xem riêng cửa hàng và vùng kho tương ứng.</p></details>
                  </>
                )
              }}
            </Later>

            </ViewPanel>
            <ViewPanel active={view === 'delivery'} name="Thời gian giao"><div className="cols">
              <Section title="Thời gian giao theo nguồn" note="Thời gian trung bình chỉ tính các đơn có đủ thông tin về mốc thời gian.">
                <div className="delivery-visual"><ChartTable columns={deliveryColumns} rows={d.delivery.map(r=>({...r,key:r.source_code}))} valueKey="mean_shipped_to_recorded_days" format={fmtDays} axisFormat={fmtDays} label="Thời gian từ gửi đến ghi nhận giao theo nguồn" color={r=>storeColor(r.name)}/></div>
                <details className="data-notes"><summary>Cách đọc thời gian</summary>{d.deliveryWarnings.map(w=><p key={w}>{w}</p>)}</details>
              </Section>
              <Section title="Đơn theo vùng kho" note="Số đơn được phân theo vùng của kho xuất hàng.">
                <div className="chart short">
                  <ResponsiveContainer>
                    <BarChart data={d.regions} layout="vertical" margin={{ top: 4, right: 32, left: 8, bottom: 0 }}>
                      <CartesianGrid stroke={GRID} horizontal={false} />
                      <XAxis type="number" tick={axisTick} tickLine={false} axisLine={AXIS_LINE} tickFormatter={fmtInt} />
                      <YAxis type="category" dataKey="name" tick={axisTick} tickLine={false} axisLine={false} width={110} />
                      <Tooltip formatter={(v) => [fmtInt(v) + ' đơn', 'Số đơn']} contentStyle={tipStyle} cursor={{ fill: '#f0eef2' }} />
                      <Bar isAnimationActive={false} dataKey="orders" fill={BURGUNDY} maxBarSize={30} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </Section>
            </div>

            </ViewPanel>
            <ViewPanel active={view === 'province'} name="Tỉnh nhận hàng"><Section title="Khu vực giao hàng" note="12 tỉnh/thành có nhiều đơn hàng nhất theo dữ liệu ghi nhận.">
              <ChartTable columns={[{accessorKey:'name',header:'Tỉnh / thành'},{accessorKey:'orders',header:'Đơn',cell:cnt,meta:num},{accessorKey:'units',header:'SL hoàn thành',cell:cnt,meta:num}]} rows={d.provinces.map(r=>({...r,key:r.name}))} valueKey="orders" label="Đơn theo tỉnh nhận" onSelect={r=>update({province:r.name})}/>
            </Section>

            </ViewPanel>
            <ViewPanel active={view === 'routes'} name="Tuyến kho tỉnh"><Later
              title="Tuyến kho → tỉnh: tỷ lệ hủy, thời gian giao và điểm rủi ro"
              state={routes}
              note={`Thống kê trong giai đoạn ${filters.from} đến ${filters.to}.${routes.data ? ` Có ${fmtInt(routes.data.length)} tuyến kho – tỉnh.` : ''} Mốc 90% thể hiện thời gian mà 90% đơn có dữ liệu giao không vượt quá.`}
            >
              {(rows) => {
                if (filters.product || filters.category !== 'all' || filters.status && filters.status !== 'all') return <p className="notice">Điểm tuyến dùng cohort thương mại toàn cửa hàng. Bỏ lọc sản phẩm/danh mục/trạng thái để xem; KPI kho phía trên vẫn theo bộ lọc.</p>
                const totalRows = rows.length
                const totalPages = Math.max(1, Math.ceil(totalRows / ROUTES_PER_PAGE))
                const currentPage = Math.min(routePage, totalPages)

                const startIndex = (currentPage - 1) * ROUTES_PER_PAGE
                const endIndex = Math.min(startIndex + ROUTES_PER_PAGE, totalRows)
                const pageRows = rows.slice(startIndex, endIndex)

                return (
                  <>
                    <div className="route-visual"><LinkedChart rows={pageRows.map((r,i)=>({...r,key:i,name:`${r.warehouse} → ${r.province}`}))} valueKey="p90" format={fmtDays} axisFormat={fmtDays} label="Mốc giao P90 các tuyến đang xem"/>
                    <DataTable
                      columns={routeColumns}
                      data={pageRows}
                      initialSort={[{ id: 'orders', desc: true }]}
                    /></div>

                    <div className="route-pagination">
                      <span className="route-pagination-info">
                        Đang xem {totalRows === 0 ? 0 : startIndex + 1}–{endIndex}
                        {' '}trong tổng số {fmtInt(totalRows)} tuyến
                      </span>

                      <div className="route-pagination-controls">
                        <button
                          type="button"
                          disabled={currentPage === 1}
                          onClick={() => setRoutePage((p) => Math.max(1, p - 1))}
                        >
                          Trước
                        </button>

                        {(() => {
                          let pages

                          if (totalPages <= 7) {
                            pages = Array.from({ length: totalPages }, (_, i) => i + 1)
                          } else if (currentPage <= 4) {
                            pages = [1, 2, 3, 4, 5, 'ellipsis-end', totalPages]
                          } else if (currentPage >= totalPages - 3) {
                            pages = [1, 'ellipsis-start', ...Array.from(
                              { length: 5 },
                              (_, i) => totalPages - 4 + i
                            )]
                          } else {
                            pages = [
                              1,
                              'ellipsis-start',
                              currentPage - 1,
                              currentPage,
                              currentPage + 1,
                              'ellipsis-end',
                              totalPages,
                            ]
                          }

                          return pages.map((page) => {
                            if (typeof page === 'string') {
                              return <span key={page}>{'…'}</span>
                            }

                            return (
                              <button
                                key={page}
                                type="button"
                                className={currentPage === page ? 'active' : ''}
                                aria-current={currentPage === page ? 'page' : undefined}
                                onClick={() => setRoutePage(page)}
                              >
                                {page}
                              </button>
                            )
                          })
                        })()}

                        <button
                          type="button"
                          disabled={currentPage === totalPages}
                          onClick={() => setRoutePage((p) => Math.min(totalPages, p + 1))}
                        >
                          Sau
                        </button>
                      </div>
                    </div>

                    <details className="data-notes"><summary>Giới hạn dữ liệu tuyến</summary><p className="fine">
                      Điểm ưu tiên rủi ro (0–100) dùng để hỗ trợ nhận diện tuyến cần chú ý,
                      không phải xác suất giao hàng thất bại. Thời gian được tính từ các
                      đơn đã có thông tin giao; những đơn chưa có ghi nhận giao chưa được
                      đưa vào, nên kết quả có thể nghiêng về các đơn giao nhanh. Mối liên
                      hệ giữa kho và tỉnh phản ánh dữ liệu lịch sử, chưa đủ để kết luận
                      đổi kho sẽ cải thiện kết quả. Mốc 90% là thống kê lịch sử: theo báo
                      cáo kiểm tra của nhóm, trên dữ liệu giữ lại chỉ khoảng 85–89% đơn
                      nằm trong mốc này, nên không dùng như cam kết giao đúng hạn.
                    </p></details>
                  </>
                )
              }}
            </Later></ViewPanel>
          </>
        )
      }}
    </Page>
  )
}
