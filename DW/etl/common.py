"""Source readers and explicit parsers. No customer fields leave this module."""
import csv
import hashlib
import re
import unicodedata
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from functools import lru_cache

ROOT = Path(__file__).resolve().parents[2]
SOURCES = {
    'shopee_bibica': ('Shopee_Bibica.xlsx', 'Shopee', 'Bibica'),
    'shopee_quasure': ('Shopee_Quasure.xlsx', 'Shopee', 'Quasure'),
    'tiktok_bibica': ('Tiktokshop_Bibica.csv', 'TikTok Shop', 'Bibica'),
    'ratings': ('Tiktok_Rating_Bibica.xlsx', 'TikTok Shop', 'Bibica'),
}
PARSER_VERSION = '2026-11-04-v3-warehouse-geography'
RATING_PARSER_VERSION='2026-11-04-xlsx-text-ids-v1'

def parser_version(key):return PARSER_VERSION+'|'+RATING_PARSER_VERSION if key=='ratings' else PARSER_VERSION

def clean(value):
    return unicodedata.normalize('NFC', '' if value is None else str(value)).replace('\xa0', ' ').strip()

@lru_cache(maxsize=4096)
def norm(value):
    return re.sub(r'\s+', ' ', clean(value)).casefold()

def digest(value):
    return hashlib.sha256(value.encode('utf8')).hexdigest()

def checksum(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()

def source_path(key):
    import os
    folder = Path(os.environ.get('SOURCE_DIR', str(ROOT/'Data'/'Data_Source_Raw')))
    path = folder / SOURCES[key][0]
    if not path.exists():
        raise FileNotFoundError(f'Missing required source: {path.name}')
    return path

def rows(path):
    if path.suffix == '.xlsx':
        from openpyxl import load_workbook
        book = load_workbook(path, read_only=True, data_only=True)
        sheet = book['orders'] if 'orders' in book.sheetnames else book['Ratings']
        it = sheet.iter_rows(values_only=True)
        header = [clean(x) for x in next(it)]
        try:
            for number, row in enumerate(it, 2):
                if any(x is not None for x in row):
                    yield number, dict(zip(header, row))
        finally:
            book.close()
    else:
        with path.open(encoding='utf-8-sig', newline='') as f:
            for number, row in enumerate(csv.DictReader(f), 2):
                yield number, row

def money(value):
    if value is None or clean(value) in ('', '-', '--', 'N/A'):
        return None
    if isinstance(value, (int,float,Decimal)):
        return Decimal(str(value))
    s = clean(value).replace('₫','').replace('VND','').replace('đ','').replace(' ','')
    if ',' in s and '.' in s:
        s = s.replace(',','') if s.rfind('.')>s.rfind(',') else s.replace('.','').replace(',','.')
    elif re.fullmatch(r'-?\d{1,3}(,\d{3})+', s):
        s = s.replace(',','')
    elif re.fullmatch(r'-?\d{1,3}(\.\d{3})+', s):
        s = s.replace('.','')
    elif ',' in s:
        s = s.replace(',','.')
    try:
        n = Decimal(s)
        return n if n.is_finite() else None
    except InvalidOperation:
        return None

def date(value):
    if value is None or value == '': return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=None).isoformat(sep=' ')
    s = clean(value)
    s = re.sub(r'(\d+) tháng (\d+) năm (\d+)', r'\1/\2/\3', s)
    for fmt in ('%Y-%m-%d %H:%M:%S','%Y-%m-%d %H:%M','%d/%m/%Y %H:%M:%S','%d/%m/%Y %H:%M','%d/%m/%Y','%Y-%m-%d','%d %b %Y %H:%M:%S'):
        try:
            return datetime.strptime(s, fmt).isoformat(sep=' ')
        except ValueError:
            pass
    return None

def status(value):
    s = norm(value)
    if s in ('completed','hoàn thành','đã hoàn tất'): return 'COMPLETED'
    if s in ('delivered','đã giao'): return 'DELIVERED'
    if s=='đã nhận được hàng' or s.startswith('người mua xác nhận đã nhận được hàng, tuy nhiên'): return 'DELIVERED'
    if s in ('canceled','cancelled','đã hủy','đã huỷ') or s.startswith(('đã hủy.', 'đã hủy ', 'đã huỷ ')): return 'CANCELED'
    if s in ('returned','refunded','đã hoàn tiền','trả hàng/hoàn tiền'): return 'RETURNED'
    if s in ('unpaid','chưa thanh toán'): return 'UNPAID'
    if s in ('awaiting shipment','awaiting collection','in transit','đang giao','đang giao hàng','chờ lấy hàng','chờ xác nhận','đã vận chuyển','cần vận chuyển','chờ giao hàng'): return 'PROCESSING'
    return 'UNKNOWN'

