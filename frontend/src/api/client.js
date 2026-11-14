// Lớp API duy nhất của giao diện. Bám đúng hợp đồng trong src/api (FastAPI, cổng 8001):
//  - mọi phản hồi dạng { data, meta };
//  - tiền trả về là chuỗi decimal → đổi sang số ở đây;
//  - bộ lọc dùng tên tham số của models.Filters (extra='forbid': tham số lạ bị từ chối 422).
import axios from 'axios'

const http = axios.create({ baseURL: '/api/v1', timeout: 90000 })

// Các khóa luôn giữ nguyên là chuỗi (mã, nhãn, băm)
const KEEP = new Set(['group_value', 'order_ref', 'evidence_ref', 'sha256', 'source_code', 'storefront_code',
  'store', 'province', 'route_province', 'canonical_status', 'database', 'native_sku_id', 'seller_sku', 'variation_name'])
const NUMERIC = /^-?\d+(\.\d+)?$/

export function toNumbers(x, key) {
  if (Array.isArray(x)) return x.map((v) => toNumbers(v, key))
  if (x && typeof x === 'object') return Object.fromEntries(Object.entries(x).map(([k, v]) => [k, toNumbers(v, k)]))
  if (typeof x === 'string' && !KEEP.has(key) && NUMERIC.test(x)) return Number(x)
  return x
}

export function errorMessage(e) {
  const r = e.response
  if (!r) return 'Không kết nối được API (mặc định http://127.0.0.1:8001). Hãy chạy backend rồi tải lại trang.'
  const d = r.data?.detail
  if (r.status === 503 && typeof d === 'string' && d.startsWith('Solver')) return 'Bộ giải không chứng nhận được nghiệm tối ưu trong thời gian cho phép. Hãy giảm số đơn hoặc nới ràng buộc.'
  if (r.status === 503) return 'Cơ sở dữ liệu chưa sẵn sàng hoặc đang bận. Kiểm tra ETL/migrate rồi thử lại.'
  if (r.status === 422) {
    if (typeof d === 'string') return d
    if (Array.isArray(d)) return 'Tham số không hợp lệ: ' + d.map((x) => (x.loc || []).slice(1).join('.') || x.type).join(', ')
  }
  return typeof d === 'string' ? d : `Máy chủ trả lỗi ${r.status}`
}

async function call(method, path, { params, body } = {}) {
  try {
    const res = await http.request({ method, url: path, params, data: body })
    return { data: toNumbers(res.data.data), meta: res.data.meta ?? {} }
  } catch (e) {
    throw new Error(errorMessage(e))
  }
}

// Chạy tối đa n tác vụ cùng lúc để không dồn dập vào PostgreSQL cục bộ
export async function pool(tasks, n = 4) {
  const out = new Array(tasks.length)
  let next = 0
  await Promise.all(Array.from({ length: Math.min(n, tasks.length) }, async () => {
    while (next < tasks.length) { const i = next++; out[i] = await tasks[i]() }
  }))
  return out
}

// ------------------------------------------------------------ bộ lọc
export const STORES = {
  bibica_tiktok_shop: { label: 'Bibica TikTok Shop', channel: 'TikTok', source: 'tiktok_bibica' },
  bibica_official_store: { label: 'Bibica Official Store', channel: 'Shopee', source: 'shopee_bibica' },
  quasure_specialized_store: { label: 'Quasure specialized store', channel: 'Shopee', source: 'shopee_quasure' },
}
export const SOURCES = Object.fromEntries(Object.entries(STORES).map(([k, v]) => [v.source, { ...v, store: k }]))

export function filterParams(f, extra = {}) {
  const p = { start_date: f.from, end_date: f.to }
  if (f.store && f.store !== 'all') p.store = f.store
  if (f.channel && f.channel !== 'all') p.channel = f.channel.toUpperCase()
  if (f.warehouse && f.warehouse !== 'all') p.warehouse_key = Number(f.warehouse)
  if (f.region && f.region !== 'all') p.warehouse_region = f.region
  if (f.category && f.category !== 'all') p.category = f.category
  if (f.province && f.province !== 'all') p.province = f.province
  if (f.status && f.status !== 'all') p.status = f.status
  if (f.product) p.product_key = f.product.key
  return { ...p, ...extra }
}

