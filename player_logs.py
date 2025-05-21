import requests
import pandas as pd
from datetime import datetime
from db import insert_or_update

def get_player_logs(player_id):
    all_logs = pd.DataFrame()

    # Collect logs for 2023–2025
    for season in ['2023', '2024', '2025']:
        url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=gameLog&season={season}"
        try:
            response = requests.get(url)
            data = response.json()
            splits = data.get('stats', [{}])[0].get('splits', [])
            if splits:
                season_logs = pd.DataFrame(splits)
                season_logs['date'] = pd.to_datetime(season_logs['date'])
                season_logs['hits'] = season_logs['stat'].apply(lambda x: x.get('hits', 0))
                all_logs = pd.concat([all_logs, season_logs], ignore_index=True)
        except Exception as e:
            print(f"[Log Warning] Failed to load {season} for player {player_id}: {e}")

    if all_logs.empty:
        return {'last_10': 0.0, 'last_20': 0.0, 'full_season': 0.0}

    all_logs = all_logs.sort_values('date', ascending=False)

    # Cache into database (optional, only current season is used here)
    for _, row in all_logs.iterrows():
        insert_or_update("REPLACE INTO player_stats VALUES (?, ?, ?, ?)",
                         (player_id, row['date'].strftime('%Y-%m-%d'), row['hits'],
                          datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    return {
        'last_10': all_logs.head(10)['hits'].mean(),
        'last_20': all_logs.head(20)['hits'].mean(),
        'full_season': all_logs['hits'].mean()
    }
