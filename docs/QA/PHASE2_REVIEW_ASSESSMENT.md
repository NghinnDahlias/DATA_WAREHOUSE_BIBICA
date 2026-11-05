# Đánh giá độc lập rating và nội dung review — 05/11/2026

## Phạm vi và kết quả thực chạy

Đã đọc trực tiếp workbook rating bất biến bằng parser Ratings hiện hành, chỉ gắn controlled labels trong bộ nhớ cho5625review đã được fact chấp nhận. Không ghi review text, buyer labels, source order IDs hoặc source-row samples vào report. Các truy vấn database đều dùng transaction read-only trên bibica_repo.

- 19/19unit tests mới PASS, gồm Unicode/word boundaries/negation, multi-label, phân biệt bao bì với sản phẩm, short shelf-life với spoilage, service claims và bootstrap theo cụm đơn.
-11/11full-data assertions PASS, native source5697rows, accepted5625, workbook SHA256 giữ nguyên và khớp ops.source_current.
-17axes được đánh giá,1939groups,1603groups có n<30. Mỗi axis cộng đúng5625reviews, không cộng các axis với nhau.
-Đã chạy sensitivity sao1/<=2/<=3, Wilson95% và bootstrap2000lần theo4661order clusters, seed20261105. Bootstrap giữ nguyên multiplicity review trong từng order.

Evidence mới ở reports/phase2_assessment/reviews.json, reviews_dimensions.json và reviews_tests.json/log. Cách chạy từ repo root như sau.

```powershell
..\.venv\Scripts\python.exe -X utf8 -m unittest tests.test_review_audit -v
..\.venv\Scripts\python.exe -X utf8 scripts/assess_reviews.py
```

## Ma trận truy vết nghiệp vụ

| Nghiệp vụ | Chỉ số/grain/join và mẫu số | Case/expected result | Kết quả mới |
|---|---|---|---|
| Đánh giá xấu dù điểm trung bình cao | Review grain, count stars<=t / accepted reviews | t1<=t2<=t3, không chia cho mọi đơn |194/262/448trên5625, nestedPASS |
| Một đơn nhiều review/mặt hàng | Reviews→order1:1, thuộc tính item được gom duy nhất trước join | Không nhân review theo số SKU |5625review-order join, naive item join thành8993 |
| Rating coverage | Distinct reviewed TikTok orders / TikTok orders | Source không có ratingexport làUNAVAILABLE |4661/63744=7,312%; hai shop Shopee NULL |
| Không nhận diện được nguyên nhân | Controlled mention rules chỉ từ review_text | Star thấp không tự gán lỗi; unknown giữ lại |195/262review<=2không có issue label rõ,31không có text |
| Thiếu/sai/vỡ/móp và rủi ro nghiêm trọng | Multi-label review text, số tuyệt đối và phân phối sao riêng | Không bị mean che, không quy lỗi carrier/kho |22missing,9wrong,55packaging,16breakage,11spoilage/expired mention |
| CSKH hứa/gửi/nhận/giải quyết | Chỉ text claims nếu có, thiếu workflow event history | Promise không phải dispatch/receipt/resolution | Mọi operational service metricUNAVAILABLE/NULL |
| So sánh kho/tỉnh/SKU/category/thời gian | Một review mỗi axis group, province riêng warehouse | Multi-warehouse ambiguity không nhân dòng, n nhỏ có interval |17axes đều cộng5625,6Unknown/ambiguous province |
| Khách hàng | Chưa có stable privacy-preserving identity contract | Không dùng buyer names làm cross-source customer identity | Customer-level ratesUNAVAILABLE |
| Bánh ăn sáng mặc định Hà Nội | Historical accepted source-line title và kho quan sát | Không suy HCM là sỉ/hết hàng/kho sai khi thiếu lý do | Có xung đột thông lệ với quan sát, cần xác nhận phạm vi |
| Shop chuyên biệt | Storefront keys độc lập với product brand/name | Không gộp hai Shopee shops hoặc đổiQuasure→Pleasure tùy ý |86SKUs specialized store,82có tokenQuasure,0Pleasure |

