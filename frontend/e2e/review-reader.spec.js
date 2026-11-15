import {test,expect} from '@playwright/test'
import fs from 'node:fs'
const ready=async page=>{await expect(page.locator('.body.loading')).toHaveCount(0);await expect(page.locator('.notice.err')).toHaveCount(0)}
const full=async page=>{await page.getByRole('button',{name:'Toàn bộ',exact:true}).click();await ready(page)}

test('overview statistics follow filters in a modal; column tooltip is readable and inside viewport',async({page,request})=>{
 await page.goto('/overview');await expect(page.locator('.overview-grid')).toBeVisible();await ready(page)
 await expect(page.locator('.insight-ribbon')).toHaveCount(0)
 await expect(page.getByLabel('Lọc theo tháng')).toHaveCount(0)
 const trigger=page.getByRole('button',{name:'Thống kê chỉ số',exact:true})
 await trigger.click();const dialog=page.getByRole('dialog',{name:'Thống kê chỉ số'})
 await expect(dialog.getByRole('heading',{name:'So sánh cửa hàng'})).toBeVisible()
 const from=await page.getByLabel('Từ ngày').inputValue(),to=await page.getByLabel('Đến ngày').inputValue()
 const k=(await (await request.get('/api/v1/overview/kpis',{params:{start_date:from,end_date:to}})).json()).data
 await expect(dialog.locator('.indicator-metrics>div').filter({hasText:'Đơn đặt'}).first().locator('strong')).toHaveText(Number(k.orders).toLocaleString('vi-VN'))
 await page.keyboard.press('Escape');await expect(dialog).toHaveCount(0);await expect(trigger).toBeFocused()
 await page.getByRole('button',{name:'Lọc Bibica TikTok Shop',exact:true}).hover()
 const tip=page.getByRole('tooltip');await expect(tip).toBeVisible()
 const measured=await tip.evaluate(e=>{const a=e.querySelector('strong').getBoundingClientRect(),b=e.querySelector('div').getBoundingClientRect(),r=e.getBoundingClientRect();return {separated:a.bottom<=b.top,x:r.left>=0&&r.right<=innerWidth,y:r.top>=0&&r.bottom<=innerHeight,lineHeight:getComputedStyle(e).lineHeight}})
 expect(measured.separated).toBe(true);expect(measured.x&&measured.y).toBe(true);expect(parseFloat(measured.lineHeight)).toBeGreaterThan(15)
 await page.mouse.move(1,1);await page.screenshot({path:'../.runtime/review-ui-overview.png'})
})

test('negative review reader reconciles counts, pages and reads redacted opinions by topic',async({page,request})=>{
 const errors=[];page.on('pageerror',e=>errors.push(e.message))
 await page.goto('/customer');await expect(page.getByRole('tab',{name:'Đánh giá tiêu cực · đọc ý kiến'})).toBeVisible();await full(page)
 const k=(await (await request.get('/api/v1/overview/kpis')).json()).data
 await page.getByRole('button',{name:'Đọc đánh giá tiêu cực',exact:true}).click()
 await expect(page.locator('.case-controls>strong')).toHaveText(`${Number(k.low_reviews).toLocaleString('vi-VN')} đánh giá`)
 await expect(page.locator('.case-detail[aria-busy="false"]')).toBeVisible()
 await expect(page.locator('.case-list-item[aria-pressed="true"]')).toHaveCount(1)
 await page.locator('.case-list-item').nth(1).click();await expect(page.locator('.case-list-item').nth(1)).toHaveAttribute('aria-pressed','true')
 await page.getByRole('button',{name:'Sau',exact:true}).click();await expect(page.locator('.case-pagination>span')).toContainText('5–8')
 await page.getByLabel('Chủ đề tiêu cực').selectOption('packaging_damage_mention')
 const expected=(await (await request.get('/api/v1/customer/review-cases',{params:{topic:'packaging_damage_mention'}})).json()).data
 await expect(page.locator('.case-controls>strong')).toHaveText(`${expected.total} đánh giá`)
 await expect(page.locator('.case-pagination>span')).toContainText('1–')
 await expect(page.locator('.case-detail[aria-busy="false"]')).toBeVisible()
 const values=await page.locator('.case-detail blockquote').count()
 expect(values).toBe(1)
 await expect(page.locator('.case-redaction-note')).toBeVisible()
 await page.getByLabel('Mức sao tiêu cực').selectOption('1')
 const onlyOne=(await (await request.get('/api/v1/customer/review-cases',{params:{topic:'packaging_damage_mention',stars_max:1}})).json()).data
 await expect(page.locator('.case-controls>strong')).toHaveText(`${onlyOne.total} đánh giá`)
 expect(errors).toEqual([])
})

