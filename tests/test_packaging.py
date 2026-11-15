import tempfile
import unittest
from pathlib import Path
import zipfile
from scripts.package_source import allowed, build_package


class SourcePackageTests(unittest.TestCase):
    def test_allowlist_excludes_private_and_generated_artifacts(self):
        for name in ['Data/Data_Source_Raw/source.xlsx', 'reports/run.json', '.runtime/log.txt',
                     'frontend/node_modules/module/index.js', 'frontend/dist/index.html',
                     'src/api/__pycache__/app.pyc', 'docs/secret.csv', 'frontend/.env',
                     '.env', 'data process/Golden/fact.csv', 'docs/db.dump']:
            self.assertFalse(allowed(Path(name)), name)
        for name in ['tests/test_api.py', 'frontend/tests/pages.test.jsx', 'frontend/e2e/review-reader.spec.js',
                     'DW/postgresql/tables/050_review_case_content.sql', 'docs/api/openapi.json', '.env.example']:
            self.assertTrue(allowed(Path(name)), name)

    def test_archive_keeps_tests_and_excludes_private_sentinel(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)/'project'
            names = ['README.md','requirements.txt','src/api/app.py','DW/etl/run.py',
                     'frontend/package.json','frontend/src/main.jsx','tests/test_api.py',
                     'frontend/tests/pages.test.jsx','frontend/e2e/review-reader.spec.js']
            for name in names + ['Data/raw.csv','reports/private.json','frontend/node_modules/private.js']:
                path=root/name;path.parent.mkdir(parents=True,exist_ok=True)
                path.write_text('synthetic fixture',encoding='utf8')
            result=build_package(root,Path(folder)/'source.zip')
            self.assertEqual(result['status'],'PASS')
            with zipfile.ZipFile(result['archive']) as z:
                self.assertIsNone(z.testzip())
                entries=z.namelist()
                self.assertEqual(len(entries),len(names)+1)
                self.assertTrue(any(n.endswith('/tests/test_api.py') for n in entries))
                self.assertFalse(any('private' in n or '/Data/' in n for n in entries))

    def test_incomplete_project_cannot_be_packaged(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                build_package(Path(folder),Path(folder)/'incomplete.zip')
