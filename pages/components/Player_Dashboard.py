import streamlit as st
import numpy as np
import pandas as pd
from nba_api.stats.endpoints import playercareerstats, playerestimatedmetrics, playergamelog, teamplayeronoffsummary
from nba_api.stats.endpoints import leaguehustlestatsplayer
from nba_api.stats.static import players
from scipy.stats import binom, norm
import plotly.express as px
import plotly.graph_objects as go
import os
import base64

#Compute z-score
def compute_z_score(element, column):
    mean = column.mean()
    std_dev = column.std()
    z_score = (element - mean) / std_dev
    return z_score

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

def get_player_team(player_id, career_data):
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
@st.cache_data
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
def load_estimated_metrics_player(player_name, timespan, season_type, career_data):
    player_id = get_player_id(player_name)
    if timespan == "Career":
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
def load_on_off_data(player_id, career_data):
    team_id = get_player_team(player_id, career_data)
    return teamplayeronoffsummary.TeamPlayerOnOffSummary(team_id).get_data_frames()

@st.cache_data
def load_hustle_stats(per_mode_time, season, season_type_all_star):
    data = leaguehustlestatsplayer.LeagueHustleStatsPlayer(
        per_mode_time=per_mode_time,
        season=season,
        season_type_all_star=season_type_all_star
    )
    return data.get_data_frames()[0]

#User input to find player, default is Donovan Mitchell
def render_player_selectbox():
    with st.expander("Player"):
        player_name = st.selectbox("Select player", get_active_players(), index=get_active_players().index("Donovan Mitchell"))

    return player_name

#Traditional season-by-season stats
def render_seasonal_traditional_stats(player_name):
    with st.expander("Per Mode"):
        per_mode = st.selectbox("", ["PerGame", "Totals", "Per36"], index=0)

    if per_mode:
        expand_basic_stats = st.checkbox("Show full table")
        data_load_state = st.text("Loading " + player_name +"'s stats")
        data = load_basic_player_stats(player_name, per_mode=per_mode).drop(["LEAGUE_ID", "PLAYER_ID"], axis=1)
        data_load_state.text("Done! Currently using cached data.")

        if expand_basic_stats:
            st.table(data)
        else:
            st.table(data.head(5))

@st.cache_data()
def load_all_estimated_metrics(season, season_type, league_id="00"):
    return playerestimatedmetrics.PlayerEstimatedMetrics(season=season, season_type=season_type, league_id="00").get_data_frames()[0]

#Estimated metrics
def render_estimated_metrics(player_name, career_data):
    with st.expander("Params"):
            timespan_options = np.unique(career_data["SEASON_ID"]).tolist()
            timespan_options.insert(0, "Career")
            timespan = st.selectbox("Timespan:", timespan_options, index=len(timespan_options)-1)

            season_type_options = ["Regular Season", "Playoffs", "Pre Season", "All Star"]
            season_type = st.selectbox("Season Type: ", season_type_options, index=0)

    
        
    data_load_state = st.text("Loading stats...")
    estimated_data = load_estimated_metrics_player(player_name=player_name, timespan=timespan, season_type=season_type, career_data=career_data)
    data_load_state.text("Done! Currently using cached data.")
    st.table(estimated_data)

    st.subheader("Z-Scores")
    z_score_stats = [
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
    ]

    z_score_stat = st.selectbox("Stat:", z_score_stats, index=2)
    #Calculate z-scores for each of the stats
    z_score_seasons = [i for i in timespan_options if i != "Career"]
    z_scores = []
    for season in z_score_seasons:
        e_metrics_season = load_all_estimated_metrics(season=season, season_type=season_type, league_id="00")
        player_raw_stat = e_metrics_season[e_metrics_season["PLAYER_ID"] == get_player_id(player_name)][z_score_stat].iloc[0]
        z_scores.append(compute_z_score(player_raw_stat, e_metrics_season[z_score_stat]))
    z_score_data = pd.DataFrame({"Season": z_score_seasons, "Z-Score": z_scores})
    z_score_data["Season"] = z_score_data["Season"].astype(str)
    z_score_data["Z-Score"] = z_score_data["Z-Score"].astype(float)
    z_score_plot = px.line(z_score_data, x="Season", y="Z-Score", markers=True)
    st.plotly_chart(z_score_plot, use_container_width=True)

    return estimated_data, timespan_options, season_type_options

