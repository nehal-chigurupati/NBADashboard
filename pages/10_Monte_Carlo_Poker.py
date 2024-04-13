import streamlit as st
from pages.components.sidebar import *
from pypokerengine.utils.card_utils import gen_cards, estimate_hole_card_win_rate
import itertools

st.set_page_config(layout="wide")
render_sidebar("Monte Carlo Poker")

suits = ["H", "D", "S", "C"]
ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
deck = [suit + rank for suit in suits for rank in ranks]


st.header("Poker Probabilities")
st.text("Generated via Monte Carlo simulations")

st.subheader("Hand Win Probabilities")
with st.expander("Hand Cards"):
    cards = st.multiselect(
        label="Hand cards",
        options=deck
    )


    
with st.expander("Flop"):
    community_cards = st.multiselect(
        label="Community cards",
        options=deck
    )

num_players = st.number_input(label="Number of players", value=4)
num_simulations = st.number_input(label="Number of simulations", value=1000)

simulate = st.button("Simulate")

if simulate:
    if cards and num_players and num_simulations:
        win_pct = estimate_hole_card_win_rate(
            nb_simulation=num_simulations,
            nb_player=num_players,
            hole_card=gen_cards(cards),
            community_card=gen_cards(community_cards)
        )

        st.code("Win pct: " + str(win_pct * 100) + "%")
    else:
        st.error("Missing entries!")



