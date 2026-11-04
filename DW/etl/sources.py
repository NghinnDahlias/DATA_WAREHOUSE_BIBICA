"""Source contracts, exact lexical IDs, shared category and warehouse rules."""
import csv,hashlib,json,re
from pathlib import Path
from .common import SOURCES,canonical,clean,norm,money,date,rows,checksum,digest
from .ratings import project_scraped_rating
from .categorization import categorize_product
from .geography import normalize_province

SCOPES={'shopee_bibica':('shopee','bibica_official_store','Bibica Official Store'),
 'shopee_quasure':('shopee','quasure_specialized_store','Quasure specialized store'),
 'tiktok_bibica':('tiktok','bibica_tiktok_shop','Bibica TikTok Shop'),
 'ratings':('tiktok','bibica_tiktok_shop','Bibica TikTok Shop')}

def province(value):
    return normalize_province(value)['customer_province']

def project(key,locator,row):
    raw=project_scraped_rating(row) if key=='ratings' and 'web_scraper_order' in row else row
    c=canonical(key,locator,raw);c['normalized_name']=norm(c.get('product_name',''))
    if key=='ratings':c['review_text_length']=len(clean(raw.get('review_text')))
    if key!='ratings':
        cat=categorize_product(c['product_name'])
        c.update(canonical_category=cat.canonical_category,category_rule=cat.rule,category_mapping_status=cat.status,
            category_mapping_method=cat.mapping_method,category_keyword_conflict=cat.keyword_conflict,customer_province=province(c['province']))
        c['product_nk']=c['sku'] or 'name:'+hashlib.md5((c['product_name']+'/'+(c['variant'] or '')).encode('utf8')).hexdigest()
        tt=key=='tiktok_bibica';c['shipped']=date(row.get('Shipped Time' if tt else 'Ngày gửi hàng'))
        for name,header in [('payment_upper','Tổng số tiền Người mua thanh toán'),('payment_lower','Tổng số tiền người mua thanh toán'),('list_unit_price','SKU Unit Original Price' if tt else 'Giá gốc')]:
            v=money(row.get(header));c[name]=str(v) if v is not None else None
    return c

def preflight(data_dir):
    missing=[name for name,_,_ in SOURCES.values() if not(data_dir/name).is_file()]
    if missing:raise FileNotFoundError('Missing required sources: '+', '.join(missing))

def records(key,path,seed_silver=None):
    if seed_silver:
        manifest=json.loads((seed_silver/'manifest.json').read_text(encoding='utf8'))
        m=manifest['files'][key];cached=seed_silver/m['file']
        if m['source_sha256']!=checksum(path) or m['sha256']!=checksum(cached):raise ValueError('Silver hash mismatch')
        h=hashlib.sha256();n=0
        with cached.open(encoding='utf-8-sig',newline='') as f:
            for row in csv.DictReader(f):
                original={k:row[k] for k in m['original_columns']}
                h.update(json.dumps(list(original.values()),ensure_ascii=False).encode('utf8')+b'\n');n+=1
                yield int(row['Source Row']),original,row.get('source_row_hash')
        if n!=m['rows'] or h.hexdigest()!=m['original_values_sha256']:raise ValueError('Silver original values mismatch')
    else:
        for locator,row in rows(path):yield locator,row,None

def require_headers(key,row):
    required=(['order_id','product_id','rating','data'] if 'web_scraper_order' in row else ['order_id','star_level','review_date']) if key=='ratings' else ['Order ID','SKU ID','Product Name','Warehouse Name','Province'] if key=='tiktok_bibica' else ['Mã đơn hàng','Tên sản phẩm','Tên kho hàng','Tỉnh/Thành phố']
    if not all(h in row for h in required):raise ValueError('Required source headers missing: '+key)
