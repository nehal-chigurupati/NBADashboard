import streamlit as st
import numpy as np
import pandas as pd
from nba_api.stats.static import players
from nba_api.stats.endpoints import playerestimatedmetrics
import unicodedata
from gekko import GEKKO


data_dir = "pages/data/"

#Params
k = 13.91

"""**utils**"""

def format_dollar_value(value):
    if value.startswith('-'):
        prefix = '-$'
        num_part = value[2:]
    else:
        prefix = '$'
        num_part = value
    
    if '.' in num_part:
        whole, cents = num_part.split('.')
        formatted_whole = '{:,}'.format(int(whole))
        return f"{prefix}{formatted_whole}.{cents}"
    else:
        formatted_whole = '{:,}'.format(int(num_part))
        return f"{prefix}{formatted_whole}"
    

"""**Calculate player costs as max of their % salary cap and comparable player % salary cap**"""

def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')

def get_all_active_players():
  active_players = pd.json_normalize(players.get_active_players())
  return active_players

def get_epm_ranks(fname=data_dir + "epm_data.csv"):
  epm_data = pd.read_csv(fname, engine="c")
  epm_data['epm_rank'] = epm_data['epm'].rank(method='min', ascending=False).astype('int')
  return epm_data[["nba_id", "name", "epm_rank"]]

def get_pct_salary_cap(fname=data_dir + "salary_data.csv", season="2023-24", salary_cap=123000000):
  salary_data = pd.read_csv(fname, engine="c")
  salary_data[season] = salary_data[season].str[1:]
  salary_data[season] = salary_data[season].str.replace(',', '', regex=False)
  salary_data = salary_data[salary_data[season].notna()]
  salary_data[season] = salary_data[season].astype(int)
  salary_data["pct_salary_cap"] = salary_data[season] / salary_cap

  return salary_data[["Player", "pct_salary_cap"]]

def get_player_comparable_salary_cap():

  epm_ranks = get_epm_ranks()
  pct_salary_cap_data = get_pct_salary_cap()

  ranks = []

  for index, row in pct_salary_cap_data.iterrows():
    try:
      player_name = strip_accents(row["Player"])
      epm_rank = epm_ranks[epm_ranks["name"] == player_name]["epm_rank"].iloc[0]
      ranks.append(epm_rank)
    except:
      ranks.append(np.nan)

  pct_salary_cap_data["epm_rank"] = ranks
  pct_salary_cap_data = pct_salary_cap_data.dropna()

  pct_salary_cap_data_sorted = pct_salary_cap_data.sort_values(by='epm_rank').reset_index(drop=True)

  pct_salary_cap_data_sorted['AvgSalaryCapSurroundingCorrected'] = np.nan

  for i in range(len(pct_salary_cap_data_sorted)):
      surrounding_players = pct_salary_cap_data_sorted['pct_salary_cap'].iloc[max(i-3, 0):min(i+4, len(pct_salary_cap_data_sorted))].tolist()
      if surrounding_players:
          pct_salary_cap_data_sorted.at[i, 'AvgSalaryCapSurroundingCorrected'] = sum(surrounding_players) / len(surrounding_players)

  return pct_salary_cap_data_sorted

def get_player_costs():
  pct_salary = get_player_comparable_salary_cap()
  pct_salary['c'] = np.maximum(pct_salary['AvgSalaryCapSurroundingCorrected'], pct_salary['pct_salary_cap'])

  return pct_salary[["Player", "c"]]

@st.cache_data()
def get_estimated_off_rating(player_names, season="2023-24"):
  """
  estimated_metrics = playerestimatedmetrics.PlayerEstimatedMetrics(season=season, league_id="00", season_type="Regular Season")
  estimated_metrics = estimated_metrics.get_data_frames()[0]
  """
  estimated_metrics = pd.read_csv(data_dir + "e_mets.csv", engine="c")

  eo = []
  ed = []
  for player in player_names:
    cleaned_name = strip_accents(player)
    e_off_rtg = estimated_metrics[estimated_metrics["PLAYER_NAME"] == cleaned_name]["E_OFF_RATING"].iloc[0]
    e_def_rtg = estimated_metrics[estimated_metrics["PLAYER_NAME"] == cleaned_name]["E_DEF_RATING"].iloc[0]
    eo.append(float(e_off_rtg) / 100.0)
    ed.append(float(e_def_rtg) / 100.0)

  out = {
      "Player": player_names,
      "eo": eo,
      "ed": ed
  }

  return pd.DataFrame(out)

def add_eo_ed(player_costs_df, season="2023-24"):
  e_mets_df = get_estimated_off_rating(player_costs_df["Player"].tolist(), season=season)

  player_costs_df = player_costs_df.merge(e_mets_df, on="Player")
  return player_costs_df

"""**Next, calculate the number of possessions per game for players**"""

def get_poss_per_game(fname=data_dir + "usage_data.csv"):
  usage_data = pd.read_csv(fname, engine="c")
  usage_data["poss_per_game"] = usage_data["POSS"] / usage_data["GP"]
  return usage_data[["PLAYER", "poss_per_game"]]

def add_np(player_df):
  poss_per_game = get_poss_per_game()

  np = []
  for index, row in player_df.iterrows():
    player_name = strip_accents(row["Player"])
    poss_per_game_val = poss_per_game[poss_per_game["PLAYER"] == player_name]["poss_per_game"].iloc[0]
    np.append(poss_per_game_val)

  player_df["np"] = np
  return player_df

"""**Finally, calculate league-wide team average possessions per game**"""

def calculate_league_poss_per_game(fname=data_dir + "team_possession_data.csv"):
  team_possession_data = pd.read_csv(fname, engine="c").dropna()
  team_possession_data["poss_per_game"] = team_possession_data["POSS"].str.replace(",","", regex=False).astype(int) / team_possession_data["GP"]
  return np.mean(team_possession_data["poss_per_game"])

