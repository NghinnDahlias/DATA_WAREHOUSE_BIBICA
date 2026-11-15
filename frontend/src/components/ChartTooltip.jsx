import {useLayoutEffect,useRef,useState} from 'react'
import {createPortal} from 'react-dom'

export default function ChartTooltip({active,payload,coordinate,host,format}) {
  const ref=useRef(null)
  const [position,setPosition]=useState({left:12,top:12})
  const row=payload?.[0]?.payload
  useLayoutEffect(()=>{
    if(!active||!row)return
    const chart=host.current?.getBoundingClientRect(),tip=ref.current?.getBoundingClientRect()
    if(!chart||!tip)return
    const x=chart.left+(coordinate?.x??0),y=chart.top+(coordinate?.y??0)
    setPosition({left:Math.max(8,Math.min(x+18,window.innerWidth-tip.width-8)),top:Math.max(8,Math.min(y+18,window.innerHeight-tip.height-8))})
  },[active,row,coordinate?.x,coordinate?.y,host])
  if(!active||!row)return null
  return createPortal(<div ref={ref} role="tooltip" className="chart-hover-card" style={position}>
    <strong>{row.name}</strong>{row.variation&&<span>{row.variation}</span>}
    <div><span>Giá trị</span><b>{format(payload[0].value)}</b></div>
  </div>,document.body)
}
