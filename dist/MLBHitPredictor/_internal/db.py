import sqlite3
from datetime import datetime

DB_NAME = "mlb_hit_predictions.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # One-time schema patch (safe to keep long-term)
    try:
        cur.execute("ALTER TABLE player_stats ADD COLUMN last_updated TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        cur.execute("ALTER TABLE bvp_stats ADD COLUMN last_updated TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        cur.execute("ALTER TABLE pitcher_stats ADD COLUMN last_updated TEXT")
    except sqlite3.OperationalError:
        pass

    # Create tables if they don't already exist
    cur.execute("""
        CREATE TABLE IF NOT EXISTS player_stats (
            player_id TEXT,
            date TEXT,
            hits INTEGER,
            last_updated TEXT,
            PRIMARY KEY (player_id, date)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS bvp_stats (
            batter_name TEXT,
            pitcher_name TEXT,
            avg REAL,
            hits INTEGER,
            abs INTEGER,
            last_updated TEXT,
            PRIMARY KEY (batter_name, pitcher_name)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS pitcher_stats (
            pitcher_id TEXT,
            era REAL,
            whip REAL,
            last_updated TEXT,
            PRIMARY KEY (pitcher_id)
        )
    """)

    conn.commit()
    conn.close()

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Create all required tables with last_updated field
    cur.execute("""
        CREATE TABLE IF NOT EXISTS player_stats (
            player_id TEXT,
            date TEXT,
            hits INTEGER,
            last_updated TEXT,
            PRIMARY KEY (player_id, date)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS bvp_stats (
            batter_name TEXT,
            pitcher_name TEXT,
            avg REAL,
            hits INTEGER,
            abs INTEGER,
            last_updated TEXT,
            PRIMARY KEY (batter_name, pitcher_name)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS pitcher_stats (
            pitcher_id TEXT,
            era REAL,
            whip REAL,
            last_updated TEXT,
            PRIMARY KEY (pitcher_id)
        )
    """)

    conn.commit()
    conn.close()


def insert_or_update(query, values):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(query, values)
    conn.commit()
    conn.close()


def fetch_one(query, values):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(query, values)
    result = cur.fetchone()
    conn.close()
    return result


def clear_all_cached_data():
    # Step 1: Delete all rows
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM player_stats")
        cursor.execute("DELETE FROM bvp_stats")
        cursor.execute("DELETE FROM pitcher_stats")
        conn.commit()

    # Step 2: VACUUM outside of transaction
    with sqlite3.connect(DB_NAME) as conn:
        conn.isolation_level = None  # allows VACUUM
        conn.execute("VACUUM")

    print("✅ All cached data cleared and DB vacuumed.")
