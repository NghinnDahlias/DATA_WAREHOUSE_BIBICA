import ViewTabs, { ViewPanel } from '../components/ViewTabs.jsx'
import LinkedChart from '../components/LinkedChart.jsx'
import { Fragment, useMemo, useState } from 'react'
import { Plus, Play, Shuffle, Trash2, TriangleAlert, ChevronDown, ChevronRight } from 'lucide-react'
import { useFilters } from '../context/FilterContext.jsx'
import { dssAllocate, dssSensitivity, dssWhatIf, dssShelfLife, getAllProducts, STORES } from '../api/client.js'
import { Section } from '../components/Page.jsx'
import { KpiRow } from '../components/KpiStrip.jsx'
import ProductPicker from '../components/ProductPicker.jsx'
import { DEFAULT_SCENARIO, buildOrders, buildScenario, reasonText, validateBatch } from '../lib/dss.js'
import { fmtDate, fmtInt, fmtDays, fmtPct } from '../lib/format.js'

const dec = (x, d = 1) => (x == null ? '—' : Number(x).toFixed(d).replace('.', ','))
// Giá trị stock_scope mà API nhận (models.Stock). Giá trị khác bị trả 422.
const STOCK_SCOPES = ['ECOMMERCE', 'WHOLESALE', 'UNVERIFIED']
let seq = 0

function Num({ label, value, onChange, min, max, step = 1, hint, placeholder }) {
  return (
    <label className="param">
      <span className="param-top"><span>{label}</span>
        <span className="param-val"><input type="number" min={min} max={max} step={step} value={value} placeholder={placeholder}
          onChange={(e) => onChange(e.target.value === '' ? '' : Number(e.target.value))} /></span></span>
      {hint && <small>{hint}</small>}
    </label>
  )
}

