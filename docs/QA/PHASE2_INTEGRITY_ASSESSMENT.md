# Kiểm toán độc lập KPI, nguồn và API Phase 2

## Phương pháp và phạm vi

Chạy mới `scripts/assess_integrity.py` trên database bibica_repo và API loopback8001. Mọi SQL kiểm toán dùng read-only REPEATABLE READ. Không thay dữ liệu nguồn, warehouse hoặc database cha. Các kiểm thử tạo fixture dùng database ngẫu nhiên riêng, tự xóa đúng database đó.

Đối soát nguồn dùng sanitized staging projections, physical locator và native-file SHA256. Lần audit này không đọc lại toàn bộ native XLSX vào parser mới. Bằng chứng nạp lại/reload được thực hiện riêng bởi tiến trình nghiệm thu chung.

Oracle KPI dùng facts/dimensions trực tiếp, không gọi các hàm cohort/KPI của API và không đọc số PASS cũ. CTE oracle được materialize, session kiểm toán đặt enable_nestloop=off để tránh lặp scan khi CTE không có column statistics. Thiết lập này không tác động cấu hình hoặc các connection của API.

## Ma trận truy vết

| Nghiệp vụ | Grain, nguồn và join | Công thức và mẫu số | Test/input và expected |
|---|---|---|---|
| Phân biệt sàn và shop | Lifecycle order scoped storefront/channel, source snapshots | COUNT order, không gộp hai shop Shopee | Source/store riêng và source-store mâu thuẫn, cohort mâu thuẫn rỗng |
| Tiền đơn không nhân do SKU/review | Lifecycle một order, accepted line và review riêng | SUM payable tại order, completed phải COMPLETED | Multi-line/multi-review fixture và full-data oracle, cùng kết quả khi join bằng EXISTS |
| Giao thoa kho/category/tỉnh | Item FK kho/category/province, order EXISTS cùng một dòng | Orders distinct trong cùng cohort, item quantity chỉ dòng đã lọc | Source×category×warehouse×province×month, không ghép cake tạiHN với candy tạiHCM để thỏa cake-HCM |
| SKU/tên hiện hành khác lịch sử | Historical item category so staging và Product Type1 | Category giao dịch theo source-line FK | Mọi accepted line giữ category đúng source name, không dùng tên Type1 để viết lại lịch sử |
| Null, zero, missing refund | Lifecycle order_amount/refund và conflict flag | NULL không bằng0, refund rate trên đơn có quan sát | Tách missing/zero/positive, empty cohort SUM/rate NULL |
| Hủy/hoàn và cutoff | Canonical status, created/shipped/delivered từ staging/order roles | Denominator mọi order kể cả UNKNOWN cho cancellation | Đối soát tất cả status/timestamps, filters date inclusive và các status rỗng |
| Rating xấu | Accepted review, historical unique-product/order link | Low-review count / review count, không chia mọi đơn | Fixture3reviews/2low trong8orders phải2/3, distinct reviewed orders2 |
| Review coverage và fan-out | One review/order relation, 630multi-review orders | Distinct reviewed TikTok orders / cohort TikTok orders | Review count và money so oracle riêng, không AVG của AVG hoặc count review theo line |
| Unknown địa lý | Customer province nguyên nghĩa destination, kho độc lập | Technical Unknown được giữ và công bố | Probe Unknown, không suy kho/tỉnh lẫn nhau |
| Thời gian so sàn | Date window chung có mặt ở cả3source | Common observed window, không chứng nhận xuất đủ ngày | Cùng start/end cho từng source, vẫn đối soát đúng expected cohort |
| Khách hàng | DW không có verified privacy-safe customer key | Distinct/cross-platform customers UNAVAILABLE | API từ chối dimension/customer filter không được hỗ trợ, tỉnh không giả thành customer identity |
| CSKH gửi bù | Không có event lifecycle đã xác minh | Promised/dispatched/received/resolved UNAVAILABLE | Không có chỉ số0 hoặc lời hứa bị coi là hoàn tất |
| Đọc đồng thời | Read-only API snapshots, không mutate warehouse | Same source request phải cùng numeric digest |24requests/4workers, HTTP200 và tổng KPI trước/sau không đổi |

## Kết quả dữ liệu quan sát

