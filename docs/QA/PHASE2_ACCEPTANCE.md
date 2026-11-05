# Nghiệm thu DSS Phase 2 theo nghiệp vụ — 05/11/2026

**Kết luận là CONDITIONAL_ACCEPTANCE cho DSS phân tích và mô phỏng có giải thích.** Các gates kỹ thuật trong cấu hình runtime được kiểm đều PASS. Điều kiện dùng kết quả để vận hành kho thật còn mở ở cuối báo cáo. Việc chốt/publish thuộc quyết định người dùng sau khi đọc kết quả này.

Phạm vi kiểm là repo DATA_WAREHOUSE_BIBICA, database bibica_repo55432, API8001. Không có thay đổi frontend. Bốn native sources bất biến, private processing/runtime vẫn ignored, không commit/push. Các snapshot61tests của lần triển khai ban đầu không thay bằng chứng mới.

## Bằng chứng thực chạy

| Phần kiểm | Kết quả hiện hành | Evidence |
|---|---|---|
| Toàn suite cũ+mới |114/114tests PASS,0failure/error/skip |reports/phase2_tests.json/log |
| Business eligibility/MILP |25/25methods,30seeded fixture cases |allocation_tests.log, tests/test_dss_business.py |
| Oracle toàn3shop |90/90scenario assignments khớp exhaustive oracle,94/94assessment checks |phase2_assessment/allocation.json |
| Source/KPI/API |20/20assertions,68cohorts,2108numeric comparisons khớp |phase2_assessment/integrity.json |
| Review audit |11/11assertions,19unit methods,17axes/1939groups |phase2_assessment/reviews*.json |
| Full-data API/DSS |18/18assertions |reports/phase2_verification.json |
| Live HTTP |32requests HTTP200,16assertions;7capability checks |phase2_live_http.json, integrity_live_v2.json |
| Đọc đồng thời giới hạn |24source requests+16targeted requests,4workers, số liệu lặp khớp |integrity.json |
| ETL/OLAP và private layers |16/16gates,11/11checks,15Golden tables/56FK reload, replay0raw writes |etl_validation.json, processing_verification.json |
| Local SQL parallel diagnostic |mode2 có12/24mismatch, mode0 có0/24; serial mitigation đã kiểm |sql_parallel_diagnostic.json |

Các unit subsets đã nằm trong114tests, không cộng chúng lại thành tổng tests mới.90scenario cases và68full-data cohort probes là kiểm ngoài unit suite.40concurrent HTTP requests khác32HTTPsmoke requests. Mode2diagnostic là đường lỗi tái hiện có chủ đích, không được đếm là PASS.

## Tiêu chí pass/fail đã áp dụng

- Mọi đối soát orders/items/reviews, tiền, quantity, category lịch sử, khóa scoped và lexical rating IDs phải không có violation. Mỗi31numeric measures của từng cohort phải khớp oracle độc lập trong tolerance1e-12 cho decimal ratios. Missing/zero không được tráo nghĩa.
- Mọi scenario tối ưu phải khả thi, không oversell SKU/capacity, giữ nguyên đơn, không dùng tồn sỉ choTMĐT. Small-batch oracle phải khớp served-count vàunperturbed utility đến7decimal places. Solver chưa chứng nhận optimum, vectorNaN/ngoài bounds hoặc sai resource phải bị từ chối.
- Review denominator là reviews, order coverage dùng distinct orders riêng. Phải công bố ngưỡng, số tuyệt đối, tỷ lệ, uncertainty, coverage vàunknown. Không suy lỗi từ sao hoặc gắn nguyên nhân kho/carrier từ tương quan.
- API input/DB/solver errors phải đúng contract và không echo buyer text/DSN. Source bytes, fingerprint nghiệp vụ và dữ liệu giữa các read-only requests phải nguyên vẹn. Dữ liệu thiếu ngoài contract phải unavailable/null, không có số0 giả.
- Nghiệm thu chỉ áp dụng cấu hình API giữ max_parallel_workers_per_gather=0 đã được retest. Chưa có chứng nhận cho runtime bật lại parallel query path, tải lớn, solver concurrency, ETL concurrency hoặc crash recovery.

## Ma trận truy vết hợp nhất

