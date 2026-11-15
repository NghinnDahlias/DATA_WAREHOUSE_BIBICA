# Source package verification — 15/11/2026

## Scope

README and frontend README were rewritten as run/test/package guides. Four obsolete root
replay logs and the superseded DB.png diagram were copied to an ignored local archive,
hash-checked and removed from source. The current DBML, SQL, all original tests and runtime
modules remain. Historical reports are retained locally because audit scripts refer to them;
the entire reports directory is excluded from the source ZIP.

## Executed checks

| Check | Result |
|---|---|
| Full Python suite | 128 passed; zero failures/errors/skips |
| React suite | 46 passed; zero failed |
| Frontend build | PASS; existing bundle-size warning |
| Extracted source ZIP, portable Python suite | 125 passed; zero failures/errors/skips |
| Portable profile exclusions | Exactly three original private-data/profiling checks |
| Original tests | All preserved; three packaging-safety tests added |
| Source ZIP integrity | CRC, manifest hashes, required source/test files and allowlist checked |
| Documentation links | Both README local links resolve |

Portable checks ran from a newly extracted project with no Data or reports directory and
no preloaded warehouse. They used installed Python dependencies and disposable databases
on the local test server. All three excluded methods remain unchanged in test_profiling.py;
the full suite still executes them. Missing database configuration produces SKIP/PARTIAL,
not a certified full pass.

The package includes nine Python test files, five React test files and five E2E spec files.
Browser E2E was not rerun for documentation/packaging cleanup; previous UI verification is
a separate dated snapshot. There were no changes to API/DSS/ETL business implementation.

## Artifact

Run `python scripts/package_source.py` from the repo root. The output is
`dist/Bibica_DW_Source.zip`; `PACKAGE_MANIFEST.json` inside lists per-file SHA-256 hashes.
Local evidence and the final ZIP checksum are in `reports/source_package.json`.

Excluded: original Data, Raw/Silver/Golden, review content, reports, .runtime, .git,
credentials, database backups, logs, caches, node_modules, test traces and compiled build.
Source tests use synthetic fixtures; private source files are supplied separately by an
authorized recipient. This package is not a preloaded database, sample-data demo or the
coursework PDF/slide submission. It does not claim a fresh dependency install, browser run,
Docker/remote CI/cloud deployment or full native-data ETL replay.
