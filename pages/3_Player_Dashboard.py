import streamlit as st
import numpy as np
import pandas as pd
from nba_api.stats.endpoints import playercareerstats, playerestimatedmetrics, playergamelog, teamplayeronoffsummary
from nba_api.stats.endpoints import leaguehustlestatsplayer
from nba_api.stats.static import players
from scipy.stats import binom, norm
import plotly.express as px
import plotly.graph_objects as go

from pages.components.Player_Dashboard import *
from pages.components.sidebar import *

st.set_page_config(layout="wide")
player_name = render_player_selectbox()
render_sidebar()

if player_name: 
    on_off, bayes_data, curr_season_games, career_data = load_all_data(player_name)

    st.title(player_name)
    st.header("Seasonal Traditional Stats")
    render_seasonal_traditional_stats(player_name)

    col1, col2 = st.columns(2)
    with col1: 
        st.header("Estimated Metrics")
        estimated_data, timespan_options, season_type_options = render_estimated_metrics(player_name, career_data)


    with col2:
        st.header("Advanced Shooting Stats")
        st.subheader("Bayesian 3P%")
        render_advanced_shooting_stats(player_name, career_data, bayes_data)


    st.header("Moving averages")
    render_moving_avgs(player_name, timespan_options, curr_season_games)

    st.header("Ratings")
    render_ratings(player_name, season_type_options, career_data)
    
    st.header("Game Logs")
    render_game_logs(player_name, timespan_options, curr_season_games)
    
    render_team_on_off(player_name, on_off)
