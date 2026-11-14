
import { useFilters } from '../context/FilterContext.jsx'
import { fmtDate } from '../lib/format.js'
import { Info } from 'lucide-react'

export function Help({text,label='Giải thích chỉ số'}) {
  return <details className="help"><summary aria-label={label} title={label}><Info size={15}/></summary><div role="note">{text}</div></details>
}

export function Section({ title, note, noteVisible = false, aside, children }) {
  return (
    <section className="section">
      <header className="section-head">
        <div>
          <h2>{title}</h2>
          {noteVisible&&note&&<p>{note}</p>}
        </div>
        <div className="section-tools">{aside}{note&&!noteVisible&&<Help text={note}/>}</div>
      </header>
      {children}
    </section>
  )
}

// Khung trang: tiêu đề, câu tóm tắt, trạng thái tải / lỗi / trống, lưu ý dữ liệu chưa chốt
export function Page({ title, headline, state, children, maturity = true, isEmpty }) {
  const { meta, filters, maturityEnd } = useFilters()
  const { data, loading, error } = state
  const empty = data && (isEmpty ? isEmpty(data) : data.kpis?.orders === 0)
  const unstable = maturity && filters.to > maturityEnd

  return (
    <>
      <header className="page-head">
        <h1>{title}</h1>
        <div className="page-tools">
          {unstable&&<span className="period-caution">Có đơn chưa chốt <Help label="Lưu ý kỳ dữ liệu" text={`Kỳ có ngày sau ${fmtDate(maturityEnd)}. Trạng thái đơn có thể chưa kết thúc; số liệu là snapshot nguồn. Mốc30ngày không phải bảo đảm đã chốt.`}/></span>}
          <Help label="Quy ước dữ liệu" text="Tiền đơn hoàn thành tính mỗi đơn một lần. Tiền dòng hàng là chỉ số riêng, không cộng với tiền đơn. Ngày có đơn không chứng minh xuất đủ kỳ. Đánh giá chỉ có TikTok; thiếu dữ liệu không phải bằng0."/>
        </div>
        {data && !empty && headline && (
          <p className="headline">{headline(data)}</p>
        )}
      </header>


      {error && (
        <div className="notice err">
          Không tải được dữ liệu: {error}
        </div>
      )}

      {!data && !error && (
        <div className="notice">Đang tải dữ liệu…</div>
      )}

      {empty && !error && (
        <div className="notice">
          {data.reason ||
            'Không có dữ liệu khớp bộ lọc. Thử mở rộng khoảng thời gian hoặc bỏ bớt bộ lọc.'}
        </div>
      )}

      {data && !empty && (
        <div className={loading ? 'body loading' : 'body'} aria-busy={loading} inert={loading?'':undefined}>
          {children(data)}
        </div>
      )}
    </>
  )
}
