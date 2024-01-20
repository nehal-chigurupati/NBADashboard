import streamlit as st
import numpy as np
import pandas as pd
from nba_api.stats.endpoints import playercareerstats, playerestimatedmetrics, playergamelog, teamplayeronoffsummary
from nba_api.stats.static import players
from scipy.stats import binom, norm
import plotly.express as px
import plotly.graph_objects as go

#Bayesian 3P% utils
def bayesian_3pt_percentage_with_credible_interval(historical_pct, current_attempts, current_made, prior_std=0.1, credible_level=0.95):

    #Prior Distribution
    prior_distribution = norm(historical_pct, prior_std)

    #Likelihood Function
    likelihood = binom(current_attempts, current_made/current_attempts)

    #Update the Prior with Current Data (Posterior Distribution)
    percentage_values = np.linspace(0, 1, 1000)  # Possible 3-point percentages
    posterior_probabilities = likelihood.pmf(current_made) * prior_distribution.pdf(percentage_values)

    # Check if the sum of posterior probabilities is very small or zero
    sum_posterior = np.sum(posterior_probabilities)
    if sum_posterior < 1e-8:
        raise ValueError("Sum of posterior probabilities is too small, check your prior_std or data.")

    # Normalize the posterior probabilities
    posterior_probabilities /= sum_posterior

    # Calculate the Bayesian 3-Point Percentage
    bayesian_estimate = np.sum(percentage_values * posterior_probabilities)

    # Calculate the credible interval
    cumulative_probabilities = np.cumsum(posterior_probabilities)
    lower_bound_idx = np.where(cumulative_probabilities >= (1 - credible_level) / 2)[0][0]
    upper_bound_idx = np.where(cumulative_probabilities >= 1 - (1 - credible_level) / 2)[0][0]

    bayesian_estimate = [bayesian_estimate]
    lower_bound = [percentage_values[lower_bound_idx]]
    upper_bound = [percentage_values[upper_bound_idx]]
    out = {
        "Bayesian 3P%": bayesian_estimate,
        "CI Lower Bound": lower_bound,
        "CI Upper Bound": upper_bound
    }

    return pd.DataFrame(out)

def get_player_team(player_id):
    # Get player career stats
    career = playercareerstats.PlayerCareerStats(player_id=player_id)
    career_data = career.get_data_frames()[0]

    # Check if the player has played any games
    if career_data.empty:
        return None

    # Get the most recent team ID
    latest_season = career_data['TEAM_ID'].iloc[-1]

    return latest_season if latest_season != 0 else None

#Moving average util
def get_moving_averages(df):
    # Sort the DataFrame by 'GAME_DATE' to ensure chronological order
    df_sorted = df.iloc[::-1].reset_index(drop=True)

    game_indices = []
    three_pt_pct = []
    fg_pct = []
    ft_pct = []
    total_plus_minus = []

    cum_3pm, cum_3pa = 0, 0
    cum_fgm, cum_fga = 0, 0
    cum_ftm, cum_fta = 0, 0
    cum_plus_minus = 0

    # Iterate through the DataFrame to compute cumulative stats
    for index, row in df_sorted.iterrows():
        game_indices.append(index)
        cum_3pm += row['FG3M']
        cum_3pa += row['FG3A']
        cum_fgm += row['FGM']
        cum_fga += row['FGA']
        cum_ftm += row['FTM']
        cum_fta += row['FTA']
        cum_plus_minus += row['PLUS_MINUS']

        # Calculate and append the percentages and cumulative plus/minus
        three_pt_pct.append(cum_3pm / cum_3pa if cum_3pa > 0 else 0)
        fg_pct.append(cum_fgm / cum_fga if cum_fga > 0 else 0)
        ft_pct.append(cum_ftm / cum_fta if cum_fta > 0 else 0)
        total_plus_minus.append(cum_plus_minus)

    out = {"GAME_NUMBER": game_indices, "3P_PCT": three_pt_pct, "FG_PCT": fg_pct, "FT_PCT": ft_pct, "TOTAL_PLUS_MINUS": total_plus_minus}
    return pd.DataFrame(out)

def get_active_players():
    player_dicts = players.get_active_players()
    return [i["full_name"] for i in player_dicts]

def get_player_career_stats(player_id):
    return playercareerstats.PlayerCareerStats(player_id=player_id).get_data_frames()[0]

