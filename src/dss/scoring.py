"""Transparent historical risk index with explicit missing-component handling."""


def score_profile(profile, prior, weights, prior_strength):
    fields = [('cancellation', 'canceled_orders', 'resolved_orders'),
              ('late_delivery', 'late_orders', 'timing_samples'),
              ('low_review', 'low_reviews', 'reviews')]
    factors = []
    for name, numerator, denominator in fields:
        n = int(profile[denominator])
        prior_n = int(prior[denominator]) if prior else 0
        baseline = float(prior[numerator]) / prior_n if prior_n else None
        rate = None
        if n:
            strength = prior_strength if baseline is not None else 0
            rate = (float(profile[numerator]) + strength * (baseline or 0)) / (n + strength)
        factors.append({'factor': name, 'events': int(profile[numerator]), 'observations': n,
                        'observed_fraction': float(profile[numerator]) / n if n else None,
                        'smoothed_fraction': rate, 'configured_weight': getattr(weights, name)})
    used_weight = sum(f['configured_weight'] for f in factors if f['smoothed_fraction'] is not None)
    score = None
    if used_weight:
        score = 100 * sum(f['configured_weight'] * f['smoothed_fraction'] for f in factors
                          if f['smoothed_fraction'] is not None) / used_weight
    for factor in factors:
        factor['effective_weight'] = factor['configured_weight'] / used_weight if used_weight and factor['smoothed_fraction'] is not None else 0
    confidence = 'SPARSE'
    if profile['timing_samples'] >= 30 and profile['resolved_orders'] >= 30:
        confidence = 'SUPPORTED'
    review_caution = {
        'availability': 'OBSERVED' if profile['reviews'] else 'UNAVAILABLE_NO_ATTRIBUTED_RATING_EVIDENCE',
        'one_star_reviews': int(profile.get('one_star_reviews', 0)),
        'low_reviews': int(profile['low_reviews']), 'rated_reviews': int(profile['reviews']),
        'low_review_wilson_95_interval': wilson_interval(int(profile['low_reviews']), int(profile['reviews'])),
        'unattributed_reviews': int(profile.get('unattributed_reviews', 0)),
        'reviewed_order_coverage': float(profile.get('reviewed_orders', 0))/profile['orders'] if profile.get('orders') else None,
        'action': 'REVIEW_NEGATIVE_EVIDENCE' if profile['low_reviews'] else
                  ('NO_OBSERVED_LOW_RATING_IN_ATTRIBUTED_COHORT' if profile['reviews'] else 'UNAVAILABLE_NO_RATING_EVIDENCE'),
        'meaning': 'Stars identify dissatisfaction, not proven defect severity or warehouse/carrier cause.',
    }
    return {'risk_score': score, 'factors': factors, 'evidence_support': confidence, 'review_caution':review_caution,
            'available_weight_fraction': used_weight / sum(weights.model_dump().values()),
            'calibrated_probability': False}


def shelf_margin(p90_days, remaining_days, extra_delay, minimum_remaining):
    arrival_remaining = remaining_days - p90_days - extra_delay
    return {'remaining_at_dispatch_days': remaining_days,
            'p90_arrival_remaining_days': arrival_remaining,
            'minimum_remaining_days': minimum_remaining,
            'feasible': arrival_remaining >= minimum_remaining,
            'basis': 'SCENARIO_REMAINING_LIFE_MINUS_HISTORICAL_P90_AND_SCENARIO_DELAY'}


def wilson_interval(events, samples):
    if not samples:
        return None
    z = 1.959963984540054
    p = events / samples
    denominator = 1 + z*z / samples
    center = (p + z*z / (2*samples)) / denominator
    half = z * ((p*(1-p)/samples + z*z/(4*samples*samples))**.5) / denominator
    return [max(0, center-half), min(1, center+half)]
