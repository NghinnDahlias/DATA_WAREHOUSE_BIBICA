"""Set-based current facts; keep existing surrogate keys and scoped foreign keys."""
def upsert(c,table,columns,select,keys):
    update=[n for n in columns if n not in keys];compare=[n for n in update if n!='ingestion_batch_key']
    c.execute(f"INSERT INTO {table} ({','.join(columns)}) {select} ON CONFLICT({','.join(keys)}) DO UPDATE SET "+
        ','.join(n+'=excluded.'+n for n in update)+' WHERE ('+','.join(table+'.'+n for n in compare)+') IS DISTINCT FROM ('+','.join('excluded.'+n for n in compare)+')')

def load_facts(c):
    dt=lambda x:f"to_char({x},'YYYYMMDD')::integer";tm=lambda x:f"to_char({x},'HH24MISS')::integer"
    cols=['order_key','channel_key','storefront_key','order_status_key','warehouse_key','province_key']
    expr=['o.order_key','g.channel_key','g.storefront_key','s.order_status_key','w.warehouse_key','p.province_key']
    for name in ['created','paid','shipped','delivered','cancelled']:
        field='canceled' if name=='cancelled' else name
        cols += [name+'_date_key',name+'_time_key'];expr += [dt('g.'+field),tm('g.'+field)]
    cols += ['source_file_key','ingestion_batch_key','order_row_count','order_amount_source','buyer_payment_source_1','buyer_payment_source_2','refund_amount_source','reconciliation_status']
    expr += ['sc.source_file_key','sc.ingestion_batch_key','g.line_count','g.amount','g.payment_upper','g.payment_lower','g.refund','g.reconciliation']
    joins=""" FROM order_group g JOIN source_scope sc USING(source_code)
      JOIN dw.dim_order_identity o ON o.storefront_key=g.storefront_key AND o.native_order_id=g.order_id
      JOIN dw.dim_order_status s ON s.storefront_key=g.storefront_key AND s.native_status=g.native_status
      LEFT JOIN dw.dim_warehouse w ON w.storefront_key=g.storefront_key AND w.native_warehouse_name=coalesce(nullif(g.warehouse_raw,''),'Unknown')
      LEFT JOIN dw.dim_province p ON p.native_province_name=g.province_raw"""
    upsert(c,'dw.fact_order_lifecycle_candidate',cols,'SELECT '+','.join(expr)+joins,['order_key'])
    cols=['order_key','channel_key','storefront_key','source_product_sku_key','warehouse_key','province_key','order_status_key']
    expr=['o.order_key','l.channel_key','l.storefront_key','p.source_product_sku_key','w.warehouse_key','g.province_key','s.order_status_key']
    for role,field in [('order_created','created'),('paid','paid'),('shipped','shipped'),('delivered','delivered')]:
        cols += [role+'_date_key',role+'_time_key'];expr += [dt('l.'+field),tm('l.'+field)]
    cols += ['source_file_key','ingestion_batch_key','source_sheet_name','physical_row_number','source_row_hash','quantity','returned_quantity','unit_price_source','gross_item_amount_source','net_item_amount_source','seller_discount_source','platform_discount_source','shipping_buyer_charge_source','order_amount_source','source_row_quality_status','source_code','category_key','category_mapping_status']
    expr += ['sc.source_file_key','sc.ingestion_batch_key','sc.sheet_name','l.row_no','l.row_hash','l.quantity','l.returned_quantity',"(l.payload->>'list_unit_price')::numeric",'l.gross','l.item_after','l.seller_discount','l.platform_discount','NULL','NULL',"'ACCEPTED'",'l.source_code','cat.category_key',"l.payload->>'category_mapping_status'"]
    joins=""" FROM valid_line l JOIN source_scope sc USING(source_code)
      JOIN dw.dim_order_identity o ON o.storefront_key=l.storefront_key AND o.native_order_id=l.order_id
      JOIN dw.dim_source_product_sku p ON p.storefront_key=l.storefront_key AND p.product_nk=l.product_nk
      JOIN dw.dim_warehouse w ON w.storefront_key=l.storefront_key AND w.native_warehouse_name=coalesce(nullif(l.warehouse_raw,''),'Unknown')
      JOIN dw.dim_province g ON g.native_province_name=l.province_raw
      JOIN dw.dim_order_status s ON s.storefront_key=l.storefront_key AND s.native_status=l.status_raw
      LEFT JOIN dw.dim_category cat ON cat.canonical_category=l.canonical_category"""
    upsert(c,'dw.fact_order_line_candidate',cols,'SELECT '+','.join(expr)+joins,['source_code','physical_row_number'])
    c.execute('''CREATE TEMP TABLE review_match ON COMMIT DROP AS
      SELECT o.order_key,l.normalized_name,min(f.source_product_sku_key) product_key,count(DISTINCT f.source_product_sku_key) candidates
      FROM dw.fact_order_line_candidate f JOIN valid_line l ON(l.source_code,l.row_no)=(f.source_code,f.physical_row_number)
      JOIN dw.dim_order_identity o USING(order_key) WHERE l.source_code='tiktok_bibica' GROUP BY 1,2''')
    cols=['order_key','channel_key','storefront_key','review_date_key','review_time_key','source_file_key','ingestion_batch_key','source_sheet_name','physical_row_number','source_row_hash','source_product_id','source_product_sku_key','star_level','has_review_text','review_text_length','product_linkage_status','review_quality_status','source_code','match_confidence']
    expr=['o.order_key','sc.channel_key','sc.storefront_key',dt('r.review_date'),tm('r.review_date'),'sc.source_file_key','sc.ingestion_batch_key','sc.sheet_name','r.row_no','r.row_hash',"r.payload->>'product_id'",'CASE WHEN m.candidates=1 THEN m.product_key END','r.stars::integer',"(r.payload->>'text_present')::boolean","coalesce((r.payload->>'review_text_length')::integer,0)","CASE WHEN m.candidates=1 THEN 'VALIDATED' ELSE 'ORDER_ONLY' END","'ACCEPTED'",'r.source_code',"CASE WHEN m.candidates=1 THEN 'EXACT_NAME_WITHIN_ORDER' ELSE 'ORDER_ONLY' END"]
    joins=""" FROM staging.review r JOIN source_scope sc USING(source_code)
      JOIN dw.dim_order_identity o ON o.storefront_key=sc.storefront_key AND o.native_order_id=r.order_id
      JOIN dw.fact_order_lifecycle_candidate f USING(order_key)
      LEFT JOIN review_match m ON m.order_key=o.order_key AND m.normalized_name=r.normalized_name
      WHERE NOT EXISTS(SELECT 1 FROM ops.quarantine q WHERE(q.source_code,q.row_no)=(r.source_code,r.row_no))"""
    upsert(c,'dw.fact_review_candidate',cols,'SELECT '+','.join(expr)+joins,['source_code','physical_row_number'])
    c.execute('''DELETE FROM dw.fact_order_lifecycle_candidate f WHERE NOT EXISTS(
      SELECT 1 FROM order_group g JOIN dw.dim_order_identity o ON o.storefront_key=g.storefront_key AND o.native_order_id=g.order_id WHERE o.order_key=f.order_key)
      AND NOT EXISTS(SELECT 1 FROM dw.fact_review_candidate r WHERE r.order_key=f.order_key)''')
