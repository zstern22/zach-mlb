def normalize(value, min_val, max_val):
    return max(0, min(1, (value - min_val) / (max_val - min_val)))


def normalize_all(logs, bvp, pitcher, park, lineup, momentum, ab_opportunity):
    # 🧠 Weighted recent performance + trend bonus/penalty
    recent_raw = (
        0.55 * logs['full_season'] +
        0.30 * logs['last_20'] +
        0.15 * logs['last_10']
    )
    if logs['last_10'] > logs['last_20'] > logs['full_season']:
        recent_raw += 0.05
    elif logs['last_10'] < logs['last_20'] < logs['full_season']:
        recent_raw -= 0.05
    recent_score = normalize(recent_raw, 0.0, 3.0)

    # 🧠 Batter vs Pitcher Score
    if bvp['bvp_abs'] < 5:
        # Too small a sample — neutral score, reduced weight
        bvp_score = 0.5
        bvp_weight = 0.05
        print(f"⚠️ Low BvP sample ({bvp['bvp_abs']} ABs) — using neutral score")
    else:
        bvp_score = normalize(bvp['bvp_avg'], 0.100, 0.400)
        bvp_score = max(0.1, min(0.9, bvp_score))  # avoid extreme flatline
        bvp_weight = 0.15
        print(f"✅ BvP score normalized: {bvp_score} from AVG {bvp['bvp_avg']}")

    # 🧠 Pitcher score with ERA-weighted and aggressive boost/penalty
    raw_pitcher_score = (pitcher['era'] * 0.6 + pitcher['whip'] * 0.4)
    pitcher_score = 1 - normalize(raw_pitcher_score, 2.00, 6.00)
    if raw_pitcher_score <= 2.50:
        pitcher_score += 0.05
    elif raw_pitcher_score >= 5.50:
        pitcher_score -= 0.05
    pitcher_score = max(0, min(1, pitcher_score))  # Clamp

    # 🧠 Momentum + streak boost
    momentum_score = normalize(momentum['recent_runs'], 2.0, 8.0)
    if momentum.get('win_streak', 0) >= 5:
        momentum_score += 0.05
    momentum_score = min(momentum_score, 1.0)

    # 🧠 Lineup, park, AB opportunity (widened range)
    lineup_score = normalize((lineup['before_obp'] + lineup['after_obp']) / 2, 0.290, 0.400)
    park_score = normalize(park, 0.80, 1.35)
    ab_score = normalize(min(6.0, max(2.5, ab_opportunity)), 2.5, 6.0)

    return {
        'RecentPerformanceScore': recent_score,
        'BatterVsPitcherScore': bvp_score,
        'PitcherStatsScore': pitcher_score,
        'ParkFactorScore': park_score,
        'LineupProtectionScore': lineup_score,
        'TeamMomentumScore': momentum_score,
        'ABOpportunityScore': ab_score,
        'DynamicWeights': {
            'BvP': bvp_weight
        }
    }
