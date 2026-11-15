import {useEffect,useState} from 'react'
import {useFilters} from '../context/FilterContext.jsx'
import {getReviewCases,getReviewCase,getReviewThemes} from '../api/client.js'
import {fmtDate,fmtInt} from '../lib/format.js'
import {THEME_LABELS} from '../lib/reviewLabels.js'
import {Help} from './Page.jsx'

export default function ReviewCases({initialTopic=''}) {
  const {filters}=useFilters()
  const [topic,setTopic]=useState(initialTopic),[starsMax,setStarsMax]=useState(2)
  const [offset,setOffset]=useState(0),[result,setResult]=useState(null),[topics,setTopics]=useState([])
  const [selected,setSelected]=useState(null),[detail,setDetail]=useState(null)
  const [loading,setLoading]=useState(true),[error,setError]=useState(''),[detailError,setDetailError]=useState('')
  const scope=JSON.stringify(filters),limit=4
  useEffect(()=>{setOffset(0);setSelected(null);setDetail(null)},[scope,topic,starsMax])
  useEffect(()=>{
    let current=true
    getReviewThemes(filters).then(d=>{if(current)setTopics(d.labels??[])}).catch(()=>{if(current)setTopics([])})
    return ()=>{current=false}
  },[scope])
  useEffect(()=>{
    let current=true
    setLoading(true);setError('');setResult(null);setSelected(null);setDetail(null)
    getReviewCases(filters,{topic,starsMax,offset,limit}).then(d=>{
      if(current){setResult(d);setSelected((d.rows.find(r=>r.content_status==='READY')??d.rows[0])?.case_key??null)}
    }).catch(e=>{if(current)setError(e.message)}).finally(()=>{if(current)setLoading(false)})
    return ()=>{current=false}
  },[scope,topic,starsMax,offset])
  useEffect(()=>{
    let current=true
    setDetail(null);setDetailError('')
    if(selected!=null)getReviewCase(filters,selected,{topic,starsMax}).then(d=>{if(current)setDetail(d)}).catch(e=>{if(current)setDetailError(e.message)})
    return ()=>{current=false}
  },[selected,scope,topic,starsMax])
  return <div className="review-cases">
    <div className="case-controls"><label>Mức sao<select aria-label="Mức sao tiêu cực" value={starsMax} onChange={e=>{setOffset(0);setStarsMax(Number(e.target.value))}}><option value="1">1 sao</option><option value="2">1–2 sao</option><option value="3">1–3 sao</option></select></label>
      <label>Chủ đề<select aria-label="Chủ đề tiêu cực" value={topic} onChange={e=>{setOffset(0);setTopic(e.target.value)}}><option value="">Tất cả chủ đề</option>{Object.entries(THEME_LABELS).map(([key,label])=><option key={key} value={key}>{label}{starsMax===2?` (${topics.find(t=>t.label===key)?.negative_mentions??0})`:''}</option>)}</select></label>
      <strong>{result?`${fmtInt(result.total)} đánh giá`:''}</strong><Help text="Số sao thấp không đồng nghĩa mọi ý kiến đều có nội dung tiêu cực. Chủ đề là nhãn từ khóa chưa xác minh. Nội dung đã che tự động thông tin cá nhân; không hiển thị tài khoản hay mã đơn. Bộ lọc ngày theo cohort đơn đặt, review không sau ngày kết thúc."/>
    </div>
    {error&&<p role="alert">{error}</p>}{loading&&<p role="status">Đang tải đánh giá…</p>}
    {!loading&&result?.total===0&&<p>Không có đánh giá khớp mức sao, chủ đề và bộ lọc này.</p>}
    {!loading&&result?.rows.length>0&&<div className="case-workspace">
      <div className="case-list-column"><div className="case-list">{result.rows.map(r=><button className={`case-list-item ${selected===r.case_key?'selected':''}`} key={r.case_key} onClick={()=>setSelected(r.case_key)} aria-pressed={selected===r.case_key}>
        <span className="case-meta"><b>{r.star_level} ★</b><time>{fmtDate(r.review_date)}</time><span>Case #{r.case_key}</span></span>
        <strong>{r.product_name}</strong><span className="case-preview">{r.preview|| (r.content_status==='NO_TEXT'?'Khách chỉ chấm sao, không có nội dung.':'Nội dung chưa được chuẩn bị.')}</span>
      </button>)}</div><div className="case-pagination"><button disabled={!offset} onClick={()=>setOffset(Math.max(0,offset-limit))}>Trước</button><span>{offset+1}–{Math.min(offset+limit,result.total)} / {fmtInt(result.total)}</span><button disabled={offset+limit>=result.total} onClick={()=>setOffset(offset+limit)}>Sau</button></div></div>
      <article className="case-detail" aria-label="Chi tiết ý kiến khách hàng" aria-busy={!detail&&!detailError}>
        {detailError?<p role="alert">{detailError}</p>:!detail?<p role="status">Đang mở ý kiến…</p>:<>
          <div className="case-detail-head"><span>{detail.star_level} ★ · {fmtDate(detail.review_date)}</span><span>Case #{detail.case_key}</span></div>
          <h3>{detail.product_name}</h3><div className="case-labels">{detail.labels.map(l=><button key={l} onClick={()=>{setOffset(0);setTopic(l)}}>{THEME_LABELS[l]??l}</button>)}</div>
          <h4>Ý kiến khách hàng</h4>{detail.content_status==='READY'?<blockquote>{detail.content}</blockquote>:<p className="notice">{detail.content_status==='NO_TEXT'?'Khách chỉ chấm sao, không có nội dung.':'Nội dung chưa sẵn sàng cho bản nguồn hiện tại. Cần chuẩn bị lại nội dung đã che thông tin.'}</p>}
          <small className="case-redaction-note">Đã che tự động thông tin cá nhân. Nhãn chủ đề cần người đọc xác minh.</small>
        </>}
      </article>
    </div>}
  </div>
}
