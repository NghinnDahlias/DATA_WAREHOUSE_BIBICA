"""Assemble Phase 3 evidence after execution; never promotes missing/failed checks."""
import hashlib
import json
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args):
    return subprocess.run(['git', '-c', 'safe.directory=' + ROOT.as_posix(), *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def main():
    checks = {}
    backend = read('reports/phase2_tests.json')
    frontend = read('reports/phase3_frontend.json')
    browser = read('reports/phase3_browser.json')
    api = read('reports/phase3_api.json')
    layouts = read('reports/phase3_layouts.json')
    replay = read('reports/phase3_features_replay.json')
    runtime = read('reports/phase3_runtime.json')
    checks['backend'] = backend['status'] == 'PASS' and backend['tests'] == 116 and backend['skipped'] == 0
    checks['frontend'] = frontend['numPassedTests'] == frontend['numTotalTests'] == 34 and frontend['numFailedTests'] == 0
    checks['browser'] = browser['stats']['expected'] == 12 and all(browser['stats'][k] == 0 for k in ['unexpected', 'skipped', 'flaky'])
    checks['full_data_api'] = api['status'] == 'PASS' and all(api['checks'].values()) and len(api['checks']) == 34
    checks['workspace_geometry'] = layouts['status'] == 'PASS' and len(layouts['measurements']) == 20 and all(m['no_horizontal_overflow'] and m['fits_one_screen'] and all(p['height'] > 0 for p in m['panels']) for m in layouts['measurements'])
    checks['feature_replay'] = replay['status'] == 'PASS' and replay['before'] == replay['after'] and replay['after']['rows'] == 5625
    checks['runtime_script_lifecycle'] = runtime['status'] == 'PASS' and runtime['reused_owned_process'] and runtime['restarted_owned_process']
    with urllib.request.urlopen('http://127.0.0.1:8001/health', timeout=5) as r:
        health = json.load(r)['data']
    with urllib.request.urlopen('http://127.0.0.1:5174/', timeout=5) as r:
        checks['live_frontend'] = r.status == 200 and b'Bibica' in r.read()
    checks['live_database'] = health['ready'] and health['database'] == 'bibica_repo'
    checks['native_git_tree_unchanged'] = not git('diff', '--name-only', 'be9117a', '--', 'Data')
    git('diff', '--check')
    checks['git_whitespace'] = True
    subprocess.run([sys.executable, '-X', 'utf8', '-m', 'compileall', '-q', 'src', 'scripts', 'DW'], cwd=ROOT, check=True)
    checks['python_compileall'] = True
    raw_log = (ROOT / '.runtime/phase3-build.log').read_bytes()
    log = raw_log.decode('utf16' if raw_log.startswith(b'\xff\xfe') else 'utf8')
    assets = [p for p in (ROOT / 'frontend/dist').rglob('*') if p.is_file()]
    checks['production_build'] = 'built in' in log and (ROOT / 'frontend/dist/index.html').is_file() and any(p.suffix == '.js' for p in assets)
    build = {'status': 'PASS' if checks['production_build'] else 'FAIL', 'command': 'npm --prefix frontend run build',
             'artifacts': {p.relative_to(ROOT).as_posix(): {'bytes':p.stat().st_size, 'sha256':sha(p)} for p in assets},
             'warnings': ['Vite JavaScript chunk exceeds 500 kB before gzip; not production network benchmarking.']}
    (ROOT / 'reports/phase3_build.json').write_text(json.dumps(build, indent=2)+'\n', encoding='utf8')
    files = set()
    for folder in ['frontend/src', 'frontend/e2e', 'frontend/tests', 'src/api', 'src/dss', 'tests']:
        files.update(p for p in (ROOT / folder).rglob('*') if p.is_file() and p.suffix in ['.js','.jsx','.py','.css'])
    for name in ['frontend/package.json','frontend/package-lock.json','frontend/vite.config.js','frontend/playwright.config.js',
                 'DW/postgresql/tables/040_api_dss.sql','scripts/build_review_theme_features.py','scripts/verify_phase3.py',
                 'scripts/start_frontend.ps1','scripts/stop_frontend.ps1','scripts/finalize_phase3.py']:
        files.add(ROOT / name)
    evidence_names = ['phase2_tests.json','phase2_tests.log','phase3_frontend.json','phase3_browser.json','phase3_api.json',
                      'phase3_layouts.json','phase3_features_replay.json','phase3_runtime.json','phase3_build.json']
    report = {
        'status': 'PASS_WITH_LIMITATIONS' if all(checks.values()) else 'FAIL',
        'executed_at': datetime.now(timezone.utc).isoformat(),
        'input_commit': git('rev-parse','HEAD'), 'origin_main_at_fetch': git('rev-parse','origin/main'),
        'local_changes_committed_or_pushed': False, 'production_automation_ready': False,
        'checks': checks, 'counts': {'backend_tests':116,'frontend_tests':34,'browser_journeys':12,'api_checks':34,'geometry_measurements':20},
        'kpis': api['kpis'], 'core_schema': {'dimensions':12,'facts':3,'foreign_keys':56},
        'review_feature': {'auxiliary_tables':1,'additional_foreign_keys':1,'rows':5625},
        'source_code_sha256': {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)},
        'evidence_sha256': {n:sha(ROOT/'reports'/n) for n in evidence_names},
        'limitations': [
            'Long tables/forms/explanations scroll inside panels; viewport fit does not mean all content visible simultaneously.',
            'Route risk does not support product/category cohort; UI hides unfiltered scores under these filters.',
            'TikTok-only reviews and unvalidated heuristic mentions; no confirmed complaint/CRM replacement lifecycle.',
            'Scenario stock/expiry/capacity, no live WMS reservation; Phase 2 conditional acceptance persists.',
            'SQL serial guard required; parallel-plan root cause remains open.',
            'No cloud/Docker/remote CI/production load or deployment certification; old PDF/ZIP not refreshed.',
        ],
    }
    (ROOT / 'reports/phase3_acceptance.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    print(json.dumps({'status':report['status'], 'checks':len(checks), 'passed':sum(checks.values()), 'counts':report['counts']}))
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
