import csv,json,os,tempfile,unittest,uuid
from pathlib import Path
import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo
from openpyxl import Workbook
from DW.etl.common import SOURCES
from DW.etl.engine import load_postgres
from DW.etl.cli import main
from DW.etl.categorization import categorize_product
from DW.etl.geography import warehouse
from DW.etl.geography import normalize_province
from DW.etl.ratings import project_scraped_rating

def sales(tt=True,**changes):
    d=({'Order ID':'100000000000000001','SKU ID':'2000000000000000001','Product Name':'Bánh TEST','Quantity':'2','SKU Subtotal Before Discount':'200','SKU Subtotal After Discount':'180','SKU Seller Discount':'20','Order Amount':'180','Created Time':'2026-10-01 10:00:00','Order Status':'Completed','Warehouse Name':'BIBICA HCM','Province':'Tỉnh Đồng Nai'} if tt else
       {'Mã đơn hàng':'S1','SKU phân loại hàng':'S1','Tên sản phẩm':'Kẹo TEST','Số lượng':'2','Giá gốc':'100','Tổng số tiền Người mua thanh toán':'180','Tổng số tiền người mua thanh toán':'180','Người bán trợ giá':'20','Ngày đặt hàng':'2026-10-01 10:00:00','Trạng Thái Đơn Hàng':'Hoàn thành','Tên kho hàng':'Kho Hà Nội','Tỉnh/Thành phố':'Tỉnh Đồng Nai'})
    d.update(changes);return d

def rating(oid='100000000000000001'):
    return {'order_id':oid,'product_id':'3000000000000000001','web_scraper_order':'1','web_scraper_start_url':'https://example.invalid/list',
       'data':'Mã đơn '+oid,'name':'SYNTHETIC','data2':'3000000000000000001','data3':'Bánh TEST','data4':'Gói TEST','data5':'Ngon','data6':'2026-10-04','rating':'5'}

