import streamlit as st
import numpy as np
import pandas as pd
from nba_api.live.nba.endpoints import scoreboard, playbyplay, boxscore
from nba_api.stats.static import players
from nba_api.stats.endpoints import playbyplayv3
import plotly.express as px
from datetime import datetime
import time
from retry import retry

def get_active_games():
    games = {}
    data = scoreboard.ScoreBoard().games.get_dict()

    for game in data:
        if int(game["period"]) > 0:
            away_team = game["awayTeam"]["teamName"]
            home_team = game["homeTeam"]["teamName"]
            game_id = str(game["gameId"])
        
            games[away_team + " @ " + home_team] = game_id
    return games

#Get player name given their ID
def get_player_name_from_id(player_id):
    player = players.find_player_by_id(player_id)
    if player:
        return player["full_name"]
    else: 
        return None

def load_all_scoreboard():
    return scoreboard.ScoreBoard().games.get_dict()


#Get scoreboard data

def load_scoreboard_data(game_id):
    data = scoreboard.ScoreBoard().games.get_dict()
    for i in data:
        if i["gameId"] == game_id:
            return i
    return None

#Get play by play data

def load_playbyplay_data(game_id, is_active):
    if is_active:
        data = playbyplay.PlayByPlay(game_id).get_dict()
        data = data["game"]["actions"]
        data = pd.json_normalize(data)
    else:
        data = playbyplayv3.PlayByPlayV3(game_id).get_data_frames()[0]
    return data

#Get box score for game

def load_box_score_data(game_id):
    data = boxscore.BoxScore(game_id=game_id).get_dict()
    away_team_players = pd.json_normalize(data["game"]["awayTeam"]["players"])
    home_team_players = pd.json_normalize(data["game"]["homeTeam"]["players"])

    away_team_statistics = pd.json_normalize(data["game"]["awayTeam"]["statistics"])
    home_team_statistics = pd.json_normalize(data["game"]["homeTeam"]["statistics"])

    return away_team_players, home_team_players, away_team_statistics, home_team_statistics

@retry()
def load_all_data(game_id):
    scoreboard_data = load_scoreboard_data(game_id)
    pbp_data = load_playbyplay_data(game_id, scoreboard_data["gameStatusText"] != "Final")
    away_team_data, home_team_data, away_team_statistics, home_team_statistics = load_box_score_data(game_id)

    return scoreboard_data, pbp_data, away_team_data, home_team_data, away_team_statistics, home_team_statistics

def render_curr_score(scoreboard_data):
    print(scoreboard_data)
    if scoreboard_data["gameStatusText"] == "Final":
        st.subheader(str(scoreboard_data["awayTeam"]["score"]) + "-" + str(scoreboard_data["homeTeam"]["score"]) + " (Final)")
    else: 
        st.subheader(str(scoreboard_data["awayTeam"]["score"]) + "-" + str(scoreboard_data["homeTeam"]["score"]))

