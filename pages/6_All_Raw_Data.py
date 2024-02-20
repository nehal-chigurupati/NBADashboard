import streamlit as st
import pandas as pd
from nba_api.stats.static import players, teams
import json
from nba_api.stats.endpoints import leaguegamelog
from pathlib import Path
import importlib
from retry import retry

from pages.components.All_Raw_Data import *
from pages.components.sidebar import *

st.set_page_config(layout="wide")
render_sidebar()

st.title("NBA Website Data Retrieval")
st.caption("For parameter patterns, see the bottom of this page.")

player_data, team_data = load_all_ref_data()

#Fetch API params

render_request_data()
                
    
col1, col2 = st.columns(2)

with col1:
    st.header("Player API IDs")
    st.write(player_data)

with col2:
    st.header("Team API IDs")
    st.write(team_data)

st.header("Game API IDs")
render_game_api_ids()

st.header("Parameters")
with st.expander("Patterns", expanded=False):
    md_text = Path("pages/api_endpoints/parameters.md").read_text()
    st.markdown(md_text)