function ScenarioEditor({ s, set, warehouses, products, onRemove, heading }) {
  const [group, setGroup] = useState('stock')
  const [stockPage, setStockPage] = useState(0)
  const pages = Math.max(1, Math.ceil(s.stocks.length / 3))
  const page = Math.min(stockPage, pages - 1)
  const upd = (patch) => set({ ...s, ...patch })
  const setMap = (field, key, v) => upd({ [field]: { ...s[field], [key]: v } })
  const addStock = () => upd({ stocks: [...s.stocks, { id: ++seq, warehouseKey: warehouses[0]?.key ?? '', productKey: products[0]?.key ?? '', units: '', shelfDays: '', scope: 'ECOMMERCE' }] })
  const setStock = (id, patch) => upd({ stocks: s.stocks.map((x) => (x.id === id ? { ...x, ...patch } : x)) })
  const excs = s.breakfastExceptions || []
  const hcmWarehouse = warehouses.find((w) => w.region === 'Hồ Chí Minh')
  const setExc = (i, patch) => upd({ breakfastExceptions: excs.map((e, j) => (j === i ? { ...e, ...patch } : e)) })
  // Bật ngoại lệ: tự thêm sẵn dòng tồn kho ECOMMERCE cho kho HCM để người dùng chỉ việc điền số lượng và hạn dùng
  const toggleExc = (on) => {
    if (!on) return upd({ breakfastExceptions: [] })
    const productKey = products[0]?.key ?? ''
    const hasStock = s.stocks.some((x) => Number(x.warehouseKey) === Number(hcmWarehouse.key) && Number(x.productKey) === Number(productKey))
    upd({
      breakfastExceptions: [{ warehouseKey: hcmWarehouse.key, productKey, reason: 'APPROVED_ECOMMERCE_EXCEPTION', evidenceRef: '', ecommerceStockConfirmed: false }],
      stocks: hasStock ? s.stocks : [...s.stocks, { id: ++seq, warehouseKey: hcmWarehouse.key, productKey, units: '', shelfDays: '', scope: 'ECOMMERCE' }],
    })
  }
  return (
    <div className="scen-edit">
      <div className="scen-head">
        <div className="scen-title-wrap">
          <strong className="scen-name">{heading}</strong>
        </div>
        {onRemove && <button type="button" className="icon-btn" onClick={onRemove} aria-label="Xóa phương án"><Trash2 size={16} /></button>}
      </div>

      <ViewTabs value={group} onChange={setGroup} label="Nhóm tham số" items={[["stock", "Tồn kho & HSD"], ["capacity", "Năng lực & giới hạn"], ["weights", "Điểm rủi ro"], ["exception", "Ngoại lệ bữa sáng"]]} />
      <ViewPanel active={group === 'stock'} name="Tồn kho và hạn dùng">
      <fieldset className="radio-row">
        <legend>Tồn kho</legend>
        <label><input type="radio" checked={s.stockMode === 'assume_available'} onChange={() => upd({ stockMode: 'assume_available' })} /> Giả định đủ hàng</label>
        <label><input type="radio" checked={s.stockMode === 'required'} onChange={() => upd({ stockMode: 'required' })} /> Nhập tồn kho theo kho/sản phẩm</label>
      </fieldset>

      {s.stockMode === 'required' && (
        <div className="stock-rows">
          {s.stocks.slice(page * 3, (page + 1) * 3).map((x) => (
            <div className="stock-row" key={x.id}>
              <label className="stock-field"><span>Kho áp dụng</span>
                <select value={x.warehouseKey} aria-label="Kho áp dụng" onChange={(e) => setStock(x.id, { warehouseKey: Number(e.target.value) })}>
                  {warehouses.map((w) => <option key={w.key} value={w.key}>{w.name}</option>)}
                </select>
              </label>
              <label className="stock-field"><span>Sản phẩm</span>
                <select value={x.productKey} aria-label="Sản phẩm" title={products.find((p) => p.key === x.productKey)?.label} onChange={(e) => setStock(x.id, { productKey: Number(e.target.value) })}>
                  {products.map((p) => <option key={p.key} value={p.key}>{p.label.slice(0, 40)}</option>)}
                </select>
              </label>
              <label className="stock-field"><span>Số lượng tồn (đơn vị)</span>
                <input type="number" min="0" step="1" value={x.units} aria-label="Số lượng tồn, đơn vị sản phẩm" placeholder="VD: 500" onChange={(e) => setStock(x.id, { units: e.target.value })} />
              </label>
              <label className="stock-field"><span>Hạn sử dụng còn (ngày)</span>
                <input type="number" min="0" max="3650" step="1" value={x.shelfDays ?? ''} aria-label="Số ngày hạn sử dụng còn lại" placeholder="VD: 90" onChange={(e) => setStock(x.id, { shelfDays: e.target.value })} />
              </label>
              <label className="stock-field"><span>Phạm vi tồn kho</span>
                <select value={x.scope || 'ECOMMERCE'} aria-label="Phạm vi tồn kho" onChange={(e) => setStock(x.id, { scope: e.target.value })}>
                  <option value="ECOMMERCE">Tồn kho E-commerce</option>
                  <option value="WHOLESALE">Hàng sỉ (không dùng cho bán qua sàn)</option>
                  <option value="UNVERIFIED">Chưa xác minh</option>
                </select>
              </label>
              <button type="button" className="icon-btn stock-remove" onClick={() => upd({ stocks: s.stocks.filter((y) => y.id !== x.id) })} aria-label="Xóa dòng tồn" title="Xóa dòng tồn"><Trash2 size={15} /></button>
            </div>
          ))}
          {pages > 1 && <div className="table-pagination"><button type="button" disabled={page === 0} onClick={() => setStockPage(page - 1)}>Trước</button><span>{page + 1} / {pages} · {s.stocks.length} dòng tồn</span><button type="button" disabled={page + 1 === pages} onClick={() => setStockPage(page + 1)}>Sau</button></div>}
          <button type="button" className="reset" disabled={!products.length} onClick={() => { addStock(); setStockPage(Math.floor(s.stocks.length / 3)) }}><Plus size={14} /> Thêm dòng tồn kho</button>
          {!products.length && <p className="fine">Thêm sản phẩm vào batch trước khi nhập tồn kho.</p>}
        </div>
      )}

      </ViewPanel>
      <ViewPanel active={group === 'capacity'} name="Năng lực và giới hạn">
      <div className="wh-grid">
        {warehouses.map((w) => (
          <div key={w.key} className="wh-box">
            <b>{w.name}</b>
            <Num label="Công suất (đơn / batch)" value={s.capacity[w.key] ?? ''} min={0} max={100000} placeholder="Không giới hạn" hint="Để trống = không giới hạn · 0 = khóa kho" onChange={(v) => setMap('capacity', w.key, v)} />
            <Num label="Chậm thêm (ngày)" value={s.delay[w.key] ?? ''} min={0} max={90} step={0.5} placeholder="0" onChange={(v) => setMap('delay', w.key, v)} />
          </div>
        ))}
      </div>

      <div className="two">
        <Num label="Giao tối đa (P90, ngày)" value={s.maxDeliveryDays} min={1} max={365} onChange={(v) => upd({ maxDeliveryDays: v })} hint="P90 là mốc 90% đơn lịch sử của tuyến, không phải cam kết giao đúng hạn." />
        <Num label="Điểm rủi ro tối đa" value={s.maxRiskScore} min={0} max={100} onChange={(v) => upd({ maxRiskScore: v })} />
      </div>
      <label className="param">
        <span className="param-top"><span>Ưu tiên giảm rủi ro so với nhanh</span><span className="param-val"><em>{Math.round(s.riskWeight * 100)}% rủi ro</em></span></span>
        <input type="range" min="0" max="1" step="0.05" value={s.riskWeight} onChange={(e) => upd({ riskWeight: Number(e.target.value) })} aria-label="Trọng số rủi ro" />
        <small>0% = chỉ xét thời gian giao, 100% = chỉ xét điểm rủi ro.</small>
      </label>
      </ViewPanel>
      <ViewPanel active={group === 'exception'} name="Ngoại lệ bữa sáng">
      {s.stockMode === 'required' ? (
        <fieldset className="radio-row breakfast-exc">
          <legend>Ngoại lệ sản phẩm bữa sáng</legend>
          <label>
            <input type="checkbox" checked={excs.length > 0} disabled={!hcmWarehouse || !products.length} onChange={(e) => toggleExc(e.target.checked)} />
            Cho phép xuất bánh bữa sáng từ kho TP.HCM (mặc định chỉ xuất từ Hà Nội)
          </label>
          {!products.length && <small>Thêm sản phẩm vào batch trước khi khai ngoại lệ.</small>}
          {excs.map((e, i) => (
            <div className="stock-row" key={i}>
              <label className="stock-field"><span>Kho ngoại lệ</span>
                <select value={e.warehouseKey} onChange={(ev) => setExc(i, { warehouseKey: Number(ev.target.value) })}>
                  {warehouses.filter((w) => w.region === 'Hồ Chí Minh').map((w) => <option key={w.key} value={w.key}>{w.name}</option>)}
                </select>
              </label>
              <label className="stock-field"><span>Sản phẩm</span>
                <select value={e.productKey} title={products.find((p) => p.key === e.productKey)?.label} onChange={(ev) => setExc(i, { productKey: Number(ev.target.value) })}>
                  {products.map((p) => <option key={p.key} value={p.key}>{p.label.slice(0, 40)}</option>)}
                </select>
              </label>
              <label className="stock-field"><span>Loại ngoại lệ</span>
                <select value={e.reason} onChange={(ev) => setExc(i, { reason: ev.target.value })}>
                  <option value="APPROVED_ECOMMERCE_EXCEPTION">Ngoại lệ TMĐT được phê duyệt</option>
                  <option value="HN_STOCKOUT_TRANSFER">Chuyển kho khi Hà Nội hết hàng</option>
                </select>
              </label>
              <label className="stock-field"><span>Mã bằng chứng</span>
                <input value={e.evidenceRef} minLength={3} maxLength={120} placeholder="VD: TICKET-HN-0001" onChange={(ev) => setExc(i, { evidenceRef: ev.target.value })} />
              </label>
              <label className="stock-field"><span>Xác nhận tồn kho E-commerce</span>
                <span><input type="checkbox" checked={e.ecommerceStockConfirmed === true} onChange={(ev) => setExc(i, { ecommerceStockConfirmed: ev.target.checked })} /> Tôi xác nhận kho có tồn kho ECOMMERCE thực tế</span>
              </label>
              <small>Cần có dòng tồn kho ECOMMERCE (kèm hạn dùng còn lại) cho đúng kho và sản phẩm này ở phía trên.</small>
            </div>
          ))}
        </fieldset>
      ) : (
        <p className="fine">Muốn khai hạn dùng còn lại hoặc ngoại lệ bữa sáng, chọn "Nhập tồn kho theo kho/sản phẩm".</p>
      )}
      </ViewPanel>
      <ViewPanel active={group === 'weights'} name="Điểm rủi ro">
      <div className="adv">
        <div className="two">
          <Num label="Trọng số hủy đơn" value={s.wCancel} min={0} max={1} step={0.1} onChange={(v) => upd({ wCancel: v })} />
          <Num label="Trọng số giao trễ" value={s.wLate} min={0} max={1} step={0.1} onChange={(v) => upd({ wLate: v })} />
          <Num label="Trọng số đánh giá thấp" value={s.wLow} min={0} max={1} step={0.1} onChange={(v) => upd({ wLow: v })} />
          <Num label="Ngưỡng trễ (ngày)" value={s.lateThresholdDays} min={1} max={365} onChange={(v) => upd({ lateThresholdDays: v })} />
          <Num label="Số mẫu tối thiểu / tuyến" value={s.minRouteSamples} min={1} max={10000} onChange={(v) => upd({ minRouteSamples: v })} />
          <Num label="Độ mạnh prior" value={s.priorStrength} min={0} max={10000} onChange={(v) => upd({ priorStrength: v })} />
          <Num label="Hạn còn tối thiểu (ngày)" value={s.minRemainingDays} min={0} max={365} onChange={(v) => upd({ minRemainingDays: v })} />
          <Num label="Sao tối đa tính là thấp" value={s.lowStarMax} min={1} max={3} onChange={(v) => upd({ lowStarMax: v })} />
        </div>
      </div>
      </ViewPanel>
    </div>
  )
}

