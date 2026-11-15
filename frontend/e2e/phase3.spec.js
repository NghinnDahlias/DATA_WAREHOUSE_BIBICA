import { test, expect } from '@playwright/test'
import fs from 'node:fs'

const fmt = (n) => n == null ? '—' : Number(n).toLocaleString('vi-VN')
const kpi = (p, label) => p.locator('.kpi').filter({ has: p.locator('.kpi-label', { hasText: label }) }).first().locator('.kpi-value')
const full = async (p) => { await p.getByRole('button', { name: 'Toàn bộ', exact: true }).click() }
const ready = async (p) => {
  await expect(p.locator('h1')).toBeVisible()
  await expect(p.locator('.body.loading')).toHaveCount(0)
  await expect(p.locator('.notice.err, .rt-error')).toHaveCount(0)
}
async function expected(request, params = {}) {
  const r = await request.get('/api/v1/overview/kpis', { params })
  expect(r.status()).toBe(200)
  return (await r.json()).data
}
async function openFilters(p) {if(!await p.getByRole('dialog',{name:'Bộ lọc chuyên sâu'}).isVisible()) await p.getByRole('button',{name:'Lọc thêm',exact:true}).click()}
async function closeFilters(p) {if(await p.getByRole('dialog',{name:'Bộ lọc chuyên sâu'}).isVisible()) await p.getByRole('button',{name:'Xong',exact:true}).click()}
async function setFilter(p,label,value) {
 await expect(p.locator('h1')).toBeVisible()
 const target=p.getByLabel(label,{exact:true})
 if(!await target.isVisible())await openFilters(p)
 await target.selectOption(value)
 await closeFilters(p)
}
async function checkOrders(p, count) { await expect(kpi(p, 'Đơn đặt')).toHaveText(fmt(count)); await ready(p) }

test('five screens load real API without JavaScript failures', async ({ page }) => {
  const errors = []
  page.on('pageerror', (e) => errors.push(e.message))
  for (const [path, title, marker] of [
    ['overview', 'Tổng quan', 'Diễn biến giá trị đơn hoàn thành'],
    ['sales', 'Sales Performance', 'Xu hướng theo kênh'],
    ['warehouse', 'Warehouse & Fulfillment', 'Hiệu suất theo kho'],
    ['customer', 'Customer Experience', 'Điểm sao và tỷ lệ tiêu cực theo tháng đặt hàng'],
    ['dss', 'DSS Simulation', 'Tạo batch mẫu'],
  ]) {
    await page.goto('/' + path)
    await expect(page.getByRole('heading', { name: title, exact: true })).toBeVisible()
    await expect(page.getByText(marker, { exact: true }).first()).toBeVisible()
    if (path !== 'dss') await ready(page)
  }
  expect(errors).toEqual([])
})

test('full-data KPI and independent channel/store/warehouse/date filters', async ({ page, request }) => {
  await page.goto('/sales'); await full(page)
  await checkOrders(page, 127588)
  await expect(kpi(page, 'Số lượng bán')).toHaveText('168.478')
  await page.getByLabel('Kênh', { exact: true }).selectOption('SHOPEE')
  await checkOrders(page, (await expected(request, { channel: 'SHOPEE' })).orders)
  await openFilters(page)
  await expect(page.getByLabel('Cửa hàng', { exact: true }).locator('option[value="bibica_tiktok_shop"]')).toHaveCount(0)
  await closeFilters(page)
  await setFilter(page,'Cửa hàng','quasure_specialized_store')
  const meta = (await (await request.get('/api/v1/meta')).json()).data
  const store = meta.stores.find((s) => s.storefront_code === 'quasure_specialized_store')
  const wh = meta.warehouses.find((w) => w.storefront_key === store.storefront_key)
  await page.getByRole('button', { name: 'Lọc thêm', exact: true }).click()
  await page.getByLabel('Kho', { exact: true }).selectOption(String(wh.warehouse_key))
  await page.getByRole('button', { name: 'Xong', exact: true }).click()
  const params = { channel: 'SHOPEE', store: store.storefront_code, warehouse_key: wh.warehouse_key, start_date: '2026-06-01', end_date: '2026-06-30' }
  await page.getByLabel('Từ ngày', { exact: true }).fill(params.start_date)
  await page.getByLabel('Đến ngày', { exact: true }).fill(params.end_date)
  await checkOrders(page, (await expected(request, params)).orders)
  await page.getByRole('button', { name: 'Đặt lại', exact: true }).click()
  await expect(page.getByLabel('Kênh', { exact: true })).toHaveValue('all')
  await openFilters(page)
  await expect(page.getByLabel('Kho', { exact: true })).toHaveValue('all')
  await closeFilters(page)
})

