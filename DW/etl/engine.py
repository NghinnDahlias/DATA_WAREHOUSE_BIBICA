"""Transactional COPY/upsert engine; source snapshots have stable logical locators."""
import csv,hashlib,json,uuid
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from .common import ROOT,SOURCES,checksum,digest,parser_version
from .sources import SCOPES,preflight,records,project,require_headers
from .facts import load_facts
from .validation import validate,olap_checks

DDL_FILES=[ROOT/'DW/postgresql/schemas/001_create_schemas.sql',ROOT/'DW/postgresql/tables/010_dw_dimensions.sql',ROOT/'DW/postgresql/tables/020_dw_facts.sql',ROOT/'DW/postgresql/constraints_indexes/constraints_indexes.sql',ROOT/'DW/postgresql/tables/030_canonical_operations.sql',ROOT/'DW/postgresql/tables/040_api_dss.sql',ROOT/'DW/postgresql/tables/050_review_case_content.sql']
ANALYZE_SQL='ANALYZE dw.dim_category,dw.dim_channel,dw.dim_storefront,dw.dim_order_status,dw.dim_warehouse,dw.dim_province,dw.dim_source_product_sku,dw.dim_date,dw.dim_time,dw.fact_order_line_candidate,dw.fact_order_lifecycle_candidate,dw.fact_review_candidate'

def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf8')

def scope(c,key,sha,n,run_id):
    channel,storefront,label=SCOPES[key]
    ch=c.execute('INSERT INTO dw.dim_channel(channel_code,channel_name) VALUES(%s,%s) ON CONFLICT(channel_code) DO UPDATE SET channel_name=excluded.channel_name RETURNING channel_key',(channel,channel.title())).fetchone()['channel_key']
    st=c.execute('INSERT INTO dw.dim_storefront(channel_key,storefront_code,storefront_name) VALUES(%s,%s,%s) ON CONFLICT(storefront_code) DO UPDATE SET storefront_name=excluded.storefront_name RETURNING storefront_key',(ch,storefront,label)).fetchone()['storefront_key']
    filename=SOURCES[key][0];sheet='Ratings' if key=='ratings' else 'csv' if filename.endswith('.csv') else 'orders'
    sf=c.execute('INSERT INTO dw.dim_source_file(source_file_name,source_sha256,sheet_name,source_kind,source_storefront) VALUES(%s,%s,%s,%s,%s) ON CONFLICT(source_file_name,source_sha256,sheet_name) DO UPDATE SET source_storefront=excluded.source_storefront RETURNING source_file_key',
      (filename,sha,sheet,'tiktok_reviews' if key=='ratings' else 'tiktok_sales' if key=='tiktok_bibica' else 'shopee_orders',label)).fetchone()['source_file_key']
    bk=c.execute("INSERT INTO dw.dim_ingestion_batch(source_file_key,batch_id,started_at,load_status,row_count_read) VALUES(%s,%s,now(),'STARTED',%s) RETURNING ingestion_batch_key",(sf,run_id+':'+key,n)).fetchone()['ingestion_batch_key']
    c.execute('INSERT INTO source_scope VALUES(%s,%s,%s,%s,%s,%s,%s,%s)',(key,ch,st,channel,storefront,sf,bk,sheet))
    return sf,bk

def ingest_source(c,key,path,old,process_dir,seed_silver):
    c.execute('CREATE TEMP TABLE incoming(LIKE raw.source_row INCLUDING DEFAULTS) ON COMMIT DROP')
    target=process_dir/'Silver'/(path.stem+'.csv') if process_dir else None
    handle=target.with_suffix('.csv.partial').open('w',encoding='utf-8-sig',newline='') if target else None
    writer=None;original_h=hashlib.sha256();headers=[];n=0
    try:
        with c.cursor().copy('COPY incoming(source_code,row_no,row_hash,payload) FROM STDIN') as copy:
            for locator,row,row_hash in records(key,path,seed_silver):
                require_headers(key,row);data=project(key,locator,row);n+=1
                row_hash=row_hash or digest(json.dumps(row,ensure_ascii=False,sort_keys=True,default=str))
                copy.write_row((key,locator,row_hash,Jsonb(data)))
                if handle:
                    if writer is None:
                        headers=list(row)
                        added=['canonical_category','category_mapping_method','category_mapping_status','category_rule','warehouse_name','warehouse_region','warehouse_mapping_status','customer_province','source_row_hash','Source Row'] if key!='ratings' else ['source_row_hash','Source Row']
                        writer=csv.DictWriter(handle,fieldnames=headers+added);writer.writeheader()
                    values={k:'' if v is None else str(v) for k,v in row.items()}
                    original_h.update(json.dumps([values[h] for h in headers],ensure_ascii=False).encode('utf8')+b'\n')
                    values.update({h:data.get(h) or '' for h in added if h not in ['Source Row','source_row_hash']})
                    values.update({'Source Row':locator,'source_row_hash':row_hash});writer.writerow(values)
    finally:
        if handle:handle.close()
    if n==0:raise ValueError('Empty required source '+path.name)
    ins=c.execute('SELECT count(*) n FROM incoming i LEFT JOIN raw.source_row r USING(source_code,row_no) WHERE r.row_no IS NULL').fetchone()['n']
    upd=c.execute('SELECT count(*) n FROM incoming i JOIN raw.source_row r USING(source_code,row_no) WHERE i.row_hash IS DISTINCT FROM r.row_hash OR i.payload IS DISTINCT FROM r.payload').fetchone()['n']
    c.execute('INSERT INTO raw.source_row SELECT * FROM incoming ON CONFLICT(source_code,row_no) DO UPDATE SET row_hash=excluded.row_hash,payload=excluded.payload')
    c.execute('DELETE FROM raw.source_row r WHERE source_code=%s AND NOT EXISTS(SELECT 1 FROM incoming i WHERE(i.source_code,i.row_no)=(r.source_code,r.row_no))',(key,))
    c.execute('DROP TABLE incoming')
    meta=None
    if target:
        # Verify persisted Silver original decoded values, never print its private rows.
        h=hashlib.sha256();count=0
        with target.with_suffix('.csv.partial').open(encoding='utf-8-sig',newline='') as f:
            for r in csv.DictReader(f):h.update(json.dumps([r[k] for k in headers],ensure_ascii=False).encode('utf8')+b'\n');count+=1
        if count!=n or h.digest()!=original_h.digest():raise RuntimeError('Silver original values changed')
        target.with_suffix('.csv.partial').replace(target)
        meta={'file':target.name,'rows':n,'sha256':checksum(target),'source_sha256':checksum(path),'original_columns':headers,'original_values_sha256':h.hexdigest()}
    return n,ins,upd,meta

