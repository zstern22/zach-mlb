import streamlit as st
import requests
from datetime import datetime, timedelta
from refresh_data import refresh_data
import math
from db import init_db
init_db()


def fetch_all_active_players_with_teams():
    teams_url = "https://statsapi.mlb.com/api/v1/teams?sportId=1"
    team_response = requests.get(teams_url)
    team_data = team_response.json()
    team_ids = [team["id"] for team in team_data.get("teams", [])]

    players = {}
    player_teams = {}
    for team_id in team_ids:
        roster_url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/roster"
        try:
            roster_response = requests.get(roster_url)
            roster = roster_response.json().get("roster", [])
            for player in roster:
                full_name = player["person"]["fullName"]
                player_id = str(player["person"]["id"])
                players[full_name] = player_id
                player_teams[full_name] = str(team_id)
        except Exception as e:
            print(f"Error fetching roster for team {team_id}: {e}")

    return players, player_teams

def get_team_schedule_and_stadium(team_id):
    today = datetime.today().date()
    end_date = today + timedelta(days=30)
    schedule_url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={team_id}&startDate={today}&endDate={end_date}&hydrate=game(content,media,decisions,probablePitchers,venue,teams)"
    schedule_data = requests.get(schedule_url).json()
    games = []
    for date_obj in schedule_data.get("dates", []):
        for game in date_obj.get("games", []):
            game_date = date_obj["date"]
            home_team_id = game["teams"]["home"]["team"]["id"]
            away_team_id = game["teams"]["away"]["team"]["id"]
            is_home = home_team_id == int(team_id)
            opponent_id = away_team_id if is_home else home_team_id
            opponent = game["teams"]["away"]["team"]["name"] if is_home else game["teams"]["home"]["team"]["name"]
            venue = game["venue"]["name"]
            probable_pitchers = []
            for side in ["home", "away"]:
                try:
                    probable = game["teams"][side].get("probablePitcher", {})
                    if probable and "fullName" in probable:
                        probable_pitchers.append(probable["fullName"])
                except:
                    continue
            if not probable_pitchers:
                roster_url = f"https://statsapi.mlb.com/api/v1/teams/{opponent_id}/roster"
                try:
                    roster_response = requests.get(roster_url).json()
                    probable_pitchers = [p["person"]["fullName"] for p in roster_response.get("roster", [])]
                except:
                    probable_pitchers = []
            label = f"{'vs' if is_home else '@'} {opponent} - {game_date}"
            games.append({
                "label": label,
                "date": game_date,
                "stadium": venue,
                "opponent_team": opponent,
                "opposing_pitchers": probable_pitchers,
                "home_team_id": home_team_id,
                "away_team_id": away_team_id
            })
    return games

def binomial_probabilities(expected_ab, hit_rate):
    dist = {}
    for k in range(0, 5):  # Only 0 to 4 hits
        try:
            prob = math.comb(expected_ab, k) * (hit_rate ** k) * ((1 - hit_rate) ** (expected_ab - k))
        except:
            prob = 0.0
        dist[k] = round(prob * 100, 1)
    return dist

    dist = {}
    for k in range(0, 6):
        if k < 5:
            try:
                prob = math.comb(expected_ab, k) * (hit_rate ** k) * ((1 - hit_rate) ** (expected_ab - k))
            except:
                prob = 0.0
        else:
            prob = 1 - sum(dist.values())
        dist[k] = round(prob * 100, 1)
    return dist

def us_odds(prob_percent):
    p = prob_percent / 100

    if p <= 0:
        return "∞"
    elif p >= 1:
        return "-∞"

    if p > 0.5:
        odds = -round(p / (1 - p) * 100)
    else:
        odds = round((1 - p) / p * 100)

    return f"{odds:+}"

@st.cache_data(show_spinner=False)
def load_data():
    players, player_teams = fetch_all_active_players_with_teams()
    team_url = "https://statsapi.mlb.com/api/v1/teams?sportId=1"
    team_data = requests.get(team_url).json()
    teams = {t['name']: str(t['id']) for t in team_data.get('teams', [])}
    return players, player_teams, teams

players, player_teams, teams = load_data()
st.title("MLB Hit Prediction Analyzer")

from db import clear_all_cached_data

if st.button("🔄 Refresh All Cached Data"):
    clear_all_cached_data()
    st.success("✅ Cache cleared. Please re-select players to trigger fresh scraping.")


