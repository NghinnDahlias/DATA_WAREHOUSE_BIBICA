// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'

const request = vi.fn()

vi.mock('axios', () => ({
  default: {
    create: () => ({ request }),
  },
}))

globalThis.ResizeObserver = class {
  observe() {}
  unobserve() {}
  disconnect() {}
}

const { default: App } = await import('../src/App.jsx')

// ============================================================
// MOCK KPI
// ============================================================

const kpiRow = {
  orders: 1000,
  completed_orders: 800,
  canceled_orders: 70,
  unknown_status_orders: 2,
  payable_observed_orders: 990,
  booked_payable: '120000000.00',
  completed_payable: '90000000.00',
  completed_orders_with_payable: 790,
  observed_refund: null,
  refund_observed_orders: 0,
  refund_positive_orders: 0,
  conflicting_orders: 12,
  tiktok_orders: 600,
  mean_created_to_recorded_delivery_days: '3.40',
  delivery_observed_orders: 700,
  accepted_lines: 1500,
  units: 2000,
  completed_units: 1700,
  unmapped_lines: 5,
  reviews: 120,
  review_stars_mean: '4.6500',
  low_reviews: 9,
  reviewed_tiktok_orders: 100,
  completed_aov: '113924.05',
  cancellation_rate: '0.0700',
  low_review_rate: '0.0750',
  review_order_coverage: '0.1667',
}

// ============================================================
// MOCK ANALYTICS
// ============================================================

const groups = {
  month: [
    {
      group_value: '2026-07',
      orders: 300,
      completed_payable: '30000000.00',
      canceled_orders: 20,
      total_groups: 2,
    },
    {
      group_value: '2026-08',
      orders: 320,
      completed_payable: '33000000.00',
      canceled_orders: 25,
      total_groups: 2,
    },
  ],

  store: [
    {
      group_value: 'bibica_tiktok_shop',
      orders: 600,
      completed_payable: '50000000.00',
      canceled_orders: 40,
      total_groups: 2,
    },
    {
      group_value: 'bibica_official_store',
      orders: 400,
      completed_payable: '40000000.00',
      canceled_orders: 30,
      total_groups: 2,
    },
  ],

  status: [
    {
      group_value: 'COMPLETED',
      orders: 800,
      completed_payable: '90000000.00',
      canceled_orders: 0,
      total_groups: 2,
    },
    {
      group_value: 'CANCELED',
      orders: 70,
      completed_payable: null,
      canceled_orders: 70,
      total_groups: 2,
    },
  ],

  category: [
    {
      group_value: 'Bánh',
      accepted_lines: 900,
      orders: 700,
      completed_units: 1000,
      completed_observed_item_payable: '60000000.00',
      total_groups: 2,
    },
    {
      group_value: null,
      accepted_lines: 5,
      orders: 5,
      completed_units: 5,
      completed_observed_item_payable: null,
      total_groups: 2,
    },
  ],

  province: [
    {
      group_value: 'Hà Nội',
      accepted_lines: 500,
      orders: 400,
      completed_units: 600,
      completed_observed_item_payable: '20000000.00',
      total_groups: 2,
    },
    {
      group_value: 'Unknown',
      accepted_lines: 5,
      orders: 5,
      completed_units: 1,
      completed_observed_item_payable: '1.00',
      total_groups: 2,
    },
  ],

  warehouse_region: [
    {
      group_value: 'Hà Nội',
      accepted_lines: 800,
      orders: 600,
      completed_units: 900,
      completed_observed_item_payable: '50000000.00',
      total_groups: 2,
    },
    {
      group_value: 'Hồ Chí Minh',
      accepted_lines: 700,
      orders: 450,
      completed_units: 800,
      completed_observed_item_payable: '40000000.00',
      total_groups: 2,
    },
  ],

  product: [
    {
      group_value: 11,
      accepted_lines: 90,
      orders: 80,
      completed_units: 150,
      completed_observed_item_payable: '5000000.00',
      total_groups: 1,
    },
  ],
}

