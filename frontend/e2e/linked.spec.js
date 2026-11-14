import {test,expect} from '@playwright/test'
import fs from 'node:fs'
const orders=p=>p.locator('.kpi').filter({has:p.locator('.kpi-label',{hasText:'Đơn đặt'})}).first().locator('.kpi-value')
const fmt=n=>Number(n).toLocaleString('vi-VN')
const loaded=async p=>{await expect(p.locator('.overview-grid')).toBeVisible();await expect(p.locator('.body.loading')).toHaveCount(0)}
const filter=async p=>p.getByRole('button',{name:'Lọc thêm',exact:true}).click()

test('overview links charts, month selection, insights and removable filters to actual KPI cohorts',async({page,request})=>{
 await page.goto('/overview');await loaded(page)
 await expect(page.getByRole('tablist')).toHaveCount(0)
 await expect(page.locator('.dashboard-card')).toHaveCount(4)
 await page.getByRole('button',{name:'Lọc Bibica Official Store',exact:true}).click()
 await expect(page.getByRole('button',{name:'Bỏ lọc store'})).toBeVisible();await loaded(page)
 let expected=(await (await request.get('/api/v1/overview/kpis',{params:{store:'bibica_official_store',start_date:await page.getByLabel('Từ ngày').inputValue(),end_date:await page.getByLabel('Đến ngày').inputValue()}})).json()).data
 await expect(orders(page)).toHaveText(fmt(expected.orders))
 await page.getByRole('button',{name:'Lọc Bánh',exact:true}).click();await loaded(page)
 await expect(page.getByRole('button',{name:'Bỏ lọc category'})).toBeVisible()
 await page.locator('.overview-trend .recharts-area-dot').nth(1).click();await loaded(page)
 await expect(page.getByLabel('Từ ngày')).toHaveValue('2026-07-01')
 await page.getByLabel('Lọc theo tháng',{exact:true}).selectOption('2026-07');await loaded(page)
 await expect(page.getByLabel('Từ ngày')).toHaveValue('2026-07-01')
 await expect(page.getByLabel('Đến ngày')).toHaveValue('2026-07-31')
 expected=(await (await request.get('/api/v1/overview/kpis',{params:{store:'bibica_official_store',category:'Bánh',start_date:'2026-07-01',end_date:'2026-07-31'}})).json()).data
 await expect(orders(page)).toHaveText(fmt(expected.orders))
 await page.getByRole('button',{name:'Bỏ lọc category'}).click();await loaded(page)
 await expect(page.getByRole('button',{name:'Bỏ lọc store'})).toBeVisible()
 const insight=page.locator('.insight-ribbon button').filter({hasText:'hủy'}).first()
 await insight.click();await loaded(page)
 await expect(page.getByRole('button',{name:'Bỏ lọc status'})).toContainText('Đã hủy')
 await filter(page)
 await expect(page.getByLabel('Trạng thái',{exact:true})).toHaveValue('CANCELED')
 await page.getByRole('button',{name:'Xong',exact:true}).click()
})

test('advanced filters scope warehouse independently from customer province and survive navigation',async({page,request})=>{
 await page.goto('/overview');await loaded(page)
 await page.getByRole('button',{name:'Toàn bộ',exact:true}).click();await loaded(page)
 await page.getByLabel('Kênh',{exact:true}).selectOption('SHOPEE');await loaded(page)
 await filter(page)
 await page.getByLabel('Cửa hàng',{exact:true}).selectOption('bibica_official_store')
 await page.getByLabel('Danh mục',{exact:true}).selectOption('Bánh')
 await page.getByLabel('Tỉnh khách',{exact:true}).selectOption('Hà Nội')
 await page.getByLabel('Trạng thái',{exact:true}).selectOption('COMPLETED')
 await page.getByLabel('Vùng kho',{exact:true}).selectOption('Hồ Chí Minh')
 const options=await page.getByLabel('Kho',{exact:true}).locator('option').evaluateAll(xs=>xs.map(x=>({value:x.value,label:x.label})))
 expect(options.filter(x=>x.value!=='all').every(x=>x.label.includes('Bibica Official Store')&&x.label.includes('Hồ Chí Minh'))).toBe(true)
 const key=options.find(x=>x.value!=='all').value
 await page.getByLabel('Kho',{exact:true}).selectOption(key)
 await page.keyboard.press('Escape');await loaded(page)
 await expect(page.getByRole('dialog')).toHaveCount(0)
 const params={channel:'SHOPEE',store:'bibica_official_store',category:'Bánh',province:'Hà Nội',status:'COMPLETED',warehouse_region:'Hồ Chí Minh',warehouse_key:key}
 const expected=(await (await request.get('/api/v1/overview/kpis',{params})).json()).data
 await expect(orders(page)).toHaveText(fmt(expected.orders))
 await page.getByRole('link',{name:'Sales Performance',exact:true}).click()
 await expect(orders(page)).toHaveText(fmt(expected.orders))
 await filter(page)
 await expect(page.getByLabel('Tỉnh khách',{exact:true})).toHaveValue('Hà Nội')
 await expect(page.getByLabel('Kho',{exact:true})).toHaveValue(key)
 await page.getByRole('button',{name:'Xong',exact:true}).click()
})

