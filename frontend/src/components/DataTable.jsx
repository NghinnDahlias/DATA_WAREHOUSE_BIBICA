import { useState } from 'react'
import { flexRender, getCoreRowModel, getSortedRowModel, useReactTable } from '@tanstack/react-table'
import { ArrowDown, ArrowUp } from 'lucide-react'

// Bảng sắp xếp được. columns dùng meta: { align: 'right' } cho cột số.
export default function DataTable({ columns, data, onRowClick, initialSort = [] }) {
  const [sorting, setSorting] = useState(initialSort)
  const table = useReactTable({
    data, columns, state: { sorting }, onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(), getSortedRowModel: getSortedRowModel(),
  })
  return (
    <div className="table-wrap">
      <table>
        <thead>
          {table.getHeaderGroups().map((hg) => (
            <tr key={hg.id}>
              {hg.headers.map((h) => {
                const dir = h.column.getIsSorted()
                return (
                  <th key={h.id} className={h.column.columnDef.meta?.align === 'right' ? 'num' : ''}
                    aria-sort={dir === 'asc' ? 'ascending' : dir === 'desc' ? 'descending' : 'none'}>
                    <button type="button" className="th-btn" onClick={h.column.getToggleSortingHandler()}>
                      {flexRender(h.column.columnDef.header, h.getContext())}
                      {dir === 'asc' && <ArrowUp size={13} aria-hidden="true" />}
                      {dir === 'desc' && <ArrowDown size={13} aria-hidden="true" />}
                    </button>
                  </th>
                )
              })}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr key={row.id} className={onRowClick ? 'clickable' : ''}
              onClick={onRowClick ? () => onRowClick(row.original) : undefined}>
              {row.getVisibleCells().map((c) => (
                <td key={c.id} className={c.column.columnDef.meta?.align === 'right' ? 'num' : ''}>
                  {flexRender(c.column.columnDef.cell, c.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
