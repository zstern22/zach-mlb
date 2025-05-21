import requests
from db import insert_or_update, fetch_one
from datetime import datetime

def get_pitcher_stats(pitcher_id):
    cached = fetch_one("SELECT era, whip FROM pitcher_stats WHERE pitcher_id = ?", (pitcher_id,))
    if cached:
        return {'era': cached[0], 'whip': cached[1]}

    url = f"https://statsapi.mlb.com/api/v1/people/{pitcher_id}/stats?stats=career&group=pitching"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        splits = data.get('stats', [{}])[0].get('splits', [])
        if not splits:
            raise ValueError("No career stats found for pitcher.")

        stat = splits[0].get('stat', {})
        era = float(stat.get('era', 5.50))
        whip = float(stat.get('whip', 1.55))

    except Exception as e:
        print(f"[Pitcher Stats Fallback] {e}")
        era, whip = 5.50, 1.55

    insert_or_update("REPLACE INTO pitcher_stats VALUES (?, ?, ?, ?)", (
        pitcher_id, era, whip, datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    return {'era': era, 'whip': whip}
