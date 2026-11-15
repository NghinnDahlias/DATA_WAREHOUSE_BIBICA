"""Build a source-only ZIP with an explicit allowlist; never include private data."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TOP = 'Bibica_DW_Source'
ROOT_FILES = {'.dockerignore', '.env.example', '.gitattributes', '.gitignore', 'AGENTS.md', 'README.md', 'requirements.txt'}
EXTENSIONS = {
    'src': {'.py'}, 'tests': {'.py'}, 'scripts': {'.py', '.ps1', '.sql'},
    'DW': {'.py', '.sql', '.dbml', '.md'}, 'docs': {'.md'},
}
FRONTEND_FILES = {'README.md', '.env.example', 'package.json', 'package-lock.json',
                  'index.html', 'vite.config.js', 'playwright.config.js'}
EXCLUDED_PARTS = {'.git', '.runtime', '.venv', '__pycache__', 'node_modules', 'dist',
                  'test-results', 'playwright-report', 'data process', 'data', 'reports'}


def allowed(relative):
    parts = relative.parts
    if any(p.casefold() in EXCLUDED_PARTS for p in parts):
        return False
    if len(parts) == 1:
        return relative.name in ROOT_FILES
    if parts[0] == 'frontend':
        if len(parts) == 2:
            return parts[1] in FRONTEND_FILES
        return parts[1] in {'src', 'tests', 'e2e'} and relative.suffix in {'.js', '.jsx', '.css'}
    if relative.as_posix() == 'docs/api/openapi.json':
        return True
    return relative.suffix in EXTENSIONS.get(parts[0], set())


def source_files(root):
    root = root.resolve()
    candidates = [root / name for name in sorted(ROOT_FILES) if (root / name).is_file()]
    for directory in (*EXTENSIONS, 'frontend'):
        base = root / directory
        if not base.exists():
            continue
        # Prune dependencies, generated files and symlinks before descending.
        def walk(folder):
            for p in sorted(folder.iterdir()):
                if p.name.casefold() in EXCLUDED_PARTS:
                    continue
                if p.is_symlink() or (hasattr(p, 'is_junction') and p.is_junction()):
                    raise ValueError('Symlinks/junctions are not allowed in source packages')
                if p.is_dir():
                    yield from walk(p)
                elif p.is_file() and allowed(p.relative_to(root)):
                    yield p
        if base.is_symlink() or (hasattr(base, 'is_junction') and base.is_junction()):
            raise ValueError('Source root must not be a symlink/junction')
        candidates.extend(walk(base))
    for p in sorted(set(candidates)):
        if p.is_symlink() or not p.resolve().is_relative_to(root):
            raise ValueError('Source path escaped package root')
        if allowed(p.relative_to(root)):
            yield p


def build_package(root, destination):
    root, destination = Path(root).resolve(), Path(destination).resolve()
    files = list(source_files(root))
    required = {'README.md', 'requirements.txt', 'src/api/app.py', 'DW/etl/run.py',
                'frontend/package.json', 'frontend/src/main.jsx', 'tests/test_api.py',
                'frontend/tests/pages.test.jsx', 'frontend/e2e/review-reader.spec.js'}
    names = {p.relative_to(root).as_posix() for p in files}
    if not required <= names:
        raise ValueError('Required source/test files missing: ' + ', '.join(sorted(required - names)))
    hashes = {}
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix('.zip.partial')
    with zipfile.ZipFile(partial, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for path in files:
            name = path.relative_to(root).as_posix()
            data = path.read_bytes()
            hashes[name] = hashlib.sha256(data).hexdigest()
            z.writestr(f'{TOP}/{name}', data)
        z.writestr(f'{TOP}/PACKAGE_MANIFEST.json', json.dumps({
            'format': 1, 'scope': 'source-only; no private data, runtime, reports or dependencies',
            'files': hashes,
        }, ensure_ascii=False, indent=2) + '\n')
    with zipfile.ZipFile(partial) as z:
        if z.testzip() is not None:
            raise ValueError('ZIP CRC validation failed')
        if set(z.namelist()) != {f'{TOP}/{p}' for p in hashes} | {f'{TOP}/PACKAGE_MANIFEST.json'}:
            raise ValueError('Unexpected archive entry')
        for name, digest in hashes.items():
            if not allowed(Path(name)) or hashlib.sha256(z.read(f'{TOP}/{name}')).hexdigest() != digest:
                raise ValueError('Archive content validation failed')
    partial.replace(destination)
    return {'status': 'PASS', 'archive': str(destination), 'source_files': len(hashes),
            'bytes': destination.stat().st_size,
            'sha256': hashlib.sha256(destination.read_bytes()).hexdigest()}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, default=ROOT/'dist/Bibica_DW_Source.zip')
    args = p.parse_args()
    print(json.dumps(build_package(ROOT, args.output), ensure_ascii=False))


if __name__ == '__main__':
    main()
