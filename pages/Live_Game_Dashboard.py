import streamlit as st
import numpy as np
import pandas as pd
from nba_api.live.nba.endpoints import scoreboard, playbyplay, boxscore
from nba_api.stats.static import players
from nba_api.stats.endpoints import playbyplayv3
import plotly.express as px
from datetime import datetime
import time

from pages.components.Live_Game_Dashboard import *
from pages.components.sidebar import *

st.set_page_config(layout="wide")
render_sidebar()

#Get user input for game
active_games = get_active_games()
game=None
if len(active_games.keys()) == 0:
    st.subheader("No active games")
else:
    with st.expander("Select game"):
        game = st.selectbox("", active_games.keys())
        game_id = active_games[game]


#Once game id is provided, begin collecting data
if game:
    #Load data
    data_load_state = st.text("Refreshing...")
    scoreboard_data, pbp_data, away_team_data, home_team_data, away_team_statistics, home_team_statistics = load_all_data(game_id)
    data_load_state.text("Done!")
    data_load_state.text("Last Refreshed at " + str(datetime.now()))
    #Set title to current game
    st.title(game)

    #Put current score up
    render_curr_score(scoreboard_data)

    #Add refresh button (need to add live updating support)
    if st.button("Force Refresh"):
        data_load_state = st.text("Refreshing...")
        scoreboard_data, pbp_data, away_team_data, home_team_data, away_team_statistics, home_team_statistics = load_all_data(game_id)
        data_load_state.text("Force Refreshed at " + str(datetime.now()))
    
    auto_refresh = st.checkbox(label="Autorefresh", value=False)

    
    #Quarter by quarter breakdown of score
    render_score_breakdown(pbp_data, scoreboard_data)
    
    #Display play by play data
    st.subheader("Play by play")
    render_pbp(pbp_data, scoreboard_data)

# Loop for refreshing data
if len(active_games) != 0 and auto_refresh:
    while True:
        # Update this part to fetch your live data
        scoreboard_data = load_scoreboard_data(game_id)
        pbp_data = load_playbyplay_data(game_id, scoreboard_data["gameStatusText"] != "Final")
        away_team_data, home_team_data, away_team_statistics, home_team_statistics = load_box_score_data(game_id)

        # Wait for a seconds before the next update 
        time.sleep(5)

        # Refresh the page
        st.rerun()
