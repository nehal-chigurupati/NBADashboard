import streamlit as st
from nba_api.stats.endpoints import playerestimatedmetrics
from nba_api.stats.static import players

def get_player_id(full_name):
    # Get all NBA players
    nba_players = players.get_players()

    # Search for the player by full name
    player = [player for player in nba_players if player['full_name'] == full_name]

    # Return the player's ID if found
    if player:
        return player[0]['id']
    else:
        return None
    
@st.cache_data
def load_data(season, season_type):
    data = playerestimatedmetrics.PlayerEstimatedMetrics(season=season, season_type=season_type, league_id="00")

    return data.get_data_frames()[0]

st.header("Player Estimated Metrics")
season = st.text_input("Season (ex: 2023-24): ")

season_type_options = ["Regular Season", "Playoffs", "Pre Season", "All Star"]
season_type = st.selectbox("Season Type: ", season_type_options)

if season and season_type_options:
    data_load_state = st.text("Loading " + season + " " + season_type + " stats...")
    data = load_data(season=season, season_type=season_type)
    data_load_state.text("Done! Currently using cached data.")
    st.write(data)