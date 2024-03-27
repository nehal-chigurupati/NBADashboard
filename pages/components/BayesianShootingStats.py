import numpy as np
import pandas as pd
import pymc as pm
from stqdm import stqdm
import arviz as az
import time
from retry import retry
import streamlit as st
#from filterpy.kalman import KalmanFilter
import plotly.graph_objs as go
from scipy import stats


from nba_api.stats.endpoints import playercareerstats, playergamelog, teamestimatedmetrics, boxscoreadvancedv3
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
  all_seasons = get_all_season_data(player_id)
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
"""
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
"""
@st.cache_data()
def compute_bWPM(player_id, bWPM_df):
   player_data = bWPM_df[bWPM_df["PLAYER_ID"] == player_id]
   percentile = player_data["PERCENTILE"]
   mean = player_data["MEAN"]
   lower_bound = player_data["HDI_LOWER_BOUND"]
   upper_bound = player_data["HDI_UPPER_BOUND"]

   return percentile, mean, lower_bound, upper_bound

    

@retry()
@st.cache_data()
def get_estimated_metrics(season="2023-24"):
    return teamestimatedmetrics.TeamEstimatedMetrics(season=season).get_data_frames()[0]

def get_team_metrics(team_full_name, data):
  ratings = data[data["TEAM_NAME"] == team_full_name][["E_OFF_RATING", "E_DEF_RATING"]]

  out = {
      "E_OFF_RATING": ratings["E_OFF_RATING"].values[0],
      "E_DEF_RATING": ratings["E_DEF_RATING"].values[0]
  }

  return out

def get_league_avg_ratings(data):
  return np.mean(data["E_OFF_RATING"])

def render_player_selection():
   active_players = pd.json_normalize(players.get_active_players())
   default_index = active_players["full_name"].tolist().index("Donovan Mitchell")
   player_name = st.selectbox(options=active_players["full_name"].tolist(), label="Select player", index=default_index)

   return active_players[active_players["full_name"] == player_name]
"""
@retry()
@st.cache_data()
def get_boxscore(game_id):
  return boxscoreadvancedv3.BoxScoreAdvancedV3(game_id=game_id).get_data_frames()[1]


@st.cache_data()
def get_matchup_ratings(team_A_name, team_A_abbrev, season="2023-24"):
  game_logs = pd.read_csv("pages/data/game_log.csv")
  matchup_logs = game_logs[game_logs["TEAM_NAME"] == team_A_name]
  game_ids = matchup_logs["GAME_ID"].tolist()

  team_A_off_rtgs = []
  team_A_def_rtgs = []
  team_B_off_rtgs = []
  team_B_def_rtgs = []

  for i in stqdm(game_ids):
    fixed_id = "00" + str(i)
    game_data = get_boxscore(fixed_id)
    A_game_data = game_data[game_data["teamTricode"] == team_A_abbrev]
    B_game_data = game_data[game_data["teamTricode"] != team_A_abbrev]
    team_A_off_rtgs.append(float(A_game_data["offensiveRating"].iloc[0]))
    team_A_def_rtgs.append(float(A_game_data["defensiveRating"].iloc[0]))
    team_B_off_rtgs.append(float(B_game_data["offensiveRating"].iloc[0]))
    team_B_def_rtgs.append(float(B_game_data["defensiveRating"].iloc[0]))

  out = {
      "TEAM_A_OFF_RATING": team_A_off_rtgs,
      "TEAM_A_DEF_RATING": team_A_def_rtgs,
      "TEAM_B_OFF_RATING": team_B_off_rtgs,
      "TEAM_B_DEF_RATING": team_B_def_rtgs
  }

  return pd.DataFrame(out)

def linear_prediction(team_A_off_rtg, team_A_def_rtg, team_B_off_rtg, team_B_def_rtg, league_avg):
  return ((team_A_off_rtg)*(team_B_def_rtg)) / league_avg, ((team_A_def_rtg)*(team_B_off_rtg)) / league_avg


@st.cache_data()
def compute_kORTG_filterpy(team_full_name, team_abbrev):
  matchups = get_matchup_ratings(team_full_name, team_abbrev)
  emets = get_estimated_metrics()
  t_emets = get_team_metrics(team_full_name, emets)
  R = get_league_avg_ratings(emets)


  initial_offensive_rating = t_emets["E_OFF_RATING"]
  #predicted_offensive_ratings = np.random.normal(110, 5, size=num_games)

  kf = KalmanFilter(dim_x=1, dim_z=1)

  kf.x = np.array([[initial_offensive_rating]])  # Initial state
  kf.P = np.array([[1]])

  kf.F = np.array([[1]])

  kf.H = np.array([[1]])

  kf.Q = np.array([[0.001]])

  kf.R = np.array([[1]])

  filtered_ratings = []

  for index, row in matchups.iterrows():
      kf.predict()

      # Now incorporate the measurement (the predicted offensive rating for the current game)
      predicted_rating, discard = linear_prediction(
          t_emets["E_OFF_RATING"],
          t_emets["E_DEF_RATING"],
          row["TEAM_B_OFF_RATING"],
          row["TEAM_B_DEF_RATING"],
          R
      )
      kf.update(np.array([[predicted_rating]]))

      # Save the filtered result
      filtered_ratings.append(kf.x[0, 0])

  return filtered_ratings
"""

