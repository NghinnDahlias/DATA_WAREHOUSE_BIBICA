"""Validate fresh evidence and record conditional Phase2 acceptance without publishing."""
import compileall
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

import httpx
from DW.etl.common import SOURCES, checksum


def git(*arguments):
    return subprocess.run(['git', '-c', 'safe.directory='+root.as_posix(), *arguments],
                          cwd=root, check=True, capture_output=True, text=True, encoding='utf8').stdout.strip()


def main():
    paths = {
        'tests': 'reports/phase2_tests.json',
        'full_data': 'reports/phase2_verification.json',
        'live_http': 'reports/phase2_live_http.json',
        'etl': 'reports/etl_validation.json',
        'layers': 'reports/processing_verification.json',
        'integrity': 'reports/phase2_assessment/integrity.json',
        'capabilities': 'reports/phase2_assessment/integrity_live_v2.json',
        'allocation': 'reports/phase2_assessment/allocation.json',
        'reviews': 'reports/phase2_assessment/reviews.json',
        'parallel': 'reports/phase2_assessment/sql_parallel_diagnostic.json',
    }
    reports = {name:json.loads((root/path).read_text(encoding='utf8')) for name,path in paths.items()}
    checks = {name+'_report_pass': value['status']=='PASS' for name,value in reports.items() if name!='parallel'}
    tests = reports['tests']
    checks['full_suite_no_skips'] = tests['tests']>=114 and tests['failures']==tests['errors']==tests['skipped']==0
    checks['independent_kpi_cohorts_match'] = reports['integrity']['details']['cohort_probe_count']==68 and reports['integrity']['details']['measure_comparisons']==2108
    checks['oracle_cases_all_three_shops'] = reports['allocation']['scenario_cases']==90 and all(reports['allocation']['checks'].values())
    checks['sql_serial_mitigation_verified'] = reports['parallel']['serial_mismatches']==0 and reports['parallel']['queries_per_mode']==24
    checks['sql_guard_present'] = 'SET LOCAL max_parallel_workers_per_gather=0' in (root/'src/api/db.py').read_text(encoding='utf8')
    checks['four_native_sources_unchanged'] = all(
        checksum(root/'Data/Data_Source_Raw'/SOURCES[row['source_code']][0])==row['sha256']
        for row in reports['full_data']['source_rows'])
    checks['no_raw_git_changes'] = not git('diff','--name-only','HEAD','--','Data')
    checks['nothing_staged'] = not git('diff','--cached','--name-only')
    checks['private_layers_ignored'] = len(git('check-ignore','data process/Raw/manifest.json','data process/Golden/schema.sql','.runtime/api-service.json').splitlines())==3
    git('diff','--check')
    checks['python_compiles'] = all(compileall.compile_dir(str(root/folder),quiet=1) for folder in ['src','DW','scripts','tests'])
    with httpx.Client(base_url='http://127.0.0.1:8001',timeout=30) as client:
        response=client.get('/health')
    checks['live_repository_db_ready'] = response.status_code==200 and response.json()['data']['database']=='bibica_repo'
    module_paths = list((root/'src/api').glob('*.py')) + list((root/'src/dss').glob('*.py'))
    module_paths += [root/'DW/etl/engine.py',root/'DW/etl/sources.py',root/'DW/postgresql/tables/040_api_dss.sql']
    source_hashes = {path.relative_to(root).as_posix():checksum(path) for path in sorted(module_paths)}
    current = reports['full_data']['kpis']
    result = {
        'status':'CONDITIONAL_ACCEPTANCE' if all(checks.values()) else 'FAIL',
        'executed_at':datetime.now(timezone.utc).isoformat(), 'client_date':'2026-11-05',
        'technical_gates':checks, 'analysis_scenario_ready':all(checks.values()),
        'production_automation_ready':False,
        'tests':tests['tests'],'allocation_scenarios':90,'integrity_assertions':len(reports['integrity']['checks']),
        'kpi_cohorts':68,'numeric_comparisons':2108,'review_assertions':len(reports['reviews']['checks']),
        'full_data_assertions':len(reports['full_data']['checks']),
        'etl_assertions':len(reports['etl']['checks']),'layer_assertions':len(reports['layers']['checks']),
        'counts':reports['etl']['counts'],'completed_payable':current['completed_payable'],'completed_units':current['completed_units'],
        'business_conditions':[
            'Reconcile breakfast SKU/effective policy and observed HCM-heavy historical warehouse labels.',
            'Confirm spoken Pleasure versus native Quasure storefront alias.',
            'Inventory/lot expiry/capacity/reservation and complaint/customer events need validated operational contracts.',
            'Review mention labels lack independently human-validated precision/recall; risk is uncalibrated.',
            'Keep serial SQL guard. Underlying parallel engine/plan cause remains unresolved.'
        ],
        'sql_diagnostic':{key:reports['parallel'][key] for key in ['queries_per_mode','parallel_mismatches','serial_mismatches']},
        'evidence_paths':paths,'evidence_sha256':{path:checksum(root/path) for path in paths.values()},
        'verified_source_sha256':source_hashes,
        'git_head':git('rev-parse','HEAD'),'origin_main':git('rev-parse','origin/main'),
        'committed_or_pushed_at_verification':False,'git_fields_are_verification_snapshot':True,
        'api_url':'http://127.0.0.1:8001/docs',
    }
    (root/'reports/phase2_acceptance.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({key:result[key] for key in ['status','technical_gates','tests','allocation_scenarios','kpi_cohorts','numeric_comparisons','counts','sql_diagnostic']},ensure_ascii=False))
    return 0 if all(checks.values()) else 1


if __name__=='__main__':
    raise SystemExit(main())