test('review theme chart and negative counter open the corresponding reading popup',async({page,request})=>{
 await page.goto('/customer');await expect(page.getByRole('tab',{name:'Chủ đề đánh giá',exact:true})).toBeVisible();await full(page)
 await page.getByRole('tab',{name:'Chủ đề đánh giá',exact:true}).click();await expect(page.locator('.rt-bars')).toBeVisible()
 await page.locator('button.rt-bar-item').filter({hasText:'Bao bì hư hỏng'}).click()
 const dialog=page.getByRole('dialog',{name:'Đánh giá tiêu cực · đọc ý kiến'})
 await expect(dialog.getByLabel('Chủ đề tiêu cực')).toHaveValue('packaging_damage_mention')
 const themes=(await (await request.get('/api/v1/customer/review-themes')).json()).data
 const n=themes.labels.find(r=>r.label==='packaging_damage_mention').negative_mentions
 await expect(dialog.locator('.case-controls>strong')).toHaveText(`${n} đánh giá`)
 await expect(dialog.locator('.case-detail[aria-busy="false"]')).toBeVisible()
 await page.keyboard.press('Escape');await expect(dialog).toHaveCount(0)
 await page.getByRole('button',{name:/Đánh giá 1–2 sao/}).click()
 await expect(dialog.getByLabel('Chủ đề tiêu cực')).toHaveValue('')
 await expect(dialog.locator('.case-controls>strong')).toHaveText(`${themes.negative_reviews_le2} đánh giá`)
})

test('overview and negative reader preserve desktop geometry and usable mobile fallback',async({page})=>{
 const measurements=[]
 for(const [width,height] of [[1366,768],[1280,720],[390,844]]){
  await page.setViewportSize({width,height})
  for(const path of ['overview','customer']){
   await page.goto('/'+path);await expect(page.locator('h1')).toBeVisible();await ready(page)
   if(path==='overview')await expect(page.locator('.overview-grid')).toBeVisible()
   if(path==='customer'){
    await page.getByRole('tab',{name:'Đánh giá tiêu cực · đọc ý kiến'}).click()
    await expect(page.locator('.case-detail[aria-busy="false"]')).toBeVisible()
   }
   const m=await page.evaluate(()=>({x:document.documentElement.scrollWidth-innerWidth,y:document.documentElement.scrollHeight-innerHeight,caseListOverflow:document.querySelector('.case-list')?document.querySelector('.case-list').scrollHeight-document.querySelector('.case-list').clientHeight:0,
    panels:[...document.querySelectorAll('.view-panel,.dashboard-card')].map(e=>({x:e.scrollWidth-e.clientWidth,y:e.scrollHeight-e.clientHeight}))}))
   measurements.push({width,height,path,...m})
   expect(m.panels).toHaveLength(path==='overview'?4:1)
   expect(m.x).toBeLessThanOrEqual(1)
   if(width>700){expect(m.y).toBeLessThanOrEqual(1);expect(m.caseListOverflow).toBeLessThanOrEqual(2);for(const p of m.panels){expect(p.x).toBeLessThanOrEqual(2);expect(p.y).toBeLessThanOrEqual(4)}}
   if(width===1366&&path==='customer')await page.screenshot({path:'../.runtime/review-ui-customer.png'})
  }
 }
 fs.writeFileSync('../.runtime/review-reader-layouts.json',JSON.stringify(measurements,null,2))
})
