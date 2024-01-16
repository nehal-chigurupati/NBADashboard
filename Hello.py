import streamlit as st

st.header("Welcome to my dashboard for basketball-related data.")

msg = """
There are a few endpoints here. Player basic stats gives seasonal data like ppg and apg, 
         while estimated metrics gives offensive/defensive/net ratings and ranks. Player and team info give the NBA's IDs for each entity.
"""

st.write(msg)
    