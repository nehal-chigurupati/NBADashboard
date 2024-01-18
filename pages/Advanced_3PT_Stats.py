import streamlit as st
import numpy as np
import pandas as pd
from nba_api.stats.endpoints import playercareerstats
from nba_api.stats.static import players
from scipy.stats import binom, norm
import numpy as np

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

    return bayesian_estimate, percentage_values[lower_bound_idx], percentage_values[upper_bound_idx]

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

def load_bayes_data(player_name):
    player_id = get_player_id(player_name)
    career_df = get_player_career_stats(player_id)
    historical_3_perc = get_historical_3pt_percentage(career_df)
    three_pa, three_pm = get_player_3p_stats(career_df)
    estimate, lower_bound, upper_bound = bayesian_3pt_percentage_with_credible_interval(historical_3_perc, three_pa, three_pm)

    return estimate, lower_bound, upper_bound

def load_seasonal_basic_stats(player_name):
    player_id = get_player_id(player_name)
    career_df = get_player_career_stats(player_id)
    

st.header("Seasonal Basic Stats")

st.header("Bayesian 3PT Stats")
player_name = st.text_input("Player: ")
if player_name:
    st.write(load_bayes_data(player_name))

 



