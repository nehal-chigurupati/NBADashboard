import streamlit as st
import requests

# Function to fetch Medium publications
def get_medium_publications(username):
    url = f"https://api.medium.com/v1/users/{username}/publications"
    response = requests.get(url)
    if response.status_code == 200:
        publications = response.json().get("data", [])
        return publications
    else:
        st.error("Error fetching Medium publications.")
        return []

# Function to display Medium publications in the app
def display_medium_publications(publications):
    st.header("Medium Publications")
    if not publications:
        st.write("No publications found.")
    else:
        for pub in publications:
            st.subheader(pub["name"])
            st.write(pub["description"])
            st.write(f"URL: {pub['url']}")
            st.write("---")