def get_nba_teams():
  nba_teams = {
    "ATL": "Atlanta Hawks",
    "BOS": "Boston Celtics",
    "BKN": "Brooklyn Nets",
    "CHA": "Charlotte Hornets",
    "CHI": "Chicago Bulls",
    "CLE": "Cleveland Cavaliers",
    "DAL": "Dallas Mavericks",
    "DEN": "Denver Nuggets",
    "DET": "Detroit Pistons",
    "GSW": "Golden State Warriors",
    "HOU": "Houston Rockets",
    "IND": "Indiana Pacers",
    "LAC": "Los Angeles Clippers",
    "LAL": "Los Angeles Lakers",
    "MEM": "Memphis Grizzlies",
    "MIA": "Miami Heat",
    "MIL": "Milwaukee Bucks",
    "MIN": "Minnesota Timberwolves",
    "NOP": "New Orleans Pelicans",
    "NYK": "New York Knicks",
    "OKC": "Oklahoma City Thunder",
    "ORL": "Orlando Magic",
    "PHI": "Philadelphia 76ers",
    "PHX": "Phoenix Suns",
    "POR": "Portland Trail Blazers",
    "SAC": "Sacramento Kings",
    "SAS": "San Antonio Spurs",
    "TOR": "Toronto Raptors",
    "UTA": "Utah Jazz",
    "WAS": "Washington Wizards"
  }

  return nba_teams

def render_b3P_leaguewide_plot(values, names):
  percentiles = [stats.percentileofscore(values, value) for value in values]
  sorted_data = sorted(zip(percentiles, names, values), reverse=True)
  sorted_data = sorted_data[:-1]

  sections = {
      '90-100th percentile': [],
      '80-90th percentile': [],
      '70-80th percentile': [],
      '60-70th percentile': [],
      '50-60th percentile': [],
      '40-50th percentile': [],
      '30-40th percentile': [],
      '20-30th percentile': []
  }

  for percentile, name, value in sorted_data:
      if percentile >= 90:
          sections['90-100th percentile'].append((percentile, value, name))
      elif percentile >= 80:
          sections['80-90th percentile'].append((percentile, value, name))
      elif percentile >= 70:
          sections['70-80th percentile'].append((percentile, value, name))
      elif percentile >= 60:
          sections['60-70th percentile'].append((percentile, value, name))
      elif percentile >= 50:
          sections['50-60th percentile'].append((percentile, value, name))
      elif percentile >= 40:
          sections['40-50th percentile'].append((percentile, value, name))
      elif percentile >= 30:
          sections['30-40th percentile'].append((percentile, value, name))
      else:
          sections['20-30th percentile'].append((percentile, value, name))

  traces = []
  for section_name, section_data in sections.items():
      percentiles, values, names = zip(*section_data)
      trace = go.Scatter(
          x=percentiles,
          y=values,
          mode='markers',
          text=names,
          marker=dict(
              size=10,
              opacity=0.7,
              line=dict(width=1),
          ),
          name=section_name
      )
      traces.append(trace)

  layout = go.Layout(title='League-wide b3P%', xaxis=dict(title='Percentile Range'), yaxis=dict(title="b3P%"), showlegend=True)

  fig = go.Figure(data=traces, layout=layout)

  st.plotly_chart(fig, use_container_width=True)