def get(row, *names):
    # Preserve case distinctions: Shopee has two materially different payment headers.
    for name in names:
        name = clean(name)
        if name in row: return row[name]
    return None

def canonical(key, number, row):
    platform, store = SOURCES[key][1:]
    if key == 'ratings':
        text = norm(get(row,'review_text'))
        # Retain only rule-based issue tags; free text can contain buyer PII.
        issues = [label for label, terms in {'chất lượng':['mốc','hỏng','vỡ','chảy','hạn sử dụng'], 'giao hàng':['giao hàng','đóng gói','vận chuyển'], 'hương vị':['ngọt','ngon','vị']}.items() if any(t in text for t in terms)]
        result=dict(order_id=clean(get(row,'order_id')), product_id=clean(get(row,'product_id')), product_name=clean(get(row,'product_name')), stars=str(money(get(row,'star_level')) or ''), review_date=date(get(row,'review_date')), issues=issues, text_present=bool(text))
        for field in ['review_signature','review_layout_status','review_id_status']:
            if row.get(field):result[field]=row[field]
        return result
    tt = platform == 'TikTok Shop'
    pick = lambda t,s: get(row,t if tt else s)
    m = lambda t,s: str(money(pick(t,s))) if money(pick(t,s)) is not None else None
    sku = clean(pick('SKU ID','SKU phân loại hàng')) or clean(get(row,'SKU sản phẩm'))
    product_name = clean(pick('Product Name','Tên sản phẩm'))
    brand = 'Quasure' if 'quasure' in norm(product_name) else ('Bibica' if 'bibica' in norm(product_name) else 'Unknown')
    qty = money(pick('Quantity','Số lượng'))
    gross = money(pick('SKU Subtotal Before Discount','Giá gốc'))
    seller = money(pick('SKU Seller Discount','Người bán trợ giá'))
    from .geography import warehouse
    return dict(**warehouse(pick('Warehouse Name','Tên kho hàng')), order_id=clean(pick('Order ID','Mã đơn hàng')), sku=sku, seller_sku=clean(pick('Seller SKU','SKU sản phẩm')), product_name=product_name,
      category=clean(get(row,'Product Category')) or 'Unknown', variant=clean(pick('Variation','Tên phân loại hàng')), brand=brand,
      status_raw=clean(pick('Order Status','Trạng Thái Đơn Hàng')), status=status(pick('Order Status','Trạng Thái Đơn Hàng')),
      created=date(pick('Created Time','Ngày đặt hàng')), paid=date(pick('Paid Time','Thời gian đơn hàng được thanh toán')), delivered=date(pick('Delivered Time','Thời gian hoàn thành đơn hàng')),
      canceled=date(get(row,'Cancelled Time')), quantity=str(qty) if qty is not None else None, gross=str(gross if tt else gross*qty) if gross is not None and qty is not None else None,
      item_after=m('SKU Subtotal After Discount','Tổng số tiền Người mua thanh toán'), unit_price=m('SKU Unit Original Price','Giá ưu đãi'),
      seller_discount=str(seller) if seller is not None else None, platform_discount=m('SKU Platform Discount','Được Shopee trợ giá'),
      order_amount=m('Order Amount','Tổng số tiền người mua thanh toán'), refund=m('Order Refund Amount',''), shipping=m('Shipping Fee After Discount','Phí vận chuyển (dự kiến)'),
      order_value=m('Order Amount','Tổng giá trị đơn hàng (VND)'), channel=clean(get(row,'Order Channel')) if tt else 'NA',
      province=clean(pick('Province','Tỉnh/Thành phố')) or 'Unknown', cancel_reason=clean(pick('Cancel Reason','Lý do hủy')) or 'Unknown',
      return_status=clean(get(row,'Trạng thái Trả hàng/Hoàn tiền','Cancelation/Return Type')), returned_quantity=m('Sku Quantity of return','Số lượng sản phẩm được hoàn trả'),
      payment=clean(pick('Payment Method','Phương thức thanh toán')) or 'Unknown')