if players and teams:
    batter_name = st.selectbox("Select Batter", sorted(players.keys()))
    player_id = players.get(batter_name)
    team_id = player_teams.get(batter_name)
    team_name = [k for k, v in teams.items() if v == team_id][0] if team_id else "Unknown"
    st.markdown(f"**Team:** {team_name}")

    game_options = get_team_schedule_and_stadium(team_id)
    game_labels = [g["label"] for g in game_options]
    selected_label = st.selectbox("Select Game", game_labels)
    selected_game = next(g for g in game_options if g["label"] == selected_label)
    game_date = selected_game["date"]
    stadium = selected_game["stadium"]
    st.markdown(f"**Stadium:** {stadium}")

    pitcher_name = st.selectbox("Select Pitcher", selected_game["opposing_pitchers"])
    pitcher_id = players.get(pitcher_name)

    debug_mode = st.checkbox("Enable debug mode")

    if st.button("Analyze Probability"):
        if player_id and pitcher_id and team_id:
            result = refresh_data(
                player_id=player_id,
                batter_name=batter_name,
                pitcher_id=pitcher_id,
                pitcher_name=pitcher_name,
                team_id=team_id,
                team=team_name,
                stadium=stadium,
                game_date=game_date,
                debug=debug_mode
            )
            if result:
                st.success("Calculation complete.")
                left, middle, right = st.columns([1, 2, 1])
                batter_img = f"https://content.mlb.com/images/headshots/current/60x60/{player_id}.png"
                pitcher_img = f"https://content.mlb.com/images/headshots/current/60x60/{pitcher_id}.png"
                batter_logo = f"https://www.mlbstatic.com/team-logos/{team_id}.svg"
                opponent_team_id = selected_game['away_team_id'] if str(team_id) == str(selected_game['home_team_id']) else selected_game['home_team_id']
                pitcher_logo = f"https://www.mlbstatic.com/team-logos/{opponent_team_id}.svg"

                with left:
                    st.image(batter_logo, width=75)
                    st.image(batter_img, caption=batter_name)
                with right:
                    st.image(pitcher_logo, width=75)
                    st.image(pitcher_img, caption=pitcher_name)
                with middle:
                    odds = binomial_probabilities(round(result['Projected ABs']), result['Hit Rate'])
                    st.markdown(f"### <div style='text-align: center;'>**{batter_name} vs {pitcher_name}**</div>", unsafe_allow_html=True)
                    prob_under = round(odds[0] + odds[1], 1)
                    prob_over = round(100 - prob_under, 1)

                    # Over/Under 0.5 hit probabilities
                    prob_u05 = round(odds[0], 1)
                    prob_o05 = round(100 - odds[0], 1)

                    st.markdown(f"<div style='text-align: center;'><strong>Probability u0.5 Hits:</strong> {prob_u05}% ({us_odds(prob_u05)})</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='text-align: center;'><strong>Probability o0.5 Hits:</strong> {prob_o05}% ({us_odds(prob_o05)})</div>", unsafe_allow_html=True)

                    st.markdown(f"<div style='text-align: center;'><strong>Probability u1.5 Hits:</strong> {prob_under}% ({us_odds(prob_under)})</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='text-align: center;'><strong>Probability o1.5 Hits:</strong> {prob_over}% ({us_odds(prob_over)})</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='text-align: center;'><strong>Raw Hit Probability Score:</strong> {round(result['Raw Score (Hit Probability)'] * 100, 1)}%</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='text-align: center;'><strong>Projected At-Bats:</strong> {round(result['Projected ABs'], 1)}</div>", unsafe_allow_html=True)

                    odds = binomial_probabilities(round(result['Projected ABs']), result['Hit Rate'])
                    st.markdown("### <div style='text-align: center;'>Betting Odds</div>", unsafe_allow_html=True)
                    for hits, pct in odds.items():
                        label = f"{hits} Hit{'s' if hits != 1 else ''}"
                        st.markdown(f"<div style='text-align: center;'><strong>{label}:</strong> {pct}% ({us_odds(pct)})</div>", unsafe_allow_html=True)

                    # Determine best bet from u/o 0.5 and 1.5 hits
                    bets = {
                        "Under 0.5 Hits": prob_u05,
                        "Over 0.5 Hits": prob_o05,
                        "Under 1.5 Hits": prob_under,
                        "Over 1.5 Hits": prob_over
                    }
                    best_bet = max(bets, key=bets.get)
                    confidence = bets[best_bet]

                    rec_text = f"Place bet on **{best_bet}**, {confidence}% chance of success."
                    risk_level = "High Risk" if confidence < 55 else "Moderate Risk" if confidence < 70 else "Low Risk"
                    risk_color = "#ff4d4d" if risk_level == "High Risk" else "#ffa500" if risk_level == "Moderate Risk" else "#4caf50"

                    # Recommendation box
                    st.markdown("### <div style='text-align: center;'>Recommendation</div>", unsafe_allow_html=True)
                    st.markdown(
                        f"""
                        <div style='text-align: center;'>
                            {rec_text}<br>
                            <strong style='color: {risk_color};'>Risk Level: {risk_level}</strong><br>
                            <span style='font-size: 0.9em; color: #888;'>Risk level reflects how often this bet would succeed historically.</span><br>
                            <progress value='{confidence}' max='100' style='width: 100%; height: 20px;'></progress>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    # BvP last updated display (outside of recommendation block)
                    if 'BvP' in result and 'last_updated' in result['BvP']:
                        bvp_time = result['BvP']['last_updated']
                        if bvp_time:
                            st.markdown(f"""
                            <div style='text-align: center; padding-top: 10px;'>
                                <span style='background-color: #eee; padding: 6px 12px; border-radius: 6px; font-size: 0.85em; color: #555;'>
                                    BvP Last Updated: {bvp_time}
                                </span>
                            </div>
                            """, unsafe_allow_html=True)


                    

        else:
            st.error("One or more selections are invalid. Please try again.")
else:
    st.warning("Loading player/team data... Please wait or refresh.")