## Phân phối rating và độ bất định

Mean rating4,6683/5 đi cùng các số tuyệt đối dưới đây. Ngưỡng<=2là convention hiện hành, sensitivity không chứng minh đó là ngưỡng nghiệp vụ duy nhất đúng.

| Ngưỡng | Reviews xấu | Tỷ lệ trên5625reviews | Wilson95% | Bootstrap95%theoorder |
|---|---:|---:|---:|---:|
|1sao|194|3,4489%|3,0029–3,9584%|2,9157–3,9979%|
|<=2sao|262|4,6578%|4,1373–5,2401%|4,0297–5,2794%|
|<=3sao|448|7,9644%|7,2853–8,7010%|7,1479–8,7785%|

Tỷ lệ trên là trong mẫu người đánh giá đã quan sát. Khoảng tin cậy không xử lý được self-selection, thiếu export hoặc khách không đánh giá, nên không được diễn giải thành tỷ lệ mọi khách không hài lòng. Wilson theo review có giả định IID mạnh hơn bootstrap order cluster, cả hai vẫn chưa xử lý dependence theo thời gian.

Có4031đơn một review,413đơn hai review,149đơn ba,38đơn bốn,19đơn năm,8đơn sáu,2đơn tám và1đơn mười. Nếu nối reviews với mọi item của order mà không bảo vệ grain,5625review thành8993dòng và làm sai tỷ lệ/điểm hoặc nhân tiền đơn.

4870reviews có product link,755order-only phải giữ Unlinked khi phân tích SKU/category. Không có review orphan order. Review dates24/08/2023–17/10/2026, không có review trước order trong các facts hiện hành. Phân tích review_month và order_month được xuất tách biệt, không dùng review-month denominator orders của tháng khác.

## Nội dung thực được gắn mention labels

4315reviews có text,1310không có text. Tagger tìm được ít nhất một controlled mention trên162reviews,9reviews có nhiều labels.5463reviews còn unknown hoặc không chứa issue phrase trong bộ từ khóa, không đồng nghĩa không có vấn đề.195negative<=2reviews không được giải thích bằng issue labels hiện hành.

| Nhóm mention | Số review có mention | Trong review<=2sao | Trong review>=4sao |
|---|---:|---:|---:|
|Thiếu hàng|22|12|6|
|Sai/nhầm hàng|9|4|3|
|Bao bì móp/vỡ/xẹp/rách|55|19|23|
|Bánh vỡ/nát|16|8|3|
|Hỏng/mốc/đã hết hạn|11|8|0|
|Cận hạn/date hoặc hạn ngắn|10|2|2|
|Hương vị/texture|41|16|19|
|Giao chậm/lâu|5|0|5|

Multi-label counts không cộng thành số distinct issue reviews. Short shelf-life được tách khỏi spoilage, không coi mọi cận date là incident an toàn thực phẩm. Không có phrase chuột cắn/côn trùng/dị vật được tagger xác nhận trong customer review_text hiện đã chiếu, nhưng đây không phải bằng chứng không xảy ra hoặc không có trong reply/khác nguồn. Regex có thể bỏ sót tiếng lóng, không dấu, lỗi chính tả, ngữ cảnh phủ định xa hoặc thuật ngữ ngoài lexicon.

Tất cả labels là UNVALIDATED_HEURISTIC_MENTION. 19unit tests chỉ kiểm cơ chế và ví dụ tổng hợp, không thay human-labeled validation corpus. Real-data precision/recall còn UNAVAILABLE.

Một review có dispatch claim và một review có resolution claim được nhận diện trong text. Hai claim không xác nhận vận đơn bù, customer receipt hoặc workflow resolved. Hứa/gửi/nhận/xử lý là các nhãn tách biệt và không được chuyển thành tỷ lệ gửi bù hoàn tất. Complaint incidence, replacement promise/dispatch/receipt/resolution count và resolution rate đềuUNAVAILABLE khi thiếu typed event history.

## So sánh đa chiều và giới hạn diễn giải

