"""Verify private exports, reload Golden in a newly created DB, and prove replay stability."""
import argparse,csv,hashlib,json,re,uuid
from pathlib import Path
import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo
from psycopg.rows import dict_row
from .common import ROOT,SOURCES,checksum
from .engine import load_postgres,dump
from .processing import golden
from .sources import project

def fingerprint(c,name):
    key=c.execute('SELECT a.attname FROM pg_index i JOIN pg_attribute a ON a.attrelid=i.indrelid AND a.attnum=ANY(i.indkey) WHERE i.indrelid=%s::regclass AND i.indisprimary ORDER BY a.attnum',('dw.'+name,)).fetchone()['attname']
    return c.execute(sql.SQL("SELECT count(*) records,md5(string_agg(md5(to_jsonb(t)::text),'' ORDER BY {})) fingerprint FROM dw.{} t").format(sql.Identifier(key),sql.Identifier(name))).fetchone()

def verify(dsn,rerun=False,data_dir=None):
    base=ROOT/'data process';data_dir=Path(data_dir or ROOT/'Data/Data_Source_Raw');checks={}
    raw=json.loads((base/'Raw/manifest.json').read_text(encoding='utf8'))
    checks['four_raw_bytes']=set(raw)==set(SOURCES) and all(checksum(data_dir/d['file'])==checksum(base/'Raw'/d['file'])==d['sha256'] for d in raw.values())
    silver=json.loads((base/'Silver/manifest.json').read_text(encoding='utf8'))['files']
    for key,m in silver.items():
        path=base/'Silver'/m['file'];h=hashlib.sha256();n=0;rules=True
        with path.open(encoding='utf-8-sig',newline='') as f:
            for row in csv.DictReader(f):
                original={k:row[k] for k in m['original_columns']};h.update(json.dumps(list(original.values()),ensure_ascii=False).encode('utf8')+b'\n');n+=1
                if key!='ratings':
                    p=project(key,int(row['Source Row']),original)
                    rules=rules and all(row[k]==str(p.get(k) or '') for k in ['canonical_category','category_rule','warehouse_name','warehouse_region','customer_province'])
        checks[key+'_silver']=checksum(path)==m['sha256'] and n==m['rows'] and h.hexdigest()==m['original_values_sha256'] and rules
    with psycopg.connect(dsn,row_factory=dict_row) as c:
        c.execute("SET TIME ZONE 'Asia/Ho_Chi_Minh'")
        before={n:fingerprint(c,n) for n in ['fact_order_line_candidate','fact_order_lifecycle_candidate','fact_review_candidate']}
    if rerun:
        r=load_postgres(data_dir,dsn,'verify-replay')
        with psycopg.connect(dsn,row_factory=dict_row) as c:
            c.execute("SET TIME ZONE 'Asia/Ho_Chi_Minh'")
            after={n:fingerprint(c,n) for n in before}
        checks['replay_zero_raw_writes']=r['inserted']==r['updated']==0
        checks['replay_fact_fingerprints']=before==after
        golden(dsn,base/'Golden')
    manifest=json.loads((base/'Golden/manifest.json').read_text(encoding='utf8'))
    schema=json.loads((base/'Golden/schema.json').read_text(encoding='utf8'))
    checks['golden_hashes']=all(checksum(base/'Golden'/m['file'])==m['sha256'] for m in manifest.values())
    pending=set(manifest);ordered=[]
    while pending:
        ready=[]
        for name in sorted(pending):
            refs={re.search(r'REFERENCES\s+(?:dw\.)?"?([a-z_]+)',v['definition']).group(1) for v in schema[name]['constraints'] if v['type']=='f'}
            if not(refs&pending):ready.append(name)
        if not ready:raise RuntimeError('Golden dependency cycle')
        ordered+=ready;pending-=set(ready)
    db='bibica_gold_'+uuid.uuid4().hex[:12];target=make_conninfo(dsn,dbname=db);created=False;loaded={}
    try:
        with psycopg.connect(dsn,autocommit=True) as c:c.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(db)))
        created=True
        with psycopg.connect(target,row_factory=dict_row) as c:
            c.execute("SET TIME ZONE 'Asia/Ho_Chi_Minh'");c.execute((base/'Golden/schema.sql').read_text(encoding='utf8'))
            for name in ordered:
                with (base/'Golden'/manifest[name]['file']).open('rb') as f,c.cursor().copy(sql.SQL('COPY dw.{} FROM STDIN WITH(FORMAT CSV,HEADER)').format(sql.Identifier(name))) as copy:
                    for chunk in iter(lambda:f.read(1024*1024),b''):copy.write(chunk)
                loaded[name]=c.execute(sql.SQL('SELECT count(*) n FROM dw.{}').format(sql.Identifier(name))).fetchone()['n']
                for a in schema[name]['columns']:
                    if a['identity']:
                        c.execute(sql.SQL("SELECT setval(pg_get_serial_sequence(%s,%s),coalesce((SELECT max({}) FROM dw.{}),1),(SELECT count(*)>0 FROM dw.{}))").format(sql.Identifier(a['name']),sql.Identifier(name),sql.Identifier(name)),('dw.'+name,a['name']))
            checks['golden_reload_counts']=all(loaded[n]==manifest[n]['rows'] for n in loaded)
            checks['golden_reload_fact_fingerprints']=all(fingerprint(c,n)==before[n] for n in before)
            fks=c.execute("SELECT count(*) n FROM pg_constraint WHERE connamespace='dw'::regnamespace AND contype='f'").fetchone()['n']
            checks['golden_foreign_keys']=fks==sum(v['type']=='f' for m in schema.values() for v in m['constraints'])
    finally:
        if created:
            with psycopg.connect(dsn,autocommit=True) as c:c.execute(sql.SQL('DROP DATABASE {}').format(sql.Identifier(db)))
    result={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'golden_tables':loaded,'foreign_keys':fks}
    dump(ROOT/'reports/processing_verification.json',result)
    root_report=json.loads((base/'manifest.json').read_text(encoding='utf8'))
    root_report['golden']=manifest;root_report['verification']=result
    dump(base/'manifest.json',root_report)
    if not all(checks.values()):raise RuntimeError('Private layer verification failed')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--dsn',required=True);p.add_argument('--rerun',action='store_true');a=p.parse_args()
    print(json.dumps(verify(a.dsn,a.rerun),ensure_ascii=False,default=str))