def render_score_breakdown(pbp_data, scoreboard_data):
    with st.expander("Score Breakdown", expanded=True):
        #Separate page into columns, one for each quarter score plot
        cols = st.columns(len(np.unique(pbp_data["period"])))
        
        for i in range(len(cols)):
            with cols[i]:
                #Collect last score from each period
                period_data = pbp_data[pbp_data["period"] == np.unique(pbp_data["period"])[i]]
                period_last_row = pbp_data[pbp_data["period"] == np.unique(pbp_data["period"])[i]].iloc[-1]
                period_last_score = str(period_last_row["scoreAway"]) + "-" + str(period_last_row["scoreHome"])

                #Get margin for each period
                period_margin = str(int(period_last_row["scoreAway"]) - int(period_last_row["scoreHome"]))
                if int(period_margin) == 0:
                    period_margin = "**Tie**"
                elif int(period_margin) < 0:
                    period_margin = "**" + period_margin + " for " + scoreboard_data["awayTeam"]["teamTricode"] + "**"
                elif int(period_margin) > 0:
                    period_margin = "**+" + period_margin + " for " + scoreboard_data["awayTeam"]["teamTricode"] + "**"

                score_string = (period_last_score + ", " + period_margin)

                #Plot scores
                scoreboard_plot = px.scatter(
                    pbp_data[pbp_data["period"] == np.unique(pbp_data["period"])[i]], 
                    x="actionNumber", 
                    y=["scoreAway", "scoreHome"],
                    title="Quarter " + str(np.unique(pbp_data["period"])[i]) + ", " + period_margin,
                    labels = {
                        "actionNumber": "Action Number",
                        "value": "Score"
                    }
                )

                newnames = {
                    "scoreAway": scoreboard_data["awayTeam"]["teamTricode"],
                    "scoreHome": scoreboard_data["homeTeam"]["teamTricode"]
                }

                scoreboard_plot.for_each_trace(lambda t: t.update(name = newnames[t.name],
                                        legendgroup = newnames[t.name],
                                        hovertemplate = t.hovertemplate.replace(t.name, newnames[t.name])
                                        )
                    )
                st.plotly_chart(scoreboard_plot, use_container_width=True)

def render_pbp(pbp_data, scoreboard_data):
    #Isolate useful data
    player_names = []
    for index, row in pbp_data.iterrows():
        player_names.append(get_player_name_from_id(row["personId"]))
    pbp_data["player_name"] = player_names
    filtered_pbp = pbp_data[["actionNumber", "period", "scoreHome", "scoreAway", "description", "shotDistance", "shotResult", "isFieldGoal", "actionType", "player_name"]]
    filtered_pbp.columns = ["Action Number", 
                            "Period", 
                            scoreboard_data["homeTeam"]["teamTricode"] + " Score",
                            scoreboard_data["awayTeam"]["teamTricode"] + " Score", 
                            "Description",
                            "Shot Distance",
                            "Shot Result",
                            "Is field goal",
                            "Action Type",
                            "Player Name"
                        ]
    #Flip order of rows in dataframe so most recent actions are displayed first
    filtered_pbp = filtered_pbp.iloc[::-1]

    #Only show 5 most recent plays by default
    expand_pbp = st.checkbox("Show full table")
    if expand_pbp:
        st.write(filtered_pbp)
    else:
        st.write(filtered_pbp.head(5))
    
    with st.expander("Player Stats", expanded=True):

        stat_options = [
            "statistics.points",
            "statistics.assists",
            "statistics.reboundsDefensive",
            "statistics.reboundsOffensive",
            "statistics.reboundsTotal"
            "statistics.blocks",
            "statistics.blocksReceived",
            "statistics.fieldGoalsAttempted",
            "statistics.FieldGoalsMade",
            "statistics.fieldGoalsPercentage",
            "statistics.foulsOffensive",
            "statistics.foulsDrawn",
            "statistics.foulsPersonal",
            "statistics.foulsTechnical",
            "statistics.freeThrowsAttempted",
            "statistics.freeThrowsMade",
            "statistics.freeThrowsPercentage",
            "statistics.plusMinusPoints",
            "statistics.pointsFastBreak",
            "statistics.pointsInThePaint",
            "statistics.pointsSecondChance",
            "statistics.steals",
            "statistics.threePointersAttempted",
            "statistics.threePointersMade",
            "statistics.threePointersPercentage",
            "statistics.turnovers",
            "statistics.twoPointersAttempted",
            "statistics.twoPointersMade",
            "statistics.twoPointersPercentage",
        ]
        player_display_stat = st.selectbox("Stat:", stat_options, index=stat_options.index("statistics.plusMinusPoints"))
        st.subheader(scoreboard_data["awayTeam"]["teamTricode"])
        fig_away = px.bar(away_team_data, x="name", y=player_display_stat)
        st.plotly_chart(fig_away, use_container_width=True)

        st.subheader(scoreboard_data["homeTeam"]["teamTricode"])
        fig_home = px.bar(home_team_data, x="name", y=player_display_stat)
        st.plotly_chart(fig_home, use_container_width=True)