"""Conservative mention tagging for an offline review audit, never causal labels.

The function returns only controlled labels, not input text, identifiers or quotations.
Production complaint/replacement states require separate operational events.
"""
import re
import unicodedata

from .scoring import wilson_interval

VERSION = '2026-11-05-review-mentions-v1'
NEGATIVE_STAR_THRESHOLDS = (1, 2, 3)

RULES = {
    'missing_items_mention': [r'giao thiếu', r'gửi thiếu', r'thiếu hàng', r'thiếu bánh', r'thiếu sản phẩm', r'thiếu [0-9]+', r'không đủ (?:hàng|sản phẩm|số lượng|bánh)'],
    'wrong_items_mention': [r'giao (?:sai|nhầm)', r'gửi (?:sai|nhầm)', r'sai (?:hàng|vị|loại)', r'nhầm (?:hàng|vị|loại)'],
    'packaging_damage_mention': [r'\bmóp\b', r'\bbẹp\b', r'\bxẹp\b', r'\brách\b', r'\bthủng\b', r'(?:hộp|bao bì|túi) (?:bị )?(?:méo|vỡ|bể|nát)', r'bung (?:hộp|túi|bao bì)'],
    'product_breakage_mention': [r'bánh (?:bị )?(?:vỡ|bể|nát)', r'vỡ (?:vụn|nát)', r'bể nát', r'nát vụn'],
    'pest_or_foreign_material_mention': [r'chuột cắn', r'phân chuột', r'có (?:chuột|gián|sâu|côn trùng)', r'dị vật'],
    'spoilage_or_expired_mention': [r'\bmốc\b', r'\bôi thiu\b', r'\bthiu\b', r'hết hạn', r'quá hạn'],
    'short_shelf_life_mention': [r'cận (?:hạn|date)', r'hạn (?:sử dụng )?(?:còn )?ngắn'],
    'taste_or_texture_mention': [r'không ngon', r'quá ngọt', r'bánh (?:bị )?khô', r'khô cứng', r'khó ăn', r'có mùi (?:hôi|lạ)'],
    'delivery_delay_mention': [r'giao (?:hàng )?(?:lâu|chậm)', r'ship (?:lâu|chậm)', r'vận chuyển (?:lâu|chậm)'],
    'replacement_promised_mention': [r'sẽ gửi bù', r'hứa.{0,32}gửi bù', r'hẹn.{0,32}gửi bù', r'bù vào đơn (?:hàng )?sau', r'gửi bù.{0,24}(?:đơn|lần) sau'],
    'replacement_dispatch_claim': [r'đã gửi bù', r'gửi bù rồi', r'đã gửi lại hàng'],
    'replacement_received_claim': [r'nhận được (?:hàng )?(?:gửi )?bù', r'nhận hàng bù rồi'],
    'resolution_confirmed_claim': [r'đã (?:được )?giải quyết', r'đã xử lý xong'],
}

SAFETY_LABELS = {'pest_or_foreign_material_mention', 'spoilage_or_expired_mention'}
DAMAGE_LABELS = {'missing_items_mention', 'wrong_items_mention', 'packaging_damage_mention', 'product_breakage_mention'}


def normalized_text(text):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', text or '').casefold()).strip()


def _affirmative_mention(text, pattern):
    for match in re.finditer(r'(?<!\w)(?:' + pattern + r')(?!\w)', text):
        prefix = re.split(r'[.!?;,\n]', text[max(0, match.start()-50):match.start()])[-1]
        denied = re.search(r'(?:không|ko|chưa|chẳng)(?:\s+(?:bị|có|hề|thấy|còn|dấu|hiệu)){0,4}\s*$', prefix)
        if not denied:
            return True
    return False


def classify_review(text):
    value = normalized_text(text)
    labels = sorted(name for name, patterns in RULES.items() if any(_affirmative_mention(value, p) for p in patterns))
    severity = 'UNKNOWN'
    if SAFETY_LABELS.intersection(labels):
        severity = 'SAFETY_SIGNAL_REQUIRES_REVIEW'
    elif DAMAGE_LABELS.intersection(labels):
        severity = 'FULFILLMENT_DAMAGE_SIGNAL'
    elif labels:
        severity = 'OTHER_EXPLICIT_MENTION'
    return {'labels': labels, 'severity': severity, 'text_present': bool(value),
            'label_status': 'UNVALIDATED_HEURISTIC_MENTION', 'confirmed_cause': None}


def rating_summary(counts_by_star, threshold):
    if threshold not in NEGATIVE_STAR_THRESHOLDS:
        raise ValueError('Audit threshold must be one of 1, 2, 3')
    counts = {int(k): int(v) for k, v in counts_by_star.items()}
    if any(star not in range(1, 6) or count < 0 for star, count in counts.items()):
        raise ValueError('Valid star counts are nonnegative and stars lie in [1,5]')
    n = sum(counts.values())
    low = sum(count for star, count in counts.items() if star <= threshold)
    return {'threshold': threshold, 'reviews': n, 'negative_reviews': low,
            'fraction': low/n if n else None, 'wilson_95_interval': wilson_interval(low, n),
            'mean_stars': sum(star*count for star, count in counts.items())/n if n else None,
            'sparse_cohort': n < 30}


def operational_service_metrics():
    return {name: {'status': 'UNAVAILABLE', 'value': None,
                   'reason': 'No typed complaint, replacement, shipment or resolution event history in supplied sources'}
            for name in ['complaint_incidence', 'replacement_promised_count', 'replacement_dispatched_count',
                         'replacement_received_count', 'replacement_resolved_count', 'replacement_resolution_rate',
                         'customer_level_complaint_rate']}


def order_cluster_interval(order_counts, *, seed=20261105, replicates=2000):
    """Bootstrap ratios by order cluster, preserving multiple reviews within each order."""
    import numpy as np

    counts = sorted((int(n), int(bad)) for n, bad in order_counts)
    if any(n <= 0 or bad < 0 or bad > n for n,bad in counts):
        raise ValueError('Each order must have positive reviews and valid negative counts')
    if len(counts) < 2:
        return None
    if replicates < 100:
        raise ValueError('At least 100 bootstrap replicates are required')
    values = np.asarray(counts, dtype=np.int64)
    generator = np.random.default_rng(seed)
    fractions = []
    for offset in range(0, replicates, 100):
        samples = generator.integers(0, len(counts), size=(min(100,replicates-offset),len(counts)))
        totals = values[samples].sum(axis=1)
        fractions.extend(totals[:,1]/totals[:,0])
    return [float(v) for v in np.quantile(fractions,[.025,.975])]
