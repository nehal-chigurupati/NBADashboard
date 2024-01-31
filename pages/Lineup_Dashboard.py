import streamlit as st
import pandas as pd
import numpy as np
from nba_api.stats.static import teams
from nba_api.stats.endpoints import shotchartlineupdetail, teamdashlineups
st.set_page_config(layout="wide")

st.text("***** IN PROGRESS ******")

def load_eppm_data():
    data = pd.read_csv("pages/lineup_evals_10_min.csv", engine="pyarrow")

    return data[["PLAYER_NAMES", "E_VAL_PER_MIN", "PTS_PER_MIN"]]


def get_all_lineup_strings():
    lineup_strings = load_eppm_data()["PLAYER_NAMES"].tolist()
    cleaned = [i.replace("'","") for i in lineup_strings]
    return cleaned

def load_all_team_abbrevs():
    all_teams = teams.get_teams()

    return [i["abbreviation"] for i in all_teams]

def render_team_person_selection():
    eppm_data = load_eppm_data()
    lineup_options = get_all_lineup_strings()
    lineup_options.append("All")
    lineup = st.selectbox("Lineup: ", lineup_options, index=len(lineup_options)-1)

    return lineup, eppm_data

def render_all_lineups(eppm_data):
    st.header("All Lineups")
    eppm_data = load_eppm_data()
    st.subheader("Expected Point Production")
    st.write(eppm_data)

st.header("Lineup Dashboard")

lineup, eppm_data = render_team_person_selection()

if lineup == "All":
    render_all_lineups(eppm_data)


