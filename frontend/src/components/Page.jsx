
import { useFilters } from '../context/FilterContext.jsx'
import { fmtDate } from '../lib/format.js'

export function Section({ title, note, aside, children }) {
  return (
    <section className="section">
      <header className="section-head">
        <div>
          <h2>{title}</h2>
          {note && <p>{note}</p>}
        </div>
        {aside}
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
        {data && !empty && headline && (
          <p className="headline">{headline(data)}</p>
        )}
      </header>

      {unstable && (
        <div className="notice warn">
          Kỳ đang xem có các ngày sau {fmtDate(maturityEnd)}. Đơn ở giai đoạn này
          thường chưa chuyển sang "Hoàn thành" nên giá trị và số lượng hoàn thành
          thấp hơn thực tế. Để so sánh đúng, chọn kỳ kết thúc trước ngày đó.
        </div>
      )}

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
        <div className={loading ? 'body loading' : 'body'}>
          {children(data)}
        </div>
      )}
    </>
  )
}