test('sales metric toggle, product ranking drilldown and scoped picker', async ({ page, request }) => {
  await page.goto('/sales'); await full(page)
  await setFilter(page,'Cửa hàng','bibica_tiktok_shop')
  await checkOrders(page, 63744)
  await page.getByRole('group', { name: 'Chỉ số', exact: true }).getByRole('button', { name: 'Đơn đặt', exact: true }).click()
  await expect(page.getByRole('group', { name: 'Chỉ số', exact: true }).getByRole('button', { name: 'Đơn đặt', exact: true })).toHaveAttribute('aria-pressed', 'true')
  await page.getByRole('button', { name: 'Theo cửa hàng', exact: true }).click()
  await page.getByRole('tab', { name: 'Sản phẩm', exact: true }).click()
  await page.getByRole('button', { name: 'Tải xếp hạng sản phẩm' }).click()
  const table = page.locator('.sales-product-card tbody')
  await expect(table.locator('tr').first()).toBeVisible()
  const response = page.waitForResponse((r) => r.url().includes('/overview/kpis') && r.url().includes('product_key=') && r.status() === 200)
  await table.locator('tr').first().press('Enter')
  await checkOrders(page, (await (await response).json()).data.orders)
  await expect(page.getByRole('button', { name: 'Bỏ lọc product' })).toBeVisible()
  await page.getByLabel('Kênh', { exact: true }).selectOption('SHOPEE')
  await expect(page.getByRole('button', { name: 'Bỏ lọc product' })).toHaveCount(0)
  await openFilters(page)
  await page.getByRole('textbox', { name: 'Sản phẩm', exact: true }).fill('Quasure')
  await expect(page.getByRole('listbox').getByRole('button').first()).toBeVisible()
  const chosen = page.waitForResponse((r) => r.url().includes('/overview/kpis') && r.url().includes('product_key=') && r.status() === 200)
  await page.getByRole('listbox').getByRole('button').first().click()
  await closeFilters(page)
  await checkOrders(page, (await (await chosen).json()).data.orders)
})

test('warehouse cohort, delivery semantics, pagination and product-filter limitation', async ({ page }) => {
  await page.goto('/warehouse'); await full(page)
  await checkOrders(page, 127588)
  const wh = page.locator('section').filter({ has: page.getByRole('heading', { name: 'Hiệu suất theo kho', exact: true }) })
  await expect(wh.locator('tbody tr').first()).toBeVisible()
  const members = new Set(await wh.locator('tbody tr').allTextContents())
  while (await wh.getByRole('button', { name: 'Trang bảng sau' }).isVisible().catch(() => false) && await wh.getByRole('button', { name: 'Trang bảng sau' }).isEnabled()) {
    await wh.getByRole('button', { name: 'Trang bảng sau' }).click()
    ;(await wh.locator('tbody tr').allTextContents()).forEach((r) => members.add(r))
  }
  expect(members.size).toBe(6)
  await page.getByRole('tab', { name: 'Tuyến kho → tỉnh', exact: true }).click()
  await expect(page.locator('.route-pagination-info')).toContainText('tuyến')
  await page.getByRole('button', { name: 'Sau', exact: true }).click()
  await expect(page.locator('.route-pagination-info')).toContainText('5–8')
  await page.getByRole('button', { name: 'Lọc thêm', exact: true }).click()
  await page.getByLabel('Danh mục', { exact: true }).selectOption('Bánh')
  await page.getByRole('button', { name: 'Xong', exact: true }).click()
  await expect(page.getByText('Điểm tuyến dùng cohort thương mại toàn cửa hàng.', { exact: false })).toBeVisible()
  await ready(page)
})

