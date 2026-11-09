import { beforeEach, describe, expect, it, vi } from 'vitest'

const request = vi.fn()
vi.mock('axios', () => ({ default: { create: () => ({ request }) } }))
const api = await import('../src/api/client.js')
const { buildOrders, buildScenario, validateBatch, DEFAULT_SCENARIO, reasonText } = await import('../src/lib/dss.js')

const env = (data, meta = {}) => ({ data: { data, meta } })
const filters = { from: '2026-06-20', to: '2026-09-18', store: 'all', region: 'all', category: 'all', product: null }

beforeEach(() => { request.mockClear(); request.mockImplementation(async () => env([])) })

describe('toNumbers', () => {
  it('đổi chuỗi decimal thành số nhưng giữ group_value và mã', () => {
    const out = api.toNumbers({ completed_payable: '9175209123.00', group_value: '2026-07', sha256: '1234', nested: [{ v: '12' }], text: 'abc' })
    expect(out).toEqual({ completed_payable: 9175209123, group_value: '2026-07', sha256: '1234', nested: [{ v: 12 }], text: 'abc' })
  })
  it('giữ NULL là null (NULL khác 0)', () => expect(api.toNumbers({ completed_aov: null }).completed_aov).toBeNull())
})

describe('filterParams', () => {
  it('chỉ gửi tham số có trong models.Filters và bỏ giá trị "all"', () => {
    const p = api.filterParams({ ...filters, store: 'bibica_tiktok_shop', region: 'Hà Nội', product: { key: 7, label: 'x' } })
    expect(p).toEqual({ start_date: '2026-06-20', end_date: '2026-09-18', store: 'bibica_tiktok_shop', warehouse_region: 'Hà Nội', product_key: 7 })
    expect(Object.keys(api.filterParams(filters))).toEqual(['start_date', 'end_date'])
  })
})

describe('errorMessage', () => {
  it('422 dạng danh sách chỉ nêu tên trường', () => {
    const m = api.errorMessage({ response: { status: 422, data: { detail: [{ loc: ['query', 'start_date'], type: 'date_parsing' }] } } })
    expect(m).toContain('start_date')
  })
  it('422 dạng chuỗi giữ nguyên thông điệp', () => expect(api.errorMessage({ response: { status: 422, data: { detail: 'Every product must belong to the requested storefront' } } })).toMatch(/Every product/))
  it('503 solver khác 503 cơ sở dữ liệu', () => {
    expect(api.errorMessage({ response: { status: 503, data: { detail: 'Solver could not certify an optimum within the runtime limit' } } })).toMatch(/Bộ giải/)
    expect(api.errorMessage({ response: { status: 503, data: { detail: 'Database unavailable' } } })).toMatch(/Cơ sở dữ liệu/)
  })
  it('mất kết nối', () => expect(api.errorMessage({})).toMatch(/8001/))
})

describe('getKpis', () => {
  it('chuyển dòng KPI của repository.kpis sang trường giao diện', async () => {
    request.mockResolvedValue(env({ orders: 127588, completed_orders: 100000, canceled_orders: 9000, unknown_status_orders: 3, payable_observed_orders: 127000,
      completed_payable: '9175209123.00', completed_aov: '91752.09', cancellation_rate: '0.0705', completed_units: '168478', review_stars_mean: '4.7000', low_review_rate: null,
      mean_created_to_recorded_delivery_days: null }, { warnings: ['NULL khác 0.'], metric_availability: { review_metrics: 'TIKTOK_OBSERVED_REVIEWS_ONLY' } }))
    const k = await api.getKpis(filters)
    expect(k.completedPayable).toBe(9175209123)
    expect(k.completedUnits).toBe(168478)
    expect(k.cancellationRate).toBeCloseTo(0.0705)
    expect(k.lowReviewRate).toBeNull()
    expect(k.meanDeliveryDays).toBeNull()
    expect(k.policies).toEqual(['NULL khác 0.'])
    expect(request.mock.calls[0][0].params).toEqual({ start_date: '2026-06-20', end_date: '2026-09-18' })
  })
})

describe('getMonthlyBySource', () => {
  it('gọi mỗi nguồn một lần, gộp theo tháng, thiếu tháng là 0', async () => {
    request.mockImplementation(async ({ params }) => env(
      params.source === 'tiktok_bibica' ? [{ group_value: '2026-07', orders: 10, completed_payable: '1000.00', canceled_orders: 1, total_groups: 1 }]
        : params.source === 'shopee_bibica' ? [{ group_value: '2026-07', orders: 5, completed_payable: '500.00', canceled_orders: 0, total_groups: 2 }, { group_value: '2026-08', orders: 4, completed_payable: '400.00', canceled_orders: 2, total_groups: 2 }]
          : []))
    const m = await api.getMonthlyBySource(filters)
    expect(request).toHaveBeenCalledTimes(3)
    expect(m.names).toHaveLength(3)
    expect(m.revenue).toEqual([
      { period: '2026-07', 'Bibica TikTok Shop': 1000, 'Bibica Official Store': 500, 'Quasure specialized store': 0 },
      { period: '2026-08', 'Bibica TikTok Shop': 0, 'Bibica Official Store': 400, 'Quasure specialized store': 0 }])
    expect(m.canceled[1]['Bibica Official Store']).toBe(2)
  })
  it('khi chọn một cửa hàng chỉ gọi một lần với source tương ứng', async () => {
    request.mockResolvedValue(env([]))
    await api.getMonthlyBySource({ ...filters, store: 'quasure_specialized_store' })
    expect(request).toHaveBeenCalledTimes(1)
    expect(request.mock.calls[0][0].params.source).toBe('shopee_quasure')
    expect(request.mock.calls[0][0].params.store).toBeUndefined()
  })
})

