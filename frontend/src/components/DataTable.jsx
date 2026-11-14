import { useEffect, useRef, useState } from 'react'
import { flexRender, getCoreRowModel, getSortedRowModel, getPaginationRowModel, useReactTable } from '@tanstack/react-table'
import { ArrowDown, ArrowUp } from 'lucide-react'

// Bảng sắp xếp được. columns dùng meta: { align: 'right' } cho cột số.
export default function DataTable({ columns, data, onRowClick, initialSort = [], minPageSize = 3, maxPageSize = 10 }) {
  const host = useRef(null)
  const [sorting, setSorting] = useState(initialSort)
  const table = useReactTable({
    data, columns, state: { sorting }, onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(), getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(), initialState: { pagination: { pageSize: 10 } },
  })
  useEffect(() => {
    const element = host.current
    const panel = element?.closest('[data-table-fit],.view-panel')
    if (!panel) return
    const measure = () => {
      const bounds = panel.getBoundingClientRect(), top = element.getBoundingClientRect().top
      if (!bounds.height) return
      const header = element.querySelector('thead')?.getBoundingClientRect().height || 32
      const rows = [...element.querySelectorAll('tbody tr')]
      const rowHeight = Math.max(32, ...rows.map((r) => r.getBoundingClientRect().height))
      const size = Math.max(minPageSize, Math.min(maxPageSize, Math.floor((bounds.bottom - top - header - 34) / rowHeight)))
      if (table.getState().pagination.pageSize !== size) table.setPageSize(size)
    }
    measure()
    const observer = new ResizeObserver(measure)
    observer.observe(panel)
    return () => observer.disconnect()
  }, [table, data, minPageSize, maxPageSize])
  return (
    <div className="paged-table" ref={host}><div className="table-wrap">
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
              tabIndex={onRowClick ? 0 : undefined}
              onKeyDown={onRowClick ? (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onRowClick(row.original) } } : undefined}
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
      {table.getPageCount() > 1 && <div className="table-pagination">
        <button type="button" disabled={!table.getCanPreviousPage()} onClick={() => table.previousPage()} aria-label="Trang bảng trước">Trước</button>
        <span>{table.getState().pagination.pageIndex + 1} / {table.getPageCount()} · {data.length} dòng</span>
        <button type="button" disabled={!table.getCanNextPage()} onClick={() => table.nextPage()} aria-label="Trang bảng sau">Sau</button>
      </div>}
    </div>
  )
}