def get_player_df():
    player_costs = get_player_costs()

    player_df = add_eo_ed(player_costs)

    player_df = add_np(player_df)

    return player_df


def objective_function(x, player_df):
  pts_added = 0
  pts_given = 0

  for i in range(len(player_df)):
    player_data = player_df.iloc[i]

    term = float(player_data["eo"]) * float(player_data["np"]) * float(x[i])
    pts_added += term

    term = float(player_data["ed"]) * float(player_data["np"]) * float(x[i])
    pts_given += term

  pts_added = pts_added ** 13.91
  pts_given = pts_given ** 13.91

  return (pts_added) / (pts_added + pts_given)


@st.cache_data()
def run_model(fixed_players, available_players, player_df, salary_cap_pct, play_time_constraint):
    player_list = player_df["Player"].tolist()
    team_np = calculate_league_poss_per_game()


    refined_player_df = player_df[player_df["Player"].isin(available_players) | player_df["Player"].isin(fixed_players)]

    refined_player_list = refined_player_df["Player"].tolist()
    fixed_players_indices = [refined_player_list.index(i) for i in fixed_players]

    m = GEKKO(remote=False)
    n = len(refined_player_df)
    salaries = refined_player_df["c"].tolist()
    poss = refined_player_df["np"].tolist()

    #x = [m.Var(lb=0, ub=1, integer=True) for _ in range(n)]
    #x = [m.Var(value=1 if i < 15 else 0, lb=0, ub=1, integer=True) for i in range(n)]
    x = [m.Var(value=1 if i in fixed_players_indices else 0, lb=0, ub=1, integer=True) for i in range(n)]

    pts_added = m.Intermediate(1)
    pts_given = m.Intermediate(1)

    for i in range(n):
        player_data = player_df.iloc[i]
        eo = player_data["eo"]
        np = player_data["np"]
        ed = player_data["ed"]

        #Intermediate terms for readability
        term_added = m.Intermediate(eo * np * x[i])
        term_given = m.Intermediate(ed * np * x[i])

        #Update pts_added and pts_given
        pts_added = m.Intermediate(pts_added + term_added)
        pts_given = m.Intermediate(pts_given + term_given)

    pts_added_powered = m.Intermediate(pts_added**13.91)
    pts_given_powered = m.Intermediate(pts_given**13.91)

    objective = pts_added_powered / (pts_added_powered + pts_given_powered)

    m.Maximize(objective)

    #Add roster size constraint
    m.Equation(m.sum(x) <= 15)
    m.Equation(m.sum(x) >= 12)

    #Add salary cap constraint
    salaries_var = [m.Const(value=salaries[i]) for i in range(n)]
    m.Equation(m.sum([salaries_var[i] * x[i] for i in range(n)]) <= salary_cap_pct)

    #Add minimum salary 
    m.Equation(m.sum([salaries_var[i] * x[i] for i in range(n)]) >= .9)

    if play_time_constraint:
        #Add play time constraint
        poss_var = [m.Const(value=poss[i]) for i in range(n)]
        m.Equation(m.sum([poss_var[i] * x[i] for i in range(n)]) >= 5*team_np)

    #Add fixed players constraint
    for idx in fixed_players_indices:
        m.Equation(x[idx] == 1)

    m.options.SOLVER=1
    m.solve(disp=True)
    solution = [x[i].value[0] for i in range(n)]

    player_names = []
    player_cost = []
    player_eo = []
    player_ed = []

    for i in range(len(solution)):
        if solution[i] == 1.0:
            player_names.append(refined_player_df["Player"].iloc[i])
            player_cost.append(refined_player_df["c"].iloc[i])
            player_eo.append(float(refined_player_df["eo"].iloc[i]) * 100.0)
            player_ed.append(float(refined_player_df["ed"].iloc[i]) * 100.0)

    roster_df = pd.DataFrame({
       "Player": player_names,
       "Salary Cap Percent": player_cost,
       "Estimated offensive rating": player_eo,
       "Estimated defensive rating": player_ed
    })
    
    exp_wins = objective_function(solution, refined_player_df)

    return roster_df, exp_wins

def render_inputs(player_list):
    salary_cap = 136000000
    salary_cap_pct = 1.0
    fixed_player_names = []
    available_player_names = []

    fixed_player_names = st.multiselect('Select players on roster', player_list)
    use_free_agents = st.checkbox("Use 2024 free agents as available players", value=True)
    free_agents = pd.read_csv(data_dir + "FreeAgents.csv", engine="c")
    with st.expander("See free agents"):
        st.dataframe(pd.read_csv(data_dir + "FreeAgents.csv", engine="c"), use_container_width=True)

    play_time_constraint = st.checkbox("Impose playing time constraint", value=False)
    if use_free_agents:
       available_players = [i for i in free_agents["Player"].tolist() if i in player_list]
    else:
       available_players = st.multiselect('Select Available Players', player_list)

    percentage = st.slider('Max percent of salary cap:', 0.9, 2.0, 1.0, step=0.01)
    # Calculate the difference
    st.text("Budget: " + format_dollar_value(str(percentage * salary_cap)))
    st.text("Salary cap (2023-24): " + "136,000,000")
    difference = (percentage * salary_cap) - salary_cap

    if difference > 0:
        st.text(format_dollar_value(str(difference)) + " above salary cap")
    elif difference == 0:
        st.text("At salary cap")
    else:
        st.text(format_dollar_value(str(difference)[1:]) + " below the salary cap")

    return fixed_player_names, available_players, percentage, play_time_constraint


   