test('TikTok negative reviews/themes and absent Shopee ratings', async ({ page, request }) => {
  await page.goto('/customer'); await full(page)
  await expect(kpi(page, 'Số đánh giá')).toHaveText('5.625')
  await expect(page.getByRole('button', { name: 'Đọc đánh giá tiêu cực', exact: true }))
    .toHaveAttribute('title', /^262 đánh giá(?: · .+)?$/)
  const themes = (await (await request.get('/api/v1/customer/review-themes')).json()).data
  expect(themes.availability).toBe('READY')
  expect(themes.audited_reviews).toBe(5625)
  await page.getByRole('tab', { name: 'Chủ đề đánh giá', exact: true }).click()
  await expect(page.locator('.rt-stat-card').filter({ has: page.locator('.rt-stat-label', { hasText: /^Tổng đánh giá$/ }) }).locator('strong')).toHaveText('5.625')
  await page.getByLabel('Kênh', { exact: true }).selectOption('SHOPEE')
  await expect(page.getByText('DW chưa có nguồn đánh giá của Shopee', { exact: false })).toBeVisible()
  await expect(page.getByText('Chưa có nguồn đánh giá Shopee.', { exact: true })).toBeVisible()
  await expect(page.locator('.rt-stat-card')).toHaveCount(0)
})

test('empty cohort and error remove stale KPI values', async ({ page }) => {
  await page.goto('/sales'); await full(page); await checkOrders(page, 127588)
  await setFilter(page,'Cửa hàng','bibica_official_store')
  await page.getByLabel('Từ ngày', { exact: true }).fill('2023-08-04')
  await page.getByLabel('Đến ngày', { exact: true }).fill('2023-08-05')
  await expect(page.getByText('Không có dữ liệu khớp bộ lọc.', { exact: false })).toBeVisible()
  await expect(page.locator('.kpi')).toHaveCount(0)
  await page.route('**/api/v1/overview/kpis?**', (route) => route.fulfill({ status: 503, json: { detail: 'Database unavailable' } }))
  await page.getByRole('button', { name: 'Đặt lại', exact: true }).click()
  await expect(page.locator('.notice.err')).toContainText('Không tải được dữ liệu')
  await expect(page.locator('.kpi')).toHaveCount(0)
})