def get_historical_3pt_percentage(career_df):

    # Filter out the current season
    filtered_df = career_df[career_df['SEASON_ID'] != "2023-24"]

    # Calculate total 3-point attempts and made shots
    total_attempts = filtered_df['FG3A'].sum()
    total_made = filtered_df['FG3M'].sum()

    # Calculate 3-point percentage
    three_point_pct = total_made / total_attempts if total_attempts > 0 else 0

    return three_point_pct

def get_player_3p_stats(career_df):
    """
    Get the 3-Point Attempts (3PA) and 3-Point Made (3PM) for a given player in a specific season.
    """

    # Filter stats by season
    season_stats = career_df[career_df['SEASON_ID'] == "2023-24"]

    if season_stats.empty:
        return None, None

    # Extract 3PA and 3PM
    three_pa = season_stats['FG3A'].iloc[0]
    three_pm = season_stats['FG3M'].iloc[0]

    return three_pa, three_pm

    
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

#Get Bayesian 3P% data
@st.cache_data
def load_bayes_data(player_name):
    player_id = get_player_id(player_name)
    career_df = get_player_career_stats(player_id)
    historical_3_perc = get_historical_3pt_percentage(career_df)
    three_pa, three_pm = get_player_3p_stats(career_df)
    out = bayesian_3pt_percentage_with_credible_interval(historical_3_perc, three_pa, three_pm)

    return out

#Get player ID
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
    
#Load estimated metrics
@st.cache_data
def load_estimated_metrics_player(player_name, timespan, season_type):
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
        for column in df.columns:
            df[column] = df[column].astype(str)
        
        return df[df["PLAYER_NAME"] == player_name].iloc[::-1]

#Get basic stats
@st.cache_data
def load_basic_player_stats(player_name, per_mode):
    player_id = get_player_id(player_name)
    career_stats = playercareerstats.PlayerCareerStats(player_id=player_id, per_mode36=per_mode)
    career_stats = career_stats.get_data_frames()[0]

    for column in career_stats.columns:
        career_stats[column] = career_stats[column].astype(str)
    return career_stats.iloc[::-1]

#Get player game data for moving averages and game log
@st.cache_data
def load_player_game_data(player_name, season, season_type="Regular Season"):
    data = playergamelog.PlayerGameLog(player_id=get_player_id(player_name), season=season, season_type_all_star=season_type)
    data = data.get_data_frames()[0]

    return data

@st.cache_data
def load_on_off_data(player_id):
    team_id = get_player_team(player_id)
    return teamplayeronoffsummary.TeamPlayerOnOffSummary(team_id).get_data_frames()


st.set_page_config(layout="wide")
with st.expander("Player"):
    player_name = st.selectbox("Select player", get_active_players(), index=get_active_players().index("Donovan Mitchell"))

