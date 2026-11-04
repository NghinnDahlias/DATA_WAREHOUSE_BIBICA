DELETE FROM ops.quarantine;
INSERT INTO ops.quarantine
SELECT source_code,row_no,'EXACT_DUPLICATE' FROM
 (SELECT source_code,row_no,row_number() OVER(PARTITION BY source_code,row_hash ORDER BY row_no) rn
  FROM raw.source_row WHERE source_code<>'ratings') x WHERE rn>1;
INSERT INTO ops.quarantine
SELECT source_code,row_no,'INVALID_LINE' FROM staging.order_line
WHERE order_id='' OR created IS NULL OR quantity IS NULL OR quantity<=0 OR gross<0 OR item_after<0;
INSERT INTO ops.quarantine
SELECT source_code,row_no,'INVALID_REVIEW' FROM staging.review
WHERE order_id='' OR stars IS NULL OR stars NOT BETWEEN 1 AND 5 OR stars<>trunc(stars) OR review_date IS NULL;
INSERT INTO ops.quarantine
SELECT source_code,row_no,'DUPLICATE_REVIEW' FROM
 (SELECT source_code,row_no,row_number() OVER(PARTITION BY review_signature ORDER BY row_no) rn
  FROM staging.review WHERE review_signature IS NOT NULL AND order_id<>'' AND stars BETWEEN 1 AND 5 AND review_date IS NOT NULL)x WHERE rn>1;
INSERT INTO ops.quarantine
SELECT r.source_code,r.row_no,'UNMATCHED_REVIEW_ORDER' FROM staging.review r
WHERE r.order_id<>'' AND NOT EXISTS(SELECT 1 FROM staging.order_line l WHERE l.source_code='tiktok_bibica' AND l.order_id=r.order_id
 AND NOT EXISTS(SELECT 1 FROM ops.quarantine q WHERE(q.source_code,q.row_no)=(l.source_code,l.row_no)));
CREATE TEMP TABLE valid_line ON COMMIT DROP AS
SELECT l.*,s.storefront_key,s.channel_key FROM staging.order_line l JOIN source_scope s USING(source_code)
WHERE NOT EXISTS(SELECT 1 FROM ops.quarantine q WHERE(q.source_code,q.row_no)=(l.source_code,l.row_no));
CREATE INDEX ON valid_line(source_code,order_id);

INSERT INTO dw.dim_order_identity(channel_key,storefront_key,native_order_id,order_namespace)
SELECT DISTINCT channel_key,storefront_key,order_id,channel_code||'|'||storefront_code||'|'||order_id
FROM valid_line JOIN source_scope USING(source_code,channel_key,storefront_key) ON CONFLICT(order_namespace) DO NOTHING;

INSERT INTO dw.dim_date(date_key,calendar_date,year,quarter,month,day,month_name,week_of_year)
SELECT to_char(d,'YYYYMMDD')::integer,d,extract(year FROM d),extract(quarter FROM d),extract(month FROM d),extract(day FROM d),to_char(d,'Month'),extract(week FROM d)
FROM(SELECT DISTINCT d::date d FROM staging.order_line l CROSS JOIN LATERAL unnest(ARRAY[created,paid,shipped,delivered,canceled])d WHERE d IS NOT NULL
 UNION SELECT review_date::date FROM staging.review WHERE review_date IS NOT NULL)x ON CONFLICT(date_key) DO NOTHING;
INSERT INTO dw.dim_time(time_key,native_time,hour,minute,second)
SELECT extract(hour FROM d)*10000+extract(minute FROM d)*100+extract(second FROM d),d::time,extract(hour FROM d),extract(minute FROM d),extract(second FROM d)
FROM(SELECT DISTINCT d::time d FROM staging.order_line l CROSS JOIN LATERAL unnest(ARRAY[created,paid,shipped,delivered,canceled])d WHERE d IS NOT NULL
 UNION SELECT review_date::time FROM staging.review WHERE review_date IS NOT NULL)x ON CONFLICT(time_key) DO NOTHING;

INSERT INTO dw.dim_warehouse(storefront_key,native_warehouse_name,normalized_warehouse_name,mapping_status,mapping_version,warehouse_region)
SELECT DISTINCT s.storefront_key,coalesce(nullif(l.warehouse_raw,''),'Unknown'),l.warehouse_name,
 CASE WHEN l.warehouse_region='Unknown' THEN 'UNMAPPED' ELSE 'VALIDATED' END,'2026-11-04-warehouse-city-v1',l.warehouse_region
