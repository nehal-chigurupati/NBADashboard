import streamlit as st
import pandas as pd
from nba_api.stats.static import players, teams
import json
from nba_api.stats.endpoints import leaguegamelog
from pathlib import Path
import importlib

def extract_api_params(json_data):
    endpoint_name = json_data["endpoint"]
    import_name = endpoint_name.lower()
    req_params = json_data["required_parameters"]
    data_sets = json_data["data_sets"]

    return endpoint_name, import_name, req_params, data_sets


@st.cache_data
def load_game_data(season_type_all_star, season):
    data = leaguegamelog.LeagueGameLog(season_type_all_star=season_type_all_star, season=season, league_id="00")
    data = data.get_data_frames()[0]
    for column in data.columns:
        data[column] = data[column].astype(str)
    return data

def load_player_data():
    player_first_names = []
    player_last_names = []
    player_id = []
    player_active = []

    for player in players.get_players():
        player_first_names.append(player["first_name"])
        player_last_names.append(player["last_name"])
        player_id.append(str(player["id"]))
        player_active.append(player["is_active"])

    out_dict = {
        "First name": player_first_names,
        "Last name": player_last_names,
        "Player ID": player_id,
        "Is active": player_active
    }
    
    return pd.DataFrame(out_dict)

def load_team_data():
    team_data = teams.get_teams()
    id = [str(team["id"]) for team in team_data]
    full_name = [team["full_name"] for team in team_data]
    abbrev = [team["abbreviation"] for team in team_data]
    nickname = [team["nickname"] for team in team_data]
    city = [team["city"] for team in team_data]
    state = [team["state"] for team in team_data]
    year_founded = [str(team["year_founded"]) for team in team_data]

    out_dict = {
        "Abbreviation": abbrev,
        "Full name": full_name,
        "Nickname": nickname,
        "ID": id,
        "City": city,
        "State": state,
        "Year founded": year_founded
    }

    return pd.DataFrame(out_dict)

def render_endpoint(endpoint_dict, key_start):
    endpoint_name, import_name, req_params, data_sets = extract_api_params(endpoint_dict)
    param_options = open("pages/params.json")
    param_options = json.load(param_options)

    with st.expander(endpoint_name):
        st.header("Get Data")
        param_input = []
        num_inputs_entered = 0
        for param in req_params:
            if param in param_options.keys():
                user_input = st.selectbox(param + ":", param_options[param], key=key_start)
            else:
                user_input = st.text_input(param + ": ", key=key_start)
            param_input.append(user_input)
            if user_input != "":
                num_inputs_entered += 1
            
            key_start += 1

        if num_inputs_entered == len(req_params):
            import_statement = f"from nba_api.stats.endpoints import {import_name}"
            exec_string =  import_statement + "\n"
            exec_string = exec_string + "data = " + import_name + "." + endpoint_name + str(param_input).replace("[", "(").replace("]", ")")
            print(exec_string)

            exec_globals = {}
            exec(exec_string, exec_globals)

            output = exec_globals.get("data")
            output = output.get_data_frames()

            st.header("Results")
            dataset_names = list(data_sets.keys())
            result_col_1, result_col_2 = st.columns(2)
            for i in range(len(output)):
                if i % 2 == 0:
                    with result_col_1:
                        st.subheader(dataset_names[i])
                        st.write(output[i])
                else:
                    with result_col_2:
                        st.subheader(dataset_names[i])
                        st.write(output[i])

        st.header("Dataset Info")
        info_col_1, info_col_2, info_col_3 = st.columns(3)
        hide = st.checkbox("Hide", value=False, key=key_start)
        key_start += 1
        if not hide:
            dataset_names = list(data_sets.keys())
            for i in range(len(dataset_names)):
                if i % 3 == 0:
                    with info_col_1:
                        st.subheader(dataset_names[i])
                        st.write(data_sets[dataset_names[i]])
                elif i % 3 == 1:
                    with info_col_2:
                        st.subheader(dataset_names[i])
                        st.write(data_sets[dataset_names[i]])
                else:
                    with info_col_3:
                        st.subheader(dataset_names[i])
                        st.write(data_sets[dataset_names[i]])

    return key_start
        


st.set_page_config(layout="wide")
print(Path.cwd())

st.title("NBA Website Data Retrieval")
st.caption("For parameter patterns, see the bottom of this page.")
st.text("**** This page has lots of bugs. It is in progress ****")

player_data = load_player_data()
team_data = load_team_data()

#Fetch API params

st.header("Call Endpoints")
hide_call = st.checkbox("Hide", value=False, key=1000000)
if not hide_call:
    f = open("pages/endpoints.json")
    api_params = json.load(f)
    f.close()
    key_start = 0
    for endpoint in api_params:
        key_start = render_endpoint(endpoint, key_start)



    
col1, col2 = st.columns(2)

with col1:
    st.header("Player API IDs")
    st.write(player_data)

with col2:
    st.header("Team API IDs")
    st.write(team_data)

st.header("Game API IDs")

season = st.text_input("Season (ex: 2023-24): ")

season_type_options = ["Regular Season", "Playoffs", "Pre Season", "All Star"]
season_type = st.selectbox("Season Type: ", season_type_options)

if season and season_type:
    data_load_state = st.text("Loading games...")
    data = load_game_data(season=season, season_type_all_star=season_type)
    data_load_state.text("Done! Currently using cached data.")
    st.write(data)

with st.expander("Parameter Patterns", expanded=False):
    md_text = Path("pages/parameters.md").read_text()
    st.markdown(md_text)