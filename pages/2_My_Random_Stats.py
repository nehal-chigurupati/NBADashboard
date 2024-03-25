import streamlit as st
from pages.components.sidebar import *
from pages.components.BayesianShootingStats import *
st.set_page_config(layout="wide")
render_sidebar("My_Random_Stats")

st.title("Bayesian Statistics")
player = render_player_selection()
render_b3P(player)

st.title("Kalman Filter Statistics")
team_abbrev = render_kORTG_team_selection()
render_kORTG(team_abbrev)