#Bayesian 3P%
def render_advanced_shooting_stats(player_name, career_data, data):
    st.subheader("Bayesian 3P%")
    try:
        st.table(data)
        st.subheader("Comparative 3PT Shooting")

        seasons = []
        diffs = []
        for index, row in career_data.iterrows():
            seasons.append(row["SEASON_ID"])
            season_3p_perc = float(career_data[career_data["SEASON_ID"] == row["SEASON_ID"]]["FG3M"].iloc[0]) / float(career_data[career_data["SEASON_ID"] == row["SEASON_ID"]]["FG3A"].iloc[0])
            diffs.append(float(data["Bayesian 3P%"].iloc[0]) - season_3p_perc)

        diffs_df = pd.DataFrame({"Season": seasons, "b3P%-s3P%": diffs})
        comp_shooting_scatter = px.scatter(diffs_df, x="Season", y="b3P%-s3P%")
        st.plotly_chart(comp_shooting_scatter, use_container_width=True)

    except:
        st.text("Insufficient 3P volume to compute.")

#Moving averages for shooting efficiency stats and plus/minus
def render_moving_avgs(player_name, timespan_options, curr_season_data):
    with st.expander("Params"):
        stat_type = st.selectbox("Stat:", ["FG_PCT", "3P_PCT", "FT_PCT", "TOTAL_PLUS_MINUS"], index=3)
        averages_timespan_options = [x for x in timespan_options if x != "Career"]
        season_moving_averages = st.selectbox("Season:", averages_timespan_options, index=len(averages_timespan_options)-1)
    
    if season_moving_averages == "2023-24":
        season_game_data = curr_season_data
    else:
        data_load_state = st.text("Loading stats...")
        season_game_data = load_player_game_data(player_name=player_name, season=season_moving_averages)
        data_load_state.text("Done! Currently using cached data.")

    moving_average_data = get_moving_averages(season_game_data)
    moving_avg_fig = px.line(moving_average_data, x="GAME_NUMBER", y=stat_type, markers=True)
    st.plotly_chart(moving_avg_fig, use_container_width=True)


#Render net/offensive/defensive ratings
def render_ratings(player_name, season_type_options, career_data):
    with st.expander("Params"):
        season_type_on_off_figs = st.selectbox("Season Type:", season_type_options, index=0)
        rating = st.selectbox("Rating:", ["Net Rating", "Offensive Rating", "Defensive Rating"], index=0)

    data_load_state = st.text("Loading stats...")
    on_off_fig_data = load_estimated_metrics_player(player_name=player_name, timespan="Career", season_type=season_type_on_off_figs, career_data=career_data)
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

def render_game_logs(player_name, timespan_options, season_game_data):
    with st.expander("Params"):
        season_game_logs = st.selectbox("Season:", timespan_options, index=len(timespan_options)-1, key=152)
    
    if season_game_logs == "2023-24":
        data_load_state = st.text("Loading stats...")
        game_log_data = load_player_game_data(player_name=player_name, season=season_game_logs)
        data_load_state.text("Done! Currently using cached data.")
    else:
        game_log_data = season_game_data

    expand_basic_stats = st.checkbox("Show full table", key=150)
    
    if expand_basic_stats: 
        st.table(game_log_data)
    else:
        st.table(game_log_data.head(5))

def render_team_on_off(player_name, data):
    with st.expander("Team On/Off", expanded=True):
        st.markdown("Team plus/minus: " + str(data[0]["PLUS_MINUS"].tolist()[0]))
        on_court_plus_minus = px.scatter(data[1], x='VS_PLAYER_NAME', y="PLUS_MINUS", title="On court plus/minus")
        st.plotly_chart(on_court_plus_minus, use_container_width=True)
        off_court_plus_minus = px.scatter(data[2], x='VS_PLAYER_NAME', y="PLUS_MINUS", title="Off court plus/minus")
        st.plotly_chart(off_court_plus_minus, use_container_width=True)

@st.cache_data
def load_all_data(player_name):
    player_id = get_player_id(player_name)
    bayes_data = load_bayes_data(player_name=player_name)
    season_game_data = load_player_game_data(player_name=player_name, season="2023-24")
    career_data = playercareerstats.PlayerCareerStats(player_id=player_id).get_data_frames()[0]
    on_off = load_on_off_data(player_id, career_data)
    return on_off, bayes_data, season_game_data, career_data

def render_svg(svg, width_percentage=None, height_percentage=None):
    """Renders the given svg string."""
    b64 = base64.b64encode(svg.encode('utf-8')).decode("utf-8")
    
    #Build the img tag with optional width and height attributes
    img_tag = f'<img src="data:image/svg+xml;base64,{b64}"'
    
    if width_percentage:
        img_tag += f' width="{width_percentage}%"'
    
    if height_percentage:
        img_tag += f' height="{height_percentage}%"'
    
    img_tag += '/>'
    
    #Render the HTML
    c = st.container()
    c.write(img_tag, unsafe_allow_html=True)

        