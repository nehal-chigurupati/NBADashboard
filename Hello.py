import streamlit as st
from pages.components.sidebar import *
st.header("Welcome to my dashboard for basketball-related data.")

msg = """
This is a work in progress, so there may be bugs. For player stats, see the player dashboard page. For live game stats, see the live game dashboard page.

For the source code, see below.
"""
st.write(msg)
st.markdown("[Github](https://github.com/nehal-chigurupati/NBADashboard)")

msg_projects = """
For my projects, see below.
"""
st.write(msg_projects)
st.markdown("[Medium](https://medium.com/@jxuwrsb)")
render_sidebar()

    