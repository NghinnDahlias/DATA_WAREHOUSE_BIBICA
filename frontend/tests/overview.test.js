import {expect,it} from 'vitest'
import {monthSelection,overviewInsights} from '../src/lib/overview.js'
it('month drilldown stays inside the selected partial interval',()=>{
 expect(monthSelection('2026-06',{from:'2026-06-21',to:'2026-09-18'})).toEqual({from:'2026-06-21',to:'2026-06-30'})
 expect(monthSelection('2026-09',{from:'2026-06-21',to:'2026-09-18'})).toEqual({from:'2026-09-01',to:'2026-09-18'})
})
it('insights describe the current cohort with denominators and suppress thin cancellation samples',()=>{
 const d={kpis:{completedPayable:1000,completedUnits:100},stores:[{group_value:'a',orders:100,canceled_orders:20,completed_payable:600},{group_value:'b',orders:2,canceled_orders:2,completed_payable:400}],categories:[{group_value:'Bánh',completed_units:70},{group_value:null,completed_units:30}]}
 expect(overviewInsights(d)).toEqual([{kind:'share',store:'a',value:.6},{kind:'cancel',store:'a',value:.2,n:100,canceled:20},{kind:'category',category:'Bánh',value:.7}])
 expect(overviewInsights({kpis:{completedPayable:null,completedUnits:null},stores:[],categories:[]})).toEqual([])
})