- Nguồn/staging→fact có54015Shopee Bibica orders,9829Quasure orders,63744TikTok orders. Accepted lines tương ứng86481/14725/77311. Không có sai lệch tiền đơn, refund nhất quán hoặc order row count trong phép đối soát từng order.
- Tất cả accepted lines giữ quantity/gross/item payable/seller subsidy từ staging. Canonical historical category và kho/tỉnh khớp projection nguồn. Tiền cấp đơn/shipping cấp đơn không được chép vào line measures để cộng lặp.
- Shopee Bibica có9450order payable0, Quasure1592 và TikTok201. Những0quan sát này khác missing refund. Shopee thiếu toàn bộ cash-refund observations. TikTok có55217NULL refund,13zero,8514positive và957reconciliation conflicts.
-68accepted lines có Unknown customer province, đều ở TikTok. Warehouse region của các accepted lines được nhận diện từ nhãn kho nguồn. Không biến các Unknown thành tỉnh theo vùng kho.
-115Shopee Bibica lines và365TikTok lines có category lịch sử khác category hiện hành của Product Type1. Đây là khác biệt lịch sử được giữ có chủ đích, source-line categorization vẫn đúng. Quasure không có trường hợp khác trong snapshot này.
-5625accepted reviews thuộc4661orders.630orders có nhiều review, tối đa10review/order. Không có review date trước ngày tạo đơn trong snapshot.4870review links được xác minh theo historical unique name,755ORDER_ONLY không được tự gán SKU.
- Minh họa phép join sai toàn đơn×items×reviews cho181622joined rows và21.082.367.974VND repeated payable. Tổng payable đúng một lần/order là11.436.241.212VND. Đây là booked observed payable mọi trạng thái, không phải net revenue hoặc completed payable. API được đối chiếu bằng oracle không fan-out.

## Kết quả kiểm thử và bằng chứng hiện hành

`reports/phase2_assessment/integrity.json` là báo cáo tổng hợp chạy mới. Nó ghi từng cohort, số measures đã so, mọi mismatch và kết quả concurrency. Chỉ dùng status hiện hành của lần chạy hoàn tất, không suy PASS từ các snapshot đang RUNNING hoặc thất bại trong quá trình sửa công cụ kiểm thử.

`reports/phase2_assessment/integrity_unit.json/log` ghi6regression mới đã chạy PASS,0skip. Cases gồm giao thoa nhiều chiều cùng dòng, contradictory source/store, Unknown destination, review denominator, customer unavailable, missing month/NULL và read-only parallel fixture.

Lần cuối20/20assertions PASS,68cohort/2108numeric measures khớp oracle. HTTP kiểm24source-cohort requests/4workers và16requests/4workers lặp riêng sourceShopeeBibica-categoryBánh, đều khớp. integrity_live_v2.json có7/7checks trên ownedserver cuối, gồm explicit unavailable capabilities và31numeric measures.

Targeted concurrency đã tái hiện sai số thật ở đường parallel query của local PostgreSQL, không thể quy mọi mismatch là lỗi test tool. Đối chứng cùng SQL/read-only snapshot cho max_parallel_workers_per_gather=2 có12/24mismatch, mode0 có0/24. API thêm SET LOCAL max_parallel_workers_per_gather=0. Source/private bytes và business fingerprints giữ nguyên. Guard được regression kiểm trong snapshot; underlying engine/plan root cause còn mở. Diagnostic lưu cả đường lỗi trong sql_parallel_diagnostic.json, initialFAILởcohort_recheck_initial.json. Requests HTTP vẫn đồng thời, SQL trong từng request chạy với mode0.

Các lỗi công cụ kiểm toán đã phát hiện gồm cú pháp interval tháng, tên parameter source_code thay vì source và nested-loop scan của CTE oracle thiếu statistics. Chúng được sửa trong script/test, không phải lỗi KPI production. API từ chối source_code với422 theo allowlist là hành vi đúng. Script có guard để oracle không im lặng bỏ qua filter bị gõ sai.

## Giới hạn và tiêu chí chốt

KPI/lineage có thể chốt trong scope local khi mọi integrity assertion và các numeric cohort comparisons đều PASS, raw hashes giữ nguyên, không có buyer/raw rows trong reports, và regression chung sau các sửa DSS vẫn PASS.

Bounded concurrent GET chỉ xác nhận24requests trên4workers của máy hiện tại. Nó không chứng nhận tải nhiều người dùng, concurrency solver/ETL, crash recovery hoặc availability production. Inventory, shelf-life, resend lifecycle và customer identity cần dữ liệu/contract khác mới đo được. Khác vùng kho-khách có thể hợp lệ và không phải lỗi integrity hoặc bằng chứng hết hàng. Readiness toàn DSS còn phụ thuộc kiểm chứng policy bánh ăn sáng, review attribution/severity và oracle allocation của các phần nghiệm thu khác.