describe('getAllBreakdown', () => {
  it('phân trang đến hết total_groups', async () => {
    const page = (n, offset) => Array.from({ length: n }, (_, i) => ({ group_value: offset + i, total_groups: 230, orders: 1 }))
    request.mockImplementation(async ({ params }) => env(page(params.offset === 0 ? 200 : 30, params.offset)))
    const rows = await api.getAllBreakdown('product', filters)
    expect(rows).toHaveLength(230)
    expect(request).toHaveBeenCalledTimes(2)
  })
})

describe('getMeta', () => {
  it('suy ra khoảng ngày từ coverage và gán nhãn cửa hàng', async () => {
    request.mockResolvedValue(env({
      stores: [{ storefront_key: 1, storefront_code: 'bibica_tiktok_shop', channel_key: 1 }],
      warehouses: [{ warehouse_key: 3, storefront_key: 1, normalized_warehouse_name: 'Kho A', warehouse_region: 'Hà Nội' }],
      categories: [{ canonical_category: 'Bánh' }], provinces: ['Hà Nội'],
      coverage: [{ source_code: 'tiktok_bibica', first_order_date: '2024-02-01', last_order_date: '2026-10-18', orders: 5, observed_days: 4 },
        { source_code: 'shopee_bibica', first_order_date: '2023-08-04', last_order_date: '2026-10-10', orders: 5, observed_days: 4 }],
      capabilities: {} }, { warnings: [] }))
    const m = await api.getMeta()
    expect(m.dateRange).toEqual({ min: '2023-08-04', max: '2026-10-18' })
    expect(m.stores[0]).toMatchObject({ code: 'bibica_tiktok_shop', label: 'Bibica TikTok Shop', channel: 'TikTok' })
    expect(m.categories).toEqual(['Bánh'])
  })
})

describe('DSS đầu vào', () => {
  const orders = [{ ref: 'D1', province: 'Hà Nội', items: [{ product: { key: 5 }, quantity: '2' }, { product: null, quantity: 1 }] }]
  it('dựng đơn đúng schema, bỏ dòng chưa chọn sản phẩm', () => {
    expect(buildOrders(orders)).toEqual([{ order_ref: 'D1', province: 'Hà Nội', items: [{ product_key: 5, quantity: 2 }] }])
  })
  it('kịch bản mặc định khớp mặc định của models.Scenario', () => {
    const s = buildScenario(DEFAULT_SCENARIO)
    expect(s).toMatchObject({ stock_mode: 'assume_available', stocks: [], capacity_orders: {}, extra_delay_days: {}, max_delivery_days: 7,
      late_threshold_days: 5, min_remaining_days: 1, max_risk_score: 100, min_route_samples: 20, prior_strength: 20, risk_weight: 0.7, low_star_max: 2,
      risk_weights: { cancellation: 0.4, late_delivery: 0.4, low_review: 0.2 } })
  })
  it('công suất, độ trễ và tồn kho chỉ gửi khi người dùng nhập', () => {
    const s = buildScenario({ ...DEFAULT_SCENARIO, stockMode: 'required', capacity: { 3: '5', 4: '' }, delay: { 3: '2.5', 4: 0 },
      stocks: [{ warehouseKey: 3, productKey: 5, units: '10', shelfDays: '', scope: 'ECOMMERCE' }] })
    expect(s.capacity_orders).toEqual({ 3: 5 })
    expect(s.extra_delay_days).toEqual({ 3: 2.5 })
    expect(s.stocks).toEqual([{ warehouse_key: 3, product_key: 5, units: 10, remaining_shelf_days: null, stock_scope: 'ECOMMERCE' }])
  })
  it('bỏ tồn kho khi ở chế độ giả định đủ hàng', () => {
    expect(buildScenario({ ...DEFAULT_SCENARIO, stocks: [{ warehouseKey: 3, productKey: 5, units: 1, scope: 'ECOMMERCE' }] }).stocks).toEqual([])
  })
  it('validateBatch bắt lỗi trước khi gọi API', () => {
    expect(validateBatch([])).toMatch(/ít nhất/)
    expect(validateBatch([{ ref: 'D1', province: '', items: [] }])).toMatch(/tỉnh/)
    expect(validateBatch([{ ref: 'D1', province: 'Hà Nội', items: [{ product: null }] }])).toMatch(/sản phẩm/)
    expect(validateBatch([{ ref: 'D1', province: 'Hà Nội', items: [{ product: { key: 1 } }, { product: { key: 1 } }] }])).toMatch(/hai lần/)
    expect(validateBatch(orders)).toBeNull()
  })
  it('dịch mã lý do, mã lạ giữ nguyên', () => {
    expect(reasonText('SHELF_LIFE_BUFFER')).toMatch(/Hạn dùng/)
    expect(reasonText('SOMETHING_NEW')).toBe('SOMETHING_NEW')
  })
})
