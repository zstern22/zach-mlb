
from player_logs import get_player_logs
from bvp_matchups import get_bvp_stats
from pitcher_stats import get_pitcher_stats
from park_factor import get_park_factor
from lineup_data import get_lineup_context
from team_momentum import get_team_momentum
from calc_helpers import normalize_all
from weights import apply_weighted_formula
from ab_opportunity import estimate_ab_opportunity
from db import init_db
import streamlit as st

def refresh_data(player_id, batter_name, pitcher_id, pitcher_name, team_id, team, stadium, game_date, debug=False):
    try:
        init_db()
        if debug: st.write("✅ Initialized local DB")
    except Exception as e:
        if debug: st.error(f"❌ Failed to initialize DB: {e}")
        return

    try:
        logs = get_player_logs(player_id)
        if debug: st.write("✅ Player logs fetched", logs)
    except Exception as e:
        if debug: st.error(f"❌ Failed to get player logs: {e}")
        return

    try:
        bvp = get_bvp_stats(player_id, pitcher_id, batter_name, pitcher_name)
        if debug: st.write("✅ Batter-vs-Pitcher stats", bvp)
    except Exception as e:
        if debug: st.error(f"❌ Failed to get BvP stats: {e}")
        return

    try:
        pitcher = get_pitcher_stats(pitcher_id)
        if debug: st.write("✅ Pitcher stats", pitcher)
    except Exception as e:
        if debug: st.error(f"❌ Failed to get pitcher stats: {e}")
        return

    try:
        park = get_park_factor(stadium)
        if debug: st.write("✅ Park factor:", park)
    except Exception as e:
        if debug: st.error(f"❌ Failed to get park factor: {e}")
        return

    try:
        lineup = get_lineup_context(batter_name, team, game_date)
        if debug: st.write("✅ Lineup context", lineup)
    except Exception as e:
        if debug: st.error(f"❌ Failed to get lineup context: {e}")
        return

    try:
        momentum = get_team_momentum(team_id)
        if debug: st.write("✅ Team momentum", momentum)
    except Exception as e:
        if debug: st.error(f"❌ Failed to get team momentum: {e}")
        return

    try:
        ab_opportunity = estimate_ab_opportunity(team_id, pitcher_id)
        if debug: st.write("✅ Estimated ABs", ab_opportunity)
    except Exception as e:
        if debug: st.error(f"❌ Failed to estimate AB opportunity: {e}")
        return

    try:
        scores = normalize_all(logs, bvp, pitcher, park, lineup, momentum, ab_opportunity)
        hit_prob = apply_weighted_formula(scores)
        if debug: st.write("✅ Normalized + weighted scores", scores)
    except Exception as e:
        if debug: st.error(f"❌ Failed to compute score: {e}")
        return

    hit_rate = logs['full_season'] / ab_opportunity if ab_opportunity > 0 else 0.25

    return {
        "Player": batter_name,
        "Opponent": pitcher_name,
        "Probability of <2 Hits": round(1 - hit_prob, 5),
        "Raw Score (Hit Probability)": round(hit_prob, 5),
        "Projected ABs": ab_opportunity,
        "Hit Rate": round(hit_rate, 5),
        "Player ID": player_id,
        "Details": scores
    }