// ============================================================
// MOCK PRODUCTS
// Giữ sản phẩm cũ cho Sales.
// Bổ sung SKU 1365 cho DSS Breakfast Demo.
// ============================================================

const products = [
  {
    product_key: 11,
    product_name: 'Bánh Hura Sữa Chua',
    historical_categories: ['Bánh'],
    accepted_lines: 90,
    completed_units: 150,
    total_products: 5,
  },
  {
    product_key: 12,
    product_name: 'Bánh Quy Bơ Hộp Thiếc',
    historical_categories: ['Bánh'],
    accepted_lines: 80,
    completed_units: 120,
    total_products: 5,
  },
  {
    product_key: 13,
    product_name: 'Combo Bánh Ăn Sáng Bibica',
    historical_categories: ['Bánh'],
    accepted_lines: 70,
    completed_units: 100,
    total_products: 5,
  },
  {
    product_key: 14,
    product_name: 'Ngũ cốc Hura Yến Mạch',
    historical_categories: ['Ngũ cốc'],
    accepted_lines: 60,
    completed_units: 90,
    total_products: 5,
  },
  {
    product_key: 1365,
    product_name: 'Sản phẩm bữa sáng Bibica',
    historical_categories: ['Bánh'],
    accepted_lines: 100,
    completed_units: 200,
    total_products: 5,
  },
]

// ============================================================
// MOCK META
// Warehouse key 2 = HCM
// Warehouse key 3 = Hanoi
// ============================================================

const meta = {
  stores: [
    {
      storefront_key: 1,
      storefront_code: 'bibica_tiktok_shop',
      channel_key: 1,
    },
    {
      storefront_key: 2,
      storefront_code: 'bibica_official_store',
      channel_key: 2,
    },
    {
      storefront_key: 3,
      storefront_code: 'quasure_specialized_store',
      channel_key: 2,
    },
  ],

  warehouses: [
    {
      warehouse_key: 2,
      storefront_key: 1,
      normalized_warehouse_name: 'Kho HCM',
      warehouse_region: 'Hồ Chí Minh',
    },
    {
      warehouse_key: 3,
      storefront_key: 1,
      normalized_warehouse_name: 'Kho Hà Nội',
      warehouse_region: 'Hà Nội',
    },
  ],

  categories: [
    { canonical_category: 'Bánh' },
    { canonical_category: 'Kẹo' },
  ],

  provinces: [
    'Hà Nội',
    'Hồ Chí Minh',
    'Đồng Nai',
    'Hải Phòng',
    'Unknown',
  ],

  coverage: [
    {
      source_code: 'tiktok_bibica',
      first_order_date: '2024-02-01',
      last_order_date: '2026-10-18',
      orders: 600,
      observed_days: 500,
    },
  ],

  capabilities: {},
}

// ============================================================
// MOCK DSS ALLOCATION
// ============================================================

const cand = (warehouseKey, feasible) => ({
  warehouse_key: warehouseKey,
  feasible,
  reasons: feasible
    ? []
    : ['INSUFFICIENT_TIMING_EVIDENCE'],

  risk: feasible
    ? { risk_score: 12.3 }
    : null,

  p90_scenario_delivery_days: feasible
    ? 4
    : null,

  evidence: feasible
    ? {
        evidence_level: 'WAREHOUSE_PROVINCE',
        timing_samples: 50,
      }
    : null,
})

const DEMO_ORDERS = [
  { order_ref: 'DEMO0', province: 'Hà Nội' },
  { order_ref: 'DEMO1', province: 'Hồ Chí Minh' },
  { order_ref: 'DEMO2', province: 'Đồng Nai' },
  { order_ref: 'DEMO3', province: 'Hải Phòng' },
]

