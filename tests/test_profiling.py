import csv
import json
import tempfile
import unittest
from pathlib import Path

from src.profiling.config import FIELDS, SOURCES
from src.profiling.run import blank, main, number, profile, read_source, timestamp


class ProfilingTests(unittest.TestCase):
    def test_source_discovery_contract(self):
        root = Path("Data/Data_Source_Raw")
        self.assertTrue(all((root / name).is_file() for name, _, _ in SOURCES.values()))

    def test_csv_multiline_and_review_duplicates(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "reviews.csv"
            header = list(FIELDS["review"].values())
            def row(order, body):
                values = {"order": order, "rating": "2", "product_id": "p1",
                          "product": "Example product", "sku_spec": "variant",
                          "text": body, "created": "2026-10-01"}
                return [values.get(key, "") for key in FIELDS["review"]]
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(header)
                writer.writerow(row("o1", "Hộp rách\nSản phẩm vỡ"))
                writer.writerow(row("o1", "Hộp rách\nSản phẩm vỡ"))
            self.assertEqual(next(read_source(path))[1], header)
            inventory, keys, quality, _, review, *_ = profile(path, "review", "test")
            self.assertEqual(inventory["records"], 2)
            self.assertEqual(keys["full_duplicate_rows"], 1)
            self.assertEqual(review["duplicate_review_candidate_rows"], 1)
            self.assertEqual(review["text_issues"]["multiline"], 2)

    def test_xlsx_stream_header(self):
        path = Path("Data/Data_Source_Raw/Shopee_Quasure.xlsx")
        stream = read_source(path)
        try:
            sheet, header, rows, fmt = next(stream)
            self.assertEqual(sheet, "orders")
            self.assertIn("Mã đơn hàng", header)
            self.assertEqual(len(next(rows)), len(header))
            self.assertEqual(fmt["format"], "xlsx")
        finally:
            stream.close()

    def test_financial_repetition_and_key_collision(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sales.csv"
            header = list(FIELDS["tiktok"].values())
            base = {"order":"o1", "sku":"s1", "quantity":"1", "created":"01/10/2026 10:00:00",
                    "unit_price":"100", "gross":"100", "seller_discount":"0",
                    "platform_discount":"0", "net_item":"100", "order_amount":"200"}
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle); writer.writerow(header)
                for sku in ("s1", "s1", "s2"):
                    vals = dict(base, sku=sku)
                    writer.writerow([vals.get(key, "") for key in FIELDS["tiktok"]])
            _, keys, _, finance, _, *_ = profile(path, "tiktok", "test")
            self.assertEqual(keys["same_order_sku_repeated"], 1)
            self.assertEqual(keys["orders_multiple_skus"], 1)
            self.assertEqual(finance["order_amount"]["raw_row_sum"], 600)
            self.assertEqual(finance["order_amount"]["deduplicated_order_sum_when_constant"], 200)

    def test_parsers(self):
        self.assertTrue(blank("-"))
        self.assertEqual(number("1.234,50"), 1234.5)
        self.assertEqual(timestamp("17/10/2026 09:21:39\t").year, 2026)
        self.assertEqual(timestamp("14 tháng 10 năm 2026").date().isoformat(), "2026-10-14")

    def test_profile_reproducibility(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ratings.csv"
            with path.open("w",encoding="utf-8",newline="") as handle:
                writer=csv.writer(handle)
                writer.writerow(FIELDS["review"].values())
                writer.writerow(["o1","p1","Product","variant","5","Tốt","","14 tháng 10 năm 2026"])
            left=profile(path,"review","test")
            right=profile(path,"review","test")
            for index in range(5):
                self.assertEqual(json.dumps(left[index],default=dict,sort_keys=True),
                                 json.dumps(right[index],default=dict,sort_keys=True))

    def test_report_generation_outputs(self):
        from tests.test_etl import rating, sales, write
        from DW.etl.ratings import project_scraped_rating
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw, reports = root / "raw", root / "reports"
            docs = reports / "profiling"
            raw.mkdir()
            complete = lambda kind, values: {**dict.fromkeys(FIELDS[kind].values(), ''), **values}
            write(raw, "tiktok_bibica", [complete('tiktok', sales())])
            write(raw, "shopee_bibica", [complete('shopee', sales(False))])
            write(raw, "shopee_quasure", [complete('shopee', sales(False))])
            write(raw, "ratings", [complete('review', {**rating(), **project_scraped_rating(rating())})])
            self.assertEqual(main(["--data-dir", str(raw), "--output-dir", str(reports)]), 0)
            self.assertFalse((root / "docs").exists())
            expected = ("source_inventory.json", "key_uniqueness.json", "data_quality.json",
                        "schema_mapping.csv", "financial_reconciliation.json", "review_profile.json")
            for name in expected:
                self.assertTrue((reports / name).is_file(), name)
            report = json.loads((reports / "source_inventory.json").read_text(encoding="utf-8"))
            self.assertEqual(set(report["sources"]), set(SOURCES))
            for item in report["sources"].values():
                self.assertGreater(item["records"], 0)
                self.assertGreater(item["columns_count"], 0)
            generated = ("data/source_inventory.md", "data/grain_analysis.md", "data/data_quality_report.md",
                         "data/cross_platform_mapping.md", "data/review_feasibility.md",
                         "business/financial_definitions.md", "business/business_requirements.md",
                         "architecture/modeling_readiness.md", "progress.md", "decisions.md")
            for name in generated:
                path = docs / name
                self.assertTrue(path.is_file() and path.stat().st_size > 100, name)

    def test_missing_sources_are_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            code = main(["--data-dir",str(root/"raw"),"--output-dir",str(root/"reports"),
                         "--docs-dir",str(root/"docs")])
            self.assertEqual(code, 2)
            report = json.loads((root/"reports/source_inventory.json").read_text(encoding="utf-8"))
            self.assertEqual(len(report["missing"]), 4)
            self.assertIn("BLOCKED",(root/"docs/data/review_feasibility.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