FROM staging.order_line l JOIN source_scope s USING(source_code)
ON CONFLICT(storefront_key,native_warehouse_name) DO UPDATE SET normalized_warehouse_name=excluded.normalized_warehouse_name,mapping_status=excluded.mapping_status,mapping_version=excluded.mapping_version,warehouse_region=excluded.warehouse_region;
INSERT INTO dw.dim_province(native_province_name,normalized_province_name,mapping_status,mapping_version)
SELECT DISTINCT province_raw,customer_province,CASE WHEN customer_province='Unknown' THEN 'UNMAPPED' ELSE 'VALIDATED' END,'2026-11-04-warehouse-province-v2' FROM staging.order_line
ON CONFLICT(native_province_name) DO UPDATE SET normalized_province_name=excluded.normalized_province_name,mapping_status=excluded.mapping_status,mapping_version=excluded.mapping_version;
INSERT INTO dw.dim_order_status(channel_key,storefront_key,native_status,reviewed_status,mapping_version,source_timezone)
SELECT DISTINCT s.channel_key,s.storefront_key,l.status_raw,l.canonical_status,'native-lifecycle-v1','Asia/Ho_Chi_Minh'
FROM staging.order_line l JOIN source_scope s USING(source_code)
WHERE NOT EXISTS(SELECT 1 FROM dw.dim_order_status d WHERE(d.channel_key,d.storefront_key,d.native_status)=(s.channel_key,s.storefront_key,l.status_raw));
UPDATE dw.dim_order_status d SET reviewed_status=l.canonical_status,mapping_version='native-lifecycle-v1',source_timezone='Asia/Ho_Chi_Minh'
FROM(SELECT DISTINCT s.channel_key,s.storefront_key,l.status_raw,l.canonical_status FROM staging.order_line l JOIN source_scope s USING(source_code)) l
WHERE(d.channel_key,d.storefront_key,d.native_status)=(l.channel_key,l.storefront_key,l.status_raw);
INSERT INTO dw.dim_order_status(channel_key,storefront_key,native_status,reviewed_status,mapping_version,source_timezone)
SELECT channel_key,storefront_key,'CONFLICT','UNKNOWN','native-lifecycle-v1','Asia/Ho_Chi_Minh' FROM source_scope s
WHERE source_code<>'ratings' AND NOT EXISTS(SELECT 1 FROM dw.dim_order_status d WHERE d.storefront_key=s.storefront_key AND d.native_status='CONFLICT');

-- Reuse a legacy SKU surrogate if available; name changes do not create new SKU keys.
WITH choices AS(SELECT p.storefront_key,l.product_nk,min(p.source_product_sku_key) k
 FROM(SELECT DISTINCT source_code,product_nk,sku FROM staging.order_line)l JOIN source_scope s USING(source_code)
 JOIN dw.dim_source_product_sku p ON p.storefront_key=s.storefront_key AND p.native_sku_id=l.sku
 WHERE p.product_nk IS NULL AND l.sku<>'' AND NOT EXISTS(SELECT 1 FROM dw.dim_source_product_sku x WHERE x.storefront_key=s.storefront_key AND x.product_nk=l.product_nk)
 GROUP BY p.storefront_key,l.product_nk)
UPDATE dw.dim_source_product_sku p SET product_nk=c.product_nk FROM choices c WHERE p.source_product_sku_key=c.k;
INSERT INTO dw.dim_source_product_sku(channel_key,storefront_key,native_product_id,native_sku_id,seller_sku,product_name,variation_name,product_nk,normalized_name,category_key,canonical_category,category_original,category_rule,category_mapping_status,mapping_status,mapping_version)
SELECT DISTINCT ON(s.storefront_key,l.product_nk) s.channel_key,s.storefront_key,NULL,l.sku,l.payload->>'seller_sku',l.product_name,l.payload->>'variant',l.product_nk,l.normalized_name,c.category_key,l.canonical_category,l.category_original,l.payload->>'category_rule',l.payload->>'category_mapping_status','VALIDATED','2026-11-04-name-rules-v1'
FROM staging.order_line l JOIN source_scope s USING(source_code) LEFT JOIN dw.dim_category c USING(canonical_category)
ORDER BY s.storefront_key,l.product_nk,l.row_no DESC
ON CONFLICT(storefront_key,product_nk) WHERE product_nk IS NOT NULL DO UPDATE SET
 product_name=excluded.product_name,variation_name=excluded.variation_name,normalized_name=excluded.normalized_name,seller_sku=excluded.seller_sku,
 category_key=excluded.category_key,canonical_category=excluded.canonical_category,category_original=excluded.category_original,category_rule=excluded.category_rule,category_mapping_status=excluded.category_mapping_status,mapping_status=excluded.mapping_status,mapping_version=excluded.mapping_version;

CREATE TEMP TABLE order_group ON COMMIT DROP AS
SELECT source_code,order_id,min(storefront_key) storefront_key,min(channel_key) channel_key,
 min(created) created,min(paid) paid,min(shipped) shipped,max(delivered) delivered,min(canceled) canceled,
 CASE WHEN count(DISTINCT status_raw)=1 THEN min(status_raw) ELSE 'CONFLICT' END native_status,
 CASE WHEN count(DISTINCT warehouse_raw)=1 THEN min(warehouse_raw) END warehouse_raw,
 CASE WHEN count(DISTINCT province_raw)=1 THEN min(province_raw) END province_raw,count(*) line_count,
 CASE WHEN count(DISTINCT order_amount)=1 THEN min(order_amount) END amount,
 CASE WHEN count(DISTINCT refund)=1 THEN min(refund) END refund,
 CASE WHEN count(DISTINCT (payload->>'payment_upper'))=1 THEN min((payload->>'payment_upper')::numeric) END payment_upper,
 CASE WHEN count(DISTINCT (payload->>'payment_lower'))=1 THEN min((payload->>'payment_lower')::numeric) END payment_lower,
 CASE WHEN count(DISTINCT order_amount)>1 OR count(DISTINCT refund)>1 OR count(DISTINCT status_raw)>1 THEN 'CONFLICTING' ELSE 'CONSTANT' END reconciliation
FROM valid_line GROUP BY source_code,order_id;
DELETE FROM dw.fact_review_candidate f WHERE NOT EXISTS(SELECT 1 FROM staging.review r WHERE(r.source_code,r.row_no)=(f.source_code,f.physical_row_number)
 AND NOT EXISTS(SELECT 1 FROM ops.quarantine q WHERE(q.source_code,q.row_no)=(r.source_code,r.row_no)));
DELETE FROM dw.fact_order_line_candidate f WHERE NOT EXISTS(SELECT 1 FROM valid_line l WHERE(l.source_code,l.row_no)=(f.source_code,f.physical_row_number));