const alloc = (label, warehouseKey, assigned = true) => ({
  scenario: { label },

  assignments: DEMO_ORDERS.map((order) => ({
    ...order,

    warehouse_key: assigned
      ? warehouseKey
      : null,

    reason: assigned
      ? 'MINIMUM_OBJECTIVE_WITHIN_BATCH_CONSTRAINTS'
      : 'NO_FEASIBLE_WAREHOUSE',

    candidates: assigned
      ? [
          cand(2, true),
          cand(3, true),
        ]
      : [
          {
            ...cand(2, false),
            reasons: ['INSUFFICIENT_REMAINING_SHELF_LIFE'],
          },
          {
            ...cand(3, false),
            reasons: ['INSUFFICIENT_REMAINING_SHELF_LIFE'],
          },
        ],
  })),

  summary: {
    requested_orders: 4,
    assigned_orders: assigned ? 4 : 0,
    unassigned_orders: assigned ? 0 : 4,

    warehouse_orders: assigned
      ? { [warehouseKey]: 4 }
      : {},

    mean_risk_score: assigned ? 12.3 : null,
    mean_p90_scenario_days: assigned ? 4 : null,
    objective_cost: assigned ? 0.5 : null,
  },

  solver: {
    method: 'binary MILP',
  },
})

// ============================================================
// MOCK API ROUTES
// ============================================================

function route({ url, method }) {
  const env = (data, m = {}) => ({
    data: {
      data,
      meta: m,
    },
  })

  if (url === '/meta') {
    return env(meta)
  }

  if (url === '/overview/dashboard') return env({kpis:kpiRow,monthly:groups.month.map(r=>({...r,period:r.group_value,storefront_code:'bibica_tiktok_shop'})),stores:groups.store,categories:groups.category,provinces:groups.province,products})

  if (url === '/overview/kpis') {
    return env(kpiRow, {
      warnings: ['Tiền đơn tính một lần.'],
    })
  }

  if (url.startsWith('/analytics/')) {
    return env(groups[url.split('/')[2]])
  }

  if (url === '/operations/delivery') {
    return env(
      [
        {
          source_code: 'tiktok_bibica',
          orders: 600,
          created_to_recorded_samples: 500,
          mean_created_to_recorded_days: '3.2',
          shipped_to_recorded_samples: 480,
          mean_shipped_to_recorded_days: '2.1',
        },
      ],
      {
        warnings: ['Shopee completion time là proxy.'],
      }
    )
  }

  if (url === '/products') {
    return env(products)
  }

  if (url === '/dss/risk') {
    return env(
      [
        {
          warehouse_key: 3,
          route_province: 'Hà Nội',
          orders: 300,
          resolved_orders: 250,
          canceled_orders: 10,
          timing_samples: 200,
          median_lead_days: 2,
          p90_lead_days: 4,
          risk_score: 8.5,
          evidence_support: 'SUPPORTED',
        },
      ],
      {
        total_groups: 1,
        warnings: [],
      }
    )
  }

  // ----------------------------------------------------------
  // DSS WHAT-IF
  // ----------------------------------------------------------

  if (url === '/dss/what-if') {
    return env(
      {
        baseline: alloc(
          'Baseline',
          3
        ),

        alternatives: [
          {
            result: alloc(
              'Ngoại lệ TMĐT HCM',
              2
            ),

            comparison: {
              changed_orders: 4,
              changed_order_refs: [
                'DEMO0',
                'DEMO1',
                'DEMO2',
                'DEMO3',
              ],
              objective_cost_delta: 0.1,
            },
          },
        ],
      },
      {
        warnings: ['Điểm rủi ro không phải xác suất.'],
      }
    )
  }

  // ----------------------------------------------------------
  // DSS SENSITIVITY
  // Baseline + HCM exception + shelf-life stress
  // ----------------------------------------------------------

  if (url === '/dss/sensitivity') {
    return env(
      {
        baseline: alloc(
          'Baseline - Bữa sáng xuất từ Hà Nội',
          3
        ),

        alternatives: [
          {
            result: alloc(
              'Ngoại lệ TMĐT HCM',
              2
            ),

            comparison: {
              changed_orders: 4,
              changed_order_refs: [
                'DEMO0',
                'DEMO1',
                'DEMO2',
                'DEMO3',
              ],
              objective_cost_delta: 0.1,
            },
          },

          {
            result: alloc(
              'Kiểm tra hạn sử dụng - HSD 5 ngày',
              null,
              false
            ),

            comparison: {
              changed_orders: 4,
              changed_order_refs: [
                'DEMO0',
                'DEMO1',
                'DEMO2',
                'DEMO3',
              ],
              objective_cost_delta: null,
            },
          },
        ],
      },
      {
        warnings: ['Điểm rủi ro không phải xác suất.'],
      }
    )
  }

  throw new Error(
    'chưa có fixture cho ' + method + ' ' + url
  )
}

