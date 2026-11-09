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

// Khung trang: tiÃªu Ä‘á», cÃ¢u tÃ³m táº¯t, tráº¡ng thÃ¡i táº£i / lá»—i / trá»‘ng, lÆ°u Ã½ dá»¯ liá»‡u chÆ°a chá»‘t
export function Page({ title, headline, state, children, maturity = true, isEmpty }) {
  const { meta, filters, maturityEnd } = useFilters()
  const { data, loading, error } = state
  const empty = data && (isEmpty ? isEmpty(data) : data.kpis?.orders === 0)
  const unstable = maturity && filters.to > maturityEnd
  return (
    <>
      <header className="page-head">
        <h1>{title}</h1>
        {data && !empty && headline && <p className="headline">{headline(data)}</p>}
      </header>
      {unstable && (
        <div className="notice warn">
          Ká»³ Ä‘ang xem cÃ³ cÃ¡c ngÃ y sau {fmtDate(maturityEnd)}. ÄÆ¡n á»Ÿ giai Ä‘oáº¡n nÃ y thÆ°á»ng chÆ°a chuyá»ƒn sang
          "HoÃ n thÃ nh" nÃªn giÃ¡ trá»‹ vÃ  sá»‘ lÆ°á»£ng hoÃ n thÃ nh tháº¥p hÆ¡n thá»±c táº¿. Äá»ƒ so sÃ¡nh Ä‘Ãºng, chá»n ká»³ káº¿t thÃºc trÆ°á»›c ngÃ y Ä‘Ã³.
        </div>
      )}

      {error && <div className="notice err">KhÃ´ng táº£i Ä‘Æ°á»£c dá»¯ liá»‡u: {error}</div>}
      {!data && !error && <div className="notice">Äang táº£i dá»¯ liá»‡uâ€¦</div>}
      {empty && !error && (
        <div className="notice">{data.reason || 'KhÃ´ng cÃ³ dá»¯ liá»‡u khá»›p bá»™ lá»c. Thá»­ má»Ÿ rá»™ng khoáº£ng thá»i gian hoáº·c bá» bá»›t bá»™ lá»c.'}</div>
      )}
      {data && !empty && <div className={loading ? 'body loading' : 'body'}>{children(data)}</div>}
    </>
  )
}