if player_name: 
    st.title(player_name)
    st.header("Seasonal Basic Stats")
    with st.expander("Per Mode"):
        per_mode = st.selectbox("", ["Per Game", "Totals", "Per 36"], index=0)
        if per_mode == "Per Game":
            per_mode = "PerGame"
        elif per_mode == "Per 36":
            per_mode = "Per36"

    if per_mode:
        expand_basic_stats = st.checkbox("Show full table")
        data_load_state = st.text("Loading " + player_name +"'s stats")
        data = load_basic_player_stats(player_name, per_mode=per_mode)
        data_load_state.text("Done! Currently using cached data.")

        if expand_basic_stats:
            st.table(data)
        else:
            st.table(data.head(5))

    col1, col2 = st.columns(2)

    with col1: 
        st.header("Estimated Metrics")
        with st.expander("Params"):
            career_data = playercareerstats.PlayerCareerStats(player_id=get_player_id(player_name), per_mode36="PerGame").get_data_frames()[0]
            timespan_options = np.unique(career_data["SEASON_ID"]).tolist()
            timespan_options.insert(0, "Career")
            timespan = st.selectbox("Timespan:", timespan_options, index=len(timespan_options)-1)

            season_type_options = ["Regular Season", "Playoffs", "Pre Season", "All Star"]
            season_type = st.selectbox("Season Type: ", season_type_options, index=0)
        
        data_load_state = st.text("Loading stats...")
        estimated_data = load_estimated_metrics_player(player_name=player_name, timespan=timespan, season_type=season_type)
        data_load_state.text("Done! Currently using cached data.")
        st.table(estimated_data)
    
    with col2:
        st.header("Advanced Shooting Stats")
        st.subheader("Bayesian 3P%")
        data_load_state = st.text("Loading stats...")
        try:
            data = load_bayes_data(player_name=player_name)
            data_load_state.text("Done! Currently using cached data.")
            st.table(data)
        except:
            st.out("Error computing b3P%.")

    st.header("Moving averages")
    with st.expander("Params"):
        stat_type = st.selectbox("Stat:", ["FG_PCT", "3P_PCT", "FT_PCT", "TOTAL_PLUS_MINUS"], index=3)
        averages_timespan_options = [x for x in timespan_options if x != "Career"]
        season_moving_averages = st.selectbox("Season:", averages_timespan_options, index=len(averages_timespan_options)-1)

    data_load_state = st.text("Loading stats...")
    season_game_data = load_player_game_data(player_name=player_name, season=season_moving_averages)
    moving_average_data = get_moving_averages(season_game_data)
    data_load_state.text("Done! Currently using cached data.")
    moving_avg_fig = px.line(moving_average_data, x="GAME_NUMBER", y=stat_type, markers=True)
    st.plotly_chart(moving_avg_fig, use_container_width=True)

    st.header("Ratings")
    with st.expander("Params"):
        season_type_on_off_figs = st.selectbox("Season Type:", season_type_options, index=0)
        rating = st.selectbox("Rating:", ["Net Rating", "Offensive Rating", "Defensive Rating"], index=0)

    data_load_state = st.text("Loading stats...")
    on_off_fig_data = load_estimated_metrics_player(player_name=player_name, timespan="Career", season_type=season_type_on_off_figs)
    data_load_state.text("Done! Currently using cached data.")

    if rating == "Net Rating":
        rate_fig = px.line(on_off_fig_data, x="SEASON", y="E_NET_RATING", markers=True)
        rank_fig = px.line(on_off_fig_data, x="SEASON", y="E_NET_RATING_RANK", markers=True)
        col3, col4 = st.columns(2)
        with col3: 
            st.plotly_chart(rate_fig)
        with col4:
            st.plotly_chart(rank_fig)

    if rating == "Offensive Rating":
        rate_fig = px.line(on_off_fig_data, x="SEASON", y="E_OFF_RATING", markers=True)
        rank_fig = px.line(on_off_fig_data, x="SEASON", y="E_OFF_RATING_RANK", markers=True)
        col3, col4 = st.columns(2)
        with col3: 
            st.plotly_chart(rate_fig)
        with col4:
            st.plotly_chart(rank_fig)   

    if rating == "Defensive Rating":
        rate_fig = px.line(on_off_fig_data, x="SEASON", y="E_DEF_RATING", markers=True)
        rank_fig = px.line(on_off_fig_data, x="SEASON", y="E_DEF_RATING_RANK", markers=True)
        col3, col4 = st.columns(2)
        with col3: 
            st.plotly_chart(rate_fig)
        with col4:
            st.plotly_chart(rank_fig)   
    
    st.header("Game Logs")
    with st.expander("Params"):
        season_game_logs = st.selectbox("Season:", timespan_options, index=len(timespan_options)-1, key=152)
    data_load_state = st.text("Loading stats...")
    game_log_data = load_player_game_data(player_name=player_name, season=season_game_logs)
    data_load_state.text("Done! Currently using cached data.")

    expand_basic_stats = st.checkbox("Show full table", key=150)
    
    if expand_basic_stats: 
        st.table(game_log_data)
    else:
        st.table(game_log_data.head(5))
    
    with st.expander("Team On/Off", expanded=False):
        data_load_state = st.text("Loading stats...")
        data = load_on_off_data(get_player_id(player_name))
        data_load_state = st.text("Using cached data.")
        st.markdown("Team plus/minus: " + str(data[0]["PLUS_MINUS"].tolist()[0]))
        col1, col2 = st.columns(2)
        with col1:
            on_court_plus_minus = px.scatter(data[1], x='VS_PLAYER_NAME', y="PLUS_MINUS", title="On court plus/minus")
            st.plotly_chart(on_court_plus_minus)
        with col2:
            off_court_plus_minus = px.scatter(data[2], x='VS_PLAYER_NAME', y="PLUS_MINUS", title="Off court plus/minus")
            st.plotly_chart(off_court_plus_minus)