def write(folder,key,records):
    path=folder/SOURCES[key][0];headers=list(dict.fromkeys(k for r in records for k in r))
    if path.suffix=='.csv':
        with path.open('w',encoding='utf8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=headers);w.writeheader();w.writerows(records)
    else:
        b=Workbook();s=b.active;s.title='Ratings' if key=='ratings' else 'orders';s.append(headers)
        for r in records:s.append([r.get(k) for k in headers])
        if key=='ratings':b.create_sheet('Nguon').append(['metadata only'])
        b.save(path);b.close()

class Contracts(unittest.TestCase):
    def test_common_rules_and_geography(self):
        for name,expected in [('Bánh ngũ cốc','Bánh'),('Ngũ cốc nguyên hạt','Ngũ cốc'),('[QUÀ TẶNG] Bánh','Quà tặng'),('Bánh kẹo','Bánh'),('[TẶNG QUÀ - DATE MỚI] Bánh','Bánh'),('không rõ',None)]:
            self.assertEqual(categorize_product(name).canonical_category,expected)
        self.assertEqual(warehouse('BIBICA HCM')['warehouse_region'],'Hồ Chí Minh')
        self.assertEqual(warehouse('Kho chưa xác định')['warehouse_region'],'Unknown')
        for text,expected in [('Tinh Dong Nai','Đồng Nai'),('Phố Hà Nội','Hà Nội'),('Khánh Hoà','Khánh Hòa'),('Thừa Thiên Huế','Thừa Thiên Huế'),('Huế','Huế')]:
            self.assertEqual(normalize_province(text)['customer_province'],expected)

    def test_text_ids_and_rounded_cells(self):
        r=rating();a=project_scraped_rating(r);self.assertEqual(a['review_id_status'],'EXACT_TEXT_IDS')
        r['order_id']=1e17;r['product_id']=3e18
        b=project_scraped_rating(r);self.assertEqual(b['order_id'],a['order_id']);self.assertEqual(b['product_id'],a['product_id'])
        r['data']='';self.assertEqual(project_scraped_rating(r)['order_id'],'')

@unittest.skipUnless(os.getenv('BIBICA_TEST_DSN'),'Set BIBICA_TEST_DSN for disposable PostgreSQL tests')
class Database(unittest.TestCase):
    def setUp(self):
        self.base=os.environ['BIBICA_TEST_DSN'];self.db='bibica_test_'+uuid.uuid4().hex[:12]
        with psycopg.connect(self.base,autocommit=True) as c:c.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(self.db)))
        self.dsn=make_conninfo(self.base,dbname=self.db);self.tmp=tempfile.TemporaryDirectory();self.folder=Path(self.tmp.name)
        write(self.folder,'shopee_bibica',[sales(False)]);write(self.folder,'shopee_quasure',[sales(False)])
        write(self.folder,'tiktok_bibica',[sales(),sales()]);write(self.folder,'ratings',[rating(),rating(),rating('100000000000000099')])

    def tearDown(self):
        self.tmp.cleanup()
        with psycopg.connect(self.base,autocommit=True) as c:c.execute(sql.SQL('DROP DATABASE {}').format(sql.Identifier(self.db)))

    def q(self,s):
        with psycopg.connect(self.dsn) as c:return c.execute(s).fetchall()

    def test_snapshot_change_replay_retraction_and_atomic_failure(self):
        first=load_postgres(self.folder,self.dsn,'first');self.assertEqual(first['counts'],{'orders':3,'items':3,'reviews':1})
        product=self.q("SELECT source_product_sku_key FROM dw.dim_source_product_sku WHERE native_sku_id='2000000000000000001'")[0][0]
        replay=load_postgres(self.folder,self.dsn,'replay');self.assertEqual((replay['inserted'],replay['updated']),(0,0));self.assertEqual(replay['counts'],first['counts'])
        changed=sales(**{'Quantity':'3','Product Name':'Bánh TEST tên mới','SKU Subtotal Before Discount':'300','Order Amount':'500','Order Status':'Cancelled'})
        new=sales(**{'SKU ID':'2000000000000000002','Quantity':'1','Product Name':'Kẹo TEST','Order Amount':'500','Order Status':'Cancelled'})
        write(self.folder,'tiktok_bibica',[changed,new]);r=load_postgres(self.folder,self.dsn,'changed')
        self.assertEqual(r['counts']['items'],4)
        self.assertEqual(self.q("SELECT source_product_sku_key FROM dw.dim_source_product_sku WHERE native_sku_id='2000000000000000001'")[0][0],product)
        self.assertEqual(self.q("SELECT order_row_count,order_amount_source FROM dw.fact_order_lifecycle_candidate f JOIN dw.dim_order_identity o USING(order_key) WHERE native_order_id='100000000000000001'")[0],(2,500))
        self.assertEqual(self.q('SELECT sum(source_line_count) FROM mart.mv_item_units_monthly')[0][0],4)
        write(self.folder,'tiktok_bibica',[new]);r=load_postgres(self.folder,self.dsn,'retracted');self.assertEqual(r['counts']['items'],3)
        before=self.q('SELECT sum(quantity) FROM dw.fact_order_line_candidate')
        write(self.folder,'shopee_bibica',[sales(False,**{'Số lượng':'99'})]);write(self.folder,'tiktok_bibica',[{'bad':'header'}])
        with self.assertRaises(ValueError):load_postgres(self.folder,self.dsn,'bad')
        self.assertEqual(self.q('SELECT sum(quantity) FROM dw.fact_order_line_candidate'),before)
        (self.folder/SOURCES['ratings'][0]).unlink()
        self.assertEqual(main(['--load','--data-dir',str(self.folder),'--dsn',self.dsn]),1)

    def test_conflict_bucket_and_cross_source_namespace(self):
        write(self.folder,'tiktok_bibica',[sales(),sales(**{'SKU ID':'other','Order Amount':'999'})])
        r=load_postgres(self.folder,self.dsn,'conflict');self.assertEqual(r['counts']['orders'],3)
        self.assertEqual(self.q('SELECT sum(review_required_order_count) FROM mart.mv_order_counts_by_storefront')[0][0],1)
        self.assertEqual(self.q("SELECT count(*) FROM dw.dim_province WHERE normalized_province_name='Đồng Nai'")[0][0],1)
        self.assertEqual(self.q("SELECT count(*) FROM dw.dim_warehouse WHERE warehouse_region='Unknown'")[0][0],0)

    def test_legacy_locator_migration_archives_duplicates_and_reuses_sku(self):
        first=load_postgres(self.folder,self.dsn,'before-legacy')
        product=self.q("SELECT source_product_sku_key FROM dw.dim_source_product_sku WHERE native_sku_id='2000000000000000001'")[0][0]
        with psycopg.connect(self.dsn) as c:
            c.execute('DROP INDEX dw.ux_line_current_locator');c.execute('DROP INDEX dw.ux_review_current_locator')
            c.execute('UPDATE dw.fact_order_line_candidate SET source_code=NULL');c.execute('UPDATE dw.fact_review_candidate SET source_code=NULL')
            c.execute('UPDATE dw.dim_source_product_sku SET product_nk=NULL')
            sf=c.execute("INSERT INTO dw.dim_source_file(source_file_name,source_sha256,sheet_name,source_kind,source_storefront) VALUES('legacy-copy.csv',%s,'csv','tiktok_sales','Bibica TikTok Shop') RETURNING source_file_key",('0'*64,)).fetchone()[0]
            columns=[r[0] for r in c.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='dw' AND table_name='fact_order_line_candidate' AND column_name<>'order_line_key' ORDER BY ordinal_position")]
            select=sql.SQL(',').join(sql.Placeholder() if n=='source_file_key' else sql.Identifier(n) for n in columns)
            c.execute(sql.SQL('INSERT INTO dw.fact_order_line_candidate ({}) SELECT {} FROM dw.fact_order_line_candidate WHERE storefront_key=(SELECT storefront_key FROM dw.dim_storefront WHERE storefront_code=\'bibica_tiktok_shop\') LIMIT 1').format(sql.SQL(',').join(map(sql.Identifier,columns)),select),(sf,))
            c.execute("UPDATE ops.source_current SET parser_version='legacy'")
        after=load_postgres(self.folder,self.dsn,'legacy-upgrade')
        self.assertEqual(after['counts'],first['counts'])
        self.assertGreaterEqual(self.q("SELECT count(*) FROM ops.migration_history WHERE entity='order_line'")[0][0],1)
        self.assertEqual(self.q("SELECT source_product_sku_key FROM dw.dim_source_product_sku WHERE native_sku_id='2000000000000000001'")[0][0],product)
