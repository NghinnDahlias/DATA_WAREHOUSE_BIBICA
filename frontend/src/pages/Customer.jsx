import { CartesianGrid, ComposedChart, Legend, Line, Bar, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useFilters } from '../context/FilterContext.jsx'
import { useReport } from '../hooks/useReport.js'
import { getKpis, pool, STORES } from '../api/client.js'
import { Page, Section } from '../components/Page.jsx'
import { KpiRow } from '../components/KpiStrip.jsx'
import DataTable from '../components/DataTable.jsx'
import { BURGUNDY } from '../lib/colors.js'
import { axisTick, AXIS_LINE, GRID, tipStyle } from '../lib/chart.js'
import { addDays } from '../lib/dates.js'
import { fmtInt, fmtPct, fmtPeriod, fmtStar } from '../lib/format.js'
import ReviewThemes from '../components/ReviewThemes.jsx'

const num = { align: 'right' }
const catColumns = [
  { accessorKey: 'name', header: 'Danh mục' },
  { accessorKey: 'reviews', header: 'Đánh giá', cell: (i) => fmtInt(i.getValue()), meta: num },
  { accessorKey: 'avgStars', header: 'Điểm TB', cell: (i) => fmtStar(i.getValue()), meta: num },
  { accessorKey: 'lowRate', header: 'Tiêu cực (1–2 sao)', cell: (i) => (i.getValue() == null ? '—' : fmtPct(i.getValue())), meta: num },
]

// Các cửa sổ tháng (tối đa 12 tháng gần nhất) nằm trong khoảng lọc
function monthWindows(from, to) {
  const out = []
  let y = Number(to.slice(0, 4)), m = Number(to.slice(5, 7))
  while (out.length < 12) {
    const first = `${y}-${String(m).padStart(2, '0')}-01`
    const next = m === 12 ? `${y + 1}-01-01` : `${y}-${String(m + 1).padStart(2, '0')}-01`
    const last = addDays(next, -1)
    const s = first < from ? from : first, e = last > to ? to : last
    if (s > e) break
    out.unshift({ period: first.slice(0, 7), from: s, to: e })
    if (first <= from) break
    m -= 1; if (m === 0) { m = 12; y -= 1 }
  }
  return out
}

function headline(d) {
  const k = d.kpis
  return `${fmtInt(k.reviews)} đánh giá TikTok trong cohort đơn đặt, điểm trung bình ${fmtStar(k.avgStars)}/5, ${fmtPct(k.lowReviewRate)} là 1–2 sao.`
}

export default function Customer() {
  const { meta, filters } = useFilters()
  const shopee = filters.store !== 'all' && STORES[filters.store].channel === 'Shopee'
  const state = useReport(async () => {
    if (shopee) return { unavailable: true, reason: 'DW chưa có nguồn đánh giá của Shopee, chỉ có đánh giá của Bibica TikTok Shop. Chọn "Tất cả" hoặc Bibica TikTok Shop để xem trang này.' }
    const f = { ...filters, store: filters.store === 'all' ? 'bibica_tiktok_shop' : filters.store }
    const wins = monthWindows(f.from, f.to)
    const [kpis, months, cats] = await Promise.all([
      getKpis(f),
      pool(wins.map((w) => () => getKpis({ ...f, from: w.from, to: w.to })), 4),
      pool(meta.categories.map((c) => () => getKpis({ ...f, category: c })), 4)])
    if (kpis.reviews === 0) return { empty: true, kpis, reason: 'Không có đánh giá TikTok nào trong khoảng thời gian và bộ lọc này. Thử mở rộng khoảng thời gian hoặc bỏ lọc danh mục/sản phẩm.' }
    return {
      kpis,
      monthly: wins.map((w, i) => ({ period: w.period, reviews: months[i].reviews, avgStars: months[i].avgStars, lowRate: months[i].lowReviewRate })),
      categories: meta.categories.map((c, i) => ({ name: c, reviews: cats[i].reviews, avgStars: cats[i].avgStars, lowRate: cats[i].lowReviewRate })),
    }
  }, [filters])

  return (
    <>
      <Page title="Customer Experience" headline={headline} state={state} maturity={false}
        isEmpty={(d) => d.unavailable || d.empty}>
        {(d) => {
          const k = d.kpis
          return (
            <div className="customer-experience">
              <KpiRow items={[
                { label: 'Số đánh giá', value: fmtInt(k.reviews), note: 'TikTok, đã qua kiểm soát chất lượng' },
                { label: 'Điểm trung bình', value: `${fmtStar(k.avgStars)} / 5`, note: 'Trung bình số sao' },
                { label: 'Đánh giá tiêu cực (1–2 sao)', value: fmtPct(k.lowReviewRate), note: `${fmtInt(k.lowReviews)} đánh giá` },
                { label: 'Độ phủ đánh giá', value: k.reviewOrderCoverage == null ? '—' : fmtPct(k.reviewOrderCoverage), note: 'Đơn TikTok có đánh giá / tổng đơn TikTok' },
              ]} />
              {k.reviews < 30 && <div className="notice warn">Chỉ có {k.reviews} đánh giá trong bộ lọc này nên các tỷ lệ kém ổn định.</div>}

              <Section title="Điểm sao và tỷ lệ tiêu cực theo tháng đặt hàng" note="Đánh giá được gom theo tháng của đơn được đánh giá. Cột: số đánh giá. Đường: tỷ lệ 1–2 sao.">
                <div className="chart">
                  <ResponsiveContainer>
                    <ComposedChart data={d.monthly} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
                      <CartesianGrid stroke={GRID} vertical={false} />
                      <XAxis dataKey="period" tickFormatter={fmtPeriod} tick={axisTick} tickLine={false} axisLine={AXIS_LINE} />
                      <YAxis yAxisId="n" tick={axisTick} tickLine={false} axisLine={false} width={40} />
                      <YAxis yAxisId="r" orientation="right" tick={axisTick} tickLine={false} axisLine={false} width={44} tickFormatter={(v) => fmtPct(v, 0)} />
                      <Tooltip formatter={(v, n) => [n === 'Tỷ lệ 1–2 sao' ? fmtPct(v) : fmtInt(v), n]} labelFormatter={fmtPeriod} contentStyle={tipStyle} />
                      <Legend wrapperStyle={{ fontSize: 12 }} />
                      <Bar yAxisId="n" name="Số đánh giá" dataKey="reviews" fill="#d9c3cc" maxBarSize={28} radius={[4, 4, 0, 0]} />
                      <Line yAxisId="r" name="Tỷ lệ 1–2 sao" dataKey="lowRate" stroke={BURGUNDY} strokeWidth={2.5} dot={{ r: 2.5, fill: BURGUNDY }} activeDot={{ r: 4 }} connectNulls />
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
              </Section>

              <Section title="Điểm đánh giá theo danh mục" note="Đánh giá gắn được tới sản phẩm thuộc danh mục (danh mục lịch sử suy từ tên dòng hàng)">
                <DataTable columns={catColumns} data={d.categories} initialSort={[{ id: 'reviews', desc: true }]} />
              </Section>
            </div>
          )
        }}
      </Page>
      <div className="customer-themes">
        <ReviewThemes />
      </div>
    </>
  )
}
