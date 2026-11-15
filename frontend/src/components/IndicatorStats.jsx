import Modal from './Modal.jsx'
import {useFilters} from '../context/FilterContext.jsx'
import {useReport} from '../hooks/useReport.js'
import {getOverviewDashboard} from '../api/client.js'
import {fmtInt,fmtPct,fmtVND,fmtDate,fmtStar} from '../lib/format.js'
import {storeLabel} from '../lib/shape.js'
import {standardKpis} from '../lib/kpis.js'
import {overviewInsights} from '../lib/overview.js'

export default function IndicatorStats({onClose}) {
  const {filters}=useFilters()
  const {data:d,loading,error}=useReport(()=>getOverviewDashboard(filters),[filters])
  const shopee=filters.channel==='SHOPEE'||['bibica_official_store','quasure_specialized_store'].includes(filters.store)
  return <Modal title="Thống kê chỉ số" onClose={onClose} className="indicator-dialog">
    <p className="dialog-scope">{fmtDate(filters.from)} – {fmtDate(filters.to)} · Theo bộ lọc đang chọn</p>
    {loading?<p role="status">Đang tính chỉ số…</p>:error?<p role="alert">{error}</p>:d&&<>
      <div className="indicator-metrics">{[...standardKpis(d.kpis,Boolean(filters.product)),
        {label:'Số đánh giá TikTok',value:shopee?'—':fmtInt(d.kpis.reviews),note:shopee?'Chưa có nguồn đánh giá Shopee':undefined},
        {label:'Điểm sao trung bình',value:d.kpis.reviews?fmtStar(d.kpis.avgStars):'—'},
        {label:'Đánh giá 1–2 sao',value:d.kpis.reviews?`${fmtInt(d.kpis.lowReviews)} · ${fmtPct(d.kpis.lowReviewRate)}`:'—'},
      ].map(item=><div key={item.label} title={item.note}><span>{item.label}</span><strong>{item.value}</strong></div>)}</div>
      <div className="calculated-insights">{overviewInsights(d).map((r,i)=><p key={i}>{r.kind==='share'?`${storeLabel(r.store)} đóng góp ${fmtPct(r.value)} tiền đơn hoàn thành.`:r.kind==='cancel'?`${storeLabel(r.store)} có tỷ lệ hủy ${fmtPct(r.value)} (${fmtInt(r.canceled)}/${fmtInt(r.n)} đơn).`:`${r.category} chiếm ${fmtPct(r.value)} sản lượng hoàn thành.`}</p>)}</div>
      <h3>So sánh cửa hàng</h3>
      <div className="indicator-table"><table><thead><tr><th>Cửa hàng</th><th>Đơn đặt</th><th>Tiền hoàn thành</th><th>Đóng góp</th><th>Hủy / đơn đặt</th></tr></thead><tbody>{d.stores.map(r=><tr key={r.group_value}><td>{storeLabel(r.group_value)}</td><td>{fmtInt(r.orders)}</td><td>{r.completed_payable==null?'—':`${fmtVND(r.completed_payable)} ₫`}</td><td>{fmtPct(d.kpis.completedPayable>0&&r.completed_payable!=null?r.completed_payable/d.kpis.completedPayable:null)}</td><td>{fmtInt(r.canceled_orders)}/{fmtInt(r.orders)} · {fmtPct(r.orders?r.canceled_orders/r.orders:null)}</td></tr>)}</tbody></table></div>
      <h3>Cơ cấu sản lượng</h3><div className="indicator-table"><table><thead><tr><th>Danh mục</th><th>SL hoàn thành</th><th>Tỷ trọng</th></tr></thead><tbody>{d.categories.map(r=><tr key={r.group_value??'unmapped'}><td>{r.group_value??'Chưa phân loại'}</td><td>{fmtInt(r.completed_units)}</td><td>{fmtPct(d.kpis.completedUnits>0&&r.completed_units!=null?r.completed_units/d.kpis.completedUnits:null)}</td></tr>)}</tbody></table></div>
    </>}
  </Modal>
}
