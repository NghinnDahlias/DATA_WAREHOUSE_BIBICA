import { Fragment, useMemo, useState } from 'react'
import { Plus, Play, Shuffle, Trash2, TriangleAlert, ChevronDown, ChevronRight } from 'lucide-react'
import { useFilters } from '../context/FilterContext.jsx'
import { dssAllocate, dssSensitivity, dssWhatIf, dssShelfLife, STORES } from '../api/client.js'
import { Section } from '../components/Page.jsx'
import ProductPicker from '../components/ProductPicker.jsx'
import { DEFAULT_SCENARIO, buildOrders, buildScenario, reasonText, validateBatch } from '../lib/dss.js'
import { fmtDate, fmtInt } from '../lib/format.js'

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

      <fieldset className="radio-row">
        <legend>Tồn kho</legend>
        <label><input type="radio" checked={s.stockMode === 'assume_available'} onChange={() => upd({ stockMode: 'assume_available' })} /> Giả định đủ hàng</label>
        <label><input type="radio" checked={s.stockMode === 'required'} onChange={() => upd({ stockMode: 'required' })} /> Nhập tồn kho theo kho/sản phẩm</label>
      </fieldset>

      {s.stockMode === 'required' && (
        <div className="stock-rows">
          {s.stocks.map((x) => (
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
          <button type="button" className="reset" disabled={!products.length} onClick={addStock}><Plus size={14} /> Thêm dòng tồn kho</button>
          {!products.length && <p className="fine">Thêm sản phẩm vào batch trước khi nhập tồn kho.</p>}
        </div>
      )}

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
      <details className="adv">
        <summary>Tham số nâng cao</summary>
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
      </details>
    </div>
  )
}

function Result({ res, whName }) {
  const [open, setOpen] = useState(null)
  const scen = [{ title: res.baseline.scenario.label + ' (gốc)', r: res.baseline, cmp: null },
    ...res.alternatives.map((a) => ({ title: a.result.scenario.label, r: a.result, cmp: a.comparison }))]
  const rows = res.baseline.assignments.map((a, i) => ({ ref: a.order_ref, province: a.province, cells: scen.map((s) => s.r.assignments[i]) }))
  const whOrders = (r) => Object.entries(r.summary.warehouse_orders).map(([k, n]) => `${whName(Number(k))}: ${n}`).join(' · ') || '—'
  const changed = (ref) => scen.slice(1).some((s) => s.cmp.changed_order_refs.includes(ref))
  const kpis = [
    { label: 'Đơn được gán kho', value: (r) => `${fmtInt(r.summary.assigned_orders)} / ${fmtInt(r.summary.requested_orders)}`, hint: 'Đơn được phân bổ / tổng đơn' },
    { label: 'Đơn chưa gán', value: (r) => fmtInt(r.summary.unassigned_orders), hint: 'Chưa tìm được kho phù hợp' },
    { label: 'Điểm rủi ro trung bình', value: (r) => dec(r.summary.mean_risk_score), hint: 'Điểm chỉ số, không phải xác suất' },
    { label: 'P90 giao trung bình', value: (r) => `${dec(r.summary.mean_p90_scenario_days)} ngày`, hint: 'Ước tính theo dữ liệu tuyến lịch sử' },
  ]
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
    <>
      {scen.filter((s) => s.r.summary.unassigned_orders > 0).map((s) => {
        const d = diagnose(s.r)
        return (
          <div key={s.title} className={`notice ${s.r.summary.assigned_orders === 0 ? 'err' : ''}`} style={{ marginBottom: 10 }}>
            <b>{s.title}:</b> {fmtInt(s.r.summary.unassigned_orders)}/{fmtInt(s.r.summary.requested_orders)} đơn chưa gán được kho.
            {d && <> Lý do phổ biến nhất: {reasonText(d.top)}. {d.hint}</>}
          </div>
        )
      })}
      <section className="dss-kpi-grid" aria-label="Tóm tắt kết quả mô phỏng" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))', gap: 12, margin: '4px 0 18px' }}>
        {kpis.map((kpi) => (
          <article key={kpi.label} className="dss-kpi-card" style={{ background: '#fff', border: '1px solid #e8e1e5', borderRadius: 12, padding: '14px 16px', minWidth: 0 }}>
            <div style={{ fontSize: 13, color: '#6f6268', fontWeight: 600 }}>{kpi.label}</div>
            <div style={{ display: 'grid', gap: 7, marginTop: 10 }}>
              {scen.map((scenario, index) => (
                <div key={scenario.title} style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 8 }}>
                  <span style={{ color: '#786d72', fontSize: 11, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{index === 0 ? 'Gốc' : scenario.title}</span>
                  <strong style={{ color: '#451326', fontSize: 17, whiteSpace: 'nowrap', fontVariantNumeric: 'tabular-nums' }}>{kpi.value(scenario.r)}</strong>
                </div>
              ))}
            </div>
            <div style={{ color: '#8a7e84', fontSize: 11, marginTop: 8 }}>{kpi.hint}</div>
          </article>
        ))}
      </section>
      <Section title="So sánh kịch bản" note="Chỉ là chênh lệch đầu ra giữa các kịch bản; mục tiêu khác trọng số không so sánh được như độ hữu dụng.">
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
              {scen.length > 1 && <tr><td>Chênh chi phí mục tiêu</td><td className="num">—</td>{scen.slice(1).map((s) => <td key={s.title} className="num">{!s.r.summary.assigned_orders ? '—' : s.cmp.objective_cost_delta == null ? 'Không so sánh được (khác trọng số)' : dec(s.cmp.objective_cost_delta, 3)}</td>)}</tr>}
            </tbody>
          </table>
        </div>
        <p className="fine">P90 là thống kê lịch sử của từng tuyến. Báo cáo kiểm tra của nhóm cho thấy trên dữ liệu giữ lại, chỉ khoảng 85–89% đơn nằm trong P90 (dưới 90%), nên không dùng P90 để cam kết thời gian giao hay an toàn hạn dùng.</p>
        <p className="fine">Bộ giải: {res.baseline.solver.method}. Nghiệm tối ưu trong phạm vi batch và các dữ liệu/ràng buộc đầu vào; kết quả mô phỏng chưa phải xác nhận hiệu quả vận hành thực tế.</p>
      </Section>

      <Section title="Phân bổ từng đơn" note="Bấm một đơn để xem lý do từng kho được chọn hoặc bị loại. Dòng tô nền là đơn đổi kho giữa các phương án.">
        <div className="table-wrap">
          <table>
            <thead><tr><th /><th>Đơn</th><th>Tỉnh / thành</th>{scen.map((s) => <th key={s.title}>{s.title}</th>)}</tr></thead>
            <tbody>
              {rows.map((r) => (
                <Fragment key={r.ref}>
                  <tr className={`clickable ${changed(r.ref) ? 'changed' : ''}`} onClick={() => setOpen(open === r.ref ? null : r.ref)}>
                    <td>{open === r.ref ? <ChevronDown size={14} /> : <ChevronRight size={14} />}</td>
                    <td>{r.ref}</td><td>{r.province}</td>
                    {r.cells.map((c, i) => (
                      <td key={i}>{c.warehouse_key ? <b>{whName(c.warehouse_key)}</b> : <span className="down">Không gán</span>}
                        <small className="sub">{reasonText(c.reason)}</small></td>))}
                  </tr>
                  {open === r.ref && (
                    <tr className="detail"><td /><td colSpan={2 + scen.length}>
                      {r.cells.map((c, i) => (
                        <div key={i} className="cand">
                          <h4>{scen[i].title}</h4>
                          <table>
                            <thead><tr><th>Kho</th><th>Khả thi</th><th>Lý do loại</th><th className="num">Rủi ro</th><th className="num">P90 giao</th><th>Bằng chứng</th></tr></thead>
                            <tbody>{c.candidates.map((k) => (
                              <tr key={k.warehouse_key}>
                                <td>{whName(k.warehouse_key)}</td><td>{k.feasible ? 'Có' : 'Không'}</td>
                                <td style={{ whiteSpace: 'normal', minWidth: 220, maxWidth: 380 }}>{k.reasons.length ? k.reasons.map(reasonText).join('; ') : '—'}</td>
                                <td className="num">{dec(k.risk?.risk_score)}</td><td className="num">{dec(k.p90_scenario_delivery_days)}</td>
                                <td>{k.evidence ? (k.evidence.evidence_level === 'WAREHOUSE_PROVINCE' ? 'Tuyến kho–tỉnh' : 'Toàn kho') + `, ${k.evidence.timing_samples} mẫu` : 'Thiếu mẫu'}</td>
                              </tr>))}</tbody>
                          </table>
                        </div>))}
                    </td></tr>
                  )}
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>
      </Section>
    </>
  )
}

export default function Dss() {
  const { meta, filters } = useFilters()
  const [store, setStore] = useState('bibica_tiktok_shop')
  const [asOf, setAsOf] = useState(filters.to)
  const [history, setHistory] = useState('')
  const [orders, setOrders] = useState([])
  const [baseline, setBaseline] = useState({ ...DEFAULT_SCENARIO })
  const [alts, setAlts] = useState([{ ...DEFAULT_SCENARIO, id: ++seq, label: 'Phương án 1' }])
  const [res, setRes] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [shelfProduct, setShelfProduct] = useState(null)
  const [shelfWarehouse, setShelfWarehouse] = useState('')
  const [shelfProvince, setShelfProvince] = useState('Hồ Chí Minh')
  const [remainingShelfDays, setRemainingShelfDays] = useState(30)
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
  const resetResults = () => { setRes(null); setError(null) }

  const changeStore = (v) => { setStore(v); setOrders([]); setShelfProduct(null); setShelfWarehouse(''); setShelfResult(null); setShelfError(null); resetResults(); setBaseline((b) => ({ ...b, stocks: [], capacity: {}, delay: {}, breakfastExceptions: [] })); setAlts((a) => a.map((x) => ({ ...x, stocks: [], capacity: {}, delay: {}, breakfastExceptions: [] }))) }

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
      // SKU 1365 đã được xác định trong bộ dữ liệu demo.
      // Không cần tải toàn bộ danh sách sản phẩm từ API.
      const product = {
        key: 1365,
        label: 'Combo Bánh Ăn Sáng Bibica (SKU 1365)',
        categories: ['Bánh'],
        units: 0,
      }

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
        setBaseline((b) => ({ ...b, label: 'Hiện trạng · Hà Nội còn hàng', stockMode: 'required', stocks: [stock(hn, 100)], breakfastExceptions: [] }))
        setAlts([{
          ...DEFAULT_SCENARIO, id: ++seq, label: 'Hà Nội hết hàng · chuyển sang HCM', stockMode: 'required',
          stocks: [stock(hn, 0), stock(hcm, 100)],
          breakfastExceptions: [{ warehouseKey: hcm.key, productKey: product.key, reason: 'HN_STOCKOUT_TRANSFER', evidenceRef: 'DEMO-HN-STOCKOUT-001', ecommerceStockConfirmed: true }],
        }])
      }

      resetResults()
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
    const scenarioError = validateScenarioInputs(baseline, 'Phương án gốc') || alts.map((a, i) => validateScenarioInputs(a, `Phương án ${i + 1}`)).find(Boolean)
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
    } catch (e) { setError(e.message); setRes(null) } finally { setBusy(false) }
  }

  return (
    <div className="dss-page">
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
            <select value={store} onChange={(e) => changeStore(e.target.value)}>
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

      <Section title="02 · Batch đơn hàng" note="Tối đa 50 đơn, mỗi đơn tối đa 20 sản phẩm. Công suất kho tính theo số đơn trong cả batch."
        aside={<div className="row-actions"><button className="reset" onClick={sample} disabled={busy}><Shuffle size={14} /> Tạo batch mẫu</button>
          <button className="reset" onClick={() => { setOrders((o) => [...o, newOrder()]); resetResults() }}><Plus size={14} /> Thêm đơn</button></div>}>
        {orders.length === 0 ? <p className="muted">Chưa có đơn. Bấm "Tạo batch mẫu" để thử nhanh hoặc "Thêm đơn".</p> : (
          <div className="orders" style={{ rowGap: 14 }}>
            {orders.map((o) => (
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
      </Section>

      <Section title="03 · Cấu hình kịch bản" note="Kịch bản gốc là mốc tham chiếu. Các phương án dùng để thay đổi công suất, độ trễ, tồn kho hoặc ngưỡng và so sánh tác động."
        aside={alts.length < 4 && <button className="reset" onClick={() => { setAlts((a) => [...a, { ...baseline, id: ++seq, label: `Phương án ${a.length + 1}` }]); resetResults() }}><Plus size={14} /> Thêm phương án</button>}>
        <div className="scen-grid">
          <ScenarioEditor heading="Kịch bản gốc" s={baseline} set={updateBaseline} warehouses={warehouses} products={batchProducts} />
          {alts.map((a, idx) => (
            <ScenarioEditor key={a.id} heading={`Phương án ${idx + 1}`} s={a} warehouses={warehouses} products={batchProducts}
              set={(v) => updateAlternative(idx, v)}
              onRemove={alts.length > 1 ? () => { setAlts((all) => all.filter((_, j) => j !== idx)); resetResults() } : null} />
          ))}
        </div>
      </Section>

      <Section title="04 · Kiểm tra hạn sử dụng" note="Đánh giá một sản phẩm tại kho và tuyến giao đã chọn. Kết quả được trả trực tiếp từ API /dss/shelf-life.">
        <div className="dss-context-grid">
          <div className="ctx-row">
            <div className="field">
              <ProductPicker value={shelfProduct} onChange={(p) => { setShelfProduct(p); setShelfResult(null); setShelfError(null) }} baseFilters={base} label="Sản phẩm" placeholder="Tìm sản phẩm cần kiểm tra…" />
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
            <Num label="Hạn sử dụng còn lại (ngày)" value={remainingShelfDays} min={0} max={3650} onChange={(v) => { setRemainingShelfDays(v); setShelfResult(null) }} />
            <Num label="Hạn dùng tối thiểu (ngày)" value={minRemainingDays} min={0} max={365} onChange={(v) => { setMinRemainingDays(v); setShelfResult(null) }} />
            <Num label="Độ trễ bổ sung (ngày)" value={shelfExtraDelay} min={0} max={90} step={0.5} onChange={(v) => { setShelfExtraDelay(v); setShelfResult(null) }} />
            <Num label="Số mẫu tuyến tối thiểu" value={shelfMinRouteSamples} min={1} max={10000} onChange={(v) => { setShelfMinRouteSamples(v); setShelfResult(null) }} />
          </div>
          <div className="row-actions">
            <button type="button" className="primary" disabled={shelfBusy || !warehouses.length} onClick={runShelfLife}><Play size={15} /> {shelfBusy ? 'Đang đánh giá…' : 'Kiểm tra hạn sử dụng'}</button>
          </div>
          {shelfError && <div className="notice err">{shelfError}</div>}
          {shelfResult && <div className="shelf-result">
            <strong>Kết quả đánh giá</strong>
            <pre style={{ whiteSpace: 'pre-wrap', overflowX: 'auto', padding: 14, borderRadius: 10, background: '#f8f5f6', border: '1px solid #eadfe4', fontSize: 12 }}>{JSON.stringify(shelfResult.data, null, 2)}</pre>
            {shelfResult.warnings.length > 0 && <ul className="warn-list">{shelfResult.warnings.map((w, i) => <li key={i}><TriangleAlert size={14} /> {w}</li>)}</ul>}
          </div>}
        </div>
      </Section>

      <div className="dss-execute">
        <div><span className="dss-eyebrow">05 · EXECUTION</span><strong>Sẵn sàng chạy mô phỏng?</strong><small>Kiểm tra batch và cấu hình kịch bản trước khi thực thi.</small></div>
        <div className="run-bar">
        <button className="primary" disabled={busy} onClick={() => run('compare')}><Play size={15} aria-hidden="true" /> {busy ? 'Đang chạy…' : 'Chạy và so sánh kịch bản'}</button>
        <button className="reset" disabled={busy} onClick={() => run('single')}>Chỉ chạy phương án gốc</button>
        </div>
      </div>

      {error && <div className="notice err">{error}</div>}
      {res && (
        <div className={busy ? 'loading' : ''}>
          <Result res={res.data} whName={whName} />
          <Section title="Lưu ý khi đọc kết quả">
            <ul className="warn-list">{(res.warnings || []).map((w) => <li key={w}><TriangleAlert size={14} aria-hidden="true" /> {w}</li>)}</ul>
          </Section>
        </div>
      )}
    </div>
  )
}