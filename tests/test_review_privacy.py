import unittest
from src.api.review_privacy import redact_review


class ReviewPrivacyTests(unittest.TestCase):
    def test_preserves_opinion_and_hides_contact_and_ids(self):
        text='bánh bị vỡ, giao thiếu 2 hộp. Hotline 0912 345 678; mã 123456789012345678. email test@example.test https://example.test/a @customer_test'
        value=redact_review(text)
        self.assertIn('bánh bị vỡ, giao thiếu 2 hộp',value)
        for private in ['0912','345','678','123456789012345678','test@example.test','example.test/a','@customer_test']:
            self.assertNotIn(private,value)

    def test_known_identity_address_and_unknown_name(self):
        value=redact_review('người mua test_customer; bánh khô. Địa chỉ: 123 đường riêng. Nguyễn Văn Kiểm Thử đặt hàng.', ['test_customer'])
        for private in ['test_customer','123 đường riêng','Nguyễn Văn Kiểm Thử']:
            self.assertNotIn(private,value)
        self.assertIn('bánh khô',value)

    def test_markup_empty_and_length(self):
        self.assertEqual(redact_review(None),'')
        self.assertEqual(redact_review('<b>bánh vỡ</b>'),'bánh vỡ')
        self.assertLessEqual(len(redact_review('x'*5000)),4000)
