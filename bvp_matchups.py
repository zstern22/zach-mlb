from datetime import datetime
from db import insert_or_update, fetch_one

def get_bvp_stats(batter_id, pitcher_id, batter_name, pitcher_name):
    # Check cache first
    cached = fetch_one(
        "SELECT avg, hits, abs, last_updated FROM bvp_stats WHERE batter_name = ? AND pitcher_name = ?",
        (batter_name, pitcher_name)
    )
    if cached:
        return {
            'bvp_avg': float(cached[0]),
            'bvp_hits': int(cached[1]),
            'bvp_abs': int(cached[2]),
            'last_updated': cached[3]
        }

    try:
        import warnings
        from pybaseball import statcast_batter, cache

        warnings.filterwarnings("ignore")
        cache.enable()

        start_dt = "2018-01-01"
        end_dt = datetime.today().strftime('%Y-%m-%d')

        print(f"📡 Fetching Statcast logs for batter {batter_name} ({batter_id}) from {start_dt} to {end_dt}")
        df = statcast_batter(player_id=int(batter_id), start_dt=start_dt, end_dt=end_dt)

        df_matchup = df[df['pitcher'] == int(pitcher_id)]

        if df_matchup.empty:
            print("⚠️ No BvP data found in batter logs.")
            avg, hits, abs_val = 0.250, 0, 0
        else:
            abs_val = (~df_matchup['events'].isnull()).sum()
            hits = df_matchup['events'].isin(['single', 'double', 'triple', 'home_run']).sum()
            avg = round(hits / abs_val, 3) if abs_val > 0 else 0.0

        last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        insert_or_update(
            "REPLACE INTO bvp_stats VALUES (?, ?, ?, ?, ?, ?)",
            (batter_name, pitcher_name, avg, hits, abs_val, last_updated)
        )

        return {
            'bvp_avg': float(avg),
            'bvp_hits': int(hits),
            'bvp_abs': int(abs_val),
            'last_updated': last_updated
        }

    except Exception as e:
        print(f"❌ Statcast fetch error for BvP: {e}")
        avg, hits, abs_val = 0.250, 0, 0
        last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        insert_or_update(
            "REPLACE INTO bvp_stats VALUES (?, ?, ?, ?, ?, ?)",
            (batter_name, pitcher_name, avg, hits, abs_val, last_updated)
        )
        return {
            'bvp_avg': float(avg),
            'bvp_hits': int(hits),
            'bvp_abs': int(abs_val),
            'last_updated': last_updated
        }
