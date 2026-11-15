"""Conservative local review display projection. Never log the input text."""
import re
import unicodedata

CONTENT_VERSION = '2026-11-15-redacted-review-v1'


def redact_review(text, identities=()):
    value = unicodedata.normalize('NFC', text or '')
    value = re.sub(r'<[^>]*>', ' ', value)
    for identity in sorted({str(x).strip() for x in identities if x}, key=len, reverse=True):
        if len(identity) >= 2:
            value = re.sub(re.escape(identity), '[đã ẩn tên]', value, flags=re.I)
    value = re.sub(r'https?://\S+|www\.\S+|[\w.+-]+@[\w.-]+\.[a-z]{2,}', '[đã ẩn liên hệ]', value, flags=re.I)
    value = re.sub(r'(?<!\w)@[\w.\-]+', '[đã ẩn tài khoản]', value)
    # Includes spaced phone numbers and native order/product/tracking identifiers.
    value = re.sub(r'(?<!\w)\+?\d(?:[\s.()\-]*\d){6,}(?!\w)', '[đã ẩn mã/số]', value)
    value = re.sub(r'\b(?=[A-Za-z0-9_-]*\d)[A-Za-z0-9_-]{10,}\b', '[đã ẩn mã]', value)
    value = re.sub(r'\d{5,}', '[đã ẩn số]', value)
    # Remove the remainder of clauses with explicit personal/address/contact cues.
    value = re.sub(r'(?i)(?:sđt|sdt|số điện thoại|điện thoại|zalo|facebook|địa chỉ|đ/c|tôi tên|mình tên|tôi là|mình là|tên tôi|nhà ở|số nhà)\s*[:：]?[^.!?;\n]*', '[đã ẩn thông tin cá nhân]', value)
    value = re.sub(r'(?i)\b(?:ngõ|hẻm|thôn|ấp|phường|xã|quận|huyện)\s+[^.!?;\n]*', '[đã ẩn địa chỉ]', value)
    # Unknown full names: prefer over-redaction to displaying a possible person's name.
    value = re.sub(r'\b[A-ZÀ-Ỹ][a-zà-ỹ]+(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]+){1,4}\b', '[đã ẩn tên riêng]', value)
    value = re.sub(r'\s+', ' ', value).strip()
    return value[:4000]
