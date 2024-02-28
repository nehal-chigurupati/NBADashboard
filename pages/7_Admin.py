import hmac
import streamlit as st
import pandas as pd
import numpy as np

def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False


if not check_password():
    st.stop()  # Do not continue if check_password is not True.

# Main Streamlit app starts here
st.header("IP Log")
st.subheader("With pages")
df = pd.read_csv("pages/components/ips_v2.csv")
st.write(df)

st.subheader("Old Version")
df_two = pd.read_csv("pages/components/ips.csv")
st.write(df_two)

st.subheader("Unique locations")
locs = np.unique(df_two["city"].tolist() + df["city"].tolist())
st.write(locs)
