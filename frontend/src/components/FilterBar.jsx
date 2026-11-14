import { RotateCcw, SlidersHorizontal, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { useFilters } from '../context/FilterContext.jsx'
import { addDays } from '../lib/dates.js'
import { STATUS_LABELS } from '../lib/kpis.js'
import ProductPicker from './ProductPicker.jsx'

function Select({label,value,onChange,children}) {
  return <label className="field"><span>{label}</span><select aria-label={label} value={value||'all'} onChange={e=>onChange(e.target.value)}>{children}</select></label>
}

export default function FilterBar() {
  const {meta,filters,update,reset,maturityEnd}=useFilters()
  const [more,setMore]=useState(false)
  const [expanded,setExpanded]=useState(false)
  const dialog=useRef(null),trigger=useRef(null)
  useEffect(()=>{
    if(!more)return
    const previous=document.activeElement
    dialog.current?.querySelector('button,select,input')?.focus()
    const key=e=>{
      if(e.key==='Escape'){setMore(false);return}
      if(e.key!=='Tab')return
      const items=[...dialog.current.querySelectorAll('button:not(:disabled),input,select')].filter(x=>x.getClientRects().length)
      const first=items[0],last=items.at(-1)
      if(e.shiftKey&&document.activeElement===first){e.preventDefault();last?.focus()}
      else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first?.focus()}
    }
    document.addEventListener('keydown',key)
    return ()=>{document.removeEventListener('keydown',key);previous?.focus()}
  },[more])
  const presets=[['30 ngày',addDays(maturityEnd,-29),maturityEnd],['90 ngày',addDays(maturityEnd,-89),maturityEnd],['1 năm',addDays(maturityEnd,-364),maturityEnd],['Toàn bộ',meta.dateRange.min,meta.dateRange.max]]
  const regions=[...new Set(meta.warehouses.map(w=>w.region))]
  const stores=meta.stores.filter(s=>filters.channel==='all'||s.channel.toUpperCase()===filters.channel)
  const active=[
    ['store',filters.store!=='all'&&meta.stores.find(s=>s.code===filters.store)?.label],
    ['category',filters.category!=='all'&&filters.category],['province',filters.province&&filters.province!=='all'&&filters.province],
    ['status',filters.status&&filters.status!=='all'&&STATUS_LABELS[filters.status]],
    ['region',filters.region!=='all'&&`Kho ${filters.region}`],
    ['warehouse',filters.warehouse!=='all'&&meta.warehouses.find(w=>String(w.key)===String(filters.warehouse))?.name],
    ['product',filters.product?.label],
  ].filter(([,label])=>label)
  return <>
    <div className={`filterbar analytical-filterbar ${expanded?'filters-expanded':''}`} role="search" aria-label="Bộ lọc dữ liệu">
      <button className="filter-disclosure" aria-expanded={expanded} onClick={()=>setExpanded(v=>!v)}>Bộ lọc {expanded?'−':'+'}</button>
      <label className="field date-field"><span>Từ</span><input aria-label="Từ ngày" type="date" value={filters.from} min={meta.dateRange.min} max={filters.to} onChange={e=>e.target.value&&update({from:e.target.value})}/></label>
      <label className="field date-field"><span>Đến</span><input aria-label="Đến ngày" type="date" value={filters.to} min={filters.from} max={meta.dateRange.max} onChange={e=>e.target.value&&update({to:e.target.value})}/></label>
      <Select label="Kênh" value={filters.channel} onChange={channel=>update({channel})}><option value="all">Tất cả nền tảng</option><option value="SHOPEE">Shopee</option><option value="TIKTOK">TikTok</option></Select>
      <div className="presets" role="group" aria-label="Khoảng thời gian nhanh">{presets.map(([label,from,to])=><button key={label} className={filters.from===from&&filters.to===to?'on':''} onClick={()=>update({from,to})}>{label}</button>)}</div>
      <button ref={trigger} className="more-filters" aria-label="Lọc thêm" aria-haspopup="dialog" aria-expanded={more} onClick={()=>setMore(true)}><SlidersHorizontal size={15}/> Bộ lọc{active.length>0&&<b>{active.length}</b>}</button>
      <button className="reset" aria-label="Đặt lại" title="Đặt lại bộ lọc" onClick={reset}><RotateCcw size={17}/></button>
      {active.length>0&&<div className="filter-tokens" aria-label="Bộ lọc đang dùng">{active.map(([key,label])=><button key={key} title={label} aria-label={`Bỏ lọc ${key}`} onClick={()=>update({[key]:key==='product'?null:'all'})}><span>{label}</span><X size={12}/></button>)}</div>}
    </div>
    {more&&createPortal(<div className="filter-backdrop" onMouseDown={e=>e.target===e.currentTarget&&setMore(false)}>
      <section className="filter-dialog" ref={dialog} role="dialog" aria-modal="true" aria-label="Bộ lọc chuyên sâu">
        <header><h2>Bộ lọc</h2><button className="icon-btn" aria-label="Đóng bộ lọc" onClick={()=>setMore(false)}><X size={19}/></button></header>
        <div className="filter-dialog-grid">
          <Select label="Cửa hàng" value={filters.store} onChange={store=>update({store})}><option value="all">Tất cả cửa hàng</option>{stores.map(s=><option key={s.code} value={s.code}>{s.label}</option>)}</Select>
          <Select label="Danh mục" value={filters.category} onChange={category=>update({category})}><option value="all">Tất cả danh mục</option>{meta.categories.map(c=><option key={c}>{c}</option>)}</Select>
          <Select label="Trạng thái" value={filters.status} onChange={status=>update({status})}><option value="all">Tất cả trạng thái</option>{Object.entries(STATUS_LABELS).map(([v,l])=><option key={v} value={v}>{l}</option>)}</Select>
          <Select label="Tỉnh khách" value={filters.province} onChange={province=>update({province})}><option value="all">Tất cả tỉnh/thành</option>{meta.provinces.map(p=><option key={p}>{p}</option>)}</Select>
          <Select label="Vùng kho" value={filters.region} onChange={region=>update({region})}><option value="all">Tất cả vùng kho</option>{regions.map(r=><option key={r} value={r}>{r}</option>)}</Select>
          <Select label="Kho" value={filters.warehouse} onChange={warehouse=>update({warehouse})}><option value="all">Tất cả kho</option>{meta.warehouses.filter(w=>{
            const s=meta.stores.find(s=>s.key===w.storeKey)
            return (filters.store==='all'||s?.code===filters.store)&&(filters.channel==='all'||s?.channel.toUpperCase()===filters.channel)&&(filters.region==='all'||w.region===filters.region)
          }).map(w=><option key={w.key} value={w.key}>{meta.stores.find(s=>s.key===w.storeKey)?.label} · {w.name}</option>)}</Select>
          <div className="filter-product"><ProductPicker label="Sản phẩm" value={filters.product} onChange={product=>update({product})} baseFilters={filters}/></div>
        </div>
        <footer><button className="reset" onClick={reset}><RotateCcw size={15}/>Đặt lại</button><button className="primary" onClick={()=>setMore(false)}>Xong</button></footer>
      </section>
    </div>,document.body)}
  </>
}
