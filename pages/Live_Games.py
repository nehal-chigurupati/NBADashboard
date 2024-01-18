import streamlit as st
import numpy as np
import pandas as pd
from nba_api.live.nba.endpoints import scoreboard, playbyplay

def load_game_ids():
    out = {}

    data = scoreboard.ScoreBoard().games.get_dict()
    for key in data[0].keys():
        out[key] = []
        for i in data:
            out[key].append(i[key])

    return pd.DataFrame(out)

def load_pbp_stats(game_id):
    data = playbyplay.PlayByPlay(game_id=game_id).get_dict()["game"]["actions"]

    out = {}
    for key in data[0].keys():
        out[key] = []
        for i in data:
            out[key].append(i[key])

    return pd.DataFrame(out)


st.header("Active Games")
data_load_state = st.text("Loading games...")
data = load_game_ids()
data_load_state.text("Done! Currently using cached data.")
st.write(data)

st.header("Play by play")
pbp_game_id = st.text_input("Game ID: ")
if pbp_game_id:
    data_load_state = st.text("Loading games...")
    pbp_data = load_pbp_stats(pbp_game_id)
    data_load_state.text("Done! Currently using cached data.")
    if st.button("Refresh Data"):
        pbp_data = load_pbp_stats(pbp_game_id)
    st.write(pbp_data)


