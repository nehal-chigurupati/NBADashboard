import streamlit as st
from pages.components.sidebar import *
from pages.components.BayesianShootingStats import *
st.set_page_config(layout="wide")
render_sidebar("My_Random_Stats")
st.text("Scroll down for team stats (Kalman Offensive Rating and Topological Offensive/Defensive/Net Range)")
st.title("Player Stats")
player = render_player_selection()
render_b3P(player)
render_bWPM(player)


st.title("Team Stats")
team_abbrev = render_kORTG_team_selection()
st.subtitle("Kalman Stats")
render_kORTG(team_abbrev)

st.subtitle("Topological Range")
col1, col2 = st.columns(2)

with col1:
    st.subtitle("Offensive Range")
    render_tORNG(team_abbrev)
with col2:
    st.subtitle("Defensive Range")
    render_tDRNG(team_abbrev)

st.subtitle("Net Range")
render_tNRNG(team_abbrev)