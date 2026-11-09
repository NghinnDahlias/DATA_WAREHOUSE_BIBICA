// Dựng đầu vào cho /dss/what-if từ trạng thái form. Giữ ở đây để kiểm thử được.
export const DEFAULT_SCENARIO = { label: 'Hiện trạng', stockMode: 'assume_available', stocks: [],
  capacity: {}, delay: {}, breakfastExceptions: [], breakfastProductKeys: [], maxDeliveryDays: 7,
  maxRiskScore: 100, riskWeight: 0.7, wCancel: 0.4, wLate: 0.4, wLow: 0.2, minRouteSamples: 20,
  priorStrength: 20, lateThresholdDays: 5, minRemainingDays: 1, lowStarMax: 2,
}

const intOrNull = (v) => (v === '' || v == null || Number.isNaN(Number(v)) ? null : Math.trunc(Number(v)))

export function buildScenario(s) {
  const capacity = {}
  Object.entries(s.capacity).forEach(([k, v]) => { const n = intOrNull(v); if (n !== null) capacity[k] = n })
  const delay = {}
  Object.entries(s.delay).forEach(([k, v]) => { if (v !== '' && v != null && Number(v) > 0) delay[k] = Number(v) })
  return {
    label: s.label.trim() || 'Kịch bản',
    stock_mode: s.stockMode,
    stocks: s.stockMode === 'required' ? s.stocks.filter((x) => x.productKey && x.warehouseKey).map((x) => ({
      warehouse_key: Number(x.warehouseKey), product_key: Number(x.productKey), units: Math.trunc(Number(x.units) || 0),
      remaining_shelf_days: x.shelfDays === '' || x.shelfDays == null ? null : Number(x.shelfDays), stock_scope: x.scope })) : [],
    capacity_orders: capacity, extra_delay_days: delay,
    breakfast_exceptions: (s.breakfastExceptions || []).map((e) => ({
      warehouse_key: Number(e.warehouseKey),
      product_key: Number(e.productKey),
      reason: e.reason,
      evidence_ref: e.evidenceRef.trim(),
      ecommerce_stock_confirmed: e.ecommerceStockConfirmed === true,
    })),
    breakfast_product_keys: (s.breakfastProductKeys || []).map(Number),
    max_delivery_days: Number(s.maxDeliveryDays), late_threshold_days: Number(s.lateThresholdDays),
    min_remaining_days: Number(s.minRemainingDays), max_risk_score: Number(s.maxRiskScore),
    min_route_samples: Math.trunc(Number(s.minRouteSamples)), prior_strength: Number(s.priorStrength),
    risk_weight: Number(s.riskWeight), low_star_max: Math.trunc(Number(s.lowStarMax)),
    risk_weights: { cancellation: Number(s.wCancel), late_delivery: Number(s.wLate), low_review: Number(s.wLow) },
  }
}

export function buildOrders(orders) {
  return orders.map((o) => ({
    order_ref: o.ref, province: o.province,
    items: o.items.filter((i) => i.product).map((i) => ({ product_key: i.product.key, quantity: Math.max(1, Math.trunc(Number(i.quantity) || 1)) })),
  }))
}

// Kiểm tra trước khi gọi API để báo lỗi dễ hiểu
export function validateBatch(orders) {
  if (!orders.length) return 'Cần ít nhất một đơn trong batch.'
  if (orders.length > 50) return 'Tối đa 50 đơn mỗi batch.'
  for (const o of orders) {
    if (!o.province) return `Đơn ${o.ref}: chưa chọn tỉnh/thành.`
    const items = o.items.filter((i) => i.product)
    if (!items.length) return `Đơn ${o.ref}: chưa có sản phẩm.`
    if (new Set(items.map((i) => i.product.key)).size !== items.length) return `Đơn ${o.ref}: một sản phẩm xuất hiện hai lần, hãy gộp số lượng.`
  }
  return null
}

export const REASONS = {
  RISK_THRESHOLD_OR_MISSING_SCORE: 'Điểm rủi ro vượt ngưỡng hoặc chưa tính được',
  DELIVERY_THRESHOLD: 'Thời gian giao P90 vượt ngưỡng cho phép',
  INSUFFICIENT_TIMING_EVIDENCE: 'Chưa đủ mẫu thời gian giao trên tuyến này',
  WHOLESALE_STOCK_NOT_ECOMMERCE: 'Tồn kho là hàng sỉ, không dùng cho bán qua sàn',
  BREAKFAST_HN_DEFAULT_REQUIRES_EXPLICIT_EXCEPTION: 'Sản phẩm bữa sáng mặc định xuất từ kho Hà Nội, cần ngoại lệ',
  BREAKFAST_HCM_REQUIRES_ECOMMERCE_STOCK: 'Kho TP.HCM cần tồn kho TMĐT cho sản phẩm bữa sáng',
  UNMAPPED_PRODUCT_MANUAL_REVIEW: 'Sản phẩm chưa phân loại, cần duyệt tay',
  GIFT_ONLY_ORDER_MANUAL_REVIEW: 'Đơn chỉ có quà tặng, cần duyệt tay',
  GIFT_REQUIRES_EXPLICIT_ECOMMERCE_STOCK: 'Quà tặng cần khai báo tồn kho TMĐT',
  MISSING_STOCK_SCENARIO: 'Chưa nhập tồn kho cho kho/sản phẩm này',
  NO_OBSERVED_SKU_AT_WAREHOUSE: 'Chưa từng thấy kho này xuất sản phẩm',
  INSUFFICIENT_SCENARIO_STOCK: 'Tồn kho kịch bản không đủ số lượng',
  MISSING_BREAKFAST_SHELF_LIFE_SCENARIO: 'Thiếu hạn dùng còn lại của sản phẩm bữa sáng',
  SHELF_LIFE_BUFFER: 'Hạn dùng còn lại không đủ sau thời gian giao P90',
  MINIMUM_OBJECTIVE_WITHIN_BATCH_CONSTRAINTS: 'Tối ưu trong ràng buộc của batch',
  SHARED_STOCK_OR_CAPACITY: 'Hết công suất hoặc tồn kho dùng chung với đơn khác',
  NO_FEASIBLE_WAREHOUSE: 'Không kho nào đáp ứng ràng buộc',
}
export const reasonText = (c) => REASONS[c] ?? c