import {Bar,BarChart,CartesianGrid,Cell,ResponsiveContainer,Tooltip,XAxis,YAxis} from 'recharts'
import {fmtAxis,fmtInt} from '../lib/format.js'
import {tipStyle} from '../lib/chart.js'

export const CATEGORY_COLORS={'Bánh':'#138d80','Kẹo':'#d47c35','Ngũ cốc':'#6377c2','Quà tặng':'#ae6fa0','Chưa phân loại':'#8798a8'}
export const shortName=(s,n=22)=>String(s).length>n?String(s).slice(0,n-1)+'…':String(s)

export default function LinkedChart({rows,valueKey='value',onSelect,color='#138d80',format=fmtInt,axisFormat,label='Biểu đồ',limit=8}) {
  const data=rows.filter(r=>r[valueKey]!=null).slice(0,limit).map(r=>({...r,plotLabel:r.plotName??r.name}))
  if(!data.length)return <div className="chart-empty">Chưa có giá trị quan sát</div>
  return <div className="linked-chart" role="group" aria-label={label}>
    {rows.length>limit&&<span className="chart-cap">Top {limit}</span>}
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} layout="vertical" margin={{top:4,right:18,left:0,bottom:0}}>
        <CartesianGrid horizontal={false} stroke="#e7edf2"/>
        <XAxis type="number" tickFormatter={axisFormat??(v=>Math.abs(v)<10?Number(v).toLocaleString('vi-VN',{maximumFractionDigits:1}):fmtAxis(v))} tick={{fontSize:11,fill:'#53697d'}} tickLine={false} axisLine={false}/>
        <YAxis type="category" dataKey="plotLabel" width={124} interval={0} tick={({x,y,payload})=><text x={x-5} y={y} dy={4} textAnchor="end" fontSize={11} fill="#29445b">{shortName(payload.value,19)}</text>} tickLine={false} axisLine={false}/>
        <Tooltip contentStyle={tipStyle} cursor={{fill:'#e9f5f2'}} formatter={v=>[format(v),'Giá trị']} labelFormatter={(_,payload)=>payload?.[0]?.payload?.name}/>
        <Bar dataKey={valueKey} isAnimationActive={false} maxBarSize={20} radius={[0,3,3,0]} onClick={d=>onSelect?.(d.payload)} cursor={onSelect?'pointer':'default'}>
          {data.map(r=><Cell key={r.key??r.name} fill={typeof color==='function'?color(r):color} role={onSelect?'button':undefined} tabIndex={onSelect?0:undefined}
            aria-label={onSelect?`Lọc ${r.name}`:undefined} onKeyDown={e=>{if(onSelect&&(e.key==='Enter'||e.key===' ')){e.preventDefault();onSelect(r)}}}/>)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  </div>
}