for (const store of ['bibica_tiktok_shop', 'bibica_official_store', 'quasure_specialized_store']) {
  test(`real DSS batch, single, what-if, sensitivity and shelf-life ${store}`, async ({ page }) => {
    await page.goto('/dss')
    await setFilter(page,'Cửa hàng',store)
    await page.getByRole('button', { name: 'Tạo batch mẫu', exact: true }).click()
    await expect(page.locator('.order-card').first()).toBeVisible()
    const run = page.waitForResponse((r) => r.url().endsWith('/dss/sensitivity') && r.request().method() === 'POST')
    await page.getByRole('button', { name: 'Chạy và so sánh kịch bản', exact: true }).click()
    const response = await run
    expect(response.status()).toBe(200)
    const data = (await response.json()).data
    expect(data.baseline.summary.requested_orders).toBe(4)
    expect(data.alternatives).toHaveLength(2)
    await expect(page.getByRole('heading', { name: 'So sánh kịch bản', exact: true })).toBeVisible()
    await page.getByRole('tab', { name: 'Phân bổ & giải thích', exact: true }).click()
    await page.locator('tr.clickable').filter({ hasText: 'DEMO0' }).click()
    await expect(page.locator('tr.detail .cand th').filter({ hasText: /^Khả thi$/ }).first()).toBeVisible()
    const single = page.waitForResponse((r) => r.url().endsWith('/dss/allocate'))
    await page.getByRole('button', { name: 'Chỉ chạy phương án gốc', exact: true }).click()
    expect((await single).status()).toBe(200)
    await page.getByRole('tab', { name: 'Tham số kịch bản', exact: true }).click()
    await page.getByRole('tablist', { name: 'Chọn kịch bản', exact: true }).getByRole('tab', { name: 'Phương án 1', exact: true }).click()
    await page.getByRole('button', { name: 'Xóa phương án', exact: true }).click()
    const whatif = page.waitForResponse((r) => r.url().endsWith('/dss/what-if'))
    await page.getByRole('button', { name: 'Chạy và so sánh kịch bản', exact: true }).click()
    expect((await whatif).status()).toBe(200)
    await page.getByRole('tab', { name: 'Mô phỏng HSD', exact: true }).click()
    await page.getByRole('textbox', { name: 'Sản phẩm', exact: true }).last().fill('')
    await page.getByRole('textbox', { name: 'Sản phẩm', exact: true }).last().focus()
    await page.getByRole('listbox').getByRole('button').first().click()
    await page.getByLabel('Giả định hạn dùng còn lại (ngày)', {exact:true}).fill('30')
    const shelf = page.waitForResponse((r) => r.url().endsWith('/dss/shelf-life'))
    await page.getByRole('button', { name: 'Chạy mô phỏng hạn dùng', exact: true }).click()
    expect((await shelf).status()).toBe(200)
    await expect(page.getByText('Kết quả đánh giá', { exact: true })).toBeVisible()
    await page.getByLabel('Đánh giá tại ngày', { exact: true }).fill('2026-09-17')
    await expect(page.getByText('Kết quả đánh giá', { exact: true })).toHaveCount(0)
    await expect(page.locator('.notice.err').filter({ hasText: 'Không tải' })).toHaveCount(0)
  })
}

test('desktop and mobile geometry audit preserves actual measurements', async ({ page }) => {
  const layouts = []
  for (const [width, height] of [[1366, 768], [1280, 720], [1846, 867], [390, 844]]) {
    await page.setViewportSize({ width, height })
    for (const path of ['overview', 'sales', 'warehouse', 'customer', 'dss']) {
      await page.goto('/' + path)
      await expect(page.locator('h1')).toBeVisible()
      if (path !== 'dss') { await expect(page.locator('.kpi-value').first()).toBeVisible(); await ready(page) }
      const m = await page.evaluate(() => ({ width: innerWidth, height: innerHeight, scrollWidth: document.documentElement.scrollWidth, scrollHeight: document.documentElement.scrollHeight,
        panels: [...document.querySelectorAll('.view-panel')].map((p) => ({ name: p.getAttribute('aria-label'), height: p.clientHeight, scrollHeight: p.scrollHeight, width: p.clientWidth, scrollWidth: p.scrollWidth })) }))
      layouts.push({ path, ...m, no_horizontal_overflow: m.scrollWidth <= width + 1, fits_one_screen: m.scrollHeight <= height + 1 })
      if (width === 1366) await page.screenshot({ path: `../.runtime/phase3-${path}.png` })
    }
  }
  fs.writeFileSync(`../reports/${process.env.QA_REPORT_PREFIX || 'phase3'}_layouts.json`, JSON.stringify({ status: layouts.every((m) => m.no_horizontal_overflow && m.fits_one_screen) ? 'PASS' : 'PARTIAL', measurements: layouts }, null, 2))
  expect(layouts).toHaveLength(20)
  expect(layouts.every((m) => m.no_horizontal_overflow && m.fits_one_screen)).toBe(true)
})

