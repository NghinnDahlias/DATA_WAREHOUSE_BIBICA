
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useFilters } from '../context/FilterContext.jsx'
import { useReport } from '../hooks/useReport.js'
import { getBreakdown, getKpis, getMonthlyBySource, SOURCES } from '../api/client.js'
import { Page, Section } from '../components/Page.jsx'
import { KpiRow } from '../components/KpiStrip.jsx'
import ShareBars from '../components/ShareBars.jsx'
import Alerts from '../components/Alerts.jsx'
import { storeColor, INK } from '../lib/colors.js'
import { axisTick, AXIS_LINE, GRID, tipStyle } from '../lib/chart.js'
import { fmtAxis, fmtDate, fmtInt, fmtPct, fmtPeriod, fmtVND } from '../lib/format.js'
import { qualityNotes, standardKpis } from '../lib/kpis.js'
import { categoryLabel, shareItems, storeLabel } from '../lib/shape.js'

const dayCount = (a, b) =>
  Math.round((new Date(b) - new Date(a)) / 864e5) + 1

function coverageRows(meta) {
  return meta.coverage
    .filter(
      (c) =>
        c.observed_days <
        dayCount(c.first_order_date, c.last_order_date)
    )
    .map((c) => ({
      source: c.source_code,
      label: SOURCES[c.source_code]?.label ?? c.source_code,
      observed: c.observed_days,
      total: dayCount(c.first_order_date, c.last_order_date),
    }))
}

