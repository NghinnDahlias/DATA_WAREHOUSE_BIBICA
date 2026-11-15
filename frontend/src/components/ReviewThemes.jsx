import DataTable from './DataTable.jsx'
import {ViewPanel} from './ViewTabs.jsx'

import { useEffect, useState } from 'react'
import { getReviewThemes } from '../api/client.js'
import { useFilters } from '../context/FilterContext.jsx'
import { Section } from './Page.jsx'
import { fmtInt } from '../lib/format.js'
import Modal from './Modal.jsx'
import ReviewCases from './ReviewCases.jsx'
import {THEME_LABELS as LABELS} from '../lib/reviewLabels.js'

const number = (value) => value == null ? '—' : fmtInt(value)

function StatCard({ label, value, note, type = '', onClick }) {
  const Tag=onClick?'button':'div'
  return (
    <Tag className={`rt-stat-card ${type}`} title={note} onClick={onClick}>
      <span className="rt-stat-label">{label}</span>
      <strong className="rt-stat-value">{value}</strong>

    </Tag>
  )
}

function ThemeBars({ labels, onSelect }) {
  const topLabels = [...labels]
    .sort((a, b) => b.mentions - a.mentions)
    .slice(0, 8)

  const max = Math.max(...topLabels.map((item) => item.mentions), 1)

  if (!topLabels.length) {
    return <div className="rt-empty">Chưa có chủ đề được ghi nhận.</div>
  }

  return (
    <div className="rt-bars">
      {topLabels.map((item) => (
        <button className="rt-bar-item" key={item.label} onClick={()=>onSelect(item.label)} title={`Đọc ${item.negative_mentions} đánh giá 1–2 sao: ${LABELS[item.label]}`}>
          <div className="rt-bar-heading">
            <span>{LABELS[item.label] || item.label}</span>
            <strong>{number(item.mentions)}</strong>
          </div>

          <div className="rt-bar-track">
            <div
              className="rt-bar-fill"
              style={{
                width: `${(item.mentions / max) * 100}%`,
              }}
            />
          </div>
        </button>
      ))}
    </div>
  )
}

export default function ReviewThemes() {
  const { filters } = useFilters()
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [caseTopic,setCaseTopic]=useState(null)

  useEffect(() => {
    let active = true

    setLoading(true)
    setError('')

    getReviewThemes(filters)
      .then((value) => {
        if (active) setResult(value)
      })
      .catch((e) => {
        if (active) setError(
          e.message || 'Không tải được chủ đề đánh giá.'
        )
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [JSON.stringify(filters)])

  if (loading) {
    return (
      <Section title="Phân tích chủ đề đánh giá">
        <div className="rt-state">Đang tải dữ liệu đánh giá...</div>
      </Section>
    )
  }

  if (error) {
    return (
      <Section title="Phân tích chủ đề đánh giá">
        <div className="rt-error">{error}</div>
      </Section>
    )
  }

  if (!result) return null

  if (result.availability && result.availability !== 'READY') return (
    <Section title="Phân tích chủ đề đánh giá"><p className="notice">{
      result.availability === 'UNAVAILABLE_NO_SHOPEE_RATING_SOURCE' ? 'Chưa có nguồn đánh giá Shopee.' :
      result.availability === 'NO_OBSERVED_REVIEWS' ? 'Không có đánh giá khớp bộ lọc.' :
      'Nhãn đánh giá chưa được nạp đủ cho nguồn hiện hành. Cần làm mới dữ liệu chủ đề.'
    }</p></Section>
  )
  const labels = result.labels || []

  const totalMentions = labels.reduce(
    (sum, item) => sum + item.mentions,
    0
  )

  return (
    <Section
      title="Phân tích chủ đề đánh giá"
      note="Nhãn từ khóa chưa xác minh; một đánh giá có thể chứa nhiều nhãn."
    >
      <div className="rt-dashboard themes-compact">

        {/* KPI */}
        <div className="rt-stats">
          <StatCard
            label="Tổng đánh giá"
            value={number(result.total_reviews)}
            note="Đánh giá trong phạm vi lọc"
          />

          <StatCard
            label="Đánh giá có nội dung"
            value={number(result.text_present_reviews)}
            note={
              result.total_reviews
                ? `${(result.text_present_reviews / result.total_reviews * 100).toFixed(1)}% tổng đánh giá`
                : 'Chưa có dữ liệu'
            }
          />

          <StatCard
            label="Đánh giá 1–2 sao"
            onClick={()=>setCaseTopic('')}
            value={number(result.negative_reviews_le2)}
            note="Đánh giá có mức sao thấp"
          />

          <StatCard
            label="Đề cập về an toàn thực phẩm"
            value={number(result.safety_signal_reviews)}
            note="Mốc, côn trùng, dị vật, hết hạn. Cần người đọc lại."
            type="rt-stat-warning"
          />
        </div>

        <div className="theme-pair-heading"><strong>Chủ đề được đề cập</strong><span>{number(totalMentions)} lượt đề cập · có thể trùng đánh giá</span></div>
        <ViewPanel active name="Chủ đề và bảng"><div className="theme-paired">
        {/* Chart */}
        <div className="rt-panel theme-chart">
          <div className="rt-panel-heading">
            <div>
              <h3>Chủ đề được đề cập nhiều nhất</h3>
              <p>Xếp hạng theo số lượt đề cập</p>
            </div>
            <span className="rt-panel-tag">TOP 8</span>
          </div>

          <ThemeBars labels={labels} onSelect={setCaseTopic}/>
        </div>


        {/* Detail table */}
        <div className="rt-panel">
          <div className="rt-panel-heading">
            <div>
              <h3>Chi tiết theo chủ đề</h3>
              <p>So sánh tổng lượt đề cập và lượt đề cập trong đánh giá 1–2 sao</p>
            </div>
          </div>

          <DataTable columns={[
            { accessorKey: 'label', header: 'Chủ đề', cell: (c) => LABELS[c.getValue()] || c.getValue() },
            { accessorKey: 'mentions', header: 'Lượt đề cập', cell: (c) => number(c.getValue()), meta: { align: 'right' } },
            { accessorKey: 'negative_mentions', header: 'Trong đánh giá 1–2 sao', cell: (c) => number(c.getValue()), meta: { align: 'right' } },
          ]} data={labels} onRowClick={r=>setCaseTopic(r.label)} initialSort={[{ id: 'mentions', desc: true }]} />
        </div>

        </div></ViewPanel>
        <details className="theme-method"><summary>Phương pháp và giới hạn</summary>
        {/* Methodology */}
        <div className="rt-method">
          <div className="rt-method-title">
            <span className="rt-method-icon">i</span>
            Lưu ý về dữ liệu
          </div>

          <p>
            Nhãn được phân loại bằng từ khóa và chưa được xác minh thủ công.
            Đây là tín hiệu đề cập, không phải nguyên nhân hay khiếu nại đã
            được xác nhận. Một đánh giá có thể được gắn nhiều nhãn.
          </p>

          <p>
            Hiện chưa có dữ liệu sự kiện để xác nhận việc gửi bù,
            nhận hàng bù hoặc xử lý khiếu nại thực tế.
          </p>
        </div>
        </details>
      </div>
      {caseTopic!==null&&<Modal title="Đánh giá tiêu cực · đọc ý kiến" className="review-reader-dialog" onClose={()=>setCaseTopic(null)}><ReviewCases initialTopic={caseTopic}/></Modal>}
    </Section>
  )
}