def load_postgres(data_dir,dsn,batch_id=None,*,process_dir=None,seed_silver=None):
    data_dir=Path(data_dir);preflight(data_dir);run_id=(batch_id or 'etl')+'-'+uuid.uuid4().hex[:12]
    # Legacy DDL includes explicit BEGIN/COMMIT. Apply it before the atomic data transaction.
    with psycopg.connect(dsn,row_factory=dict_row,autocommit=True) as c:
        c.execute('SELECT pg_advisory_lock(4031262)')
        for path in DDL_FILES:c.execute(path.read_text(encoding='utf-8-sig'))
        c.execute("INSERT INTO ops.etl_run(run_id,status) VALUES(%s,'RUNNING')",(run_id,))
    inserted=updated=0;source_counts={};silver_files={}
    try:
        with psycopg.connect(dsn,row_factory=dict_row) as c:
            c.execute('SET LOCAL statement_timeout=0');c.execute('SELECT pg_advisory_xact_lock(4031262)')
            c.execute('CREATE TEMP TABLE source_scope(source_code text PRIMARY KEY,channel_key bigint,storefront_key bigint,channel_code text,storefront_code text,source_file_key bigint,ingestion_batch_key bigint,sheet_name text) ON COMMIT DROP')
            for key,(filename,_,_) in SOURCES.items():
                path=data_dir/filename;sha=checksum(path)
                old=c.execute('SELECT * FROM ops.source_current WHERE source_code=%s',(key,)).fetchone()
                version=parser_version(key)+('|repo-current-v3-shipped' if key.startswith('shopee_') else '|repo-current-v2')
                unchanged=old and old['sha256']==sha and old['parser_version']==version
                n=old['row_count'] if unchanged else 0
                need_export=process_dir and not(process_dir/'Silver'/(path.stem+'.csv')).exists()
                if not unchanged or need_export:
                    n,ins,upd,meta=ingest_source(c,key,path,old,process_dir,seed_silver);inserted+=ins;updated+=upd
                    if meta:silver_files[key]=meta
                sf,bk=scope(c,key,sha,n,run_id);source_counts[key]=n
                c.execute('INSERT INTO ops.source_current VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT(source_code) DO UPDATE SET source_file_key=excluded.source_file_key,sha256=excluded.sha256,parser_version=excluded.parser_version,row_count=excluded.row_count,run_id=excluded.run_id',(key,sf,sha,version,n,run_id))
                c.execute("UPDATE dw.dim_ingestion_batch SET load_status=%s,completed_at=now(),row_count_loaded=%s WHERE ingestion_batch_key=%s",('REPLAYED' if unchanged else 'LOADED',0 if unchanged else n,bk))
            c.execute((ROOT/'DW/etl/transform.sql').read_text(encoding='utf8'));load_facts(c);checks=validate(c)
            c.execute(ANALYZE_SQL)
            c.execute((ROOT/'DW/04_sql/olap/02_materialized_views.sql').read_text(encoding='utf8'));checks.update(olap_checks(c))
            counts=c.execute('SELECT (SELECT count(*) FROM dw.fact_order_lifecycle_candidate) orders,(SELECT count(*) FROM dw.fact_order_line_candidate) items,(SELECT count(*) FROM dw.fact_review_candidate) reviews').fetchone()
            quarantine=c.execute('SELECT source_code,reason,count(*) records FROM ops.quarantine GROUP BY 1,2 ORDER BY 1,2').fetchall()
            c.execute("UPDATE ops.etl_run SET status='SUCCESS',ended_at=now(),counts=%s WHERE run_id=%s",(Jsonb(counts),run_id))
        report={'status':'PASS','run_id':run_id,'source_counts':source_counts,'inserted':inserted,'updated':updated,'counts':counts,'quarantine':quarantine,'checks':checks}
        is_default_source=data_dir.resolve()==(ROOT/'Data/Data_Source_Raw').resolve()
        report['mode']='FULL' if is_default_source else 'CUSTOM'
        if is_default_source:dump(ROOT/'reports/etl_validation.json',report)
        elif process_dir:dump(process_dir/'validation.json',report)
        if process_dir:
            from .categorization import CATEGORY_VERSION
            from .geography import GEOGRAPHY_VERSION
            mp=process_dir/'Silver/manifest.json';previous=json.loads(mp.read_text(encoding='utf8'))['files'] if mp.exists() else {}
            previous.update(silver_files);dump(mp,{'version':CATEGORY_VERSION,'geography_version':GEOGRAPHY_VERSION,'files':previous})
        return report
    except Exception as e:
        with psycopg.connect(dsn,autocommit=True) as c:c.execute("UPDATE ops.etl_run SET status='FAILED',ended_at=now(),error_code=%s WHERE run_id=%s",(type(e).__name__,run_id))
        raise
