import unittest

from src.dss.review_audit import classify_review, operational_service_metrics, order_cluster_interval, rating_summary


class ReviewAuditTests(unittest.TestCase):
    def test_empty_unknown_does_not_mean_no_problem(self):
        self.assertEqual(classify_review('')['severity'], 'UNKNOWN')
        self.assertFalse(classify_review('')['text_present'])
        self.assertIsNone(classify_review('Tốt')['confirmed_cause'])

    def test_multilabel_missing_wrong_and_breakage(self):
        result = classify_review('Giao thiếu 1 gói, giao nhầm vị. Bánh vỡ nát, hộp bị móp.')
        self.assertTrue({'missing_items_mention','wrong_items_mention','product_breakage_mention','packaging_damage_mention'} <= set(result['labels']))

    def test_packaging_and_product_are_distinct(self):
        self.assertEqual(classify_review('Hộp móp')['labels'], ['packaging_damage_mention'])
        self.assertEqual(classify_review('Bánh vỡ vụn')['labels'], ['product_breakage_mention'])

    def test_safety_mentions_are_separate_from_frequency(self):
        for value in ['Có dấu hiệu chuột cắn', 'Bánh bị mốc', 'Có dị vật trong bánh']:
            self.assertEqual(classify_review(value)['severity'], 'SAFETY_SIGNAL_REQUIRES_REVIEW')

    def test_short_shelf_life_is_not_confirmed_spoilage(self):
        result = classify_review('Hàng cận date, hạn sử dụng ngắn')
        self.assertEqual(result['labels'], ['short_shelf_life_mention'])
        self.assertEqual(result['severity'], 'OTHER_EXPLICIT_MENTION')

    def test_negated_damage_is_not_labelled(self):
        for value in ['Hộp không bị móp', 'Bánh không bị vỡ', 'Không có dấu hiệu chuột cắn', 'Không giao thiếu']:
            self.assertEqual(classify_review(value)['labels'], [])

    def test_negative_taste_is_not_fulfillment_fault(self):
        result = classify_review('Bánh không ngon và quá ngọt')
        self.assertEqual(result['labels'], ['taste_or_texture_mention'])
        self.assertIsNone(result['confirmed_cause'])

    def test_promise_is_not_dispatch_receipt_or_resolution(self):
        result = classify_review('Shop hứa sẽ gửi bù vào đơn sau, nhưng chưa nhận được hàng bù.')
        self.assertIn('replacement_promised_mention', result['labels'])
        self.assertNotIn('replacement_received_claim', result['labels'])
        self.assertNotIn('replacement_dispatch_claim', result['labels'])
        self.assertNotIn('resolution_confirmed_claim', result['labels'])

    def test_dispatch_claim_is_not_receipt(self):
        result = classify_review('Shop đã gửi bù. Chưa nhận được hàng bù.')
        self.assertIn('replacement_dispatch_claim', result['labels'])
        self.assertNotIn('replacement_received_claim', result['labels'])

    def test_received_is_not_resolution(self):
        result = classify_review('Đã nhận được hàng bù nhưng chưa giải quyết xong vấn đề.')
        self.assertIn('replacement_received_claim', result['labels'])
        self.assertNotIn('resolution_confirmed_claim', result['labels'])

    def test_explicit_resolution_remains_claim(self):
        result = classify_review('Shop đã giải quyết xong.')
        self.assertIn('resolution_confirmed_claim', result['labels'])
        self.assertEqual(result['label_status'], 'UNVALIDATED_HEURISTIC_MENTION')

    def test_no_input_text_or_identity_in_output(self):
        value = 'PRIVATE_SENTINEL - hộp móp'
        self.assertNotIn('PRIVATE_SENTINEL', str(classify_review(value)))

    def test_threshold_sensitivity_nested_and_correct_denominator(self):
        counts = {1:2,2:3,3:5,4:10,5:80}
        results = [rating_summary(counts,t) for t in [1,2,3]]
        self.assertEqual([r['negative_reviews'] for r in results], [2,5,10])
        self.assertEqual([r['fraction'] for r in results], [.02,.05,.1])

    def test_missing_and_zero(self):
        self.assertIsNone(rating_summary({},2)['fraction'])
        self.assertEqual(rating_summary({5:10},2)['fraction'],0)
        self.assertTrue(rating_summary({5:10},2)['sparse_cohort'])

    def test_invalid_star_counts_and_threshold(self):
        for counts, threshold in [({0:1},2),({6:1},2),({1:-1},2),({1:1},4)]:
            with self.assertRaises(ValueError):
                rating_summary(counts,threshold)

    def test_service_absence_unavailable_not_zero(self):
        self.assertTrue(all(r['status']=='UNAVAILABLE' and r['value'] is None for r in operational_service_metrics().values()))

    def test_cluster_interval_requires_multiple_clusters(self):
        self.assertIsNone(order_cluster_interval([]))
        self.assertIsNone(order_cluster_interval([(2,1)]))
        with self.assertRaises(ValueError):order_cluster_interval([(2,3),(1,0)])

    def test_cluster_interval_is_reproducible_and_order_invariant(self):
        counts=[(2,1),(1,0),(5,2),(3,0)]
        a=order_cluster_interval(counts,replicates=100)
        self.assertEqual(a,order_cluster_interval(counts[::-1],replicates=100))
        self.assertGreaterEqual(a[0],0)
        self.assertLessEqual(a[1],1)

    def test_cluster_interval_extreme_events(self):
        self.assertEqual(order_cluster_interval([(2,0),(4,0)],replicates=100),[0,0])
        self.assertEqual(order_cluster_interval([(2,2),(4,4)],replicates=100),[1,1])


if __name__=='__main__':
    unittest.main()