function Result({ res, whName }) {
  const [open, setOpen] = useState(null)
  const [detailView, setDetailView] = useState('summary')
  const [candidateScenario, setCandidateScenario] = useState('0')
  const [orderPage, setOrderPage] = useState(0)
  const scen = [{ title: res.baseline.scenario.label + ' (gốc)', r: res.baseline, cmp: null },
    ...res.alternatives.map((a) => ({ title: a.result.scenario.label, r: a.result, cmp: a.comparison }))]
  const rows = res.baseline.assignments.map((a, i) => ({ ref: a.order_ref, province: a.province, cells: scen.map((s) => s.r.assignments[i]) }))
  const resultPage = Math.min(orderPage, Math.max(0, Math.ceil(rows.length / 5) - 1))
  const whOrders = (r) => Object.entries(r.summary.warehouse_orders).map(([k, n]) => `${whName(Number(k))}: ${n}`).join(' · ') || '—'
  const changed = (ref) => scen.slice(1).some((s) => s.cmp.changed_order_refs.includes(ref))
  const HINTS = {
    MISSING_BREAKFAST_SHELF_LIFE_SCENARIO: 'Bánh bữa sáng cần tồn kho kèm "Hạn sử dụng còn (ngày)": ở mục 03 chọn "Nhập tồn kho theo kho/sản phẩm" rồi điền hạn dùng.',
    MISSING_STOCK_SCENARIO: 'Ở mục 03 chọn "Nhập tồn kho theo kho/sản phẩm" và khai tồn cho kho/sản phẩm này.',
    INSUFFICIENT_SCENARIO_STOCK: 'Tăng số lượng tồn kho hoặc giảm số lượng trong đơn.',
    BREAKFAST_HN_DEFAULT_REQUIRES_EXPLICIT_EXCEPTION: 'Muốn xuất từ kho TP.HCM, khai "Ngoại lệ sản phẩm bữa sáng" ở mục 03.',
    BREAKFAST_HCM_REQUIRES_ECOMMERCE_STOCK: 'Kho TP.HCM cần dòng tồn kho ECOMMERCE cho sản phẩm bữa sáng.',
    SHELF_LIFE_BUFFER: 'Tăng hạn dùng còn lại hoặc giảm "Giao tối đa (P90)".',
    DELIVERY_THRESHOLD: 'Tăng "Giao tối đa (P90)" hoặc giảm độ trễ thêm của kho.',
    RISK_THRESHOLD_OR_MISSING_SCORE: 'Tăng "Điểm rủi ro tối đa" hoặc giảm số mẫu tối thiểu/tuyến.',
    INSUFFICIENT_TIMING_EVIDENCE: 'Tuyến này chưa đủ mẫu lịch sử; giảm "Số mẫu tối thiểu / tuyến" trong tham số nâng cao.',
  }
  const diagnose = (r) => {
    const n = {}
    r.assignments.filter((a) => !a.warehouse_key).forEach((a) => a.candidates.forEach((k) => (k.reasons || []).forEach((c) => { n[c] = (n[c] || 0) + 1 })))
    const top = Object.entries(n).sort((x, y) => y[1] - x[1])[0]?.[0]
    return top ? { top, hint: HINTS[top] } : null
  }
  return (
    <div className="dss-results">
      <ViewTabs value={detailView} onChange={setDetailView} label="Kết quả mô phỏng" items={[["summary", "So sánh"], ["orders", "Phân bổ & giải thích"]]} />
      <ViewPanel active={detailView === 'summary'} name="So sánh kịch bản">
      {scen.filter((s) => s.r.summary.unassigned_orders > 0).map((s) => {
        const d = diagnose(s.r)
        return (
          <details key={s.title} className={`notice scenario-diagnostic ${s.r.summary.assigned_orders === 0 ? 'err' : ''}`}>
            <summary><b>{s.title}:</b> {fmtInt(s.r.summary.unassigned_orders)}/{fmtInt(s.r.summary.requested_orders)} đơn chưa gán được kho.</summary>
            {d && <p>Lý do phổ biến nhất: {reasonText(d.top)}. {d.hint}</p>}
          </details>
        )
      })}
      <Section title="So sánh kịch bản" note="Chênh lệch mô phỏng; mục tiêu khác trọng số không so sánh trực tiếp.">
        <div className="scenario-summary-visual">
        <div className="scenario-comparison-chart"><LinkedChart rows={scen.map((s,i)=>({key:i,name:s.title,value:s.r.summary.assigned_orders}))} label="Số đơn gán kho theo kịch bản" color="#168b7d"/></div>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Chỉ số</th>{scen.map((s) => <th key={s.title} className="num">{s.title}</th>)}</tr></thead>
            <tbody>
              <tr><td>Đơn được gán kho</td>{scen.map((s) => <td key={s.title} className="num">{fmtInt(s.r.summary.assigned_orders)} / {fmtInt(s.r.summary.requested_orders)}</td>)}</tr>
              <tr><td>Đơn không gán được</td>{scen.map((s) => <td key={s.title} className="num">{fmtInt(s.r.summary.unassigned_orders)}</td>)}</tr>
              <tr><td>Phân bổ theo kho</td>{scen.map((s) => <td key={s.title} className="num small">{whOrders(s.r)}</td>)}</tr>
              <tr><td>Điểm rủi ro trung bình</td>{scen.map((s) => <td key={s.title} className="num">{dec(s.r.summary.mean_risk_score)}</td>)}</tr>
              <tr><td>P90 giao trung bình (ngày)</td>{scen.map((s) => <td key={s.title} className="num">{dec(s.r.summary.mean_p90_scenario_days)}</td>)}</tr>
              <tr><td>Chi phí mục tiêu</td>{scen.map((s) => <td key={s.title} className="num">{(s.r.summary.assigned_orders ? dec(s.r.summary.objective_cost, 3) : '—')}</td>)}</tr>
              {scen.length > 1 && <tr><td>Số đơn đổi kho so với gốc</td><td className="num">—</td>{scen.slice(1).map((s) => <td key={s.title} className="num"><b>{fmtInt(s.cmp.changed_orders)}</b></td>)}</tr>}
              {scen.length > 1 && <tr><td>Chênh chi phí mục tiêu</td><td className="num">—</td>{scen.slice(1).map((s) => <td key={s.title} className="num">{!s.r.summary.assigned_orders ? '—' : s.cmp.objective_cost_delta == null || s.cmp.same_assigned_cohort === false ? 'Khác trọng số hoặc tập đơn'  : dec(s.cmp.objective_cost_delta, 3)}</td>)}</tr>}
            </tbody>
          </table>
        </div>
        </div>
        <details className="data-notes"><summary>Phương pháp và giới hạn so sánh</summary><p className="fine">P90 là thống kê lịch sử của từng tuyến. Báo cáo kiểm tra của nhóm cho thấy trên dữ liệu giữ lại, chỉ khoảng 85–89% đơn nằm trong P90 (dưới 90%), nên không dùng P90 để cam kết thời gian giao hay an toàn hạn dùng.</p>
        <p className="fine">Bộ giải: {res.baseline.solver.method}. Nghiệm tối ưu trong phạm vi batch và các dữ liệu/ràng buộc đầu vào; kết quả mô phỏng chưa phải xác nhận hiệu quả vận hành thực tế.</p></details>
      </Section>

      </ViewPanel>
      <ViewPanel active={detailView === 'orders'} name="Phân bổ từng đơn"><Section title="Phân bổ từng đơn" note="Bấm một đơn để xem lý do từng kho được chọn hoặc bị loại. Dòng tô nền là đơn đổi kho giữa các phương án.">
        <div className="table-wrap">
          <table>
            <thead><tr><th /><th>Đơn</th><th>Tỉnh / thành</th>{scen.map((s) => <th key={s.title}>{s.title}</th>)}</tr></thead>
            <tbody>
              {rows.slice(resultPage * 5, (resultPage + 1) * 5).map((r) => (
                <Fragment key={r.ref}>
                  <tr className={`clickable ${changed(r.ref) ? 'changed' : ''}`} onClick={() => setOpen(open === r.ref ? null : r.ref)}>
                    <td>{open === r.ref ? <ChevronDown size={14} /> : <ChevronRight size={14} />}</td>
                    <td>{r.ref}</td><td>{r.province}</td>
                    {r.cells.map((c, i) => (
                      <td key={i}>{c.warehouse_key ? <b>{whName(c.warehouse_key)}</b> : <span className="down">Không gán</span>}
                        <small className="sub" title={reasonText(c.reason)}>{reasonText(c.reason)}</small></td>))}
                  </tr>
                  {open === r.ref && (
                    <tr className="detail"><td /><td colSpan={2 + scen.length}>
                      <ViewTabs value={candidateScenario} onChange={setCandidateScenario} label="Giải thích theo kịch bản" items={scen.map((s, i) => [String(i), s.title])} />
                      {r.cells.map((c, i) => i === Number(candidateScenario) ? (
                        <div key={i} className="cand">
                          <h4>{scen[i].title}</h4>
                          <table>
                            <thead><tr><th scope="col">Kho</th><th scope="col">Khả thi</th><th scope="col">Lý do loại</th><th scope="col" className="num">Rủi ro</th><th scope="col" className="num">P90 giao</th><th scope="col">Bằng chứng</th></tr></thead>
                            <tbody>{c.candidates.map((k) => (
                              <tr key={k.warehouse_key}>
                                <td>{whName(k.warehouse_key)}</td><td>{k.feasible ? 'Có' : 'Không'}</td>
                                <td style={{ whiteSpace: 'normal', minWidth: 220, maxWidth: 380 }}>{k.reasons.length ? k.reasons.map(reasonText).join('; ') : '—'}</td>
                                <td className="num">{dec(k.risk?.risk_score)}</td><td className="num">{dec(k.p90_scenario_delivery_days)}</td>
                                <td>{k.evidence ? (k.evidence.evidence_level === 'WAREHOUSE_PROVINCE' ? 'Tuyến kho–tỉnh' : 'Toàn kho') + `, ${k.evidence.timing_samples} mẫu` : 'Thiếu mẫu'}</td>
                              </tr>))}</tbody>
                          </table>
                        </div>) : null)}
                    </td></tr>
                  )}
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>
        {rows.length > 5 && <div className="table-pagination"><button type="button" disabled={resultPage === 0} onClick={() => { setOrderPage(resultPage - 1); setOpen(null) }}>Trước</button><span>{resultPage + 1} / {Math.ceil(rows.length / 5)} · {rows.length} đơn</span><button type="button" disabled={(resultPage + 1) * 5 >= rows.length} onClick={() => { setOrderPage(resultPage + 1); setOpen(null) }}>Sau</button></div>}
      </Section>
      </ViewPanel>
    </div>
  )
}

export default function Dss() {
  const { meta, filters } = useFilters()
  const [view, setView] = useState('batch')
  const [scenarioKey, setScenarioKey] = useState('baseline')
  const [store, setStore] = useState('bibica_tiktok_shop')
  const [asOf, setAsOf] = useState(filters.to)
  const [history, setHistory] = useState('')
  const [orders, setOrders] = useState([])
  const [batchPage, setBatchPage] = useState(0)
  const visibleBatchPage = Math.min(batchPage, Math.max(0, Math.ceil(orders.length / 4) - 1))
  const [baseline, setBaseline] = useState({ ...DEFAULT_SCENARIO })
  const [alts, setAlts] = useState([{ ...DEFAULT_SCENARIO, id: ++seq, label: 'Phương án 1' }])
  const [res, setRes] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [shelfProduct, setShelfProduct] = useState(null)
  const [shelfWarehouse, setShelfWarehouse] = useState('')
  const [shelfProvince, setShelfProvince] = useState('Hồ Chí Minh')
  const [remainingShelfDays, setRemainingShelfDays] = useState('')
  const [minRemainingDays, setMinRemainingDays] = useState(1)
  const [shelfExtraDelay, setShelfExtraDelay] = useState(0)
  const [shelfMinRouteSamples, setShelfMinRouteSamples] = useState(20)
  const [shelfBusy, setShelfBusy] = useState(false)
  const [shelfError, setShelfError] = useState(null)
  const [shelfResult, setShelfResult] = useState(null)

  const storeKey = meta.stores.find((s) => s.code === store)?.key
  const warehouses = meta.warehouses.filter((w) => w.storeKey === storeKey)
  const selectedShelfWarehouse = shelfWarehouse || warehouses[0]?.key || ''
  // Tên kho chuẩn hóa thường đã chứa tên vùng ("Kho Hà Nội"): chỉ thêm vùng khi tên chưa có để tránh "Kho Hà Nội (Hà Nội)"
  const whName = (k) => {
    const w = meta.warehouses.find((x) => x.key === k)
    if (!w) return `Kho #${k}`
    return w.region && !w.name.toLowerCase().includes(w.region.toLowerCase()) ? `${w.name} (${w.region})` : w.name
  }
  const base = useMemo(() => ({ from: meta.dateRange.min, to: asOf, store, region: 'all', category: 'all', product: null }), [meta, asOf, store])
  const batchProducts = useMemo(() => {
    const m = new Map()
    orders.forEach((o) => o.items.forEach((i) => i.product && m.set(i.product.key, i.product)))
    return [...m.values()]
  }, [orders])

  const newOrder = () => ({ ref: `D${++seq}`, province: 'Hà Nội', items: [{ id: ++seq, product: null, quantity: 1 }] })
  const setOrder = (ref, patch) => { setOrders((os) => os.map((o) => (o.ref === ref ? { ...o, ...patch } : o))); resetResults() }
  const resetResults = () => { setRes(null); setError(null); setShelfResult(null); setShelfError(null) }

  const changeStore = (v) => { setStore(v); setOrders([]); setShelfProduct(null); setShelfWarehouse(''); setShelfResult(null); setShelfError(null); resetResults(); setBaseline((b) => ({ ...b, stocks: [], capacity: {}, delay: {}, breakfastExceptions: [], breakfastProductKeys: [] })); setAlts((a) => a.map((x) => ({ ...x, stocks: [], capacity: {}, delay: {}, breakfastExceptions: [], breakfastProductKeys: [] }))) }

  const updateBaseline = (v) => { setBaseline(v); resetResults() }
  const updateAlternative = (idx, v) => { setAlts((all) => all.map((x, j) => (j === idx ? { ...v, id: x.id } : x))); resetResults() }

  const validateScenarioInputs = (scenario, label) => {
    const numeric = (value) => value === '' || value == null ? null : Number(value)
    for (const [key, value] of Object.entries(scenario.capacity || {})) {
      const n = numeric(value)
      if (n !== null && (!Number.isInteger(n) || n < 0 || n > 100000)) return `${label}: công suất kho phải là số nguyên từ 0 đến 100.000.`
    }
    for (const [key, value] of Object.entries(scenario.delay || {})) {
      const n = numeric(value)
      if (n !== null && (!Number.isFinite(n) || n < 0 || n > 90)) return `${label}: độ trễ thêm phải từ 0 đến 90 ngày.`
    }
    const bounded = [
      ['Giao tối đa', scenario.maxDeliveryDays, 1, 365], ['Điểm rủi ro tối đa', scenario.maxRiskScore, 0, 100],
      ['Trọng số rủi ro', scenario.riskWeight, 0, 1], ['Trọng số hủy đơn', scenario.wCancel, 0, 1],
      ['Trọng số giao trễ', scenario.wLate, 0, 1], ['Trọng số đánh giá thấp', scenario.wLow, 0, 1],
      ['Ngưỡng trễ', scenario.lateThresholdDays, 1, 365], ['Số mẫu tối thiểu', scenario.minRouteSamples, 1, 10000],
      ['Độ mạnh prior', scenario.priorStrength, 0, 10000], ['Hạn còn tối thiểu', scenario.minRemainingDays, 0, 365],
      ['Sao tối đa tính là thấp', scenario.lowStarMax, 1, 3],
    ]
    for (const [name, value, min, max] of bounded) {
      const n = numeric(value)
      if (n === null || !Number.isFinite(n) || n < min || n > max) return `${label}: ${name} phải nằm trong khoảng ${min}–${max}.`
    }
    if (scenario.stockMode === 'required') {
      for (const stock of scenario.stocks || []) {
        const units = numeric(stock.units)
        if (units === null || !Number.isInteger(units) || units < 0) return `${label}: số lượng tồn phải là số nguyên không âm.`
        const shelfDays = numeric(stock.shelfDays)
        if (shelfDays !== null && (!Number.isInteger(shelfDays) || shelfDays < 0 || shelfDays > 3650)) return `${label}: số ngày hạn sử dụng còn lại phải là số nguyên từ 0 đến 3.650.`
        if (stock.scope && !STOCK_SCOPES.includes(stock.scope)) return `${label}: phạm vi tồn kho không hợp lệ.`
      }
    }

    for (const e of scenario.breakfastExceptions || []) {
      if (!e.warehouseKey || !e.productKey) {
        return `${label}: ngoại lệ bữa sáng cần chọn kho và sản phẩm.`
      }
      if (!/^[A-Za-z0-9][A-Za-z0-9_.:/-]{2,119}$/.test(e.evidenceRef || '')) {
        return `${label}: mã bằng chứng ngoại lệ không đúng định dạng.`
      }
      if (e.ecommerceStockConfirmed !== true) {
        return `${label}: cần xác nhận tồn kho ECOMMERCE thực tế trước khi dùng ngoại lệ.`
      }
      const exceptionWarehouse = warehouses.find((w) => Number(w.key) === Number(e.warehouseKey))
      if (!exceptionWarehouse || exceptionWarehouse.region !== 'Hồ Chí Minh') {
        return `${label}: ngoại lệ này chỉ áp dụng cho kho TP.HCM.`
      }

      const stock = (scenario.stocks || []).find(
        (x) =>
          Number(x.warehouseKey) === Number(e.warehouseKey) &&
          Number(x.productKey) === Number(e.productKey)
      )

      if (
        scenario.stockMode !== 'required' ||
        !stock ||
        stock.scope !== 'ECOMMERCE'
      ) {
        return `${label}: ngoại lệ HCM cần tồn kho ECOMMERCE tương ứng.`
      }
    }
    return null
  }


  const runShelfLife = async () => {
    if (remainingShelfDays === '' || remainingShelfDays == null) return setShelfError('Nhập số ngày hạn dùng còn lại giả định. Dataset không có HSD/lô hàng.')
    if (!shelfProduct?.key) return setShelfError('Hãy chọn sản phẩm cần kiểm tra.')
    if (!selectedShelfWarehouse) return setShelfError('Cửa hàng hiện tại chưa có kho để đánh giá.')
    if (!shelfProvince || shelfProvince === 'Unknown') return setShelfError('Hãy chọn tỉnh/thành nhận hàng hợp lệ.')
    if (!Number.isFinite(Number(remainingShelfDays)) || Number(remainingShelfDays) < 0 || Number(remainingShelfDays) > 3650) return setShelfError('Hạn sử dụng còn lại phải từ 0 đến 3.650 ngày.')
    if (!Number.isFinite(Number(minRemainingDays)) || Number(minRemainingDays) < 0 || Number(minRemainingDays) > 365) return setShelfError('Hạn dùng tối thiểu phải từ 0 đến 365 ngày.')
    if (!Number.isFinite(Number(shelfExtraDelay)) || Number(shelfExtraDelay) < 0 || Number(shelfExtraDelay) > 90) return setShelfError('Độ trễ thêm phải từ 0 đến 90 ngày.')
    if (!Number.isInteger(Number(shelfMinRouteSamples)) || Number(shelfMinRouteSamples) < 1 || Number(shelfMinRouteSamples) > 10000) return setShelfError('Số mẫu tối thiểu phải là số nguyên từ 1 đến 10.000.')

    setShelfBusy(true)
    setShelfError(null)
    setShelfResult(null)
    try {
      const { data, meta: responseMeta } = await dssShelfLife({
        store,
        product_key: Number(shelfProduct.key),
        warehouse_key: Number(selectedShelfWarehouse),
        province: shelfProvince,
        as_of: asOf,
        remaining_shelf_days: Number(remainingShelfDays),
        min_remaining_days: Number(minRemainingDays),
        extra_delay_days: Number(shelfExtraDelay),
        min_route_samples: Number(shelfMinRouteSamples),
      })
      setShelfResult({ data, warnings: responseMeta.warnings || [] })
    } catch (e) {
      setShelfError(e.message)
    } finally {
      setShelfBusy(false)
    }
  }

  const sample = async () => {
    setBusy(true)
    setError(null)

    try {
      const catalog = await getAllProducts(base)
      const commercial = catalog.filter((p) => (p.historical_categories || []).some((c) => ['Bánh', 'Kẹo', 'Ngũ cốc'].includes(c)))
      const name = (p) => p.product_name.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase()
      const selected = commercial.find((p) => /an sang|bua sang|breakfast/.test(name(p))) || commercial[0]
      if (!selected) throw new Error('Không có sản phẩm thương mại trong cửa hàng và mốc lịch sử đã chọn.')
      const product = { key: selected.product_key, label: selected.product_name, categories: selected.historical_categories, store: selected.storefront_code, sku: selected.native_sku_id, variation: selected.variation_name }

      const provinces = [
        'Hà Nội',
        'Hồ Chí Minh',
        'Đồng Nai',
        'Hải Phòng',
      ]

      const missingProvince = provinces.find(
        (province) => !meta.provinces.includes(province)
      )

      if (missingProvince) {
        throw new Error(
          `Dữ liệu cửa hàng chưa có tỉnh mẫu: ${missingProvince}.`
        )
      }

      // Chỉ tạo batch, không thay đổi kịch bản gốc
      // và các phương án người dùng đang cấu hình.
      setOrders(
        provinces.map((province, i) => ({
          ref: `DEMO${i}`,
          province,
          items: [
            {
              id: ++seq,
              product,
              quantity: 2,
            },
          ],
        }))
      )

      // Kịch bản demo: Hà Nội còn hàng (gốc) → Hà Nội hết hàng, chuyển sang HCM bằng ngoại lệ.
      // Số tồn, hạn dùng và mã bằng chứng dưới đây là DỮ LIỆU GIẢ ĐỊNH để minh họa, không phải tồn kho thật.
      const hn = warehouses.find((w) => w.region === 'Hà Nội')
      const hcm = warehouses.find((w) => w.region === 'Hồ Chí Minh')
      if (hn && hcm) {
        const stock = (w, units) => ({ id: ++seq, warehouseKey: w.key, productKey: product.key, units, shelfDays: 30, scope: 'ECOMMERCE' })
        setBaseline({ ...DEFAULT_SCENARIO, label: 'DEMO · Hà Nội mặc định', stockMode: 'required', stocks: [stock(hn, 100), stock(hcm, 100)], capacity: { [hcm.key]: 0 } })
        setAlts([{
          ...DEFAULT_SCENARIO, id: ++seq, label: 'Hà Nội hết hàng · chuyển sang HCM', stockMode: 'required',
          stocks: [stock(hn, 0), stock(hcm, 100)], capacity: { [hn.key]: 0 },
          breakfastExceptions: [{ warehouseKey: hcm.key, productKey: product.key, reason: 'HN_STOCKOUT_TRANSFER', evidenceRef: 'DEMO-HN-STOCKOUT-001', ecommerceStockConfirmed: true }],
        }, {
          ...DEFAULT_SCENARIO, id: ++seq, label: 'DEMO · Stress hạn dùng', stockMode: 'required',
          stocks: [stock(hn, 100), stock(hcm, 100)].map((x) => ({ ...x, shelfDays: 5 })),
          capacity: { [hcm.key]: 0 }, delay: { [hn.key]: 4, [hcm.key]: 4 }, minRemainingDays: 1,
        }])
      }

      resetResults(); setBatchPage(0); setView('batch')
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }


  const run = async (mode) => {
    const problem = validateBatch(orders)
    if (problem) return setError(problem)
    if (history && history > asOf) return setError('Ngày bắt đầu lịch sử phải trước hoặc bằng ngày đánh giá.')
    const scenarioError = validateScenarioInputs(baseline, 'Phương án gốc') || (mode !== 'single' && alts.map((a, i) => validateScenarioInputs(a, `Phương án ${i + 1}`)).find(Boolean))
    if (scenarioError) return setError(scenarioError)
    if (orders.length > 50) return setError('Batch tối đa 50 đơn.')
    if (orders.some((o) => o.items.length > 20)) return setError('Mỗi đơn tối đa 20 sản phẩm.')
    if (orders.some((o) => o.items.some((i) => !Number.isInteger(Number(i.quantity)) || Number(i.quantity) < 1 || Number(i.quantity) > 100000))) return setError('Số lượng mỗi sản phẩm phải là số nguyên từ 1 đến 100.000.')
    if (new Set(orders.map((o) => o.ref.trim())).size !== orders.length) return setError('Mã đơn trong batch không được trùng nhau.')
    setBusy(true); setError(null); setRes(null)
    const common = { store, as_of: asOf, history_start: history || null, orders: buildOrders(orders) }
    try {
      if (mode === 'single') {
        const { data, meta: m } = await dssAllocate({ ...common, scenario: buildScenario(baseline) })
        setRes({ data: { baseline: data, alternatives: [] }, warnings: m.warnings })
      } else if (alts.length === 1) {
        const { data, meta: m } = await dssWhatIf({ ...common, baseline: buildScenario(baseline), alternative: buildScenario(alts[0]) })
        setRes({ data, warnings: m.warnings })
      } else {
        const { data, meta: m } = await dssSensitivity({ ...common, baseline: buildScenario(baseline), alternatives: alts.map(buildScenario) })
        setRes({ data, warnings: m.warnings })
      }
      setView('results')
    } catch (e) { setError(e.message); setRes(null) } finally { setBusy(false) }
  }

  return (
    <fieldset className="dss-page" disabled={busy || shelfBusy}>
      <header className="page-head dss-hero">
        <div>
          <span className="dss-eyebrow">DECISION SUPPORT · BIBICA RETAIL</span>
          <h1>DSS Simulation</h1>
          <p className="headline">Mô phỏng phân bổ đơn hàng và so sánh các phương án vận hành dựa trên dữ liệu lịch sử giao hàng, hủy đơn và đánh giá của Bibica.</p>
        </div>
        <div className="dss-hero-meta"><span className="dss-live-dot" /> Dữ liệu kết nối API</div>
      </header>

      <Section title="01 · Thiết lập dữ liệu" note="Chọn cửa hàng và mốc thời gian dùng làm cơ sở đánh giá.">
        <div className="dss-context-grid">
          <div className="ctx-row">
          <label className="field"><span>Cửa hàng</span>
            <select aria-label="Cửa hàng" value={store} onChange={(e) => changeStore(e.target.value)}>
              {Object.entries(STORES).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
            </select></label>
          <label className="field"><span>Đánh giá tại ngày</span>
            <input type="date" value={asOf} min={meta.dateRange.min} max={meta.dateRange.max} onChange={(e) => { if (e.target.value) { setAsOf(e.target.value); resetResults() } }} /></label>
          <label className="field"><span>Lịch sử từ ngày (tùy chọn)</span>
            <input type="date" value={history} min={meta.dateRange.min} max={asOf} onChange={(e) => { setHistory(e.target.value); resetResults() }} /></label>
          </div>
          <p className="dss-context-note">Lịch sử dùng đến ngày {fmtDate(asOf)}. Trạng thái đơn là ảnh chụp hiện tại, nên đơn gần ngày này có thể chưa phản ánh kết quả cuối cùng.</p>
        </div>
      </Section>

      <ViewTabs value={view} onChange={setView} label="Étapes DSS" items={[["batch", "Đơn hàng"], ["scenario", "Tham số kịch bản"], ["shelf", "Mô phỏng HSD"], ["results", "Kết quả"]]} />
      <ViewPanel active={view === 'batch'} name="Đơn hàng"><Section title="02 · Batch đơn hàng" note="DEMO là nhu cầu, tồn kho và HSD giả định; SKU lấy từ catalog. Tạo mẫu sẽ thay batch và các kịch bản đang nhập."
        aside={<div className="row-actions"><button className="reset" onClick={sample} disabled={busy}><Shuffle size={14} /> Tạo batch mẫu</button>
          <button className="reset" disabled={orders.length >= 50} onClick={() => { setBatchPage(Math.floor(orders.length / 4)); setOrders((o) => [...o, newOrder()]); resetResults() }}><Plus size={14} /> Thêm đơn</button></div>}>
        {orders.length === 0 ? <p className="muted">Chưa có đơn. Bấm "Tạo batch mẫu" để thử nhanh hoặc "Thêm đơn".</p> : (
          <div className="orders" style={{ rowGap: 14 }}>
            {orders.slice(visibleBatchPage * 4, (visibleBatchPage + 1) * 4).map((o) => (
              <div className="order-card" key={o.ref}>
                <div className="order-top">
                  <b>{o.ref}</b>
                  <select value={o.province} aria-label="Tỉnh nhận hàng" onChange={(e) => setOrder(o.ref, { province: e.target.value })}>
                    {meta.provinces.filter((p) => p !== 'Unknown').map((p) => <option key={p}>{p}</option>)}
                  </select>
                  <button type="button" className="icon-btn" onClick={() => { setOrders((os) => os.filter((x) => x.ref !== o.ref)); resetResults() }} aria-label={`Xóa đơn ${o.ref}`}><Trash2 size={15} /></button>
                </div>
                {o.items.map((i) => (
                  <div className="item-row" key={i.id} style={{ marginTop: 6 }}>
                    <ProductPicker value={i.product} baseFilters={base}
                      onChange={(p) => setOrder(o.ref, { items: o.items.map((x) => (x.id === i.id ? { ...x, product: p } : x)) })} />
                    <input type="number" min="1" max="100000" value={i.quantity} aria-label="Số lượng"
                      onChange={(e) => setOrder(o.ref, { items: o.items.map((x) => (x.id === i.id ? { ...x, quantity: e.target.value } : x)) })} />
                    {o.items.length > 1 && <button type="button" className="icon-btn" aria-label="Xóa sản phẩm"
                      onClick={() => setOrder(o.ref, { items: o.items.filter((x) => x.id !== i.id) })}><Trash2 size={14} /></button>}
                  </div>
                ))}
                {o.items.length < 20 && <button type="button" className="reset" onClick={() => setOrder(o.ref, { items: [...o.items, { id: ++seq, product: null, quantity: 1 }] })}><Plus size={13} /> Thêm sản phẩm</button>}
              </div>
            ))}
          </div>
        )}
        {orders.length > 4 && <div className="table-pagination"><button type="button" aria-label="Trang đơn trước" disabled={visibleBatchPage === 0} onClick={() => setBatchPage(visibleBatchPage - 1)}>Trước</button><span>{visibleBatchPage + 1} / {Math.ceil(orders.length / 4)} · {orders.length} đơn</span><button type="button" aria-label="Trang đơn sau" disabled={(visibleBatchPage + 1) * 4 >= orders.length} onClick={() => setBatchPage(visibleBatchPage + 1)}>Sau</button></div>}
      </Section>

      </ViewPanel>
      <ViewPanel active={view === 'scenario'} name="Tham số kịch bản"><Section title="03 · Cấu hình kịch bản" note="Kịch bản gốc là mốc tham chiếu. Các phương án dùng để thay đổi công suất, độ trễ, tồn kho hoặc ngưỡng và so sánh tác động."
        aside={alts.length < 4 && <button className="reset" onClick={() => { setAlts((a) => [...a, { ...baseline, id: ++seq, label: `Phương án ${a.length + 1}` }]); resetResults() }}><Plus size={14} /> Thêm phương án</button>}>
        <ViewTabs value={alts.some((a) => String(a.id) === scenarioKey) ? scenarioKey : 'baseline'} onChange={setScenarioKey} label="Chọn kịch bản"
          items={[["baseline", "Kịch bản gốc"], ...alts.map((a, idx) => [String(a.id), `Phương án ${idx + 1}`])]} />
        <div className="scen-grid single-scenario">
          {!alts.some((a) => String(a.id) === scenarioKey) ?
            <ScenarioEditor key="baseline" heading="Kịch bản gốc" s={baseline} set={updateBaseline} warehouses={warehouses} products={batchProducts} /> :
            alts.filter((a) => String(a.id) === scenarioKey).map((a) => {
              const idx = alts.findIndex((x) => x.id === a.id)
              return <ScenarioEditor key={a.id} heading={`Phương án ${idx + 1}`} s={a} warehouses={warehouses} products={batchProducts}
                set={(v) => updateAlternative(idx, v)} onRemove={alts.length > 1 ? () => { setAlts((all) => all.filter((x) => x.id !== a.id)); setScenarioKey('baseline'); resetResults() } : null} />
            })}
        </div>
      </Section>

      </ViewPanel>
      <ViewPanel active={view === 'shelf'} name="Mô phỏng HSD"><Section title="04 · Mô phỏng hạn dùng — giả định" noteVisible note="Dataset không có NSX, HSD hoặc dữ liệu lô hàng. Nhập giả định để mô phỏng với thời gian giao lịch sử; không xác nhận sản phẩm còn hạn.">
        <div className="dss-context-grid">
          <div className="ctx-row">
            <div className="field">
              <ProductPicker value={shelfProduct} onChange={(p) => { setShelfProduct(p); setShelfResult(null); setShelfError(null) }} baseFilters={{ ...base, category: 'Bánh' }} label="Sản phẩm" placeholder="Tìm sản phẩm bánh cần kiểm tra…" />
            </div>
            <label className="field"><span>Kho xuất hàng</span>
              <select value={selectedShelfWarehouse} onChange={(e) => { setShelfWarehouse(Number(e.target.value)); setShelfResult(null) }}>
                {warehouses.map((w) => <option key={w.key} value={w.key}>{w.name}</option>)}
              </select>
            </label>
            <label className="field"><span>Tỉnh/thành nhận hàng</span>
              <select value={shelfProvince} onChange={(e) => { setShelfProvince(e.target.value); setShelfResult(null) }}>
                {meta.provinces.filter((p) => p !== 'Unknown').map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
            </label>
          </div>
          <div className="two">
            <Num label="Giả định hạn dùng còn lại (ngày)" value={remainingShelfDays} min={0} max={3650} onChange={(v) => { setRemainingShelfDays(v); setShelfResult(null) }} />
            <Num label="Đệm hạn dùng giả định (ngày)" value={minRemainingDays} min={0} max={365} onChange={(v) => { setMinRemainingDays(v); setShelfResult(null) }} />
            <Num label="Độ trễ bổ sung (ngày)" value={shelfExtraDelay} min={0} max={90} step={0.5} onChange={(v) => { setShelfExtraDelay(v); setShelfResult(null) }} />
            <Num label="Số mẫu tuyến tối thiểu" value={shelfMinRouteSamples} min={1} max={10000} onChange={(v) => { setShelfMinRouteSamples(v); setShelfResult(null) }} />
          </div>
          <div className="row-actions">
            <button type="button" className="primary" disabled={shelfBusy || !warehouses.length} onClick={runShelfLife}><Play size={15} /> {shelfBusy ? 'Đang đánh giá…' : 'Chạy mô phỏng hạn dùng'}</button>
          </div>
          {shelfError && <div className="notice err">{shelfError}</div>}
          {shelfResult && <div className="shelf-result">
            <strong>Kết quả đánh giá</strong>
            {shelfResult.data.status === 'INSUFFICIENT_EVIDENCE' ? <p className="notice">Chưa đủ mẫu thời gian giao để đánh giá tuyến này.</p> : <>
              <p className={`notice ${shelfResult.data.shelf_life.feasible ? '' : 'warn'}`}>
                {shelfResult.data.shelf_life.feasible ? 'Đủ đệm hạn dùng theo kịch bản.' : 'Không đủ đệm hạn dùng theo kịch bản.'}
              </p>
              <KpiRow items={[
                { label: 'Hạn còn khi xuất', value: fmtDays(shelfResult.data.shelf_life.remaining_at_dispatch_days), note: 'Giả định đầu vào' },
                { label: 'Hạn còn khi tới nơi theo P90', value: fmtDays(shelfResult.data.shelf_life.p90_arrival_remaining_days), note: `Yêu cầu tối thiểu ${fmtDays(shelfResult.data.shelf_life.minimum_remaining_days)}` },
                { label: 'Lịch sử vượt đệm giả định', value: fmtPct(shelfResult.data.historical_threshold_exceedance.fraction), note: `${fmtInt(shelfResult.data.historical_threshold_exceedance.exceedances)} / ${fmtInt(shelfResult.data.historical_threshold_exceedance.samples)} quan sát` },
              ]} />
              <p className="fine">Thời gian P90 {fmtDays(shelfResult.data.evidence.p90_lead_days)}, {fmtInt(shelfResult.data.evidence.timing_samples)} mẫu. {shelfResult.data.evidence.evidence_level === 'WAREHOUSE_ALL_PROVINCES' ? 'Dùng dữ liệu toàn kho do tuyến thiếu mẫu.' : 'Dùng dữ liệu tuyến kho–tỉnh.'} Tỷ lệ vượt đệm là quan sát lịch sử theo giả định, chưa phải xác suất sản phẩm hỏng.</p>
            </>}
            {shelfResult.warnings.length > 0 && <ul className="warn-list">{shelfResult.warnings.map((w, i) => <li key={i}><TriangleAlert size={14} /> {w}</li>)}</ul>}
          </div>}
        </div>
      </Section>

      </ViewPanel>
      <div className="dss-execute" hidden={view === 'shelf'}>
        <div><span className="dss-eyebrow">05 · EXECUTION</span><strong>Sẵn sàng chạy mô phỏng?</strong><small>Kiểm tra batch và cấu hình kịch bản trước khi thực thi.</small></div>
        <div className="run-bar">
        <button className="primary" disabled={busy} onClick={() => run('compare')}><Play size={15} aria-hidden="true" /> {busy ? 'Đang chạy…' : 'Chạy và so sánh kịch bản'}</button>
        <button className="reset" disabled={busy} onClick={() => run('single')}>Chỉ chạy phương án gốc</button>
        </div>
      </div>

      {error && view !== 'shelf' && <div className="notice err">{error}</div>}
      <ViewPanel active={view === 'results'} name="Kết quả DSS">
      {!res && <p className="notice">Nhập đơn hàng và tham số, sau đó chạy mô phỏng để xem kết quả.</p>}
      {res && (
        <div className={`dss-result-body ${busy ? 'loading' : ''}`}>
          <Result res={res.data} whName={whName} />
          <details className="dss-warnings"><summary>Lưu ý khi đọc kết quả</summary>
            <ul className="warn-list">{(res.warnings || []).map((w) => <li key={w}><TriangleAlert size={14} aria-hidden="true" /> {w}</li>)}</ul>
          </details>
        </div>
      )}
      </ViewPanel>
    </fieldset>
  )
}
