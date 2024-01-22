#!/usr/bin/env python
# coding: utf-8

# In[1]:


import numpy as np
import pandas as pd
from nba_api.stats.endpoints import leaguegamelog, playbyplayv3, gamerotation, teamestimatedmetrics, teamgamelog
from nba_api.stats.static import teams
import streamlit as st


# In[2]:


def generate_nba_seasons(start_year, end_year):
    seasons = []
    for year in range(start_year, end_year):
        next_year = str(year + 1)[-2:]  # Get last two digits of the next year
        season = f"{year}-{next_year}"
        seasons.append(season)
    return seasons


# In[3]:


def get_bench_points(game_id):
    rotation_data = gamerotation.GameRotation(game_id=game_id).get_data_frames()
    #Away team
    away_rotation_data = rotation_data[0]
    away_team_id = np.unique(rotation_data[0]["TEAM_ID"]).tolist()[0]
    
    #Home team
    home_rotation_data = rotation_data[1]
    home_team_id = np.unique(rotation_data[1]["TEAM_ID"]).tolist()[0]
    
    
    away_bench_points = 0
    for index, row in away_rotation_data.iterrows():
        if 0.0 not in away_rotation_data[away_rotation_data["PERSON_ID"] == row["PERSON_ID"]]["IN_TIME_REAL"].tolist():
            away_bench_points += row["PLAYER_PTS"]

    home_bench_points = 0
    for index, row in home_rotation_data.iterrows():
        if 0.0 not in home_rotation_data[home_rotation_data["PERSON_ID"] == row["PERSON_ID"]]["IN_TIME_REAL"].tolist():
            home_bench_points += row["PLAYER_PTS"]

    return away_bench_points, away_team_id, home_bench_points, home_team_id


# In[4]:

st.text("Ignore this page - I'm using it as a way of running some data collection remotely on the streamlit community cloud")
def run_bench_points_collection():


    # In[5]:

    seasons = generate_nba_seasons(2018, 2022)
    all_teams = [team["id"] for team in teams.get_teams()]


    # In[ ]:


    #Collect game logs (including game IDs)
    team_ids = []
    game_ids = []
    season_ids = []
    bench_points = []
    off_ratings = []
    season_win_pct = []
    counter = 1
    for season in seasons:
        st.text("Evaluating season " + str(counter) + "/" + str(len(seasons)))
        counter += 1
        season_game_ids = np.unique(leaguegamelog.LeagueGameLog(season=season).get_data_frames()[0]["GAME_ID"])
        team_data = teamestimatedmetrics.TeamEstimatedMetrics(season=season).get_data_frames()[0]
        team_data = team_data[["TEAM_ID", "E_OFF_RATING", "W_PCT"]]
        counter_game = 1
        for game in season_game_ids:
            st.text("Processing game " + str(counter) + "/" + str(len(season_game_ids)))
            counter += 1
            away_bench_pts, away_id, home_bench_pts, home_id = get_bench_points(game)
            
            #Get offensive rating of both teams
            off_rating_away = team_data[team_data["TEAM_ID"] == away_id]["E_OFF_RATING"]
            off_rating_home = team_data[team_data["TEAM_ID"] == home_id]["E_OFF_RATING"]
            
            #Get win percent of both teams
            w_pct_away = team_data[team_data["TEAM_ID"] == away_id]["W_PCT"]
            w_pct_home = team_data[team_data["TEAM_ID"] == home_id]["W_PCT"]
            
            #Add away team data
            team_ids.append(away_id)
            game_ids.append(game)
            season_ids.append(season)
            bench_points.append(away_bench_pts)
            off_ratings.append(off_rating_away)
            season_win_pct.append(w_pct_away)
            
            #Add home team data
            team_ids.append(home_id)
            game_ids.append(game)
            season_ids.append(season)
            bench_points.append(home_bench_pts)
            off_ratings.append(off_rating_home)
            season_win_pct.append(w_pct_home)
    out = {
        'TEAM_ID': team_ids,
        "GAME_ID": game_ids,
        "SEASON": season_ids,
        "BENCH_PTS": bench_points,
        "OFF_RTG": off_ratings,
        "SEASON_W_PCT": season_win_pct
    }

    out_df = pd.DataFrame(out)
    out_df.to_csv("BENCH_POINTS_REG_SEASON.csv")

    return out_df

run_code = st.button("Execute code")

if run_code:
    out_df = run_bench_points_collection()

download = st.button("View/download data")

if download:
    data = pd.read_csv("BENCH_POINTS_REG_SEASON.csv")
    st.write(data)