def render_b3P(player_df):
    player_id = player_df["id"].tolist()[0]
    with st.expander("Bayesian Three Point Percent", expanded=True):
        st.markdown("**b3P%**")
        b3P_df = pd.read_csv("pages/data/b3P.csv")
        player_row = b3P_df[b3P_df["player_id"] == player_id]
        mean, lower, upper = player_row["mean"].iloc[0], player_row["hdi_lower"].iloc[0], player_row["hdi_upper"].iloc[0]
        try:
            #trace, mean, lower, upper = compute_b3P(player_id)
            player_row = b3P_df[b3P_df["player_id"] == player_id]
            mean, lower, upper = player_row["mean"].iloc[0], player_row["hdi_lower"].iloc[0], player_row["hdi_upper"].iloc[0]
            out = {
                "95% HDI lower bound": [lower],
                "Mean": [mean],
                "95% HDI upper bound": [upper]
            }
            st.table(pd.DataFrame(out))

        except:
          st.text("Precomputed value unavailable. This could be because the player does not take sufficiently many 3P shots, or because this stat is only available for players in the top 200 minutes played per game in the 2023-24 season. ")
        
        render_b3P_leaguewide_plot(b3P_df["mean"].tolist(), b3P_df["player_name"].tolist())
        
  
def render_kORTG_team_selection():
  options = [i for i in list(get_nba_teams().keys()) if i != "LAC"]
  default_ind = options.index("CLE")
  team_name = st.selectbox(options=options, label="Select team", index=default_ind)

  return team_name

def render_tRNG_team_selection():
  options = [i for i in list(get_nba_teams().keys()) if i != "LAC"]
  default_ind = options.index("CLE")
  team_name = st.selectbox(options=options, label="Select team:", index=default_ind)

  return team_name

def render_kORTG_leaguewide_plot(values, names):
  percentiles = [stats.percentileofscore(values, value) for value in values]
  sorted_data = sorted(zip(percentiles, names, values), reverse=True)
  sorted_data = sorted_data[:-1]

  sections = {
      '90-100th percentile': [],
      '80-90th percentile': [],
      '70-80th percentile': [],
      '60-70th percentile': [],
      '50-60th percentile': [],
      '40-50th percentile': [],
      '30-40th percentile': [],
      '20-30th percentile': []
  }

  for percentile, name, value in sorted_data:
      if percentile >= 90:
          sections['90-100th percentile'].append((percentile, value, name))
      elif percentile >= 80:
          sections['80-90th percentile'].append((percentile, value, name))
      elif percentile >= 70:
          sections['70-80th percentile'].append((percentile, value, name))
      elif percentile >= 60:
          sections['60-70th percentile'].append((percentile, value, name))
      elif percentile >= 50:
          sections['50-60th percentile'].append((percentile, value, name))
      elif percentile >= 40:
          sections['40-50th percentile'].append((percentile, value, name))
      elif percentile >= 30:
          sections['30-40th percentile'].append((percentile, value, name))
      else:
          sections['20-30th percentile'].append((percentile, value, name))

  traces = []
  for section_name, section_data in sections.items():
      percentiles, values, names = zip(*section_data)
      trace = go.Scatter(
          x=percentiles,
          y=values,
          mode='markers',
          text=names,
          marker=dict(
              size=10,
              opacity=0.7,
              line=dict(width=1),
          ),
          name=section_name
      )
      traces.append(trace)

  layout = go.Layout(
      title='League-wide kORTG',
      xaxis=dict(title='Percentile Range'),
      yaxis=dict(title='kORTG'),
      showlegend=True,
  )

  fig = go.Figure(data=traces, layout=layout)

  st.plotly_chart(fig, use_container_width=True)
   

def render_kORTG(team_abbrev):
  with st.expander("Kalman Offensive Rating", expanded=True):
    kORTG_df = pd.read_csv("pages/data/kORTG.csv")
    st.markdown("**kORTG**")
    try:
      team_dict = get_nba_teams()
      vals = kORTG_df[team_abbrev].dropna().tolist()
      st.text("kORTG:")
      st.code(vals[-1])


      fig = go.Figure()
      fig.add_trace(go.Scatter(x=np.arange(len(vals)), y=vals, mode='lines+markers', name='kORTG'))
      fig.update_layout(
        title=team_abbrev + "'s " + "kORTG Trajectory",
        xaxis_title="Game Number",
        yaxis_title="Season Offensive Rating"
      )
      st.plotly_chart(fig, use_container_width=True)

      teams = list(kORTG_df.columns)
      kortg_vals = [[i for i in kORTG_df[i].dropna().tolist()][-1] for i in teams]
      render_kORTG_leaguewide_plot(kortg_vals, teams)

    except:
           st.code("Error in computation. Reporting bug. ")
  

