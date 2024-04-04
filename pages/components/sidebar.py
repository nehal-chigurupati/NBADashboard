import streamlit as st
import time
from pages.components.Live_Game_Dashboard import get_active_games, load_scoreboard_data, render_curr_score, load_all_scoreboard
from pages.components.ip import loc
import os
import base64
from retry import retry

nba_team_abbreviations = [
    'ATL', 'BOS', 'BKN', 'CHA', 'CHI', 'CLE', 'DAL', 'DEN',
    'DET', 'GSW', 'HOU', 'IND', 'LAC', 'LAL', 'MEM', 'MIA',
    'MIL', 'MIN', 'NOP', 'NYK', 'OKC', 'ORL', 'PHI', 'PHX',
    'POR', 'SAC', 'SAS', 'TOR', 'UTA', 'WAS'
]

def render_svg(svg, width_percentage=None, height_percentage=None):
    """Renders the given svg string."""
    b64 = base64.b64encode(svg.encode('utf-8')).decode("utf-8")
    
    #Build the img tag with optional width and height attributes
    img_tag = f'<img src="data:image/svg+xml;base64,{b64}"'
    
    if width_percentage:
        img_tag += f' width="{width_percentage}%"'
    
    if height_percentage:
        img_tag += f' height="{height_percentage}%"'
    
    img_tag += '/>'
    
    # Render the HTML
    c = st.container()
    c.write(img_tag, unsafe_allow_html=True)

def render_svgs_horizontally(svgs, width_percentage=None, height_percentage=None):
    """Renders multiple SVG strings side by side horizontally."""
    container = st.container()

    for svg in svgs:
        b64 = base64.b64encode(svg.encode('utf-8')).decode("utf-8")

        # Build the img tag with optional width and height attributes
        img_tag = f'<img src="data:image/svg+xml;base64,{b64}"'
        
        if width_percentage:
            img_tag += f' width="{width_percentage}%"'
        
        if height_percentage:
            img_tag += f' height="{height_percentage}%"'
        
        img_tag += '/>'

        # Write the img tag to the container
        container.write(img_tag, unsafe_allow_html=True)

#@retry()
def render_sidebar_game_scores():
    st.subheader("Game Scores")
    active_games = get_active_games()
    for game in active_games.keys():
        render_curr_score(load_scoreboard_data(active_games[game]))
    
    if len(active_games) == 0:
        st.write("No active games")

def render_team(team_abbrev, width, height):
    render_svg(open("pages/images/team_logos/" + team_abbrev + ".svg").read(), width, height)

def render_teams():
    st.subheader("Teams")
    for f in os.listdir("pages/images/team_logos"):
        if f[-3:] == "svg":
            render_svg(open("pages/images/team_logos/" + f).read(), 10, 10)

def render_game_score(away_team_abbrev, home_team_abbrev, away_score, home_score, period, time_remaining_in_period, gameStatusText):
    col1, col2, col3 = st.columns(3)

    with col1:
        render_team(away_team_abbrev, 50, 50)
        st.write(away_score)
    
    with col2:
        time_remaining_in_period = time_remaining_in_period[2:].replace("M", ":")
        st.write(time_remaining_in_period)

        st.markdown("**Quarter " + str(period) + "**")
        if gameStatusText == "Final":
            st.markdown("**Final Score**")

    
    with col3:
        render_team(home_team_abbrev, 50, 50)
        st.write(home_score)
    
def render_future_game(away_team_abbrev, home_team_abbrev, away_score, home_score, gameStatusText):
    col1, col2, col3 = st.columns(3)

    with col1:
        render_team(away_team_abbrev, 50, 50)
        #st.write(away_score)
    
    with col2:
        st.write(gameStatusText)
    
    with col3:
        render_team(home_team_abbrev, 50, 50)
        #st.write(home_score)

def is_nba_team_game(game):
    away_team_abbrev = game["awayTeam"]["teamTricode"]
    home_team_abbrev = game["homeTeam"]["teamTricode"]
        
    return ((away_team_abbrev in nba_team_abbreviations) and (home_team_abbrev in nba_team_abbreviations))

def filter_for_nba_team_games(game_data):
    return [game for game in game_data if is_nba_team_game(game)]


def render_todays_games():
    game_data = filter_for_nba_team_games(load_all_scoreboard())
    if len(game_data) == 0:
        st.write("No games today")
    else:
        for game in game_data:
            away_team_abbrev = game["awayTeam"]["teamTricode"]
            home_team_abbrev = game["homeTeam"]["teamTricode"]

            away_team_score = game["awayTeam"]["score"]
            home_team_score = game["homeTeam"]["score"]

            period = game['period']
            game_clock = game['gameClock']

            gameStatusText = game["gameStatusText"]

            if "ET" in gameStatusText:
                render_future_game(away_team_abbrev, home_team_abbrev, away_team_score, home_team_score, gameStatusText)
            else:
                render_game_score(away_team_abbrev, home_team_abbrev, away_team_score, home_team_score, period, game_clock, gameStatusText)
            st.divider()
    
def render_sidebar(page_name):
    loc(page_name)
    st.toast("Please excuse the slow speeds, Streamlit's community cloud heavily limits compute.\n I'm working on some optimizations.", icon="⏱️")
    with st.sidebar:
        st.subheader("Games Today")
        try:
            initial_visit = True
            refresh = st.button("Refresh")
        
            if refresh or initial_visit:
                render_todays_games()
                if initial_visit:
                    initial_visit = False
        except:
            st.text("The NBA's website is blocking my requests right now.")
        
     
        
    
