def apply_weighted_formula(scores):
    weights = scores.get('DynamicWeights', {})
    return (
        0.35 * scores['RecentPerformanceScore'] +
        weights.get('BvP', 0.15) * scores['BatterVsPitcherScore'] +
        0.15 * scores['PitcherStatsScore'] +
        0.05 * scores['ParkFactorScore'] +
        0.05 * scores['LineupProtectionScore'] +
        0.05 * scores['TeamMomentumScore'] +
        0.10 * scores['ABOpportunityScore']
    )

