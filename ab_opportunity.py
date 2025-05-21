import requests

def estimate_ab_opportunity(team_id, pitcher_id):
    try:
        # Get team runs per game
        team_url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/stats?stats=season"
        team_data = requests.get(team_url).json()
        team_splits = team_data.get("stats", [{}])[0].get("splits", [])
        team_stats = team_splits[0].get("stat", {}) if team_splits else {}
        runs_per_game = float(team_stats.get("runsPerGame", 4.5))

        # Get pitcher ERA
        pitcher_url = f"https://statsapi.mlb.com/api/v1/people/{pitcher_id}/stats?stats=season&season=2025"
        pitcher_data = requests.get(pitcher_url).json()
        pitcher_splits = pitcher_data.get("stats", [{}])[0].get("splits", [])
        pitcher_stats = pitcher_splits[0].get("stat", {}) if pitcher_splits else {}
        era = float(pitcher_stats.get("era", 4.50))

        # Clamp and scale
        era = max(era, 1.0)
        runs_per_game = max(runs_per_game, 1.0)
        base_ab = 4.1
        modifier = min(1.5, max(0.5, runs_per_game / era))
        return round(base_ab * modifier, 2)

    except Exception as e:
        print(f"[AB Estimation Error] {e}")
        return 4.2  # fallback
