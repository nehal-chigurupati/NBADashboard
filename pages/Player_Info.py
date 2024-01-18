import streamlit as st
import pandas as pd
from nba_api.stats.static import players

def load_data():
    player_first_names = []
    player_last_names = []
    player_id = []
    player_active = []

    for player in players.get_players():
        player_first_names.append(player["first_name"])
        player_last_names.append(player["last_name"])
        player_id.append(str(player["id"]))
        player_active.append(player["is_active"])

    out_dict = {
        "First name": player_first_names,
        "Last name": player_last_names,
        "Player ID": player_id,
        "Is active": player_active
    }
    
    return pd.DataFrame(out_dict)

st.set_page_config(layout="wide")
st.header("All player info")
data = load_data()
st.write(data)