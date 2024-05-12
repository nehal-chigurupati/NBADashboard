import streamlit as st
import pandas as pd
from pages.components.sidebar import *
from pages.components.Roster_Construction_Model import *
st.set_page_config(layout="wide")
render_sidebar("Roster_Construction_Model")


st.session_state.optimization_status = st.empty()
def gekko_callback(intermediate_result):
    #Update Streamlit app with the intermediate result
    st.session_state.optimization_status.text(f"Current Objective: {intermediate_result}")

st.warning("Note: I have yet to implement a few exceptions, so some current rosters may wrongly appear as exceeding the salary cap.")
st.title("Roster Construction Models")
st.subheader("Model v3: Soft cap with Bird/Early Bird/Non-Bird/Minimum Exceptions, Single-year scope")
st.markdown("For background on this model, see [here](https://github.com/nehal-chigurupati/RosterConstruction/blob/main/README.pdf)")
player_df = pd.read_csv("pages/data/player_df.csv")

fixed_player_names, available_vets, available_player_names, salary_cap_pct, play_time_constraint = render_inputs(player_df["Player"].tolist())
num_years_on_team = []
for i in available_vets:
    number = st.number_input("Enter " + i + "'s number of consecutive years on the team", 1, 20, "min", 1)
    num_years_on_team.append(number)

exec_model = st.button("Optimize")


if exec_model:
    try:
        roster, e_win_pct = optimize(fixed_player_names, available_vets, num_years_on_team, available_player_names, player_df, salary_cap_pct, play_time_constraint, _callback=gekko_callback)

        st.dataframe(roster, use_container_width=True)
        st.write("Expected win percent: " + str(e_win_pct * 100) + "%")
        #st.write("Percent of salary cap spent: " + str(np.sum(roster["Salary Cap Percent"]) * 100) + "%")
    except:
        st.write("No possible roster configuration possible (this may be because I haven't programmed all exceptions yet). Try increasing the total budget")