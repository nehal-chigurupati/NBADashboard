import streamlit as st
import numpy as np
import pandas as pd
from nba_api.live.nba.endpoints import scoreboard, playbyplay
from nba_api.stats.static import players
from nba_api.stats.endpoints import playbyplayv3
import plotly.express as px
from datetime import datetime

st.set_page_config(layout="wide")


#Load all active games
def get_active_games():
    games = {}
    data = scoreboard.ScoreBoard().games.get_dict()

    for game in data:
        #for now, don't filter to see if it is final
        if game["gameStatusText"] != "a":
            away_team = game["awayTeam"]["teamName"]
            home_team = game["homeTeam"]["teamName"]
            game_id = str(game["gameId"])
        
            games[away_team + " @ " + home_team] = game_id

    return games

def get_player_name_from_id(player_id):
    player = players.find_player_by_id(player_id)
    if player:
        return player["full_name"]
    else: 
        return None


@st.cache_data
def load_scoreboard_data(game_id):
    data = scoreboard.ScoreBoard().games.get_dict()
    for i in data:
        if i["gameId"] == game_id:
            return i
    return None

@st.cache_data
def load_playbyplay_data(game_id, is_active):
    if is_active:
        data = playbyplay.PlayByPlay(game_id).get_data_frames()[0]
    else:
        data = playbyplayv3.PlayByPlayV3(game_id).get_data_frames()[0]
    return data

placeholder = st.empty()
active_games = get_active_games()
game_id = None
if len(active_games.keys()) == 0:
    st.subheader("No active games")
else:
    with st.expander("Select game"):
        game = st.selectbox("", active_games.keys())
        game_id = active_games[game]


if game_id:
    data_load_state = st.text("Refreshing...")
    scoreboard_data = load_scoreboard_data(game_id)
    pbp_data = load_playbyplay_data(game_id, scoreboard_data["gameStatusText"] != "Final")
    data_load_state.text("Done!")

    st.title(game)

    if scoreboard_data["gameStatusText"] == "Final":
        st.subheader(str(scoreboard_data["awayTeam"]["score"]) + "-" + str(scoreboard_data["homeTeam"]["score"]) + " (Final)")
    else: 
        st.subheader(str(scoreboard_data["awayTeam"]["score"]) + "-" + str(scoreboard_data["homeTeam"]["score"]))

    if st.button("Refresh Data"):
            data_load_state = st.text("Refreshing...")
            pbp_data = load_playbyplay_data(game_id, scoreboard_data["gameStatusText"] != "Final")
            scoreboard_data = load_scoreboard_data(game_id)
            data_load_state.text("Refreshed at " + str(datetime.now()))
    
    with st.expander("Score Breakdown", expanded=True):
        cols = st.columns(len(np.unique(pbp_data["period"])))
        
        for i in range(len(cols)):
            with cols[i]:
                period_data = pbp_data[pbp_data["period"] == np.unique(pbp_data["period"])[i]]
                period_last_row = pbp_data[pbp_data["period"] == np.unique(pbp_data["period"])[i]].iloc[-1]
                period_last_score = str(period_last_row["scoreAway"]) + "-" + str(period_last_row["scoreHome"])
                period_margin = str(int(period_last_row["scoreAway"]) - int(period_last_row["scoreHome"]))

                if int(period_margin) == 0:
                    period_margin = "**Tie**"
                elif int(period_margin) < 0:
                    period_margin = "**" + period_margin + " for " + scoreboard_data["awayTeam"]["teamTricode"] + "**"
                elif int(period_margin) > 0:
                    period_margin = "**+" + period_margin + " for " + scoreboard_data["awayTeam"]["teamTricode"] + "**"

                score_string = (period_last_score + ", " + period_margin)

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
    
    st.subheader("Play by play")
    print(pbp_data.columns)

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
    expand_pbp = st.checkbox("Show full table")
    if expand_pbp:
        st.write(filtered_pbp)
    else:
        st.write(filtered_pbp.head(5))

    col1, col2 = st.columns(2)

    with col1:
        st.subheader(scoreboard_data["awayTeam"]["teamTricode"])


    with col2:
        st.subheader(scoreboard_data["homeTeam"]["teamTricode"])