def render_bWPM_box_plot(bWPM_df):
  names = bWPM_df["PLAYER_NAME"].tolist()
  values = bWPM_df["MEAN"].tolist()
  percentiles = bWPM_df["PERCENTILE"].tolist()
  sorted_data = sorted(zip(percentiles, names, values), reverse=True)

  sections = {
      '90-100th percentile': [],
      '80-90th percentile': [],
      '70-80th percentile': [],
      '60-70th percentile': [],
      '50-60th percentile': [],
      '40-50th percentile': [],
      '30-40th percentile': [],
      '20-30th percentile': []
  }

  for percentile, name, value in sorted_data:
      if percentile >= 90:
          sections['90-100th percentile'].append((percentile, value, name))
      elif percentile >= 80:
          sections['80-90th percentile'].append((percentile, value, name))
      elif percentile >= 70:
          sections['70-80th percentile'].append((percentile, value, name))
      elif percentile >= 60:
          sections['60-70th percentile'].append((percentile, value, name))
      elif percentile >= 50:
          sections['50-60th percentile'].append((percentile, value, name))
      elif percentile >= 40:
          sections['40-50th percentile'].append((percentile, value, name))
      elif percentile >= 30:
          sections['30-40th percentile'].append((percentile, value, name))
      else:
          sections['20-30th percentile'].append((percentile, value, name))

  traces = []
  for section_name, section_data in sections.items():
      percentiles, values, names = zip(*section_data)
      trace = go.Scatter(
          x=percentiles,
          y=values,
          mode='markers',
          text=names,
          marker=dict(
              size=10,
              opacity=0.7,
              line=dict(width=1),
          ),
          name=section_name
      )
      traces.append(trace)

  layout = go.Layout(
      title='League-wide bWPM',
      xaxis=dict(title='Percentile Range'),
      yaxis=dict(title='bWPM'),
      showlegend=True,
  )

  fig = go.Figure(data=traces, layout=layout)

  st.plotly_chart(fig, use_container_width=True)

def render_bWPM(player):
   player_id = player["id"].tolist()[0]
   
   bWPM_data = pd.read_csv("pages/data/bWPM.csv")
   with st.expander('Bayesian Weighted Plus-Minus', expanded=True):
      st.markdown("**bWPM**")
      if player_id in bWPM_data["PLAYER_ID"].tolist():
        percentile, mean, hdi_lower, hdi_upper = compute_bWPM(player_id, bWPM_data)
        st.code("Percentile: " + str(percentile.iloc[0]))
        st.code("Raw Score: " + str(mean.iloc[0]))

        out = {
          "95% HDI Lower Bound": [hdi_lower.iloc[0]],
          "Posterior Mean": [mean.iloc[0]],
          "95% HDI Upper Bound": [hdi_upper.iloc[0]]
        }

        st.table(pd.DataFrame(out))


      else:
         st.text("bWPM only available for players in the top 200 minutes per game played in the 2023-24 season.")
      
      render_bWPM_box_plot(bWPM_data)

