import streamlit as st
import pandas as pd
from pages.components.sidebar import *
from pages.components.Roster_Construction_Model import *

st.set_page_config(layout="wide")
render_sidebar("Roster_Construction_Model")

st.title("Roster Construction Models")
st.subheader("Model 1: Hard Cap & Single-Year Scope")
st.markdown("For background on this model, see [here](https://github.com/nehal-chigurupati/RosterConstruction/blob/main/README.pdf)")
player_df = get_player_df()
fixed_player_names, available_player_names, salary_cap_pct, play_time_constraint = render_inputs(player_df["Player"].tolist())

exec_model = st.button("Run Model")

if exec_model:
    try:
        roster, e_win_pct = run_model(fixed_player_names, available_player_names, player_df, salary_cap_pct, play_time_constraint)

        st.dataframe(roster, use_container_width=True)
        st.write("Expected win percent: " + str(e_win_pct * 100) + "%")
        st.write("Percent of salary cap spent: " + str(np.sum(roster["Salary Cap Percent"]) * 100) + "%")
    except:
        st.write("There are no possible rosters given the salary constraint presented. Try increasing the budget.")