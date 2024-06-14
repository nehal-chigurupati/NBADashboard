import streamlit as st
from pages.components.sidebar import *
from pages.components.BayesianShootingStats import *
st.set_page_config(layout="wide")
render_sidebar("My_Random_Stats")

st.text("For b3P% and bWPM, see the Player Stats tab. For kORTG and topological range, see Team Stats.")
tab1, tab2 = st.tabs(["Player Stats (b3P%, dvr3P%, bWPM, )", "Team Stats (kORTG, tRNG)"])

with tab1:
    st.title("Player Stats")
    player = render_player_selection()
    st.title(player["full_name"].iloc[0])
    render_b3P(player)
    render_dvr3P()
    render_bWPM(player)

with tab2:
    st.title("Team Stats")
    team_abbrev = render_kORTG_team_selection()
    st.title(team_abbrev)
    st.header("Kalman Offensive Rating (kORTG)")
    render_kORTG(team_abbrev)

    render_explore_tRNG = st.toggle("Explore Topological Range Data", value=False, key=6)
    if render_explore_tRNG:
      renderer = get_pyg_renderer("pages/data/PERSISTENCE_MEANS.csv")
      renderer.render_explore()

    col3, col4 = st.columns(2)

    with col3:
        st.header("Topological Offensive Range (tORNG)")
        render_tORNG(team_abbrev)
    with col4:
        st.header("Topological Defensive Range (tDRNG)")
        render_tDRNG(team_abbrev)

    st.header("Topological Net Range (tNRNG)")
    render_tNRNG(team_abbrev)