| ID | Nghiệp vụ → chỉ số | Nguồn/grain/join và công thức/mẫu số | Input và expected result | Kết quả / evidence |
|---|---|---|---|---|
| B01 | Ba shop/sàn vàSKU riêng | Lifecycle source+order identity, product scoped storefront | Source/store riêng, contradiction rỗng, warehouse khác shop422 |PASS, integrity vàAPI tests |
| B02 | Tiền đơn không nhân SKU/review | Một lifecycle/order, SUMpayable một lần; item/review tổng riêng | Multi-line/multi-review, EXISTS cùng dòng |PASS,68cohorts; fan-out demo có số sai để đối chiếu |
| B03 | Hoàn-hủy/null/zero | Order status vàrefund nhất quán; cancel/totalorders, refundpositive/observedrefund | Giữ UNKNOWN ởdenominator, NULL khác0, emptySUMNULL |PASS, source reconciliation từngorder |
| B04 | Thời gian | Created/shipped/delivered role dates, ngày local inclusive | Mixed-source mean unavailable, timestamps không lùi, knownfuture outcomes excluded |PASS, cutoff tests vàfullsource timestamps |
| B05 | Category/SKU lịch sử | FactlinecategoryFK từ tên staging, khôngnativeTikTokcategory | Type1 đổi tên không viết lại lịch sử |PASS,480lines khácType1 được giữ đúng source-line |
| B06 | Kho vàtỉnh/vùng nhận | Kho từ nativewarehouse scopedstore, tỉnh từsource riêng | Unknown giữ nguyên, kho không suy từtỉnh |PASS,68Unknownprovince lines;không có approvedmacroregion/customeridentity contract |
| B07 | Rating xấu | Một acceptedreview, COUNTstars<=t/COUNTreviews | Threshold1/2/3 nested, không dùng127588orders làmdenominator |PASS,194/262/448trên5625 |
| B08 | Coverage vàmultiplicity | DISTINCTreviewedTikTokorders/TikTokorders |630multi-revieworders, max10; ORDER_ONLYkhông giảSKU |PASS,4661/63744,755SKU-unlinked |
| B09 | Severity/nguyên nhân | Reviewtext chỉ controlledmulti-label mentions, không rawtext ra report | Negation, unknown, bao bì khác bánh vỡ, cận hạn khác hỏng |MechanismPASS, real-label accuracyUNAVAILABLE |
| B10 | CSKH gửi bù | Chưa có typedpromise/dispatch/receipt/resolution events | Promise không thành hoàn tất; thiếu không thành0 |PASSavailability contract, operationalmetricsUNAVAILABLE |
| B11 | Chuyển kho linh hoạt | Scenario stock/capacity theoSKU/kho, khách tỉnh là inputđộc lập | KháchHàNội có thể xuấtHCM khiHNkhôngđủstock |PASS, không có objective cân bằng kho hoặc inferredstockoutcause |
| B12 | Breakfast mặc địnhHN | Name-explicit hoặcmanualSKU policy, HCMexception scoped | HCMnhanh hơn không tự được chọn, HCM cần evidence+ECOMMERCEstock+HSD |PASS25business methods; nguồnHCMmâu thuẫn thông lệ cònđiều kiện xác nhận |
| B13 | Nguyên đơn, mixedgift | Toàn SKUquantity từ batch, stock/capacity cộng toànbatch | Kho mỗi nơi thiếu mộtSKU thìunassigned; mixedgift cầnexplicitgiftstock |PASS,6877historicalmixedgiftorders làpopulation liênquan |
| B14 | Thiếu cả mạng/tie/solver | Binaryassignment+unassigned, maximize served rồiminutility | Scarce stock, input đảo thứ tự, nonoptimal/NaN/boundsfail |PASS, exhaustiveoracle vànegativebackendtests |
| B15 | HSD/scoring/what-if | Remaining-at-dispatch scenario−historicalp90−delay−buffer; cùng snapshot | Biên bằngbuffer đủ, tăngdelay hoặc giảmHSD không tự giảmexceedance |PASS, mức rủi ro vẫn làruleindex |
| B16 | So sánh đa chiều | Source/shop/month/SKU/category/warehouse/province vàintersections | Cohortcùngngày/dòng, không AVGofAVG |PASS,68KPIcohorts và17reviewaxes |
| B17 | Khách hàng | Không có stableprivacy-preservingcustomerkey | Không dùng buyername/province giảcustomeridentity |UNAVAILABLE được test422/metadata |
| B18 | Đồng thời vàprivacy | Read-onlyREPEATABLE READ, serialSQL trong từngrequest |40boundedHTTPrequests khớp, privatefields khôngxuất |PASStrong cấu hìnhguard, parallelenginecause chưa giải quyết gốc |

Chi tiết đầy đủ theo từng nhóm nằm ở PHASE2_INTEGRITY_ASSESSMENT.md, PHASE2_ALLOCATION_ASSESSMENT.md và PHASE2_REVIEW_ASSESSMENT.md. Mỗi nhóm có các test names, formulas và fileevidence riêng.

## Các lỗi đã tìm và sửa

| Mức | Lỗi tái hiện | Sửa và regression |
|---|---|---|
| P1 | Breakfast chưa cóHN-default, generic/wholesale stock có thể mởHCM | Scopedexception+ECOMMERCEstock, manualSKUoverride, khônginfer tồnTMĐT từhistoricalsales |
| P1 | Review của order nhiều kho bị gắn lặp cho từngkho | UniquehistoricalSKU/orderwarehouse, ambiguousgiữunattributed; fixture3reviews phân1HN/2HCM |
| P1 | Mixedgift bị loại cùng gift-only | Whole-order mixedcommercial+gift chấpnhận explicitgiftstock, gift-only/Unmappedmanualreview |
| P1 | Backend báo success với malformed/nonoptimal result có thể qua guard | Status/gap/finite/bounds/integer/resource validation, timeoutkhônggọioptimum |
| P2 | Scarce-stocktie thay mapping khi đảo input | Sắp variable/resource order theo stablekeys, permutationtest |
| P2 | Outcome có ngày hủy/giao saucutoff vẫn vào trạng thái scoring | Loại knownfuture outcomes, côngbố snapshot event-time thiếu |
| P1mitigated | SQLparallel query mode làm cohort KPI dao động dưới concurrentreads | SET LOCALmax_parallel_workers_per_gather=0,24serial đốichứng và40HTTPrequestsretest; nguyênnhân engine/plan gốc cònmở |

