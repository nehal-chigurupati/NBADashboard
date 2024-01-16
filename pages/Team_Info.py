import streamlit as st
import pandas as pd
import numpy as np
from nba_api.stats.static import teams

def load_data():
    team_data = teams.get_teams()
    id = [str(team["id"]) for team in team_data]
    full_name = [team["full_name"] for team in team_data]
    abbrev = [team["abbreviation"] for team in team_data]
    nickname = [team["nickname"] for team in team_data]
    city = [team["city"] for team in team_data]
    state = [team["state"] for team in team_data]
    year_founded = [team["year_founded"] for team in team_data]

    out_dict = {
        "Abbreviation": abbrev,
        "Full name": full_name,
        "Nickname": nickname,
        "ID": id,
        "City": city,
        "State": state,
        "Year founded": year_founded
    }

    return pd.DataFrame(out_dict)

st.header("Basic team info")

data = load_data()

st.write(data)

