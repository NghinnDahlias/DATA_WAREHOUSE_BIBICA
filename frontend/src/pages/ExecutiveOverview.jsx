import {useState} from 'react'
import {Area,ComposedChart,CartesianGrid,Legend,Line,ResponsiveContainer,Tooltip,XAxis,YAxis} from 'recharts'
import {Calculator} from 'lucide-react'
import IndicatorStats from '../components/IndicatorStats.jsx'
import {useFilters} from '../context/FilterContext.jsx'
import {useReport} from '../hooks/useReport.js'
import {getOverviewDashboard} from '../api/client.js'
import {Page,Section} from '../components/Page.jsx'
import {KpiRow} from '../components/KpiStrip.jsx'
import ChartTable from '../components/ChartTable.jsx'
import LinkedChart,{CATEGORY_COLORS} from '../components/LinkedChart.jsx'
import {storeColor} from '../lib/colors.js'
import {fmtAxis,fmtInt,fmtPct,fmtPeriod,fmtVND} from '../lib/format.js'
import {standardKpis,qualityNotes} from '../lib/kpis.js'
import {storeLabel} from '../lib/shape.js'
import {monthSelection} from '../lib/overview.js'
import {productIdentity} from '../lib/productIdentity.js'

export default function ExecutiveOverview() {
  const {filters,update}=useFilters()
  const [byStore,setByStore]=useState(false)
  const [statistics,setStatistics]=useState(false)
  const state=useReport(()=>getOverviewDashboard(filters),[filters])
  const money=v=>v==null?'—':`${fmtVND(v)} ₫`
  return <><Page title="Tổng quan" state={state} actions={<button className="feature-trigger" onClick={()=>setStatistics(true)}><Calculator size={15}/>Thống kê chỉ số</button>}>{d=>{
    const selectProduct=r=>update({product:{key:r.key,label:r.name,store:r.store,sku:r.sku,variation:r.variation}})
    const products=d.products.map((p,i)=>({key:p.product_key,name:p.product_name,plotName:`#${i+1} · ${p.variation_name||p.product_name}`,store:p.storefront_code,sku:p.native_sku_id,variation:p.variation_name,units:p.completed_units,value:p.completed_item_value,orders:p.orders}))
    const stores=d.stores.map(r=>({key:r.group_value,name:storeLabel(r.group_value),value:r.completed_payable,orders:r.orders,cancelRate:r.orders?r.canceled_orders/r.orders:null})).sort((a,b)=>(b.value??-1)-(a.value??-1))
    const categories=d.categories.map(r=>({key:r.group_value,name:r.group_value??'Chưa phân loại',units:r.completed_units,value:r.completed_observed_item_payable,orders:r.orders})).sort((a,b)=>(b.units??0)-(a.units??0))
    const columns=[{accessorKey:'name',header:'Sản phẩm / SKU',cell:c=><span className="product-cell" title={`${c.getValue()} — ${productIdentity(c.row.original)}`}><span>{c.getValue()}</span></span>},
      {accessorKey:'units',header:'SL bán',cell:c=>fmtInt(c.getValue()),meta:{align:'right'}},
      {accessorKey:'value',header:'Tiền dòng',cell:c=>money(c.getValue()),meta:{align:'right'}}]
    return <div className="overview-board">
      <KpiRow items={standardKpis(d.kpis,Boolean(filters.product))}/>
      <div className="overview-grid">
        <section className="dashboard-card overview-trend"><Section title="Diễn biến giá trị đơn hoàn thành" note="Theo tháng đặt hàng, mỗi đơn một lần. Bấm điểm để lọc trong tháng. Tháng đầu/cuối có thể chưa đủ; tháng thiếu dữ liệu để trống, không tự gán0."
          aside={<><div className="toggle"><button aria-pressed={!byStore} className={!byStore?'on':''} onClick={()=>setByStore(false)}>Tổng</button><button aria-pressed={byStore} className={byStore?'on':''} onClick={()=>setByStore(true)}>Theo cửa hàng</button></div></>}>
          <div className="board-chart" role="group" aria-label="Xu hướng tương tác"><ResponsiveContainer width="100%" height="100%"><ComposedChart data={d.monthly} margin={{top:8,right:16,left:0,bottom:0}} onClick={e=>e?.activeLabel&&update(monthSelection(e.activeLabel,filters))}>
            <CartesianGrid stroke="#e7edf2" vertical={false}/><XAxis dataKey="period" tickFormatter={fmtPeriod} tick={{fontSize:11,fill:'#53697d'}} tickLine={false} axisLine={false} minTickGap={26}/>
            <YAxis tickFormatter={fmtAxis} tick={{fontSize:11,fill:'#53697d'}} tickLine={false} axisLine={false} width={58}/>
            <Tooltip contentStyle={{border:'1px solid #d7e4ed',borderRadius:6}} labelFormatter={fmtPeriod} formatter={(v,n)=>[money(v),n==='total'?'Tiền hoàn thành':n]}/>
            {byStore&&<Legend wrapperStyle={{fontSize:11}}/>}
            {byStore?d.names.map(name=><Line key={name} dataKey={name} type="linear" stroke={storeColor(name)} strokeWidth={2} dot={{r:3}} activeDot={{r:5}} isAnimationActive={false}/>):<Area type="linear" dataKey="total" stroke="#138d80" fill="#138d8014" strokeWidth={2.3} dot={{r:3,fill:'white',strokeWidth:2}} activeDot={{r:5}} isAnimationActive={false}/>}
          </ComposedChart></ResponsiveContainer></div>
        </Section></section>
        <section className="dashboard-card overview-stores"><Section title="Đóng góp cửa hàng" note="Tiền đơn hoàn thành. Các cửa hàng là nhóm không trùng nhau; bấm cột để lọc toàn dashboard.">
          <LinkedChart rows={stores} onSelect={r=>update({store:r.key})} color={r=>storeColor(r.name)} format={money} label="Đóng góp cửa hàng"/>
          <div className="store-summary">{stores.map(r=><button key={r.key} onClick={()=>update({store:r.key})}><i style={{background:storeColor(r.name)}}/><span>{r.name}</span><b>{fmtPct(d.kpis.completedPayable>0?r.value/d.kpis.completedPayable:null)}</b></button>)}</div>
        </Section></section>
        <section className="dashboard-card overview-products"><Section title="SKU nổi bật" note="Top8SKU theo số lượng hoàn thành. Tiền dòng là giá trị quan sát riêng của SKU, không phải tiền toàn đơn. Bấm cột hoặc dòng để lọc; không gộp SKU trùng tên.">
          <ChartTable rows={products} columns={columns} onSelect={selectProduct} valueKey="units" label="SKU theo sản lượng" minPageSize={1}/>
        </Section></section>
        <section className="dashboard-card overview-categories"><Section title="Cơ cấu sản lượng" note="Danh mục lịch sử trên dòng hàng, cùng quy tắc tên cho cả3nguồn. Đơn có thể chứa nhiều danh mục; không cộng số đơn giữa nhóm.">
          <LinkedChart rows={categories} valueKey="units" color={r=>CATEGORY_COLORS[r.name]} onSelect={r=>r.key&&update({category:r.key})} label="Sản lượng theo danh mục"/>
          <div className="category-totals">{categories.map(r=><button key={r.name} disabled={!r.key} onClick={()=>update({category:r.key})}><i style={{background:CATEGORY_COLORS[r.name]}}/><span>{r.name}</span><b>{fmtInt(r.units)}</b></button>)}</div>
        </Section></section>
      </div>
      {qualityNotes(d.kpis).length>0&&<details className="board-quality"><summary>{qualityNotes(d.kpis).length} lưu ý dữ liệu</summary>{qualityNotes(d.kpis).map(n=><p key={n.title}>{n.title}. {n.detail}</p>)}</details>}
    </div>
  }}</Page>{statistics&&<IndicatorStats onClose={()=>setStatistics(false)}/>}</>
}
