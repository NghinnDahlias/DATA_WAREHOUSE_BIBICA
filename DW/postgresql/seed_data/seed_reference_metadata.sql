BEGIN;

INSERT INTO dw.dim_channel (channel_code, channel_name)
VALUES
    ('tiktok', 'TikTok Shop'),
    ('shopee', 'Shopee')
ON CONFLICT (channel_code) DO UPDATE
SET channel_name = EXCLUDED.channel_name;

INSERT INTO dw.dim_storefront (channel_key, storefront_code, storefront_name, product_line)
SELECT c.channel_key, x.storefront_code, x.storefront_name, x.product_line
FROM (
    VALUES
        ('tiktok', 'bibica_tiktok_shop', 'Bibica TikTok Shop', NULL::text),
        ('shopee', 'bibica_official_store', 'Bibica Official Store', NULL::text),
        ('shopee', 'quasure_specialized_store', 'Quasure specialized store', 'Quasure')
) AS x(channel_code, storefront_code, storefront_name, product_line)
JOIN dw.dim_channel c ON c.channel_code = x.channel_code
ON CONFLICT (storefront_code) DO UPDATE
SET channel_key = EXCLUDED.channel_key,
    storefront_name = EXCLUDED.storefront_name,
    product_line = EXCLUDED.product_line;

INSERT INTO dw.dim_source_file
    (source_file_name, source_sha256, sheet_name, source_kind, source_storefront)
VALUES
    ('Tiktokshop_Bibica.csv',
     'bcd3b91a63c11c6dbff2b58ea6d8540a218937040e1ae123ab7a522233dcee2b',
     'csv', 'tiktok_sales', 'Bibica TikTok Shop'),
    ('Tiktokshop_Bibica_Rating.csv',
     'aa24d78941a1cb63b7ef083ad3cc9cea1fcb58874b4b7dfa6d24f058b9ea7cb8',
     'csv', 'tiktok_reviews', 'Bibica TikTok Shop'),
    ('Shopee_Bibica.xlsx',
     'd48b9fd897d0981562d7d1c8138d0b0ab95d4785c6992a010e939655a6bf54bc',
     'orders', 'shopee_orders', 'Bibica Official Store'),
    ('Shopee_Quasure.xlsx',
     '62f846ddb4fec6bf90a0bad78e8aada409f67348b2fcb9019f5e1b1e8acb0b6d',
     'orders', 'shopee_orders', 'Quasure specialized store')
ON CONFLICT (source_file_name, source_sha256, sheet_name) DO UPDATE
SET source_kind = EXCLUDED.source_kind,
    source_storefront = EXCLUDED.source_storefront;

COMMIT;
