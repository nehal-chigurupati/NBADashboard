import streamlit as st
from nba_api.stats.endpoints import playercareerstats
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
def load_data(player_name, per_mode):
    player_id = get_player_id(player_name)
    career_stats = playercareerstats.PlayerCareerStats(player_id=player_id, per_mode36=per_mode)
    career_stats = career_stats.get_data_frames()[0]
    career_stats["PLAYER_ID"] = career_stats["PLAYER_ID"].astype(str)
    career_stats["TEAM_ID"] = career_stats["TEAM_ID"].astype(str)
    return career_stats


st.header("Player Basic Stats")
player_name = st.text_input("Player name: ")


per_mode = st.selectbox("Per: ", ["Per Game", "Totals", "Per 36"])
if per_mode == "Per Game":
    per_mode = "PerGame"
elif per_mode == "Per 36":
    per_mode = "Per36"

if player_name and per_mode:
    data_load_state = st.text("Loading " + player_name +"'s stats")
    data = load_data(player_name, per_mode=per_mode)
    data_load_state.text("Done! Currently using cached data.")
    st.write(data)