test('all analysis tabs stay reachable within the workspace', async ({ page }) => {
  const errors = []
  page.on('pageerror', (e) => errors.push(e.message))
  for (const path of ['overview', 'sales', 'warehouse', 'customer', 'dss']) {
    await page.goto('/' + path)
    if(path==='overview'){await expect(page.locator('.overview-grid')).toBeVisible();continue}
    await expect(page.getByRole('tablist').first()).toBeVisible()
    const names = await page.getByRole('tablist').first().getByRole('tab').allTextContents()
    for (const name of names) {
      await page.getByRole('tablist').first().getByRole('tab', { name, exact: true }).click()
      await expect(page.getByRole('tablist').first().getByRole('tab', { name, exact: true })).toHaveAttribute('aria-selected', 'true')
      await expect(page.getByRole('tabpanel').first()).toBeVisible()
      const box = await page.getByRole('tabpanel').first().boundingBox()
      expect(box.height).toBeGreaterThan(100)
      expect(box.y + box.height).toBeLessThanOrEqual(769)
    }
  }
  expect(errors).toEqual([])
})

test('mobile filters open, apply a real channel cohort and collapse', async ({ page, request }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/sales')
  await page.getByRole('button', { name: 'Bộ lọc +', exact: true }).click()
  await page.getByRole('button', { name: 'Toàn bộ', exact: true }).click()
  await page.getByLabel('Kênh', { exact: true }).selectOption('SHOPEE')
  await page.getByRole('button', { name: 'Bộ lọc −', exact: true }).click()
  await checkOrders(page, (await expected(request, { channel: 'SHOPEE' })).orders)
  await expect(page.getByLabel('Kênh', { exact: true })).not.toBeVisible()
  await expect(page.getByRole('tabpanel').first()).toBeVisible()
})


test('rare SKU from reported screenshot keeps exact identity and KPI grain', async ({page,request})=>{
  const row=(await (await request.get('/api/v1/products',{params:{product_key:8}})).json()).data[0]
  expect(row.storefront_code).toBe('bibica_official_store')
  await page.goto('/sales');await full(page)
  await openFilters(page)
  await page.getByRole('textbox',{name:'Sản phẩm',exact:true}).fill(row.native_sku_id)
  await page.locator('button[data-product-key="8"]').click()
  await expect(page.getByRole('button',{name:'Đổi sản phẩm'})).toContainText(row.variation_name)
  await closeFilters(page)
  await checkOrders(page,4)
  await expect(kpi(page,'Số lượng bán')).toHaveText('1')
  await expect(kpi(page,'Tỷ lệ hủy')).toHaveText('75,0%')
  await expect(page.getByText(/Tiền hiển thị là tiền toàn đơn có chứa SKU/)).toBeVisible()
  const actual=await expected(request,{product_key:8})
  expect(actual.canceled_orders).toBe(3)
  expect(Number(actual.completed_payable)).toBe(57615)
})

test('shelf-life is explicitly hypothetical with no preset expiry or batch controls',async({page})=>{
  await page.goto('/dss')
  await page.getByRole('tab',{name:'Mô phỏng HSD',exact:true}).click()
  await expect(page.getByText(/Dataset không có NSX, HSD hoặc dữ liệu lô hàng/)).toBeVisible()
  await expect(page.getByLabel('Giả định hạn dùng còn lại (ngày)',{exact:true})).toHaveValue('')
  await expect(page.getByRole('button',{name:'Chạy và so sánh kịch bản',exact:true})).toBeHidden()
  let requests=0
  page.on('request',r=>{if(r.url().endsWith('/dss/shelf-life')) requests++})
  await page.getByRole('button',{name:'Chạy mô phỏng hạn dùng',exact:true}).click()
  await expect(page.getByText(/Nhập số ngày hạn dùng còn lại giả định/)).toBeVisible()
  expect(requests).toBe(0)
})
