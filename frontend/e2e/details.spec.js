import {test,expect} from '@playwright/test'
import fs from 'node:fs'
test('all analytical detail panels retain paired visuals without desktop overflow',async({page})=>{
 const records=[]
 try {
  for(const [width,height]of[[1280,720],[1366,768]]) {
   await page.setViewportSize({width,height})
   for(const path of ['sales','warehouse','customer']) {
    await page.goto('/'+path)
    await expect(page.locator('.kpi-value').first()).toBeVisible()
    await expect(page.locator('.body.loading')).toHaveCount(0)
    const tabs=await page.getByRole('tablist').first().getByRole('tab').allTextContents()
    for(const tab of tabs) {
     await page.getByRole('tablist').first().getByRole('tab',{name:tab,exact:true}).click()
     if(path==='sales'&&tab==='Sản phẩm'){
      await page.getByRole('button',{name:'Tải xếp hạng sản phẩm'}).click()
      await expect(page.locator('.sales-product-card .chart-table')).toBeVisible()
     }
     if(path==='customer'&&tab==='Chủ đề đánh giá')await expect(page.locator('.theme-paired .rt-bars')).toBeVisible()
     await expect(page.getByText('Đang tải…',{exact:true})).toHaveCount(0)
     await expect(page.locator('.body.loading')).toHaveCount(0)
     const panels=await page.locator('.view-panel:visible').evaluateAll(xs=>xs.map(e=>({name:e.getAttribute('aria-label'),height:e.clientHeight,vertical:e.scrollHeight-e.clientHeight,horizontal:e.scrollWidth-e.clientWidth})))
     records.push({path,tab,width,height,panels})
     expect(panels.every(p=>p.vertical<=4&&p.horizontal<=4),JSON.stringify(records.at(-1))).toBe(true)
     await page.screenshot({path:`../.runtime/linked-${path}-${tabs.indexOf(tab)}-${width}.png`})
    }
   }
  }
 }finally{fs.writeFileSync('../reports/linked_detail_layouts.json',JSON.stringify(records,null,2))}
})
