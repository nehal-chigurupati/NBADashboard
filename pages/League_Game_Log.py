import streamlit as st
import pandas as pd
import numpy as np
from nba_api.stats.endpoints import leaguegamelog

@st.cache_data
def load_data(season_type_all_star, season):
    data = leaguegamelog.LeagueGameLog(season_type_all_star=season_type_all_star, season=season, league_id="00")
    data = data.get_data_frames()[0]
    for column in data.columns:
        data[column] = data[column].astype(str)
    
    return data

st.header("League Game Log")

season = st.text_input("Season (ex: 2023-24): ")

season_type_options = ["Regular Season", "Playoffs", "Pre Season", "All Star"]
season_type = st.selectbox("Season Type: ", season_type_options)

if season and season_type:
    data_load_state = st.text("Loading games...")
    data = load_data(season=season, season_type_all_star=season_type)
    data_load_state.text("Done! Currently using cached data.")
    st.write(data)