| Cohort | Negative<=2 / reviews | Tỷ lệ | Wilson95% |
|---|---:|---:|---:|
|Kho Hà Nội|147/1822|8,0681%|6,9040–9,4086%|
|Kho Hồ Chí Minh|115/3803|3,0239%|2,5253–3,6174%|
|Bánh–Hà Nội|126/1306|9,6478%|8,1628–11,3694%|
|Bánh–HCM|56/1825|3,0685%|2,3705–3,9636%|
|Recorded shipped→delivered0–2ngày|159/3981|3,9940%|3,4287–4,6479%|
|Trên2–5ngày|100/1630|6,1350%|5,0699–7,4063%|
|Trên5ngày|3/14|21,4286%|7,5714–47,5892%|

Đây là associations trong cohort đã review. Thời gian giao không phải distance. Chênh lệch kho vẫn có thể do SKU, product mix, tỉnh, thời gian, selection và các biến chưa đo. Cột theo category chưa kiểm soát đầy đủ những biến đó.14reviews giao trên5ngày quá ít để kết luận tỷ lệ tổng thể21,43% hoặc quy lỗi vận chuyển xa.1603/1939groups n<30được flag, không xếp hạng kho/carrier bằng tỷ lệ thô rồi gọi nguyên nhân đã xác nhận.

Kho gắn theo unique matched-product warehouse nếu được, hoặc unique order warehouse cho order-only. Những quan sát đó chỉ là warehouse association. Không giả định có bằng chứng kho gây ra complaint. Source không có stockout/reassignment reasons đáng tin, nên gửi khác vùng không được tự gán lý do hết hàng hoặc coi là lỗi.

## Mâu thuẫn cần xác nhận nghiệp vụ

Tên dòng lịch sử chứa đúng ăn sáng/bữa sáng/breakfast trong canonical Bánh cho các số dưới đây. Đây là source-line names lịch sử, không dùng Product Type1 mới nhất để gán ngược mọi giao dịch cũ.

| Nguồn | Kho Hà Nội, accepted lines | Kho HCM, accepted lines |
|---|---:|---:|
|Shopee Bibica|47|469|
|TikTok Bibica|115|1275|
|Shopee Quasure|0|0|

Quan sát phần này khác thông lệ người dùng mô tả rằng bánh ăn sáng TMĐT mặc định Hà Nội và HCM hiếm. Nó không chứng minh user sai, nguồn sai, warehouse labels đảo hoặc các dòng HCM là bán sỉ. Product naming có thể rộng hơn phạm vi nhóm hàng được mô tả hoặc quy trình thay đổi theo thời gian. Cần xác nhận danh sách SKU/phạm vi hiệu lực và cách xuất kho trong export. Giữ nguyên facts, áp chính sách đề xuất có version/ngoại lệ rõ nếu đã được người dùng quy định, và không coi historical HCM sales tự động là proof tồn kho TMĐT hiện tại.

Catalog thực có3storefront riêng. Quasure specialized store có86SKUs,82tên chứaQuasure. Bibica Official Store có663SKUs,87tênQuasure. Bibica TikTok có731SKUs,127tênQuasure. Không tìm thấy tokenPleasure trong các catalog names. Tên Pleasure trong voice background cần mapping được xác nhận, chưa có căn cứ đổi storefront keys hoặc gộp shop.

## Kết luận nghiệm thu phần review

Kiểm đúng grain, negative-rating denominator, orphan/multiplicity, threshold sensitivity, text privacy và traceability PASS trong phạm vi đã chạy. Số liệu review cho phép ưu tiên điều tra theo absolute frequency, severity và cohort có uncertainty, không đủ chứng minh warehouse/carrier/đường xa gây hỏng hoặc hệ thống CSKH đã xử lý xong.

Phần review có thể chốt như công cụ hỗ trợ phân tích có điều kiện. Chưa đủ để chốt mô hình dự báo failure/spoilage đã hiệu chuẩn, causal warehouse ranking hoặc operational service-success KPI. Điều kiện nghiệp vụ còn mở gồm xác nhận scope bánh ăn sáng/HN-default đối chiếu observedHCM, mappingPleasure/Quasure, và human review label validation trước khi dùng issue tags để tự động ra quyết định vận hành.