export default function ExecutiveOverview() {
  const { meta, filters, update } = useFilters()

  const state = useReport(async () => {
    const [kpis, store, category, monthly] = await Promise.all([
      getKpis(filters),
      getBreakdown('store', filters),
      getBreakdown('category', filters),
      getMonthlyBySource(filters),
    ])

    return {
      kpis,
      monthly,
      stores: shareItems(
        store.rows,
        'completed_payable',
        storeLabel
      ),
      categories: shareItems(
        category.rows,
        'completed_observed_item_payable',
        categoryLabel
      ),
    }
  }, [filters])

  return (
    <Page
      title="Executive Overview"
      headline={() => ''}
      state={state}
    >
      {(d) => (
        <div className="retail-overview">

          {/* BUSINESS HIGHLIGHTS */}
          <section className="retail-hero retail-hero-v2">
            <div className="retail-hero-copy">
              <span className="retail-overline">
                BIBICA · RETAIL INTELLIGENCE
              </span>

              <h2>
                Business
                <br />
                Highlights
              </h2>

              <p>
                Điểm nhấn về cửa hàng và danh mục đang đóng góp
                vào giá trị đơn hoàn thành trong kỳ báo cáo.
              </p>

              <div className="retail-hero-meta">
                <span className="retail-status-dot" />
                <span>
                  Dữ liệu cập nhật đến {fmtDate(meta.dateRange.max)}
                </span>
              </div>
            </div>

            <div className="retail-hero-aside">
              <span className="retail-aside-label">
                CỬA HÀNG ĐÓNG GÓP CAO NHẤT
              </span>

              <strong className="retail-highlight-name">
                {d.stores[0]?.name ?? 'Chưa có dữ liệu'}
              </strong>

              <span className="retail-aside-note">
                {d.stores[0]
                  ? `${fmtPct(d.stores[0].share, 0)} giá trị đơn hoàn thành`
                  : 'Không có dữ liệu cửa hàng'}
              </span>

              <div className="retail-hero-divider" />

              <div className="retail-hero-mini">
                <div>
                  <span>Danh mục đóng góp cao nhất</span>
                  <b>
                    {d.categories[0]?.name ?? 'Chưa có dữ liệu'}
                  </b>
                </div>

                <div>
                  <span>Tỷ trọng danh mục</span>
                  <b>
                    {d.categories[0]
                      ? fmtPct(d.categories[0].share, 0)
                      : '—'}
                  </b>
                </div>
              </div>
            </div>

            <div className="retail-hero-decoration" />
          </section>

          {/* KPI */}
          <section className="retail-kpi-section">
            <div className="retail-section-heading">
              <div>
                <span className="retail-eyebrow">
                  PERFORMANCE INDICATORS
                </span>
                <h2>Chỉ số vận hành</h2>
              </div>

              <span className="retail-section-caption">
                Theo bộ lọc hiện tại
              </span>
            </div>

            <div className="retail-kpi-wrap">
              <KpiRow items={standardKpis(d.kpis)} />
            </div>
          </section>

          {/* REVENUE TREND */}
          <section className="retail-chart-section">
            <div className="retail-section-heading">
              <div>
                <span className="retail-eyebrow">
                  SALES TREND
                </span>

                <h2>Diễn biến giá trị đơn hoàn thành</h2>

                <p>
                  Theo tháng đặt hàng và cửa hàng.
                  API chỉ cung cấp chiều tháng.
                </p>
              </div>

              <span className="retail-chart-unit">
                ĐƠN VỊ: VND
              </span>
            </div>

            <div className="retail-chart-frame">
              <ResponsiveContainer width="100%" height={340}>
                <BarChart
                  data={d.monthly.revenue}
                  margin={{
                    top: 12,
                    right: 18,
                    left: 8,
                    bottom: 4,
                  }}
                >
                  <CartesianGrid
                    stroke={GRID}
                    vertical={false}
                  />

                  <XAxis
                    dataKey="period"
                    tickFormatter={fmtPeriod}
                    tick={axisTick}
                    tickLine={false}
                    axisLine={AXIS_LINE}
                  />

                  <YAxis
                    tickFormatter={fmtAxis}
                    tick={axisTick}
                    tickLine={false}
                    axisLine={false}
                    width={64}
                  />

                  <Tooltip
                    formatter={(v, n) => [
                      fmtVND(v) + ' ₫',
                      n,
                    ]}
                    labelFormatter={fmtPeriod}
                    contentStyle={tipStyle}
                    cursor={{ fill: '#f7eef2' }}
                  />

                  <Legend
                    iconType="circle"
                    wrapperStyle={{ fontSize: 12 }}
                  />

                  {d.monthly.names.map((n) => (
                    <Bar
                      key={n}
                      dataKey={n}
                      stackId="rev"
                      fill={storeColor(n)}
                      maxBarSize={58}
                      radius={[3, 3, 0, 0]}
                    />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            </div>
          </section>

          {/* STORE AND CATEGORY ANALYSIS */}
          <section className="retail-analysis-section">
            <div className="retail-section-heading">
              <div>
                <span className="retail-eyebrow">
                  CHANNEL & CATEGORY MIX
                </span>
                <h2>Cơ cấu đóng góp kinh doanh</h2>
              </div>
            </div>

            <div className="retail-analysis-grid">

              <div className="retail-analysis-card">
                <div className="retail-card-heading">
                  <div>
                    <span className="retail-card-index">
                      01 / STORE
                    </span>
                    <h3>Hiệu quả theo cửa hàng</h3>
                    <p>
                      Tỷ trọng giá trị đơn hoàn thành
                    </p>
                  </div>
                </div>

                <ShareBars
                  items={d.stores}
                  colorFor={storeColor}
                  onSelect={(i) =>
                    update({ store: i.key })
                  }
                />
              </div>

              <div className="retail-analysis-card">
                <div className="retail-card-heading">
                  <div>
                    <span className="retail-card-index">
                      02 / CATEGORY
                    </span>
                    <h3>Cơ cấu theo danh mục</h3>
                    <p>
                      Giá trị dòng hàng quan sát của đơn hoàn thành
                    </p>
                  </div>
                </div>

                <ShareBars
                  items={d.categories.filter(
                    (c) => c.raw.group_value
                  )}
                  colorFor={() => INK}
                  onSelect={(i) =>
                    update({ category: i.key })
                  }
                />
              </div>

            </div>
          </section>

          {/* DATA QUALITY */}
          <section className="retail-quality-section">
            <div className="retail-section-heading">
              <div>
                <span className="retail-eyebrow">
                  DATA GOVERNANCE
                </span>

                <h2>Chất lượng dữ liệu và lưu ý</h2>

                <p>
                  Các cảnh báo được tổng hợp từ chính
                  những trường KPI mà API trả về.
                </p>
              </div>
            </div>

            <div className="retail-quality-grid">

              <div className="retail-quality-card">
                <h3>Chất lượng dữ liệu</h3>
                <Alerts items={qualityNotes(d.kpis)} />
              </div>

              <details
                className="retail-coverage-card"
                open
              >
                <summary>
                  Độ phủ dữ liệu theo cửa hàng
                </summary>

                <div className="table-wrap coverage-table">
                  <table>
                    <thead>
                      <tr>
                        <th scope="col">Cửa hàng</th>
                        <th scope="col" className="num">
                          Ngày có đơn
                        </th>
                        <th scope="col" className="num">
                          Ngày trong khoảng quan sát
                        </th>
                      </tr>
                    </thead>

                    <tbody>
                      {coverageRows(meta).map((c) => (
                        <tr key={c.source}>
                          <td>{c.label}</td>
                          <td className="num">
                            {fmtInt(c.observed)}
                          </td>
                          <td className="num">
                            {fmtInt(c.total)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <p className="fine">
                  Ngày có đơn không chứng minh nguồn đã xuất đủ
                  mọi ngày, nên không dùng độ phủ này để tính
                  tăng trưởng giữa các kỳ.
                </p>
              </details>

            </div>

            <details className="policies retail-policies">
              <summary>
                Quy ước số liệu của KPI Contract
              </summary>

              <ul>
                {d.kpis.policies.map((p) => (
                  <li key={p}>{p}</li>
                ))}
              </ul>
            </details>
          </section>

          {/* FOOTNOTE */}
          <p className="retail-footnote">
            "Giá trị đơn hoàn thành" là số tiền người mua
            thanh toán theo dữ liệu sàn, mỗi đơn tính một lần
            (không phải doanh thu thuần kế toán).
            Chưa có lợi nhuận, tồn kho và tăng trưởng vì dữ liệu
            hoặc hợp đồng KPI chưa cho phép.
            Dữ liệu đến {fmtDate(meta.dateRange.max)}.
          </p>

        </div>
      )}
    </Page>
  )
}
