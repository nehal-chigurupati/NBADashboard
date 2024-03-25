import numpy as np
import pandas as pd
import pymc as pm
from stqdm import stqdm
import arviz as az
import time
from retry import retry
import streamlit as st


from nba_api.stats.endpoints import playercareerstats, playergamelog
from nba_api.stats.static import players

from pages.components.Terminal_Redirect import *

@st.cache_data()
def get_all_season_data(player_id):
   return playercareerstats.PlayerCareerStats(player_id=player_id).get_data_frames()[0]["SEASON_ID"].tolist()

@st.cache_data()
@retry()
def get_season_data(player_id, season):
   return playergamelog.PlayerGameLog(player_id=player_id, season=season).get_data_frames()[0]

@st.cache_data()
def get_player_game_percentages(player_id):
  print("Collecting all season data...")
  all_seasons = get_all_season_data(player_id)
  print("Collected!")
  logs = []
  for i in stqdm(range(len(all_seasons))):
    logs.append(get_season_data(player_id, all_seasons[i]))
    time.sleep(.25)

  log = pd.concat(logs)
  log = log.sort_values('Game_ID')

  attempts = log["FG3A"]
  makes = log["FG3M"]
  total_attempts = attempts.sum()
  total_makes = makes.sum()
  career_percentage = total_makes / total_attempts

  return attempts.tolist(), makes.tolist(), career_percentage

def convert_to_binary_array(attempts, makes):
    arr = []
    for attempt, make in zip(attempts, makes):
        arr.extend([1] * make)
        arr.extend([0] * (attempt - make))
    return arr

@st.cache_data
def compute_b3P(player_id):
  shooting_attempts, shooting_successes, perc = get_player_game_percentages(player_id)
  shots = convert_to_binary_array(shooting_attempts, shooting_successes)

  with pm.Model() as model:

      theta = pm.Beta('theta', alpha=1, beta=1)
      y = pm.Bernoulli('y', p=theta, observed=shots)

      start = pm.find_MAP()
      step = pm.Metropolis()
      trace = pm.sample(len(shots), step=step, start=start)
      summary_stats = az.summary(trace, var_names=['theta'], hdi_prob=0.95)
      mean = summary_stats.loc['theta', 'mean']
      hdi_lower = summary_stats.loc['theta', 'hdi_2.5%']
      hdi_upper = summary_stats.loc['theta', 'hdi_97.5%']

  #return mean_shooting_skill, hdi_lower, hdi_upper

  return trace, mean, hdi_lower, hdi_upper

def render_player_selection():
   active_players = pd.json_normalize(players.get_active_players())
   player_name = st.selectbox(options=active_players["full_name"].tolist(), label="Select player")

   return active_players[active_players["full_name"] == player_name]

def render_b3P(player_df):
    player_id = player_df["id"].tolist()[0]
    with st.expander("Bayesian Statistics", expanded=True):
        st.markdown("**Bayesian 3P%**")
        try:
            trace, mean, lower, upper = compute_b3P(player_id)
            out = {
                "95% HDI lower bound": [lower],
                "Mean": [mean],
                "95% HDI upper bound": [upper]
            }
            st.table(pd.DataFrame(out))
        except:
           st.code("Insufficient 3 point shot attempts.")