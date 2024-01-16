import streamlit as st
import numpy as np
import pandas as pd
from nba_api.stats.endpoints import playbyplayv3


@st.cache_data
def load_data(game_id):
    data = playbyplayv3.PlayByPlayV3(game_id=game_id)
    data = data.get_data_frames()[0]
    for column in data.columns:
        data[column] = data[column].astype(str)
    
    return data

st.header("Game Play by Play")
game_id = st.text_input("Enter the game ID:")

if game_id:
    data_load_state = st.text("Loading plays...")
    data = load_data(game_id=game_id)
    data_load_state.text("Done! Currently using cached data.")
    st.write(data)