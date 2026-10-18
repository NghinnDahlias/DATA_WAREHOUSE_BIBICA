# Bibica E-Commerce Data Warehouse & DSS — Phase 1

This project contains reproducible source discovery and profiling only. The four prepared exports are included unchanged in `Data/Data_Source_Raw`. No database, ETL pipeline, API, or frontend is created in this phase.

## Run

From `Datawarehouse_DSS`:

```powershell
python -m pip install -r requirements.txt
python -m src.profiling.run
python -m unittest discover -s tests -v
```

Optional paths:

```powershell
python -m src.profiling.run --data-dir Data/Data_Source_Raw --output-dir reports --docs-dir docs
```

The CLI reads CSV with Python's quoted-field parser and streams XLSX rows with openpyxl. It fails on missing required columns rather than silently guessing mappings. Existing report files in the chosen output directory are regenerated. Raw source files are never written. Reports contain counts, field names, source fingerprints, and aggregate diagnostics, without raw customer values or review text.

The assignment PDF is in the parent workspace and was read for course requirements. The four project raw exports are byte-identical to the corresponding named files in the parent `Data` directory. See `docs/progress.md`, `docs/decisions.md`, and `docs/validation.md` for findings and gate status.
