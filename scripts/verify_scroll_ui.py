"""Roll up executed compact-UI evidence; no ETL or production-readiness claim."""
import hashlib
import json
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def metrics(rows):
    panels = [p for row in rows for p in row['panels']]
    return {'views':len(rows), 'scrolling_panels':sum(p['overflow'] > 4 for p in panels),
            'max_vertical_overflow_px':max(p['overflow'] for p in panels)}


def main():
    before = read('.runtime/scroll-before.json')
    after = read('.runtime/scroll-after.json')
    details = read('reports/scroll_detail_layouts.json')
    browser = read('reports/scroll_browser.json')
    frontend = read('reports/scroll_frontend.json')
    previous = read('reports/phase3_acceptance.json')
    expected_kpis = read('reports/phase3_api.json')['kpis']
    checks = {
        'same_54_view_cohorts': [(r['width'],r['height'],r['path'],r['tab']) for r in before] == [(r['width'],r['height'],r['path'],r['tab']) for r in after] and len(after) == 54,
        'common_desktop_panels_fit': all(r['horizontal'] <= 1 and r['documentOverflow'] <= 1 and all(p['overflow'] <= 4 for p in r['panels']) for r in after),
        '51_expanded_panels_fit': len(details) == 51 and all(r['overflow'] <= 4 and r['horizontal'] <= 4 and r['height'] > 100 for r in details),
        '15_browser_journeys': browser['stats']['expected'] == 15 and all(browser['stats'][k] == 0 for k in ['unexpected','skipped','flaky']),
        '34_component_tests': frontend['numPassedTests'] == frontend['numTotalTests'] == 34 and frontend['numFailedTests'] == 0,
        'api_and_dss_implementation_unchanged': all(sha(ROOT/n) == value for n,value in previous['source_code_sha256'].items() if n.startswith(('src/api/','src/dss/','DW/'))),
    }
    with urllib.request.urlopen('http://127.0.0.1:8001/api/v1/overview/kpis', timeout=30) as r:
        current = json.load(r)['data']
    checks['full_data_kpis_unchanged'] = all(str(current[k]) == str(v) for k,v in expected_kpis.items())
    with urllib.request.urlopen('http://127.0.0.1:8001/health', timeout=5) as r:
        health = json.load(r)['data']
    checks['live_repository_database'] = health['ready'] and health['database'] == 'bibica_repo'
    with urllib.request.urlopen('http://127.0.0.1:5174/', timeout=5) as r:
        checks['live_frontend'] = r.status == 200
    cmd = ['git','-c','safe.directory='+ROOT.as_posix()]
    subprocess.run([*cmd,'diff','--check'],cwd=ROOT,capture_output=True,check=True)
    checks['whitespace'] = True
    raw = (ROOT/'.runtime/scroll-build.log').read_bytes()
    log = raw.decode('utf16' if raw.startswith(b'\xff\xfe') else 'utf8')
    files = [p for p in (ROOT/'frontend/src').rglob('*') if p.is_file()]
    index = ROOT/'frontend/dist/index.html'
    checks['fresh_production_build'] = 'built in' in log and index.exists() and index.stat().st_mtime >= max(p.stat().st_mtime for p in files)
    comparison = {'status':'PASS' if all(checks.values()) else 'FAIL','before':metrics(before),'after':metrics(after),'measurements_before':before,'measurements_after':after}
    (ROOT/'reports/scroll_comparison.json').write_text(json.dumps(comparison,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    files += list((ROOT/'frontend/e2e').glob('*.js')) + [ROOT/'frontend/playwright.config.js', Path(__file__).resolve()]
    report = {'status':comparison['status'],'executed_at':datetime.now(timezone.utc).isoformat(),'checks':checks,
              'counts':{'component_tests':34,'browser_journeys':15,'main_desktop_views':54,'expanded_desktop_panels':51},
              'comparison':{'before':comparison['before'],'after':comparison['after']},
              'api_stall_observed_during_work':read('reports/scroll_runtime_recovery.json'),
              'production_runtime_certified':False,'committed_or_pushed':False,
              'source_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)},
              'limitations':['Common real-data and DEMO states verified; arbitrary long lists, explanations and narrow screens may scroll within panels.',
                             'Existing DSS scenario/data availability and Phase 2 operational limitations remain.',
                             'An API stall was observed, recovered by owned-process restart; underlying cause not established or fixed by UI work.']}
    (ROOT/'reports/scroll_acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'status':report['status'],'checks':checks,'comparison':report['comparison']}))
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
