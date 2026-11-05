"""Run every existing/new unittest, recording fresh execution evidence."""
import io
import json
import sys
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
started = time.perf_counter()
stream = io.StringIO()
result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.discover(str(root/'tests')))
report = {'status': 'PASS' if result.wasSuccessful() and not result.skipped else 'FAIL' if not result.wasSuccessful() else 'PARTIAL',
          'executed_at': datetime.now(timezone.utc).isoformat(), 'tests': result.testsRun,
          'failures': len(result.failures), 'errors': len(result.errors), 'skipped': len(result.skipped),
          'elapsed_seconds': round(time.perf_counter()-started,3)}
(root/'reports/phase2_tests.log').write_text(stream.getvalue(),encoding='utf8')
(root/'reports/phase2_tests.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(stream.getvalue())
print(json.dumps(report))
sys.exit(0 if result.wasSuccessful() else 1)
