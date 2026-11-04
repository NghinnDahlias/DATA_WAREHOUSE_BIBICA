"""Controlled warehouse aliases observed in the exports, never inferred from buyers."""
import re
import unicodedata

GEOGRAPHY_VERSION = '2026-11-04-warehouse-province-v2'
ALIASES = {
    'kho hồ chí minh': ('Kho Hồ Chí Minh', 'Hồ Chí Minh'),
    'hcm': ('Kho Hồ Chí Minh', 'Hồ Chí Minh'),
    'bibica hcm': ('Kho Hồ Chí Minh', 'Hồ Chí Minh'),
    'kho hà nội': ('Kho Hà Nội', 'Hà Nội'),
    'hn': ('Kho Hà Nội', 'Hà Nội'),
    'bibica hn': ('Kho Hà Nội', 'Hà Nội'),
}

def warehouse(value):
    raw = unicodedata.normalize('NFC', '' if value is None else str(value)).strip()
    token = re.sub(r'\s+', ' ', raw).casefold()
    found = ALIASES.get(token)
    return {'warehouse_raw': raw, 'warehouse_name': found[0] if found else raw or 'Unknown',
            'warehouse_region': found[1] if found else 'Unknown',
            'warehouse_mapping_status': 'Mapped' if found else 'Unmapped'}

# Names observed in these exports. This is a spelling dictionary, not a map of
# present-day administrative mergers: historic names remain separate members.
PROVINCES=('Hồ Chí Minh|Hà Nội|Hải Phòng|Đà Nẵng|Cần Thơ|Huế|Thừa Thiên Huế|An Giang|Bà Rịa - Vũng Tàu|Bạc Liêu|Bắc Giang|Bắc Kạn|Bắc Ninh|Bến Tre|Bình Dương|Bình Định|Bình Phước|Bình Thuận|Cà Mau|Cao Bằng|Đắk Lắk|Đắk Nông|Điện Biên|Đồng Nai|Đồng Tháp|Gia Lai|Hà Giang|Hà Nam|Hà Tĩnh|Hải Dương|Hậu Giang|Hòa Bình|Hưng Yên|Khánh Hòa|Kiên Giang|Kon Tum|Lai Châu|Lâm Đồng|Lạng Sơn|Lào Cai|Long An|Nam Định|Nghệ An|Ninh Bình|Ninh Thuận|Phú Thọ|Phú Yên|Quảng Bình|Quảng Nam|Quảng Ngãi|Quảng Ninh|Quảng Trị|Sóc Trăng|Sơn La|Tây Ninh|Thái Bình|Thái Nguyên|Thanh Hóa|Tiền Giang|Trà Vinh|Tuyên Quang|Vĩnh Long|Vĩnh Phúc|Yên Bái').split('|')

def _fold(value):
    t=unicodedata.normalize('NFD',value.casefold()).replace('đ','d')
    t=''.join(c for c in t if unicodedata.category(c)!='Mn')
    return re.sub(r'[^a-z0-9]','',t)

PROVINCE_LOOKUP={_fold(v):v for v in PROVINCES}
PROVINCE_LOOKUP.update({'hochiminhcity':'Hồ Chí Minh','hcm':'Hồ Chí Minh','hanoi':'Hà Nội',
 'kiengiang':'Kiên Giang','kiengiangprovince':'Kiên Giang','daclak':'Đắk Lắk','dacnong':'Đắk Nông'})

def normalize_province(value):
    raw=unicodedata.normalize('NFC','' if value is None else str(value)).strip()
    label=raw
    for _ in range(3):
        label=re.sub(r'^(?:tỉnh|tinh|thành\s+phố|thanh\s+pho|tp[.]?|phố|pho)\s*','',label,flags=re.I).strip()
    found=PROVINCE_LOOKUP.get(_fold(label))
    return {'customer_province':found or 'Unknown','province_mapping_status':'Mapped' if found else 'Unmapped'}
