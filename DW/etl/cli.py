"""CLI failures are nonzero; no raw rows, buyer data or driver details are printed."""
import argparse,json,os
from pathlib import Path
from .common import ROOT,SOURCES
from .sources import preflight,records,project,require_headers
from .engine import load_postgres

def dry_run(data_dir):
    data_dir=Path(data_dir);preflight(data_dir);counts={}
    for key,(name,_,_) in SOURCES.items():
        n=0
        for locator,row,_ in records(key,data_dir/name):require_headers(key,row);project(key,locator,row);n+=1
        counts[key]=n
    return {'status':'INSPECTED','source_counts':counts,'database_loaded':False},0

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    m=p.add_mutually_exclusive_group(required=True);m.add_argument('--dry-run',action='store_true');m.add_argument('--load',action='store_true');m.add_argument('--process',action='store_true')
    p.add_argument('--data-dir',type=Path,default=ROOT/'Data/Data_Source_Raw');p.add_argument('--dsn',default=os.getenv('BIBICA_DSN'));p.add_argument('--batch-id');p.add_argument('--seed-silver',type=Path)
    a=p.parse_args(argv)
    if not a.dry_run and not a.dsn:p.error('--dsn or BIBICA_DSN is required; use a separate repo database')
    try:
        if a.dry_run:r,code=dry_run(a.data_dir)
        elif a.process:
            from .processing import process
            r=process(a.data_dir,a.dsn,a.batch_id,a.seed_silver);code=0
        else:r=load_postgres(a.data_dir,a.dsn,a.batch_id);code=0
        print(json.dumps(r,ensure_ascii=False,default=str));return code
    except Exception as e:
        print(json.dumps({'status':'FAIL','error_code':type(e).__name__}));return 1
