import { fmtInt, fmtPct, fmtVND } from './format.js'

// Dải KPI chuẩn theo KPI Contract: M01, M03, M06, M07, M08
export function standardKpis(k, productFiltered = false) {
  return [
    { label: 'Đơn đặt', value: fmtInt(k.orders), note: productFiltered ? 'Các đơn có dòng SKU đã chọn, gồm mọi trạng thái' : 'Gồm cả đơn hủy và chưa hoàn thành' },
    { label: 'Giá trị đơn hoàn thành', value: k.completedPayable == null ? '—' : `${fmtVND(k.completedPayable)} ₫`, note: `${fmtInt(k.completedOrders)} đơn hoàn thành` + (productFiltered ? ' có SKU; tiền toàn đơn' : '') },
    { label: 'Số lượng bán', value: fmtInt(k.completedUnits), note: productFiltered ? 'Chỉ số lượng SKU đã chọn trong đơn hoàn thành' : 'Sản phẩm của đơn hoàn thành' },
    { label: 'Giá trị đơn trung bình', value: k.completedAov == null ? '—' : `${fmtVND(k.completedAov)} ₫`, note: 'Trên đơn hoàn thành có giá trị' },
    { label: 'Tỷ lệ hủy', value: k.cancellationRate == null ? '—' : fmtPct(k.cancellationRate), note: `${fmtInt(k.canceledOrders)} đơn hủy` },
  ]
}

// Cảnh báo chất lượng dữ liệu rút từ chính các trường KPI trả về
export function qualityNotes(k) {
  const out = []
  if (k.conflictingOrders) out.push({ level: 'info', title: `${fmtInt(k.conflictingOrders)} đơn có giá trị mâu thuẫn giữa các dòng nguồn`, detail: 'DW đánh dấu CONFLICTING; các đơn này vẫn nằm trong tổng.' })
  if (k.unknownStatusOrders) out.push({ level: 'info', title: `${fmtInt(k.unknownStatusOrders)} đơn chưa xác định được trạng thái`, detail: 'Nằm trong mẫu số số đơn nhưng không thuộc hoàn thành hay hủy.' })
  if (k.unmappedLines) out.push({ level: 'info', title: `${fmtInt(k.unmappedLines)} dòng hàng chưa có danh mục`, detail: 'Hiển thị là "Chưa phân loại" trong phân rã theo danh mục.' })
  const cov = k.orders ? k.payableObservedOrders / k.orders : 1
  if (cov < 0.98) out.push({ level: 'warn', title: `Chỉ ${fmtPct(cov, 1)} đơn có giá trị thanh toán quan sát`, detail: 'Giá trị đơn tính trên phần có dữ liệu; phần còn lại là NULL, không phải 0.' })
  return out
}

export const STATUS_LABELS = {
  COMPLETED: 'Hoàn thành', DELIVERED: 'Đã giao, chờ xác nhận', CANCELED: 'Đã hủy', PROCESSING: 'Đang xử lý',
  UNPAID: 'Chưa thanh toán', RETURNED: 'Hoàn trả', UNKNOWN: 'Không xác định',
}
