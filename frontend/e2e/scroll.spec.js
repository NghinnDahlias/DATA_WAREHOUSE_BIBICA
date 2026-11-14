import { test, expect } from '@playwright/test'
import fs from 'node:fs'

async function fit(panel, records, name, width) {
  await expect(panel).toBeVisible()
  const m = await panel.evaluate((e) => ({height:e.clientHeight, overflow:e.scrollHeight-e.clientHeight, horizontal:e.scrollWidth-e.clientWidth}))
  records.push({name,width,...m})
  expect(m.height).toBeGreaterThan(100)
  expect(m.overflow, `${width} ${name}`).toBeLessThanOrEqual(4)
  expect(m.horizontal, `${width} ${name}`).toBeLessThanOrEqual(4)
}

test('expanded themes and every scenario parameter group fit desktop panels', async ({ page }) => {
  const measurements = []
  try {
    for (const [width,height] of [[1366,768],[1280,720],[1846,867]]) {
      await page.setViewportSize({width,height})
      await page.goto('/customer')
      await expect(page.locator('.kpi-value').first()).toBeVisible()
      await page.getByRole('tab', {name:'Chủ đề đánh giá',exact:true}).click()
      await expect(page.locator('.rt-stat-value').first()).toBeVisible()
      await fit(page.getByRole('tabpanel',{name:'Chủ đề và bảng',exact:true}),measurements,'Chủ đề và bảng',width)
      await expect(page.locator('.theme-paired .rt-bars')).toBeVisible()
      await expect(page.locator('.theme-paired table')).toBeVisible()
      await page.goto('/dss')
      await page.getByRole('button',{name:'Tạo batch mẫu',exact:true}).click()
      await expect(page.locator('.order-card').first()).toBeVisible()
      await page.getByRole('tab',{name:'Tham số kịch bản',exact:true}).click()
      const scenarios=await page.getByRole('tablist',{name:'Chọn kịch bản',exact:true}).getByRole('tab').allTextContents()
      for(const scenario of scenarios) {
        await page.getByRole('tablist',{name:'Chọn kịch bản',exact:true}).getByRole('tab',{name:scenario,exact:true}).click()
        for(const [tab,name] of [['Tồn kho & HSD','Tồn kho và hạn dùng'],['Năng lực & giới hạn','Năng lực và giới hạn'],['Điểm rủi ro','Điểm rủi ro'],['Ngoại lệ bữa sáng','Ngoại lệ bữa sáng']]) {
          await page.getByRole('tablist',{name:'Nhóm tham số',exact:true}).getByRole('tab',{name:tab,exact:true}).click()
          await fit(page.getByRole('tabpanel',{name,exact:true}),measurements,`${scenario} ${name}`,width)
        }
      }
      await page.getByRole('button',{name:'Chạy và so sánh kịch bản',exact:true}).click()
      await expect(page.getByRole('heading',{name:'So sánh kịch bản',exact:true})).toBeVisible()
      await fit(page.getByRole('tabpanel',{name:'So sánh kịch bản',exact:true}),measurements,'Kết quả so sánh',width)
      await page.getByRole('tab',{name:'Phân bổ & giải thích',exact:true}).click()
      await page.locator('tr.clickable').filter({hasText:'DEMO0'}).click()
      await expect(page.locator('.cand')).toHaveCount(1)
      await fit(page.getByRole('tabpanel',{name:'Phân bổ từng đơn',exact:true}),measurements,'Giải thích phân bổ',width)
      if(width===1366) await page.screenshot({path:'../.runtime/scroll-dss-explanation.png'})
    }
  } finally {
    fs.writeFileSync('../reports/scroll_detail_layouts.json',JSON.stringify(measurements,null,2))
  }
})

test('switching parameter groups retains edits in the submitted scenario', async ({ page }) => {
  await page.goto('/dss')
  await page.getByRole('button',{name:'Tạo batch mẫu',exact:true}).click()
  await expect(page.locator('.order-card').first()).toBeVisible()
  await page.getByRole('tab',{name:'Tham số kịch bản',exact:true}).click()
  await page.getByLabel('Số lượng tồn, đơn vị sản phẩm',{exact:true}).first().fill('42')
  await page.getByRole('tablist',{name:'Nhóm tham số',exact:true}).getByRole('tab',{name:'Điểm rủi ro',exact:true}).click()
  await page.getByRole('tablist',{name:'Chọn kịch bản',exact:true}).getByRole('tab',{name:'Phương án 1',exact:true}).click()
  await page.getByRole('tablist',{name:'Chọn kịch bản',exact:true}).getByRole('tab',{name:'Kịch bản gốc',exact:true}).click()
  await expect(page.getByLabel('Số lượng tồn, đơn vị sản phẩm',{exact:true}).first()).toHaveValue('42')
  const sent=page.waitForResponse(r=>r.url().endsWith('/dss/allocate'))
  await page.getByRole('button',{name:'Chỉ chạy phương án gốc',exact:true}).click()
  const response=await sent
  expect(response.status()).toBe(200)
  expect(response.request().postDataJSON().scenario.stocks[0].units).toBe(42)
})

test('batch paging reaches new orders and preserves the existing batch', async ({ page }) => {
  await page.goto('/dss')
  await page.getByRole('button',{name:'Tạo batch mẫu',exact:true}).click()
  await expect(page.locator('.order-card')).toHaveCount(4)
  await page.getByRole('button',{name:'Thêm đơn',exact:true}).click()
  await expect(page.locator('.order-card')).toHaveCount(1)
  await page.locator('.order-card').getByRole('button',{name:/^Xóa đơn /}).click()
  await expect(page.locator('.order-card')).toHaveCount(4)
  await expect(page.getByText('DEMO0',{exact:true})).toBeVisible()
})
