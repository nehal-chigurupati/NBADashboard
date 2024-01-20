import streamlit as st
import numpy as np
import pandas as pd
from nba_api.live.nba.endpoints import scoreboard, playbyplay, boxscore
from nba_api.stats.static import players
from nba_api.stats.endpoints import playbyplayv3
import plotly.express as px
from datetime import datetime
import time

st.set_page_config(layout="wide")


#Load all active games
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


#Get user input for game
active_games = get_active_games()
game=None
if len(active_games.keys()) == 0:
    st.subheader("No active games")
else:
    with st.expander("Select game"):
        game = st.selectbox("", active_games.keys())
        game_id = active_games[game]


#Once game id is provided, begin collecting data
if game:
    #Load data
    data_load_state = st.text("Refreshing...")
    scoreboard_data = load_scoreboard_data(game_id)
    pbp_data = load_playbyplay_data(game_id, scoreboard_data["gameStatusText"] != "Final")
    away_team_data, home_team_data, away_team_statistics, home_team_statistics = load_box_score_data(game_id)
    data_load_state.text("Done!")
    data_load_state.text("Last Refreshed at " + str(datetime.now()))
    #Set title to current game
    st.title(game)

    #Put current score up
    if scoreboard_data["gameStatusText"] == "Final":
        st.subheader(str(scoreboard_data["awayTeam"]["score"]) + "-" + str(scoreboard_data["homeTeam"]["score"]) + " (Final)")
    else: 
        st.subheader(str(scoreboard_data["awayTeam"]["score"]) + "-" + str(scoreboard_data["homeTeam"]["score"]))

    #Add refresh button (need to add live updating support)
    if st.button("Force Refresh"):
            data_load_state = st.text("Refreshing...")
            pbp_data = load_playbyplay_data(game_id, scoreboard_data["gameStatusText"] != "Final")
            scoreboard_data = load_scoreboard_data(game_id)
            away_team_data, home_team_data, away_team_statistics, home_team_statistics = load_box_score_data(game_id)
            data_load_state.text("ForcRefreshed at " + str(datetime.now()))
    auto_refresh = st.checkbox(label="Autorefresh", value=True)
    
    #Quarter by quarter breakdown of score
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
    
    #Display play by play data
    st.subheader("Play by play")

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

    with st.expander("Box Score"):

        st.subheader(scoreboard_data["awayTeam"]["teamTricode"])
        st.text("Player Stats")
        st.write(away_team_data)


        st.subheader(scoreboard_data["homeTeam"]["teamTricode"])
        st.text("Player Stats")
        st.write(home_team_data)

        st.subheader("Comparison")
        comp_stat_options = [
            "assists",
            "assistsTurnoverRatio",
            "benchPoints",
            "biggestLead",
            "biggestLeadScore",
            "biggestScoringRun",
            "biggestScoringRunScore",
            "blocks",
            "blocksReceived",
            "fastBreakPointsAttempted",
            "fastBreakPointsMade",
            "fastBreakPointsPercentage",
            "fieldGoalsAttempted",
            "fieldGoalsEffectiveAdjusted",
            "fieldGoalsMade",
            "fieldGoalsPercentage",
            "foulsOffensive",
            "foulsDrawn",
            "foulsPersonal",
            "foulsTeam",
            "foulsTechnical",
            "foulsTeamTechnical",
            "freeThrowsAttempted",
            "freeThrowsMade",
            "freeThrowsPercentage",
            "points",
            "pointsAgainst",
            "pointsFastBreak",
            "pointsFromTurnovers",
            "pointsInThePaint",
            "pointsInThePaintAttempted",
            "pointsInThePaintMade",
            "pointsInThePaintPercentage",
            "pointsSecondChance",
            "reboundsDefensive",
            "reboundsOffensive",
            "reboundsPersonal",
            "reboundsTeam",
            "reboundsTeamDefensive",
            "reboundsTeamOffensive",
            "reboundsTotal",
            "steals",
            "threePointersAttempted",
            "threePointersMade",
            "threePointersPercentage",
            "timesTied",
            "trueShootingAttempts",
            "trueShootingPercentage",
            "turnovers",
            "turnoversTeam",
            "turnoversTotal",
            "twoPointsAttempted",
            "twoPointersMade",
            "twoPointersPercentage"
        ]
        out_comp = pd.concat([away_team_statistics, home_team_statistics])
        out_comp.insert(loc=0, column="Team", value=[scoreboard_data["awayTeam"]["teamTricode"], scoreboard_data["homeTeam"]["teamTricode"]])
        comp_bar_select = st.selectbox("Stat:", comp_stat_options, index=comp_stat_options.index("fieldGoalsPercentage"))
        comp_bar_graph = px.bar(out_comp, x="Team", y=comp_bar_select)
        st.plotly_chart(comp_bar_graph, user_container_width=True)
        st.write(out_comp)
    



# Placeholder for live data
placeholder = st.empty()

# Loop for refreshing data
if auto_refresh:
    while True:
        # Update this part to fetch your live data
        scoreboard_data = load_scoreboard_data(game_id)
        pbp_data = load_playbyplay_data(game_id, scoreboard_data["gameStatusText"] != "Final")
        away_team_data, home_team_data, away_team_statistics, home_team_statistics = load_box_score_data(game_id)

        # Wait for a seconds before the next update 
        time.sleep(5)

        # Refresh the page
        st.rerun()
