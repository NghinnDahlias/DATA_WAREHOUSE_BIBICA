
import { useEffect, useState } from 'react'
import { getReviewThemes } from '../api/client.js'
import { useFilters } from '../context/FilterContext.jsx'
import { Section } from './Page.jsx'
import { fmtInt } from '../lib/format.js'

const LABELS = {
  missing_items_mention: 'Giao thiếu hàng',
  wrong_items_mention: 'Giao sai sản phẩm',
  packaging_damage_mention: 'Bao bì hư hỏng',
  product_breakage_mention: 'Sản phẩm vỡ, nát',
  pest_or_foreign_material_mention: 'Côn trùng hoặc dị vật',
  spoilage_or_expired_mention: 'Hư hỏng hoặc hết hạn',
  short_shelf_life_mention: 'Hạn sử dụng ngắn',
  taste_or_texture_mention: 'Chất lượng, hương vị',
  delivery_delay_mention: 'Giao hàng chậm',
  replacement_promised_mention: 'Hứa gửi bù',
  replacement_dispatch_claim: 'Đề cập đã gửi bù',
  replacement_received_claim: 'Đề cập đã nhận hàng bù',
  resolution_confirmed_claim: 'Đề cập đã xử lý',
}

const number = (value) => fmtInt(value ?? 0)

function StatCard({ label, value, note, type = '' }) {
  return (
    <div className={`rt-stat-card ${type}`}>
      <span className="rt-stat-label">{label}</span>
      <strong className="rt-stat-value">{value}</strong>
      <span className="rt-stat-note">{note}</span>
    </div>
  )
}

function ThemeBars({ labels }) {
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
        <div className="rt-bar-item" key={item.label}>
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
        </div>
      ))}
    </div>
  )
}

export default function ReviewThemes() {
  const { filters } = useFilters()
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

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

  const labels = result.labels || []

  const totalMentions = labels.reduce(
    (sum, item) => sum + item.mentions,
    0
  )

  return (
    <Section
      title="Phân tích chủ đề đánh giá"
      note="Theo dõi các vấn đề được khách hàng đề cập trong đánh giá TikTok theo bộ lọc hiện tại."
    >
      <div className="rt-dashboard">

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

        {/* Summary */}
        <div className="rt-summary">
          <div>
            <span className="rt-summary-label">
              Tổng lượt đề cập theo chủ đề
            </span>
            <strong>{number(totalMentions)}</strong>
          </div>

          <span className="rt-summary-description">
            Một đánh giá có thể chứa nhiều chủ đề khác nhau.
          </span>
        </div>

        {/* Chart */}
        <div className="rt-panel">
          <div className="rt-panel-heading">
            <div>
              <h3>Chủ đề được đề cập nhiều nhất</h3>
              <p>Xếp hạng theo số lượt đề cập</p>
            </div>
            <span className="rt-panel-tag">TOP 8</span>
          </div>

          <ThemeBars labels={labels} />
        </div>

        {/* Detail table */}
        <div className="rt-panel">
          <div className="rt-panel-heading">
            <div>
              <h3>Chi tiết theo chủ đề</h3>
              <p>So sánh tổng lượt đề cập và lượt đề cập trong đánh giá 1–2 sao</p>
            </div>
          </div>

          <div className="rt-table-wrap">
            <table className="rt-table">
              <thead>
                <tr>
                  <th>Chủ đề / nội dung</th>
                  <th className="rt-number">Lượt đề cập</th>
                  <th className="rt-number">Trong đánh giá 1–2 sao</th>
                </tr>
              </thead>

              <tbody>
                {[...labels]
                  .sort((a, b) => b.mentions - a.mentions)
                  .map((item) => (
                    <tr key={item.label}>
                      <td>
                        <span className="rt-topic-name">
                          {LABELS[item.label] || item.label}
                        </span>
                      </td>

                      <td className="rt-number">
                        <strong>{number(item.mentions)}</strong>
                      </td>

                      <td className="rt-number">
                        <span className={
                          item.negative_mentions > 0
                            ? 'rt-negative-value'
                            : ''
                        }>
                          {number(item.negative_mentions)}
                        </span>
                      </td>
                    </tr>
                  ))}

                {!labels.length && (
                  <tr>
                    <td colSpan="3" className="rt-empty">
                      Chưa phát hiện chủ đề thuộc các nhãn đã định nghĩa.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

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

      </div>
    </Section>
  )
}
