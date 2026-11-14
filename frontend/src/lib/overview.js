export function monthSelection(period,filters) {
  const [year,month]=period.split('-').map(Number)
  const last=new Date(Date.UTC(year,month,0)).getUTCDate()
  const from=`${period}-01`,to=`${period}-${last}`
  return {from:from<filters.from?filters.from:from,to:to>filters.to?filters.to:to}
}

// Descriptive cohort facts only. No growth, forecast or causal explanation.
export function overviewInsights(d) {
  const out=[]
  const stores=d.stores.filter(r=>r.completed_payable!=null).sort((a,b)=>b.completed_payable-a.completed_payable)
  const total=d.kpis.completedPayable
  if(stores.length>1&&total>0)out.push({kind:'share',store:stores[0].group_value,value:stores[0].completed_payable/total})
  const candidates=d.stores.filter(r=>r.orders>=30&&r.canceled_orders>0).sort((a,b)=>b.canceled_orders/b.orders-a.canceled_orders/a.orders)
  if(candidates.length)out.push({kind:'cancel',store:candidates[0].group_value,value:candidates[0].canceled_orders/candidates[0].orders,n:candidates[0].orders,canceled:candidates[0].canceled_orders})
  const cats=d.categories.filter(r=>r.group_value&&r.completed_units>0).sort((a,b)=>b.completed_units-a.completed_units)
  if(cats.length&&d.kpis.completedUnits>0)out.push({kind:'category',category:cats[0].group_value,value:cats[0].completed_units/d.kpis.completedUnits})
  return out
}
