import streamlit as st
from pages.components.sidebar import *
from pages.components.BayesianShootingStats import *
st.set_page_config(layout="wide")
render_sidebar("Bayesian_Shooting_Stats")

player = render_player_selection()
render_b3P(player)