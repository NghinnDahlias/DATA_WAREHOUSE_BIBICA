"""Run every existing/new unittest, recording fresh execution evidence."""
import argparse
import io
import json
import sys
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--portable', action='store_true', help='Exclude two checks requiring native source files.')
args = parser.parse_args()
suite = unittest.defaultTestLoader.discover(str(root/'tests'))
excluded = []
if args.portable:
    private_checks = {'ProfilingTests.test_source_discovery_contract', 'ProfilingTests.test_xlsx_stream_header'}
    def cases(node):
        for test in node:
            if isinstance(test, unittest.TestSuite):
                yield from cases(test)
            else:
                yield test
    included = []
    for test in cases(suite):
        if any(test.id().endswith(name) for name in private_checks):
            excluded.append(test.id())
        else:
            included.append(test)
    if len(excluded) != len(private_checks):
        raise RuntimeError('Portable profile does not match the two native-source checks')
    suite = unittest.TestSuite(included)
started = time.perf_counter()
stream = io.StringIO()
result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
report = {'status': 'PASS' if result.wasSuccessful() and not result.skipped else 'FAIL' if not result.wasSuccessful() else 'PARTIAL',
          'executed_at': datetime.now(timezone.utc).isoformat(), 'tests': result.testsRun,
          'failures': len(result.failures), 'errors': len(result.errors), 'skipped': len(result.skipped),
          'elapsed_seconds': round(time.perf_counter()-started,3),
          'profile': 'portable' if args.portable else 'full', 'excluded_private_checks': excluded}
(root/'reports').mkdir(exist_ok=True)
stem = 'portable_tests' if args.portable else 'phase2_tests'
(root/f'reports/{stem}.log').write_text(stream.getvalue(),encoding='utf8')
(root/f'reports/{stem}.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(stream.getvalue())
print(json.dumps(report))
sys.exit(0 if result.wasSuccessful() else 1)