test('overview SKU drilldown retains identity, incompatible category is empty, API error clears stale metrics',async({page,request})=>{
 await page.goto('/overview');await loaded(page)
 const chosen=page.waitForResponse(r=>r.url().includes('/overview/dashboard')&&r.url().includes('product_key='))
 await page.locator('.overview-products tbody tr').first().press('Enter')
 const data=(await (await chosen).json()).data
 await expect(orders(page)).toHaveText(fmt(data.kpis.orders))
 await expect(page.getByRole('button',{name:'Bỏ lọc product'})).toBeVisible()
 await filter(page)
 await expect(page.getByRole('button',{name:'Đổi sản phẩm'})).toContainText('SKU')
 const productKey=Number(new URL((await chosen).url()).searchParams.get('product_key'))
 const original=(await (await request.get('/api/v1/products',{params:{product_key:productKey}})).json()).data[0]
 const incompatible=['Bánh','Kẹo','Ngũ cốc','Quà tặng'].find(c=>!original.historical_categories.includes(c))
 await page.getByLabel('Danh mục',{exact:true}).selectOption(incompatible)
 await page.getByRole('button',{name:'Xong',exact:true}).click()
 await expect(page.getByText(/Không có dữ liệu khớp bộ lọc/)).toBeVisible()
 await expect(page.locator('.overview-grid')).toHaveCount(0)
 await page.route('**/api/v1/overview/dashboard*',r=>r.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'Database unavailable'})}))
 await page.getByRole('button',{name:'Đặt lại',exact:true}).click()
 await expect(page.locator('.notice.err')).toBeVisible()
 await expect(page.locator('.kpi')).toHaveCount(0)
})

test('linked dashboards keep charts and numeric columns visible across desktop sizes',async({page})=>{
 const measures=[]
 for(const [width,height] of [[1280,720],[1366,768],[1846,867]]){
  await page.setViewportSize({width,height});await page.goto('/overview');await loaded(page)
  await expect(page.locator('.overview-products th')).toHaveCount(3)
  const record=await page.evaluate(()=>({width:innerWidth,height:innerHeight,docX:document.documentElement.scrollWidth-innerWidth,docY:document.documentElement.scrollHeight-innerHeight,
    cards:[...document.querySelectorAll('.dashboard-card')].map(e=>({class:e.className,overflow:e.scrollHeight-e.clientHeight})),tables:[...document.querySelectorAll('.data-surface .table-wrap')].map(e=>({x:e.scrollWidth-e.clientWidth})),board:document.querySelector('.overview-grid').getBoundingClientRect().toJSON()}))
  expect(record.docX).toBeLessThanOrEqual(1);expect(record.docY).toBeLessThanOrEqual(1)
  expect(record.cards.every(c=>c.overflow<=3)).toBe(true)
  expect(record.tables.every(t=>t.x<=1)).toBe(true)
  expect(record.board.bottom).toBeLessThanOrEqual(height)
  measures.push(record)
  await page.screenshot({path:`../.runtime/linked-overview-${width}.png`})
  await page.goto('/sales');await page.getByRole('tab',{name:'Danh mục & vùng kho',exact:true}).click()
  await expect(page.locator('.chart-table:visible')).toHaveCount(2)
  await expect(page.getByRole('group',{name:'Danh mục theo sản lượng'})).toBeVisible()
  await page.getByRole('tab',{name:'Tỉnh nhận hàng',exact:true}).click()
  await expect(page.locator('.chart-table')).toHaveCount(1)
  await expect(page.getByRole('group',{name:'Đơn theo tỉnh khách'})).toBeVisible()
 }
 fs.writeFileSync('../reports/linked_board_layouts.json',JSON.stringify(measures,null,2))
})
