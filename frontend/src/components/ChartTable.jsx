import LinkedChart from './LinkedChart.jsx'
import DataTable from './DataTable.jsx'

export default function ChartTable({rows,columns,onSelect,valueKey='units',format,axisFormat,color,label,minPageSize=2}) {
  return <div className="chart-table">
    <LinkedChart rows={rows} valueKey={valueKey} format={format} axisFormat={axisFormat} color={color} onSelect={onSelect} label={label}/>
    <div className="data-surface" data-table-fit><DataTable columns={columns} data={rows} onRowClick={onSelect} minPageSize={minPageSize} maxPageSize={6}/></div>
  </div>
}