def render_tRNG_leaguewide_plot(values, names, stat_name):
  percentiles = [stats.percentileofscore(values, value) for value in values]
  sorted_data = sorted(zip(percentiles, names, values), reverse=True)
  sorted_data = sorted_data[:-1]

  sections = {
      '90-100th percentile': [],
      '80-90th percentile': [],
      '70-80th percentile': [],
      '60-70th percentile': [],
      '50-60th percentile': [],
      '40-50th percentile': [],
      '30-40th percentile': [],
      '20-30th percentile': []
  }

  for percentile, name, value in sorted_data:
      if percentile >= 90:
          sections['90-100th percentile'].append((percentile, value, name))
      elif percentile >= 80:
          sections['80-90th percentile'].append((percentile, value, name))
      elif percentile >= 70:
          sections['70-80th percentile'].append((percentile, value, name))
      elif percentile >= 60:
          sections['60-70th percentile'].append((percentile, value, name))
      elif percentile >= 50:
          sections['50-60th percentile'].append((percentile, value, name))
      elif percentile >= 40:
          sections['40-50th percentile'].append((percentile, value, name))
      elif percentile >= 30:
          sections['30-40th percentile'].append((percentile, value, name))
      else:
          sections['20-30th percentile'].append((percentile, value, name))

  traces = []
  for section_name, section_data in sections.items():
      percentiles, values, names = zip(*section_data)
      trace = go.Scatter(
          x=percentiles,
          y=values,
          mode='markers',
          text=names,
          marker=dict(
              size=10,
              opacity=0.7,
              line=dict(width=1),
          ),
          name=section_name
      )
      traces.append(trace)

  layout = go.Layout(
      title='League-wide ' + stat_name,
      xaxis=dict(title='Percentile Range'),
      yaxis=dict(title=stat_name),
      showlegend=True,
  )

  fig = go.Figure(data=traces, layout=layout)

  st.plotly_chart(fig, use_container_width=True)

def render_tORNG(team_abbrev):
  with st.expander("Topological Offensive Range", expanded=True):
    tRNG_df = pd.read_csv("pages/data/PERSISTENCE_MEANS.csv")
    values = tRNG_df["OFF_MEAN_H0_DEATH"].tolist()
    team_abbrevs = tRNG_df["abbreviation_x"].tolist()
    percentiles = [stats.percentileofscore(values, value) for value in values]
    st.markdown("**tORNG**")
    try:
      team_dict = get_nba_teams()
      off_val = tRNG_df[tRNG_df["abbreviation_x"] == team_abbrev]["OFF_MEAN_H0_DEATH"]
      st.code("Percentile: " + str(percentiles[team_abbrevs.index(team_abbrev)]))
      st.code("Raw Score: " + str(off_val.iloc[0]))
      render_tRNG_leaguewide_plot(tRNG_df["OFF_MEAN_H0_DEATH"].tolist(), tRNG_df["abbreviation_x"].tolist(), stat_name = "tORG")
    except:
      st.code("Error in computation. Reporting bug. ")

def render_tDRNG(team_abbrev):
  with st.expander("Topological Defensive Range", expanded=True):
    tRNG_df = pd.read_csv("pages/data/PERSISTENCE_MEANS.csv")
    values = tRNG_df["DEF_MEAN_H0_DEATH"].tolist()
    team_abbrevs = tRNG_df["abbreviation_x"].tolist()
    percentiles = [stats.percentileofscore(values, value) for value in values]
    st.markdown("**tORNG**")
    try:
      team_dict = get_nba_teams()
      off_val = tRNG_df[tRNG_df["abbreviation_x"] == team_abbrev]["DEF_MEAN_H0_DEATH"]
      st.code("Percentile: " + str(percentiles[team_abbrevs.index(team_abbrev)]))
      st.code("Raw Score: " + str(off_val.iloc[0]))
      render_tRNG_leaguewide_plot(tRNG_df["DEF_MEAN_H0_DEATH"].tolist(), tRNG_df["abbreviation_x"].tolist(), stat_name="tDRNG")
    except:
      st.code("Error in computation. Reporting bug. ")

def render_tNRNG(team_abbrev):
  with st.expander("Topological Net Range", expanded=True):
    tRNG_df = pd.read_csv("pages/data/PERSISTENCE_MEANS.csv")
    values = tRNG_df["NET_MEAN_H0_DEATH"].tolist()
    team_abbrevs = tRNG_df["abbreviation_x"].tolist()
    percentiles = [stats.percentileofscore(values, value) for value in values]
    st.markdown("**tNRNG**")
    try:
      team_dict = get_nba_teams()
      off_val = tRNG_df[tRNG_df["abbreviation_x"] == team_abbrev]["NET_MEAN_H0_DEATH"]
      st.code("Percentile: " + str(percentiles[team_abbrevs.index(team_abbrev)]))
      st.code("Raw Score: " + str(off_val.iloc[0]))
      render_tRNG_leaguewide_plot(tRNG_df["NET_MEAN_H0_DEATH"].tolist(), tRNG_df["abbreviation_x"].tolist(), stat_name="tNRNG")
    except:
      st.code("Error in computation. Reporting bug. ")
          
   
   
   