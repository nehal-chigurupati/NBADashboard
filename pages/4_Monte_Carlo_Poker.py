import streamlit as st
from pages.components.sidebar import *
from pypokerengine.utils.card_utils import gen_cards, estimate_hole_card_win_rate
import itertools
import pandas as pd
from stqdm import stqdm
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
render_sidebar("Monte Carlo Poker")

suits = ["H", "D", "S", "C"]
ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
deck = [suit + rank for suit in suits for rank in ranks]



def group_card(card):
    rank = card[0] 
    if rank in '2345':
        return 'Low'
    elif rank in '6789':
        return 'Mid'
    elif rank in 'TJQK':
        return 'High'
    return 'Ace' if rank == 'A' else rank

def render_heatmap(prob_df):
    prob_df['Card1_group'] = prob_df['Card1'].apply(group_card)
    prob_df['Card2_group'] = prob_df['Card2'].apply(group_card)

    grouped_pivot_table = prob_df.groupby(['Card1_group', 'Card2_group'])['Probability'].mean().unstack()

    ordered_groups = ['Low', 'Mid', 'High', 'Ace']
    grouped_pivot_table = grouped_pivot_table.reindex(index=ordered_groups[::-1], columns=ordered_groups)

    fig = px.imshow(grouped_pivot_table,
                    labels=dict(x="Card 2 Group", y="Card 1 Group", color="Probability"),
                    x=['Low', 'Mid', 'High', 'Ace'],
                    y=['Ace', 'High', 'Mid', 'Low'],
                    text_auto=True,
                    color_continuous_scale='RdBu_r')
    fig.update_layout(
                    xaxis_title="Card 2 Group (Low: 2-5, Mid: 6-9, High: T-J-Q-K, Ace: A)",
                    yaxis_title="Card 1 Group (Ace: A, High: T-J-Q-K, Mid: 6-9, Low: 2-5)",
                    margin=dict(t=100, l=200),
                    width=800, height=600)
    st.plotly_chart(fig, use_container_width=True)

def postflop_odds(card_list, deck, nb_player, nb_simulation=1000):
    all_possible_hands = list(itertools.combinations(deck, 2))
    all_possible_hands = [list(hand) for hand in all_possible_hands]
    all_possible_hands = [gen_cards(hand) for hand in all_possible_hands]
    stringed_card_list = list(itertools.combinations(deck, 2))

    sim_probs = []
    for i in stqdm(range(len(all_possible_hands))):
        hand = all_possible_hands[i]
        sim_probs.append(
            estimate_hole_card_win_rate(
                nb_simulation = nb_simulation,
                nb_player = nb_player,
                hole_card=hand,
                community_card=gen_cards(card_list)
            )
        )
    df = pd.DataFrame(stringed_card_list, columns=['Card1', 'Card2'])
    df['Probability'] = sim_probs

    df['Card1'] = df['Card1'].apply(lambda x: x[1:] + x[0])
    df['Card2'] = df['Card2'].apply(lambda x: x[1:] + x[0])

    return df

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

st.subheader("Precomputed Preflop odds")
prob_df = pd.read_csv("pages/data/preflop_probs.csv")
with st.expander("Raw Probabilities"):
    st.dataframe(prob_df, use_container_width=True)

render_heatmap(prob_df)

st.subheader("Postflop odds")
num_players = st.number_input("Enter num players:", value=4)
comm_cards = st.multiselect(
        label="Postflop cards",
        options=deck
    )
generate = st.button("Generate postflop heatmap")
if generate:
    prob_df = postflop_odds(comm_cards, deck, nb_player=num_players)
    render_heatmap(prob_df)