// ------------------------------------------------------------ danh mục
export async function getMeta() {
  const { data, meta } = await call('get', '/meta')
  const cov = data.coverage || []
  return {
    stores: data.stores.map((s) => ({ key: s.storefront_key, code: s.storefront_code, ...STORES[s.storefront_code] })),
    warehouses: data.warehouses.map((w) => ({ key: w.warehouse_key, storeKey: w.storefront_key, name: w.normalized_warehouse_name, region: w.warehouse_region })),
    categories: data.categories.map((c) => c.canonical_category),
    provinces: data.provinces,
    coverage: cov,
    dateRange: { min: cov.map((c) => c.first_order_date).sort()[0], max: cov.map((c) => c.last_order_date).sort().at(-1) },
    capabilities: data.capabilities,
    warnings: meta.warnings ?? [],
  }
}

// ------------------------------------------------------------ KPI
export async function getKpis(f, extra = {}) {
  const { data: r, meta } = await call('get', '/overview/kpis', { params: filterParams(f, extra) })
  return mapKpis(r, meta)
}

export function mapKpis(r, meta = {}) {
  return {
    orders: r.orders, completedOrders: r.completed_orders, canceledOrders: r.canceled_orders,
    unknownStatusOrders: r.unknown_status_orders, payableObservedOrders: r.payable_observed_orders,
    bookedPayable: r.booked_payable, completedPayable: r.completed_payable, completedAov: r.completed_aov,
    cancellationRate: r.cancellation_rate, conflictingOrders: r.conflicting_orders,
    observedRefund: r.observed_refund, refundOrderRate: r.refund_order_rate,
    acceptedLines: r.accepted_lines, completedUnits: r.completed_units, unmappedLines: r.unmapped_lines,
    meanDeliveryDays: r.mean_created_to_recorded_delivery_days, deliveryObservedOrders: r.delivery_observed_orders,
    reviews: r.reviews, avgStars: r.review_stars_mean, lowReviews: r.low_reviews, lowReviewRate: r.low_review_rate,
    reviewOrderCoverage: r.review_order_coverage, tiktokOrders: r.tiktok_orders,
    availability: meta.metric_availability ?? {}, policies: meta.warnings ?? [],
  }
}

export async function getOverviewDashboard(f) {
  const { data, meta } = await call('get', '/overview/dashboard', {params: filterParams(f)})
  const periods = [...new Set(data.monthly.map(r => r.period))].sort()
  const names = [...new Set(data.monthly.map(r => STORES[r.storefront_code]?.label ?? r.storefront_code))]
  const monthly = periods.map(period => {
    const rows=data.monthly.filter(r=>r.period===period)
    const known=rows.filter(r=>r.completed_payable!=null)
    return {period,total:known.length?known.reduce((a,r)=>a+r.completed_payable,0):null,
      orders:rows.reduce((a,r)=>a+r.orders,0),
      ...Object.fromEntries(names.map(name=>[name,rows.find(r=>(STORES[r.storefront_code]?.label??r.storefront_code)===name)?.completed_payable??null]))}
  })
  return {...data,kpis:mapKpis(data.kpis,meta),monthly,names}
}

// ------------------------------------------------------------ breakdown
export async function getBreakdown(dim, f, { limit = 200, offset = 0, extra = {} } = {}) {
  const { data, meta } = await call('get', `/analytics/${dim}`, { params: filterParams(f, { limit, offset, ...extra }) })
  return { rows: data, total: data[0]?.total_groups ?? 0, grain: meta.grain, warnings: meta.warnings ?? [] }
}