Initial allocationFAIL được giữ trong allocation_initial.json/log. Targeted SQLFAIL được giữ trong cohort_recheck_initial.json. Bộđối chứngsql_parallel_diagnostic.json chứa numericexpected/actual aggregates, không buyer/source rows. GuardSQL là điều kiện cấu hình đã kiểm, không tuyên bố đã sửa corePostgreSQL.

## Số liệu và insight có thể sử dụng

Kho giữ127588orders/178517acceptedlines/5625reviews. Giá trị thanh toán đơnCOMPLETED9175209123VND và168478completedunits không đổi. Các fingerprint orders/items/reviews và4sourcehashes không đổi. Galaxy12dims/3facts/56FK được giữ.

Ratingmean4,6683/5 đi cùng262reviews<=2sao,4,6578%; Wilson95%4,1373–5,2401%, order-clusterbootstrap4,0297–5,2794%. Chỉ4661/63744TikTokorders córeview,7,312%. Hai shopShopee không córatingexport.755reviewchưa gắnSKU,195/262negative chưa cóexplicitissue label,31negative khôngcótext.1603/1939nhóm n<30 đượcflag.

Offline controlledmentions gồm55bao bì,16bánhvỡ,22thiếu,9sai và11hỏng/hếthạn.23bao bì mentions nằm ởstars4/5. Các nhãn này hỗ trợ đọc/ưu tiên xem xét, chưa là incidentđãxácnhận hoặc nguyênnhân. Có1dispatchclaim và1resolutionclaim trongtext, vẫn khôngcóoperational service metrics khi thiếu eventhistory. KhoHN/HCM vàdurationkhác nhau chỉ là association có confounding vàselection, khôngđủ quy lỗi kho/carrier/đườngxa.

MILP khớp oracle cả90scenario và phục vụ nhiều hơn feasiblegreedy trong6case. Đây là hiệu quả thuật toán trong giảđịnh resource. Objectivechưa tối đa doanh thu/profit, không có new-demand ordervalue/cost/loss contract để đo lợi ích tiền. Historical p90 trên holdout chỉ đạt84,91–89,39%coverage, chưa bảo đảm90%giaođúnghạn hoặc an toàn thực phẩm.

Demo hiện hành cho4đơn breakfast vềHN mặc định. Nếu HNcapacity0 và có ngoại lệTMĐTHCM được khai minh thị thì4đơn đổi kho. HSD5ngày+delay4ngày+buffer1ngày làm4đơn khôngđủđiềukiện. Không ép phảicóassignment hoặc balanceHN/HCM.

## Điều kiện trước khi dùng cho vận hành thực

1. Xác nhận danh sách SKU, hiệu lực chính sách bánh ăn sáng mặc định Hà Nội và ý nghĩa nhãn kho trong nguồn. Tên dòng lịch sử ghi nhận 162 dòng ở Hà Nội và 1.744 dòng ở HCM, khác mô tả HCM hiếm. Lý do khác biệt cần được xác minh từ nghiệp vụ.
2. Xác nhận mapping tên Pleasure/Quasure. Nguồn và catalog đang ghi Quasure, ba shop và các khóa riêng theo shop được giữ nguyên.
3. Cần nguồn WMS, lô/hạn dùng, năng lực kho và cơ chế giữ chỗ hàng nếu điều phối thực tế giữa nhiều yêu cầu. Constraints hiện chỉ áp dụng trong một batch kịch bản.
4. Nhãn nội dung review cần tập gán nhãn độc lập trước khi dùng để tự động quyết định. Cần lịch sử CRM/khiếu nại/gửi bù để đo các bước hứa, gửi, nhận và giải quyết. Phân tích theo khách hàng cần hợp đồng định danh bảo vệ riêng tư đã xác minh.
5. Giữ cấu hình truy vấn tuần tự. Chỉ bật lại parallel sau khi điều tra và regression trên môi trường đích. Tải production, đồng thời solver và crash recovery chưa được kiểm. Hiệu quả giảm hư hỏng hoặc tăng doanh thu thực tế chưa được chứng minh.

Các điều kiện này không ngăn tái lập demo/SQL/KPI/phân tích trong scope đã kiểm. Người dùng có thể chốt Phase2 ở mức DSSphântích/môphỏng cóđiềukiện, đồng thời giữ các điều kiện vận hành là openitems trong hồsơ nghiệmthu.
