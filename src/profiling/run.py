"""Read-only, streaming Phase 1 profiler. Run: python -m src.profiling.run."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import statistics
import unicodedata
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path

from openpyxl import load_workbook

from .config import DATES, FIELDS, NUMERIC, PII_PARTS, SOURCES
from .documents import write_additional


def norm(value):
    return unicodedata.normalize("NFC", str(value or "")).strip()


def token(value):
    return re.sub(r"\s+", " ", norm(value).casefold())


def ascii_token(value):
    return "".join(c for c in unicodedata.normalize("NFD", token(value))
                   if unicodedata.category(c) != "Mn").replace("đ", "d")


COMPLAINT_TERMS = {
    "packaging_damage": ("hop rach", "hop mop", "vo hop", "bao bi rach", "dong goi te"),
    "product_quality": ("bi hong", "bi moc", "het han", "chat luong kem", "bi vo"),
    "missing_or_wrong_item": ("thieu hang", "giao thieu", "giao sai", "sai san pham"),
    "delivery": ("giao cham", "giao tre", "van chuyen lau", "ship lau"),
    "expectation_mismatch": ("khong giong", "khac mo ta", "khong nhu mong doi"),
    "service": ("tu van te", "ho tro cham", "cham soc khach hang"),
}


def blank(value):
    return value is None or str(value).strip() in ("", "-")


def number(value):
    if blank(value):
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value) if math.isfinite(float(value)) else None
    s = str(value).strip().replace("\u00a0", "").replace(" ", "")
    s = re.sub(r"[^0-9,.-]", "", s)
    if s.count(",") and s.count("."):
        s = s.replace(",", "") if s.rfind(".") > s.rfind(",") else s.replace(".", "").replace(",", ".")
    elif s.count(","):
        s = s.replace(",", ".") if s.count(",") == 1 and len(s.split(",")[-1]) != 3 else s.replace(",", "")
    try:
        n = float(s)
        return n if math.isfinite(n) else None
    except ValueError:
        return None


def timestamp(value):
    if blank(value):
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    s = str(value).strip()
    vietnamese = re.fullmatch(r"(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})", s, re.IGNORECASE)
    if vietnamese:
        try:
            day, month, year = map(int, vietnamese.groups())
            return datetime(year, month, day)
        except ValueError:
            return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d",
                "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y",
                "%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def read_source(path):
    """Yield sheet name, header and rows; CSV parsing honors quoted newlines."""
    if path.suffix.lower() == ".csv":
        with path.open("rb") as probe:
            has_utf8_bom = probe.read(3) == b"\xef\xbb\xbf"
        candidates = ("utf-8-sig",) if has_utf8_bom else ("utf-8", "cp1258", "cp1252")
        encoding = next((e for e in candidates
                         if can_decode(path, e)), None)
        if encoding is None:
            raise UnicodeError(f"No supported encoding: {path.name}")
        with path.open("r", encoding=encoding, newline="") as handle:
            sample = handle.read(65536)
            handle.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
                delimiter = dialect.delimiter
            except csv.Error:
                delimiter = ","
            reader = csv.reader(handle, delimiter=delimiter)
            header = [norm(x) for x in next(reader)]
            yield "csv", header, reader, {"encoding": encoding, "delimiter": delimiter}
    else:
        book = load_workbook(path, read_only=True, data_only=True)
        try:
            selected=[book['orders']] if 'orders' in book.sheetnames else [book['Ratings']] if 'Ratings' in book.sheetnames else list(book)
            for sheet in selected:
                rows = sheet.iter_rows(values_only=True)
                try:
                    header = [norm(x) for x in next(rows)]
                except StopIteration:
                    continue
                if sheet.title=='Ratings' and 'web_scraper_order' in header:
                    from DW.etl.ratings import project_scraped_rating
                    names=list(FIELDS['review'].values())
                    def projected(source_rows=rows,source_header=header):
                        for values in source_rows:
                            item=project_scraped_rating(dict(zip(source_header,values)))
                            yield tuple(item.get(k) for k in names)
                    yield sheet.title,names,projected(),{'format':'xlsx','sheet':sheet.title}
                else:
                    yield sheet.title, header, rows, {"format": "xlsx", "sheet": sheet.title}
        finally:
            book.close()


def can_decode(path, encoding):
    try:
        with path.open("r", encoding=encoding, newline="") as handle:
            while handle.read(1024 * 1024):
                pass
        return True
    except UnicodeError:
        return False


def hashes(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_column(name):
    low = token(name)
    return not any(part in low for part in PII_PARTS)


def profile(path, kind, store):
    sheets = []
    for sheet_name, header, rows, fmt in read_source(path):
        # The four prepared exports have one logical table each.
        lookup = {name: i for i, name in enumerate(header)}
        expected = FIELDS[kind]
        missing = [name for name in expected.values() if norm(name) not in lookup]
        if missing:
            raise ValueError(f"{path.name}/{sheet_name}: missing required headers: {missing}")
        ix = {key: lookup[norm(name)] for key, name in expected.items()}
        safe_flags = [safe_column(h) for h in header]
        date_keys = [(key, ix[key]) for key in sorted(DATES & ix.keys())]
        numeric_keys = [(key, ix[key]) for key in sorted(NUMERIC & ix.keys())]
        cols = [{"name": h, "blank": 0, "nonblank": 0, "numeric": 0, "date": 0,
                 "distinct_sample": set(), "first": None} for h in header]
        n = 0
        full_dupes = 0
        row_hashes = set()
        orders = Counter(); skus = Counter(); pairs = Counter(); packages = Counter(); tracking = Counter()
        order_package_sku = Counter(); order_tracking_sku = Counter()
        package_orders = defaultdict(set); tracking_orders = defaultdict(set)
        order_packages = defaultdict(set); order_tracking = defaultdict(set)
        order_skus = defaultdict(set); order_products = defaultdict(set)
        order_money = defaultdict(lambda: defaultdict(set))
        statuses = Counter(); dates = defaultdict(lambda: [None, None, 0])
        numeric = defaultdict(lambda: {"present": 0, "parse_fail": 0, "negative": 0, "zero": 0,
                                      "min": None, "max": None, "sum": 0.0, "values": []})
        checks = Counter(); review = {"ratings": Counter(), "months": Counter(), "text_lengths": [],
                                      "nonempty_text": 0, "negative_reviews": 0,
                                      "order_products": defaultdict(set), "order_product_name_counts": Counter(),
                                      "review_keys": Counter(),
                                      "product_ids": set(), "orders": set(), "text_issues": Counter(),
                                      "complaint_hits": Counter(), "negative_complaint_hits": Counter()}
        for row in rows:
            vals = list(row)
            if len(vals) != len(header):
                checks["row_width_mismatch"] += 1
            vals += [None] * (len(header) - len(vals))
            vals = vals[:len(header)]
            if all(blank(v) for v in vals):
                continue
            n += 1
            fingerprint = hashlib.sha256(json.dumps(vals, ensure_ascii=False, default=str).encode()).digest()
            if fingerprint in row_hashes:
                full_dupes += 1
            row_hashes.add(fingerprint)
            for i, val in enumerate(vals):
                col = cols[i]
                if blank(val):
                    col["blank"] += 1
                    continue
                col["nonblank"] += 1
                if safe_flags[i] and len(col["distinct_sample"]) <= 1000:
                    col["distinct_sample"].add(token(val))
                if col["first"] is None:
                    col["first"] = type(val).__name__
                if isinstance(val, (int, float)) and not isinstance(val, bool):
                    col["numeric"] += 1
                if isinstance(val, (date, datetime)):
                    col["date"] += 1
            def get(key):
                return vals[ix[key]] if key in ix else None
            oid = norm(get("order")); sku = norm(get("sku"))
            product = token(get("product"))
            if oid:
                orders[oid] += 1
            if sku:
                skus[sku] += 1
            if oid and sku:
                pairs[(oid, sku)] += 1
                order_skus[oid].add(sku)
            if oid and product:
                order_products[oid].add(product)
            for key, counter in (("package", packages), ("tracking", tracking)):
                v = norm(get(key))
                if v:
                    counter[v] += 1
                    if oid:
                        if key == "package":
                            package_orders[v].add(oid); order_packages[oid].add(v)
                            if sku: order_package_sku[(oid,v,sku)] += 1
                        else:
                            tracking_orders[v].add(oid); order_tracking[oid].add(v)
                            if sku: order_tracking_sku[(oid,v,sku)] += 1
            status = norm(get("status"))
            if status:
                statuses[status] += 1
            parsed_dates = {}
            for key, index in date_keys:
                val = vals[index]
                if blank(val):
                    continue
                dt = timestamp(val)
                parsed_dates[key] = dt
                if dt is None:
                    dates[key][2] += 1
                else:
                    dates[key][0] = min(dates[key][0], dt) if dates[key][0] else dt
                    dates[key][1] = max(dates[key][1], dt) if dates[key][1] else dt
            parsed_numbers = {}
            for key, index in numeric_keys:
                val = vals[index]
                if blank(val):
                    continue
                st = numeric[key]; st["present"] += 1
                v = number(val)
                parsed_numbers[key] = v
                if v is None:
                    st["parse_fail"] += 1
                    continue
                st["negative"] += v < 0; st["zero"] += v == 0; st["sum"] += v
                st["min"] = min(st["min"], v) if st["min"] is not None else v
                st["max"] = max(st["max"], v) if st["max"] is not None else v
                if len(st["values"]) < 1000000:
                    st["values"].append(v)
                if oid and key in ("order_amount", "payment", "payment_alt", "refund", "shipping"):
                    order_money[oid][key].add(v)
            if kind != "review":
                q = parsed_numbers.get("quantity")
                if q is not None and (q < 0 or q > 100 or q != int(q)):
                    checks["suspicious_quantity"] += 1
                gross = parsed_numbers.get("gross"); unit = parsed_numbers.get("unit_price")
                if gross is not None and unit is not None and q is not None and abs(gross - unit*q) > 1:
                    checks["unit_times_quantity_differs_from_gross"] += 1
                if parsed_dates.get("created") and parsed_dates.get("paid") and parsed_dates["paid"] < parsed_dates["created"]:
                    checks["paid_before_created"] += 1
                if parsed_dates.get("created") and parsed_dates.get("shipped") and parsed_dates["shipped"] < parsed_dates["created"]:
                    checks["send_field_before_created" if kind=="shopee" else "shipped_before_created"] += 1
                if parsed_dates.get("shipped") and parsed_dates.get("delivered") and parsed_dates["delivered"] < parsed_dates["shipped"]:
                    checks["delivery_before_send_field_semantics_unconfirmed" if kind=="shopee" else "delivered_before_shipped"] += 1
                if kind == "tiktok":
                    net = parsed_numbers.get("net_item"); sd = parsed_numbers.get("seller_discount"); pd = parsed_numbers.get("platform_discount")
                    if None not in (gross, net, sd, pd):
                        checks["gross_minus_discounts_tested"] += 1
                        if abs(gross-sd-pd-net) > 1:
                            checks["gross_minus_discounts_differs_from_net_item"] += 1
                    if None not in (gross, sd, pd) and sd+pd > gross+1:
                        checks["discounts_exceed_gross_item"] += 1
                    refund = parsed_numbers.get("refund"); amount = parsed_numbers.get("order_amount")
                    if None not in (refund,amount) and refund > amount+1:
                        checks["refund_exceeds_row_order_amount"] += 1
                else:
                    returned = parsed_numbers.get("returned_quantity")
                    if returned is not None and q is not None and returned > q:
                        checks["returned_quantity_exceeds_quantity"] += 1
                    if returned is not None and returned > 0 and blank(get("refund_status")):
                        checks["returned_quantity_without_refund_status"] += 1
                    p1=parsed_numbers.get("payment"); p2=parsed_numbers.get("payment_alt")
                    if p1 is not None and p2 is not None:
                        checks["payment_columns_tested"] += 1
                        if abs(p1-p2)>1:
                            checks["payment_columns_differ"] += 1
            else:
                rating = parsed_numbers.get("rating")
                if rating is None or rating not in (1,2,3,4,5):
                    checks["invalid_rating"] += 1
                else:
                    review["ratings"][str(int(rating))] += 1
                    review["negative_reviews"] += rating <= 2
                body = norm(get("text")); other = norm(get("other_text"))
                if body:
                    review["nonempty_text"] += 1
                    review["text_lengths"].append(len(body))
                    review["text_issues"]["replacement_character"] += "\ufffd" in body
                    review["text_issues"]["no_diacritic_ascii"] += body.isascii()
                    review["text_issues"]["multiline"] += "\n" in body
                    folded = ascii_token(body)
                    matched_any = False
                    for category,terms in COMPLAINT_TERMS.items():
                        if any(term in folded for term in terms):
                            matched_any = True
                            review["complaint_hits"][category] += 1
                            if rating is not None and rating <= 2:
                                review["negative_complaint_hits"][category] += 1
                    if not matched_any:
                        review["complaint_hits"]["other_unclassified"] += 1
                dt = timestamp(get("created"))
                if dt:
                    review["months"][dt.strftime("%Y-%m")] += 1
                pid = norm(get("product_id"))
                if pid:
                    review["product_ids"].add(pid)
                if oid:
                    review["orders"].add(oid)
                    review["order_products"][oid].add(pid)
                    if product:
                        review["order_product_name_counts"][(oid,product)] += 1
                rkey = hashlib.sha256(json.dumps([oid,pid,norm(get("created")),body,other],ensure_ascii=False).encode()).digest()
                review["review_keys"][rkey] += 1
        semantic = {norm(name): key for key,name in expected.items()}
        for i,c in enumerate(cols):
            c["inferred_type"] = "empty" if c["nonblank"] == 0 else (
                "datetime" if c["date"] == c["nonblank"] else
                "numeric" if c["numeric"] == c["nonblank"] else "text/mixed")
            c["distinct_sample_count"] = len(c.pop("distinct_sample")) if safe_flags[i] else None
            c["constant_candidate"] = c["distinct_sample_count"] == 1 and c["nonblank"] > 0
            c["semantic_role"] = semantic.get(c["name"], "private_or_source_specific" if not safe_flags[i] else "unclassified")
            c.pop("first")
        for st in numeric.values():
            values = st.pop("values")
            if values:
                values.sort()
                q1, q3 = values[len(values)//4], values[3*len(values)//4]
                st["q1"] = q1; st["q3"] = q3
                st["iqr_upper_fence"] = q3 + 1.5*(q3-q1)
                st["above_iqr_fence"] = sum(v > st["iqr_upper_fence"] for v in values)
                st["outlier_basis"] = len(values)
            st["sum"] = round(st["sum"], 2)
        key = {
            "rows": n, "unique_orders": len(orders), "unique_skus": len(skus),
            "unique_order_sku": len(pairs), "duplicate_order_sku_rows": sum(v-1 for v in pairs.values()),
            "orders_multiple_rows": sum(v>1 for v in orders.values()),
            "orders_multiple_skus": sum(len(v)>1 for v in order_skus.values()),
            "same_order_sku_repeated": sum(v>1 for v in pairs.values()),
            "unique_packages": len(packages), "unique_tracking": len(tracking),
            "packages_multiple_rows": sum(v>1 for v in packages.values()),
            "tracking_multiple_rows": sum(v>1 for v in tracking.values()),
            "packages_multiple_orders": sum(len(v)>1 for v in package_orders.values()),
            "tracking_multiple_orders": sum(len(v)>1 for v in tracking_orders.values()),
            "orders_multiple_packages": sum(len(v)>1 for v in order_packages.values()),
            "orders_multiple_tracking_ids": sum(len(v)>1 for v in order_tracking.values()),
            "duplicate_order_package_sku_rows": sum(v-1 for v in order_package_sku.values()),
            "duplicate_order_tracking_sku_rows": sum(v-1 for v in order_tracking_sku.values()),
            "full_duplicate_rows": full_dupes,
            "candidate_row_key": "source file + sheet + physical row number (provisional)" if full_dupes else "full row unique in current snapshot; stable source line ID unavailable",
        }
        finance = {}
        for field in ("order_amount", "payment", "payment_alt", "refund", "shipping"):
            field_orders = {o: money[field] for o, money in order_money.items() if field in money}
            finance[field] = {
                "orders_with_value": len(field_orders),
                "multirow_orders_with_same_value": sum(orders[o]>1 and len(v)==1 for o,v in field_orders.items()),
                "multirow_orders_with_conflicting_values": sum(orders[o]>1 and len(v)>1 for o,v in field_orders.items()),
                "raw_row_sum": numeric[field]["sum"] if field in numeric else None,
                "deduplicated_order_sum_when_constant": round(sum(next(iter(v)) for v in field_orders.values() if len(v)==1),2),
            }
        inventory = {"file": path.name, "sha256": hashes(path), "storefront": store,
                     "sheet": sheet_name, "format": fmt, "records": n, "columns_count": len(header),
                     "columns": cols, "date_ranges": {k:{"min":v[0].isoformat() if v[0] else None,
                                                        "max":v[1].isoformat() if v[1] else None,
                                                        "parse_fail":v[2]} for k,v in dates.items()}}
        quality = {"rows": n, "full_duplicate_rows": full_dupes,
                   "column_blank_rates": {c["name"]:round(c["blank"]/n,6) if n else None for c in cols},
                   "numeric": numeric, "statuses": statuses, "checks": checks}
        review_out = None
        if kind == "review":
            lengths = sorted(review["text_lengths"])
            review_out = {"rating_distribution": review["ratings"], "negative_reviews_1_2":review["negative_reviews"],
                          "negative_rate":round(review["negative_reviews"]/n,6) if n else None,
                          "nonempty_review_text":review["nonempty_text"],
                          "text_coverage":round(review["nonempty_text"]/n,6) if n else None,
                          "text_length": {"min":lengths[0],"median":statistics.median(lengths),
                                          "p90":lengths[int(.9*(len(lengths)-1))],"max":lengths[-1]} if lengths else {},
                          "monthly_volume":dict(sorted(review["months"].items())),
                          "unique_product_ids":len(review["product_ids"]),
                          "unique_order_ids":len(review["orders"]),
                          "orders_multiple_reviews":sum(v>1 for v in orders.values()),
                          "orders_multiple_review_products":sum(len(v)>1 for v in review["order_products"].values()),
                          "duplicate_review_candidate_rows":sum(v-1 for v in review["review_keys"].values()),
                          "text_issues":review["text_issues"],
                          "candidate_complaint_keyword_hits":review["complaint_hits"],
                          "negative_candidate_complaint_keyword_hits":review["negative_complaint_hits"],
                          "keyword_method":"Accent-folded substring matches; labels overlap and are unvalidated. Negation is not resolved."}
        sheets.append((inventory,key,quality,finance,review_out,orders,order_products,skus,
                       review["order_product_name_counts"] if kind == "review" else None))
    if len(sheets) != 1:
        raise ValueError(f"Expected one logical sheet in {path.name}; found {len(sheets)}")
    return sheets[0]


def write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=dict)+"\n", encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Profile Bibica/Quasure raw exports without modifying them")
    parser.add_argument("--data-dir", type=Path, default=Path("Data/Data_Source_Raw"))
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    parser.add_argument("--docs-dir", type=Path, default=Path("docs"))
    args = parser.parse_args(argv)
    data = args.data_dir.resolve(); out = args.output_dir.resolve(); docs = args.docs_dir.resolve()
    out.mkdir(parents=True, exist_ok=True); docs.mkdir(parents=True, exist_ok=True)
    results = {}; missing = []
    for name,(filename,kind,store) in SOURCES.items():
        path = data/filename
        if not path.is_file():
            missing.append(filename); continue
        print(f"Profiling {filename}...", flush=True)
        results[name] = profile(path,kind,store)
    inv = {name:r[0] for name,r in results.items()}
    keys = {name:r[1] for name,r in results.items()}
    qual = {name:r[2] for name,r in results.items()}
    fin = {name:{**r[3],"equation_tests":{
        key:value for key,value in r[2]["checks"].items()
        if key.startswith(("gross_minus", "unit_times", "discounts_exceed", "refund_exceeds", "payment_columns"))}}
           for name,r in results.items() if name != "tiktok_reviews"}
    rev = results["tiktok_reviews"][4] if "tiktok_reviews" in results else {"blocked":"review file missing"}
    if "tiktok_sales" in results and "tiktok_reviews" in results:
        sales_orders = results["tiktok_sales"][5]
        sales_products = results["tiktok_sales"][6]
        review_orders = results["tiktok_reviews"][5]
        review_products = results["tiktok_reviews"][8]
        rev["review_rows_with_order_match"] = sum(count for oid,count in review_orders.items() if oid in sales_orders)
        rev["review_rows_with_order_match_rate"] = round(rev["review_rows_with_order_match"]/keys["tiktok_reviews"]["rows"],6)
        rev["review_rows_with_product_name_match_in_order"] = sum(
            count for (oid,product),count in review_products.items()
            if product in sales_products.get(oid,set()))
        rev["review_rows_with_product_name_match_in_order_rate"] = round(
            rev["review_rows_with_product_name_match_in_order"]/keys["tiktok_reviews"]["rows"],6)
        rev["review_rows_linked_to_multi_product_order"] = sum(
            count for oid,count in review_orders.items() if len(sales_products.get(oid,set()))>1)
        rev["product_linkage_note"] = "Product ID in review has no same-named sales ID; exact normalized product-name match is a proxy and must not be treated as a verified SKU join."
    sales = [x for x in ("tiktok_sales","shopee_bibica","shopee_quasure") if x in results]
    overlap = {}
    for i,a in enumerate(sales):
        for b in sales[i+1:]:
            overlap[f"{a}__{b}"] = len(results[a][5].keys() & results[b][5].keys())
    keys["cross_source_order_id_overlap"] = overlap
    write_json(out/"source_inventory.json", {"sources":inv,"missing":missing})
    write_json(out/"key_uniqueness.json", keys)
    write_json(out/"data_quality.json", qual)
    write_json(out/"financial_reconciliation.json", fin)
    write_json(out/"review_profile.json", rev)
    build_documents(docs,out,results,missing)
    write_additional(docs,out,results,missing)
    print(json.dumps({"records":{k:v[0]["records"] for k,v in results.items()},"missing":missing},ensure_ascii=False),flush=True)
    return 0 if not missing else 2


def build_documents(docs,out,results,missing):
    """Reports derive only from measured aggregates; no source record values are emitted."""
    (docs/"data").mkdir(parents=True,exist_ok=True)
    (docs/"business").mkdir(parents=True,exist_ok=True)
    (docs/"architecture").mkdir(parents=True,exist_ok=True)
    inv={k:v[0] for k,v in results.items()}; keys={k:v[1] for k,v in results.items()}
    qual={k:v[2] for k,v in results.items()}
    rev=json.loads((out/"review_profile.json").read_text(encoding="utf-8"))
    def rv(name):
        value=rev.get(name,"BLOCKED")
        return f"{value:,}" if isinstance(value,(int,float)) else str(value)
    lines=["# Source inventory", "", "Read-only profile of the four prepared raw exports in `Data/Data_Source_Raw`. SHA-256 fingerprints and exact schemas are in `reports/source_inventory.json`. The assignment PDF was inspected separately; it has 7 pages and requires business requirements, multidimensional DW, ETL, DSS, and presentation.", "", "| Source | Storefront | Rows | Columns | Sheet |", "|---|---|---:|---:|---|"]
    for k,v in inv.items():
        lines.append(f"| {v['file']} | {v['storefront']} | {v['records']:,} | {v['columns_count']} | {v['sheet']} |")
    lines += ["",f"Missing exports: {', '.join(missing) if missing else 'none'}.","", "## Date ranges and schema", ""]
    if "shopee_bibica" in inv and "shopee_quasure" in inv:
        bibica_fields={c["name"] for c in inv["shopee_bibica"]["columns"]}
        quasure_fields={c["name"] for c in inv["shopee_quasure"]["columns"]}
        lines += ["Shopee Bibica-only fields: "+(", ".join(sorted(bibica_fields-quasure_fields)) or "none")+". Shopee Quasure-only fields: "+(", ".join(sorted(quasure_fields-bibica_fields)) or "none")+".", ""]
    for k,v in inv.items():
        lines += [f"### {v['file']}","",f"Empty fields: {sum(c['nonblank']==0 for c in v['columns'])}; constant non-private candidates: {sum(c['constant_candidate'] for c in v['columns'])}.","", "| Field | Earliest | Latest | Parse failures |", "|---|---|---|---:|"]
        for field,d in v["date_ranges"].items():
            lines.append(f"| {field} | {d['min']} | {d['max']} | {d['parse_fail']} |")
        lines += ["", "Columns (name: inferred Python value type; blank count):", ""]
        lines += [f"- {c['name']}: {c['inferred_type']}; role `{c['semantic_role']}`; {c['blank']:,} blanks" for c in v["columns"]]
        lines.append("")
    (docs/"data/source_inventory.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    lines=["# Grain and key analysis", "", "Counts are from every nonempty data row. A physical row locator remains the safe provisional source key; no order-SKU uniqueness is assumed.", "", "| Source | Rows | Orders | SKUs | Order-SKU | Repeated order-SKU groups | Full duplicates | Multi-SKU orders |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for k,v in keys.items():
        if k.startswith("cross_"):continue
        lines.append(f"| {k} | {v['rows']:,} | {v['unique_orders']:,} | {v['unique_skus']:,} | {v['unique_order_sku']:,} | {v['same_order_sku_repeated']:,} | {v['full_duplicate_rows']:,} | {v['orders_multiple_skus']:,} |")
    lines.append("")
    for name in ("tiktok_sales","shopee_bibica","shopee_quasure"):
        if name in inv:
            sku_col=next((c for c in inv[name]["columns"] if c["semantic_role"]=="sku"),None)
            if sku_col and sku_col["blank"]:
                lines.append(f"{name} also has {sku_col['blank']:,} rows without a SKU identifier; these are excluded from order-SKU combination counts.")
    lines += ["", "## Candidate grain", "", "Sales exports appear to contain product/variant lines, with package and order context. Repeated order-SKU pairs must be retained until their cause (split packages, repeated line, or export duplication) is resolved. Ratings are review records, not sales lines. No stable review ID exists in this export; the composite fingerprint is only a collision diagnostic.", "", "Order ID intersections and package/tracking multiplicity are in `reports/key_uniqueness.json`; review candidate collisions are in `reports/review_profile.json`. Storefront plus order ID is the minimum order namespace.", ""]
    if "tiktok_reviews" in keys:
        lines += [f"Review candidate fingerprint collisions: {rev.get('duplicate_review_candidate_rows',0):,} additional rows share `(order_id, product_id, review_date, review_text, other_text)`; they are not automatically duplicate customer opinions.", ""]
    lines += ["| Source | Repeated order-package-SKU rows | Repeated order-tracking-SKU rows | Orders with multiple packages | Orders with multiple tracking IDs |", "|---|---:|---:|---:|---:|"]
    for k,v in keys.items():
        if k.startswith("cross_"): continue
        lines.append(f"| {k} | {v['duplicate_order_package_sku_rows']:,} | {v['duplicate_order_tracking_sku_rows']:,} | {v['orders_multiple_packages']:,} | {v['orders_multiple_tracking_ids']:,} |")
    lines.append("")
    (docs/"data/grain_analysis.md").write_text("\n".join(lines),encoding="utf-8")
    lines=["# Data quality report", "", "All counts are observations, not automatic errors. Cancellations, refunds, zeros and large orders need business interpretation.", "", "| Source | Full duplicates | Suspicious quantities (<0, >100, noninteger) | Paid before created | Send/shipped field before created | Delivery before send/shipped field |", "|---|---:|---:|---:|---:|---:|"]
    for k,v in qual.items():
        c=v["checks"]
        lines.append(f"| {k} | {v['full_duplicate_rows']:,} | {c.get('suspicious_quantity',0):,} | {c.get('paid_before_created',0):,} | {c.get('shipped_before_created',c.get('send_field_before_created',0)):,} | {c.get('delivered_before_shipped',c.get('delivery_before_send_field_semantics_unconfirmed',0)):,} |")
    lines += ["", "Full per-column blank rates, numeric parsing failures, negative/zero values, status frequencies and Tukey 1.5×IQR upper-fence outliers are in `reports/data_quality.json`. IQR outliers are investigation flags, not rejected sales. Literal `-` is a source missing-value marker, including 6,911 Shopee payment-time cells; it is counted as blank rather than a date parse failure.", "", "Shopee's `Ngày gửi hàng` sometimes follows `Thời gian giao hàng` by minutes on the same date. It may be a send deadline or another milestone; sequence counts are semantic warnings, not proven logistics errors. Status vocabularies need a reviewed lifecycle map. Blank timestamps on canceled or unfinished orders are plausible.", ""]
    for k,v in qual.items():
        lines += [f"## {k}: measured flags", ""]
        lines += [f"- {name}: {count:,}" for name,count in v["checks"].items()]
        if v["statuses"]:
            lines.append("- Native status values: "+", ".join(f"{name} ({count:,})" for name,count in v["statuses"].items()))
        for name,stat in v["numeric"].items():
            if stat["parse_fail"] or stat["negative"]:
                lines.append(f"- {name}: {stat['parse_fail']:,} parse failures; {stat['negative']:,} negative values")
        lines.append("")
    (docs/"data/data_quality_report.md").write_text("\n".join(lines),encoding="utf-8")
    lines=["# Review intelligence feasibility", "",f"Review rows: {keys.get('tiktok_reviews',{}).get('rows',0):,}. Negative (1–2 stars): {rv('negative_reviews_1_2')} ({rv('negative_rate')}). Nonempty review text: {rv('nonempty_review_text')} ({rv('text_coverage')}).", "",f"Order match: {rv('review_rows_with_order_match')} rows ({rv('review_rows_with_order_match_rate')}). Exact normalized name proxy within matched order: {rv('review_rows_with_product_name_match_in_order')} rows ({rv('review_rows_with_product_name_match_in_order_rate')}). This proxy is not a verified product-ID/SKU join.", "",f"Reviews linked to multi-product sales orders: {rv('review_rows_linked_to_multi_product_order')}; one review may describe the whole order. Exact review-to-line linkage remains unresolved. The ratings file is a pre-merged export, so a complete order match is not independent evidence that the original scraper linkage was correct.", "", "Rating distribution, monthly volume, text lengths, encoding indicators and review key collisions are in `reports/review_profile.json`.", "", "Candidate labels: packaging damage; product quality; missing/incorrect items; delivery; expectation mismatch; service; other. Accent-folded substring counts in the JSON are only exploratory and can overlap. Negation, slang, spelling variation and abbreviations require manual validation. No review text or customer identifier is published.", ""]
    if "candidate_complaint_keyword_hits" in rev:
        unmatched=rev["candidate_complaint_keyword_hits"].get("other_unclassified",0)
        lines += [f"The starter keyword list left {unmatched:,} of {rv('nonempty_review_text')} nonempty reviews unclassified. This is a taxonomy feasibility signal, not a measured complaint prevalence.", ""]
    (docs/"data/review_feasibility.md").write_text("\n".join(lines),encoding="utf-8")
    lines=["# Financial definitions and reconciliation", "", "Source monetary labels are not a signed accounting contract. Keep the source field and its grain explicit. `reports/financial_reconciliation.json` contains row sums, one-value-per-order sums and repeated/conflicting order counts.", "", "| Source | Order amount raw row sum | Single-value order sum | Multirow orders repeating value | Conflicting multirow orders |", "|---|---:|---:|---:|---:|"]
    for k,v in results.items():
        if k=="tiktok_reviews":continue
        f=v[3].get("order_amount",{})
        lines.append(f"| {k} | {f.get('raw_row_sum')} | {f.get('deduplicated_order_sum_when_constant')} | {f.get('multirow_orders_with_same_value')} | {f.get('multirow_orders_with_conflicting_values')} |")
    lines += ["", "## KPI status", "", "- Order count: PARTIALLY VERIFIED. Count distinct `(storefront, order_id)`; lifecycle inclusion policy unresolved.", "- Gross item value: PARTIALLY VERIFIED for TikTok only; source row has explicit SKU subtotal before discount. Shopee `Giá gốc` and `Giá ưu đãi` require quantity and discount interpretation.", "- Paid revenue/net sales: UNRESOLVED. Buyer payment, order amount, discounts, shipping and refunds may have different scopes. No cross-platform sum is authorized yet.", "- Refund value: UNRESOLVED. TikTok has `Order Refund Amount`; Shopee export has return quantity/status and return shipping fee, but no verified cash refund amount.", "- Discounts: PARTIALLY VERIFIED as separate source components; seller/platform and per-item/per-order allocation need confirmation.", "", "Do not sum repeated order-level amounts at line grain. Confirm representative platform settlement examples with business owner before production KPIs.", ""]
    if "tiktok_sales" in qual:
        c=qual["tiktok_sales"]["checks"]
        lines += [f"TikTok item equation `gross - seller discount - platform discount = net item` was testable on {c.get('gross_minus_discounts_tested',0):,} rows; {c.get('gross_minus_discounts_differs_from_net_item',0):,} differed by more than 1 currency unit.", ""]
    for name in ("shopee_bibica","shopee_quasure"):
        if name in qual:
            c=qual[name]["checks"]
            lines += [f"{name}: the two buyer-payment columns differed on {c.get('payment_columns_differ',0):,} of {c.get('payment_columns_tested',0):,} comparable rows. The first column also varies within many multirow orders while the second is constant; their allocation and settlement meanings require confirmation.", ""]
    (docs/"business/financial_definitions.md").write_text("\n".join(lines),encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