export async function getAllBreakdown(dim, f, onProgress) {
  const rows = []
  let total = Infinity
  for (let offset = 0; offset < total; offset += 200) {
    const page = await getBreakdown(dim, f, { offset })
    rows.push(...page.rows)
    total = page.total
    onProgress?.(rows.length, total)
    if (!page.rows.length) break
  }
  return rows
}

// groupBy: 'store' (mỗi cửa hàng một đường) hoặc 'channel' (TikTok / Shopee, gộp 2 cửa hàng Shopee)
export async function getMonthlyBySource(f, groupBy = 'store') {
  const sources = f.store && f.store !== 'all' ? [STORES[f.store].source] : Object.keys(SOURCES).filter((s) => !f.channel || f.channel === 'all' || SOURCES[s].channel.toUpperCase() === f.channel.toUpperCase())
  const base = { ...f, store: 'all' }
  const results = await Promise.all(sources.map((s) => getBreakdown('month', base, { extra: { source: s } })))
  const labelOf = (src) => (groupBy === 'channel' ? SOURCES[src].channel : SOURCES[src].label)
  const byPeriod = {}
  results.forEach((res, i) => {
    const label = labelOf(sources[i])
    res.rows.forEach((r) => {
      const row = (byPeriod[r.group_value] ??= { period: r.group_value })
      const cur = row[label] ?? { orders: 0, revenue: null, canceled: 0 }
      row[label] = {
        orders: cur.orders + r.orders,
        revenue: r.completed_payable == null ? cur.revenue : (cur.revenue ?? 0) + r.completed_payable,
        canceled: cur.canceled + r.canceled_orders,
      }
    })
  })
  const names = [...new Set(sources.map(labelOf))]
  const rows = Object.values(byPeriod).sort((a, b) => a.period.localeCompare(b.period))
  const series = (m) => rows.map((r) => ({ period: r.period, ...Object.fromEntries(names.map((n) => [n, r[n]?.[m] ?? null])) }))
  return { names, revenue: series('revenue'), orders: series('orders'), canceled: series('canceled') }
}

export async function getDelivery(f) {
  const { data, meta } = await call('get', '/operations/delivery', { params: filterParams(f) })
  return { rows: data, warnings: meta.warnings ?? [] }
}

export async function searchProducts(f, search, limit = 20, offset = 0) {
  const { data } = await call('get', '/products', { params: filterParams(f, { search, limit, offset, sort: 'orders' }) })
  return data.map((p) => ({ key: p.product_key, label: p.product_name, categories: p.historical_categories, units: p.completed_units,
    store: p.storefront_code, sku: p.native_sku_id, variation: p.variation_name, orders: p.orders, total: p.total_products }))
}

export async function getAllProducts(f) {
  const out = []
  let total = Infinity
  for (let offset = 0; offset < total; offset += 200) {
    const { data } = await call('get', '/products', { params: filterParams(f, { limit: 200, offset }) })
    out.push(...data)
    total = data[0]?.total_products ?? 0
    if (!data.length) break
  }
  return out
}

// ------------------------------------------------------------ DSS
// Ma trận kho → tỉnh của một cửa hàng. Lấy hết các trang (mỗi trang tối đa 200 tuyến).
export async function getRisk(store, asOf, historyStart) {
  const rows = []
  let total = Infinity
  let warnings = []
  for (let offset = 0; offset < total; offset += 200) {
    const { data, meta } = await call('get', '/dss/risk', { params: { store, as_of: asOf, history_start: historyStart, limit: 200, offset } })
    rows.push(...data)
    total = meta.total_groups ?? 0
    warnings = meta.warnings ?? []
    if (!data.length) break
  }
  return { rows, total, warnings }
}

export const dssAllocate = (body) => call('post', '/dss/allocate', { body })
export const dssWhatIf = (body) => call('post', '/dss/what-if', { body })
export const dssSensitivity = (body) => call('post', '/dss/sensitivity', { body })
export const dssShelfLife = (body) => call('post', '/dss/shelf-life', { body })

export async function getReviewThemes(f) {
  const { data } = await call('get', '/customer/review-themes', {
    params: filterParams(f),
  })
  return data
}