// ============================================================
// TEST SETUP
// ============================================================

beforeEach(() => {
  cleanup()
  request.mockReset()
  request.mockImplementation(async (a) => route(a))
})

const at = (path) =>
  render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>
  )

// ============================================================
// TESTS
// ============================================================

describe('các trang dựng được với dữ liệu theo hợp đồng API', () => {
  it('tab bàn phím chỉ dựng panel đang chọn và quay lại được biểu đồ', async () => {
    at('/sales')
    const first = await screen.findByRole('tab', { name: 'Xu hướng', exact: true })
    first.focus()
    await userEvent.keyboard('{End}')
    expect(screen.getByRole('tab', { name: 'Sản phẩm', exact: true }).getAttribute('aria-selected')).toBe('true')
    expect(screen.getByText('Tải xếp hạng sản phẩm')).toBeTruthy()
    await userEvent.keyboard('{Home}')
    expect(screen.queryByText('Tải xếp hạng sản phẩm')).toBeNull()
    expect(screen.getByText('Xu hướng theo kênh')).toBeTruthy()
  })

  it('bảng dài phân trang sau khi sắp xếp, không mất dòng ngoài trang đầu', async () => {
    const { default: DataTable } = await import('../src/components/DataTable.jsx')
    render(<DataTable columns={[{ accessorKey: 'value', header: 'Giá trị' }]} data={Array.from({ length: 25 }, (_, i) => ({ value: i + 1 }))} />)
    expect(document.querySelectorAll('tbody tr')).toHaveLength(10)
    await userEvent.click(screen.getByRole('button', { name: 'Trang bảng sau' }))
    expect(document.querySelector('tbody tr').textContent).toBe('11')
    await userEvent.click(screen.getByRole('button', { name: 'Trang bảng sau' }))
    expect(document.querySelectorAll('tbody tr')).toHaveLength(5)
  })

  // ----------------------------------------------------------
  // EXECUTIVE OVERVIEW
  // ----------------------------------------------------------

  it('Executive Overview', async () => {
    at('/overview')

    // KPI số đơn đặt là dữ liệu ổn định hơn câu headline diễn giải.
    expect(
      (await screen.findAllByText('1.000'))[0]
    ).toBeTruthy()

    expect(screen.queryByRole('tab')).toBeNull()
    expect(screen.getByText('SKU nổi bật')).toBeTruthy()
    expect(screen.getByText('Cơ cấu sản lượng')).toBeTruthy()

    expect(
      screen.getByText(/12 đơn có giá trị mâu thuẫn/)
    ).toBeTruthy()
  })

  it('overview keeps extra calculations in an on-demand modal and removes the month dropdown', async () => {
    at('/overview')
    await screen.findByText('SKU nổi bật')
    expect(document.querySelector('.insight-ribbon')).toBeNull()
    expect(screen.queryByLabelText('Lọc theo tháng')).toBeNull()
    expect(screen.queryByRole('dialog')).toBeNull()
    await userEvent.click(screen.getByRole('button',{name:'Thống kê chỉ số'}))
    await screen.findByRole('heading',{name:'So sánh cửa hàng'})
    expect(screen.getByRole('dialog',{name:'Thống kê chỉ số'})).toBeTruthy()
    await userEvent.keyboard('{Escape}')
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(document.activeElement.textContent).toContain('Thống kê chỉ số')
  })

  // ----------------------------------------------------------
  // SALES PERFORMANCE
  // ----------------------------------------------------------

  it('Sales Performance, gồm xếp hạng sản phẩm tải theo yêu cầu', async () => {
    at('/sales')

    expect(
      await screen.findByText('Xu hướng theo kênh')
    ).toBeTruthy()

    await userEvent.click(screen.getByRole('tab', { name: 'Sản phẩm', exact: true }))
    await userEvent.click(
      screen.getByText('Tải xếp hạng sản phẩm')
    )

    expect(
      await screen.findByText('Bánh Hura Sữa Chua')
    ).toBeTruthy()
  })

  it('Sales: chuyển giữa Theo kênh và Theo cửa hàng', async () => {
    at('/sales')

    await screen.findByText('Xu hướng theo kênh')

    const btn = screen.getByRole('button', {
      name: 'Theo cửa hàng',
    })

    await userEvent.click(btn)

    expect(
      btn.getAttribute('aria-pressed')
    ).toBe('true')
  })

  // ----------------------------------------------------------
  // WAREHOUSE & FULFILLMENT
  // ----------------------------------------------------------

  it('Warehouse & Fulfillment', async () => {
    at('/warehouse')

    expect(
      await screen.findByText('Hiệu suất theo kho')
    ).toBeTruthy()

    expect(
      screen.getByText(/Tuyến kho → tỉnh/)
    ).toBeTruthy()
  })

  it('Warehouse hiện KPI và hiệu suất kho trước khi bảng tuyến kho → tỉnh tải xong', async () => {
    let release

    const gate = new Promise((r) => {
      release = r
    })

    request.mockImplementation(async (a) => {
      if (a.url === '/dss/risk') {
        await gate
      }

      return route(a)
    })

    at('/warehouse')

    expect(
      await screen.findByText('Hiệu suất theo kho')
    ).toBeTruthy()

    await waitFor(() =>
      expect(
        screen.getAllByText(/Kho Hà Nội/).length
      ).toBeGreaterThan(0)
    )

    expect(
      screen.getByText(/Tuyến kho → tỉnh/)
    ).toBeTruthy()

    await userEvent.click(screen.getByRole('tab', { name: 'Tuyến kho → tỉnh', exact: true }))
    expect(
      screen.getAllByText('Đang tải…').length
    ).toBeGreaterThan(0)

    release()

    await waitFor(() =>
      expect(
        screen.queryAllByText('Đang tải…')
      ).toHaveLength(0)
    )

    // Chọn đúng phần thông tin phân trang; cụm '3 tuyến' cũng xuất hiện
    // trong ghi chú của section nên getByText(/3 tuyến/) bị trùng.
    const routePagination = screen.getByText(
      (_, element) => element?.classList?.contains('route-pagination-info')
    )
    expect(routePagination.textContent).toMatch(/trong tổng số\s*3 tuyến/)
  })

  it('Warehouse: lỗi ở bảng tuyến chỉ báo trong khối đó, phần còn lại vẫn dùng được', async () => {
    request.mockImplementation(async (a) => {
      if (a.url === '/dss/risk') {
        const e = new Error('x')

        e.response = {
          status: 503,
          data: {
            detail: 'Database unavailable',
          },
        }

        throw e
      }

      return route(a)
    })

    at('/warehouse')
    await screen.findByText('Hiệu suất theo kho')
    await userEvent.click(screen.getByRole('tab', { name: 'Tuyến kho → tỉnh', exact: true }))
    expect(
      await screen.findByText(/Không tải được phần này/)
    ).toBeTruthy()

    expect(
      screen.getByRole('heading', { name: 'Warehouse & Fulfillment', exact: true })
    ).toBeTruthy()
    await userEvent.click(screen.getByRole('tab', { name: 'Tỉnh nhận hàng', exact: true }))
    expect(
      screen.getByText('Khu vực giao hàng')
    ).toBeTruthy()
  })

  // ----------------------------------------------------------
  // CUSTOMER EXPERIENCE
  // ----------------------------------------------------------

  it('Customer Experience', async () => {
    at('/customer')
    await screen.findByRole('heading', { name: 'Customer Experience', exact: true })
    await userEvent.click(await screen.findByRole('tab', { name: 'Chủ đề đánh giá', exact: true }))

    expect(
      await screen.findByText(/Phân tích chủ đề đánh giá/)
    ).toBeTruthy()

    expect(
      screen.getAllByText(/4,65/).length
    ).toBeGreaterThan(0)
  })

  it('Customer Experience báo rõ lý do khi lọc cửa hàng Shopee và vẫn giữ tiêu đề phân tích chủ đề đánh giá', async () => {
    at('/customer')
    await screen.findByRole('heading', { name: 'Customer Experience', exact: true })
    await userEvent.click(await screen.findByRole('tab', { name: 'Chủ đề đánh giá', exact: true }))

    await screen.findByText(/Phân tích chủ đề đánh giá/)

    await userEvent.click(screen.getByRole('button',{name:'Lọc thêm',exact:true}))
    await userEvent.selectOptions(screen.getByLabelText('Cửa hàng',{exact:true}),'bibica_official_store')
    await userEvent.click(screen.getByRole('button',{name:'Xong',exact:true}))

    expect(
      await screen.findByText(
        /DW chưa có nguồn đánh giá của Shopee/
      )
    ).toBeTruthy()

    expect(
      screen.getAllByText(/Phân tích chủ đề đánh giá/).length
    ).toBeGreaterThan(0)
  })

  // ----------------------------------------------------------
  // DSS BREAKFAST DEMO
  // ----------------------------------------------------------

  it('DSS: batch mẫu bữa sáng có 4 đơn và chạy 3 kịch bản', async () => {
    at('/dss')

    await userEvent.click(
      await screen.findByText('Tạo batch mẫu')
    )
    await waitFor(() => expect(screen.getAllByText('DEMO0').length).toBeGreaterThan(0))

    await userEvent.click(
      await screen.findByText('Chạy và so sánh kịch bản')
    )

    expect(
      await screen.findByText('So sánh kịch bản')
    ).toBeTruthy()

    // Phải gọi sensitivity vì có 2 phương án thay thế.
    const call = request.mock.calls.find(
      (c) => c[0].url === '/dss/sensitivity'
    )

    expect(call).toBeTruthy()

    const body = call[0].data

    expect(body.store).toBe('bibica_tiktok_shop')

    // --------------------------------------------------------
    // 1. Kiểm tra 4 đơn mẫu
    // --------------------------------------------------------

    expect(body.orders).toHaveLength(4)

    expect(
      body.orders.map((o) => o.order_ref)
    ).toEqual([
      'DEMO0',
      'DEMO1',
      'DEMO2',
      'DEMO3',
    ])

    expect(
      body.orders.map((o) => o.province)
    ).toEqual([
      'Hà Nội',
      'Hồ Chí Minh',
      'Đồng Nai',
      'Hải Phòng',
    ])

    // Cả 4 đơn cùng SKU 1365, mỗi đơn số lượng 2.
    expect(
      body.orders.every((o) =>
        o.items.length === 1 &&
        o.items[0].product_key === 13 &&
        o.items[0].quantity === 2
      )
    ).toBe(true)

    // --------------------------------------------------------
    // 2. Kiểm tra baseline
    // --------------------------------------------------------

    expect(
      body.baseline.stock_mode
    ).toBe('required')

    expect(
      body.baseline.stocks
    ).toHaveLength(2)

    expect(
      body.baseline.stocks
    ).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          warehouse_key: 2,
          product_key: 13,
          units: 100,
          remaining_shelf_days: 30,
          stock_scope: 'ECOMMERCE',
        }),

        expect.objectContaining({
          warehouse_key: 3,
          product_key: 13,
          units: 100,
          remaining_shelf_days: 30,
          stock_scope: 'ECOMMERCE',
        }),
      ])
    )

    // --------------------------------------------------------
    // 3. Kiểm tra phương án ngoại lệ HCM
    // --------------------------------------------------------

    expect(
      body.alternatives
    ).toHaveLength(2)

    const hcmScenario = body.alternatives[0]

    expect(
      hcmScenario.capacity_orders
    ).toEqual({
      '3': 0,
    })

    expect(
      hcmScenario.breakfast_exceptions
    ).toEqual([
      {
        warehouse_key: 2,
        product_key: 13,
        reason: 'HN_STOCKOUT_TRANSFER',
        evidence_ref: 'DEMO-HN-STOCKOUT-001',
        ecommerce_stock_confirmed: true,
      },
    ])

    // --------------------------------------------------------
    // 4. Kiểm tra phương án stress HSD
    // --------------------------------------------------------

    const shelfScenario = body.alternatives[1]

    expect(
      shelfScenario.stocks
    ).toHaveLength(2)

    expect(
      shelfScenario.stocks.every(
        (s) => s.remaining_shelf_days === 5
      )
    ).toBe(true)

    expect(
      shelfScenario.extra_delay_days
    ).toEqual({
      '2': 4,
      '3': 4,
    })

    expect(
      shelfScenario.min_remaining_days
    ).toBe(1)

    // --------------------------------------------------------
    // 5. Kiểm tra kết quả hiển thị
    // --------------------------------------------------------

    expect(
      screen.queryByText(/Kho Hà Nội \(Hà Nội\)/)
    ).toBeNull()

    // DEMO0 xuất hiện ở thẻ đơn và bảng kết quả sau khi chạy mô phỏng.
    // Click mã đơn ở thẻ batch để mở phần chi tiết phân bổ.
    await userEvent.click(screen.getByRole('tab', { name: 'Phân bổ & giải thích', exact: true }))
    await userEvent.click(
      screen.getAllByText('DEMO0')[0]
    )

    expect(
      screen.getAllByText('Kho HCM (Hồ Chí Minh)').length
    ).toBeGreaterThan(0)
  })

  // ----------------------------------------------------------
  // DSS ERROR HANDLING
  // ----------------------------------------------------------

  it('DSS: hiển thị detail lỗi 422 do API trả về', async () => {
    request.mockImplementation(async (a) => {
      if (a.url === '/dss/sensitivity') {
        const e = new Error('x')

        e.response = {
          status: 422,
          data: {
            detail:
              'Province must be recognized by the observed spelling dictionary',
          },
        }

        throw e
      }

      return route(a)
    })

    at('/dss')

    await userEvent.click(
      await screen.findByText('Tạo batch mẫu')
    )
    await waitFor(() => expect(screen.getAllByText('DEMO0').length).toBeGreaterThan(0))

    await userEvent.click(
      await screen.findByText('Chạy và so sánh kịch bản')
    )

    expect(
      await screen.findByText(
        /Province must be recognized/
      )
    ).toBeTruthy()
  })

  // ----------------------------------------------------------
  // DSS STOCK SCOPE
  // ----------------------------------------------------------

  it('DSS: phạm vi tồn kho chỉ gửi giá trị mà API nhận (ECOMMERCE, WHOLESALE, UNVERIFIED)', async () => {
    const API_SCOPES = [
      'ECOMMERCE',
      'WHOLESALE',
      'UNVERIFIED',
    ]

    at('/dss')

    await userEvent.click(
      await screen.findByText('Tạo batch mẫu')
    )
    await waitFor(() => expect(screen.getAllByText('DEMO0').length).toBeGreaterThan(0))

    await userEvent.click(screen.getByRole('tab', { name: 'Tham số kịch bản', exact: true }))
    await userEvent.click(
      screen.getAllByLabelText(/Nhập tồn kho/)[0]
    )

    await userEvent.click(
      screen.getAllByText(/Thêm dòng tồn kho/)[0]
    )

    const scopeSelect = screen.getAllByLabelText(
      'Phạm vi tồn kho'
    )[0]

    const values = [
      ...scopeSelect.querySelectorAll('option'),
    ].map((o) => o.value)

    expect(values.length).toBeGreaterThan(0)

    expect(
      values.filter((v) => !API_SCOPES.includes(v))
    ).toEqual([])
  })
})
