import streamlit as st
from nba_api.stats.endpoints import playerestimatedmetrics, playercareerstats
from nba_api.stats.static import players
import numpy as np
import pandas as pd
import plotly.express as px

def get_player_id(full_name):
    # Get all NBA players
    nba_players = players.get_players()

    # Search for the player by full name
    player = [player for player in nba_players if player['full_name'] == full_name]

    # Return the player's ID if found
    if player:
        return player[0]['id']
    else:
        return None
    
@st.cache_data
def load_data(season, season_type):
    data = playerestimatedmetrics.PlayerEstimatedMetrics(season=season, season_type=season_type, league_id="00").get_data_frames()[0]
    for column in data.columns:
        data[column] = data[column].astype(str)
    return data

@st.cache_data
def load_data_player(player_name, timespan, season_type):
    player_id = get_player_id(player_name)
    if timespan == "Career":
        career_data = playercareerstats.PlayerCareerStats(player_id=player_id).get_data_frames()[0]
        seasons = np.unique(career_data["SEASON_ID"]).tolist()

    
        dfs = []
        for season in seasons:
            df = playerestimatedmetrics.PlayerEstimatedMetrics(season=season, season_type=season_type)
            df = df.get_data_frames()[0]
            for column in df.columns:
                df[column] = df[column].astype(str)
            df["SEASON"] = [season]*len(df)
            dfs.append(df)
        out = pd.concat(dfs)
        return out[out["PLAYER_NAME"] == player_name]
    else:
        df = playerestimatedmetrics.PlayerEstimatedMetrics(season=timespan, season_type=season_type)
        df = df.get_data_frames()[0]
        print(df)
        for column in df.columns:
            df[column] = df[column].astype(str)
        
        return df[df["PLAYER_NAME"] == player_name]


st.header("Season Estimated Metrics")
season = st.text_input("Season (ex: 2023-24): ")

season_type_options = ["Regular Season", "Playoffs", "Pre Season", "All Star"]
season_type = st.selectbox("Season Type: ", season_type_options)

if season and season_type:
    data_load_state = st.text("Loading " + season + " " + season_type + " stats...")
    data = load_data(season=season, season_type=season_type)
    data_load_state.text("Done! Currently using cached data.")
    st.write(data)

st.header("Player Estimated Metrics")
player = st.text_input("Player name: ")
player_id = get_player_id(player)
if player:
    career_data = playercareerstats.PlayerCareerStats(player_id=player_id, per_mode36="PerGame").get_data_frames()[0]
    timespan_options = np.unique(career_data["SEASON_ID"]).tolist()
    timespan_options.append("Career")
    timespan = st.selectbox("Timespan:", timespan_options)
season_type_opt_2 = st.selectbox("Season Type: ", season_type_options, key=150)


if player and timespan and season_type_opt_2:
    data_load_state = st.text("Loading stats...")
    data = load_data_player(player_name=player, timespan=timespan, season_type=season_type_opt_2)
    data_load_state.text("Done! Currently using cached data.")
    st.write(data)

st.header("Career Evolution Scatterplot")
player_name = st.text_input("Player name:")
stat_options = [
    "GP",
    "W",
    "L",
    "W_PCT",
    "MIN",
    "E_OFF_RATING",
    "E_DEF_RATING",
    "E_NET_RATING",
    "E_AST_RATIO",
    "E_OREB_PCT",
    "E_DREB_PCT",
    "E_REB_PCT",
    "E_TOV_PCT",
    "E_USG_PCT",
    "E_PACE",
    "GP_RANK",
    "W_RANK",
    "L_RANK",
    "W_PCT_RANK",
    "MIN_RANK",
    "E_OFF_RATING_RANK",
    "E_DEF_RATING_RANK",
    "E_NET_RATING_RANK", 
    "E_AST_RATIO_RANK",
    "E_OREB_PCT_RANK",
    "E_DREB_PCT_RANK",
    "E_REB_PCT_RANK",
    "E_TOV_PCT_RANK",
    "E_USG_PCT_RANK",
    "E_PACE_RANK"
]

plot_types = st.multiselect("Stats:", stat_options)
season_type_opt_3 = st.selectbox("Season Type: ", season_type_options, key=151)

if player_name and plot_types:
    data_load_state = st.text("Loading stats...")
    data = load_data_player(player_name=player_name, timespan="Career", season_type=season_type_opt_3)
    data_load_state.text("Done! Currently using cached data.")

    for stat in plot_types:
        fig = px.scatter(data, x="SEASON", y=stat)
        st.plotly_chart(fig)
