import streamlit as st
import pandas as pd
import numpy as np
from nba_api.stats.static import teams
from nba_api.stats.endpoints import shotchartlineupdetail, teamdashlineups
import matplotlib as mpl
import matplotlib.pyplot as plt
import urllib.request
from PIL import Image
import plotly.graph_objects as go
st.set_page_config(layout="wide")

st.text("***** IN PROGRESS ******")

def load_image_from_github(url):
    with urllib.request.urlopen(url) as response:
        image = Image.open(response)
    return image

class ShotCharts:
        def __init__(self) -> None:
                pass
        
        def create_court(ax: mpl.axes, color="white") -> mpl.axes:
                """ Create a basketball court in a matplotlib axes
                """
                # Short corner 3PT lines
                ax.plot([-220, -220], [0, 140], linewidth=2, color=color)
                ax.plot([220, 220], [0, 140], linewidth=2, color=color)
                # 3PT Arc
                ax.add_artist(mpl.patches.Arc((0, 140), 440, 315, theta1=0, theta2=180, facecolor='none', edgecolor=color, lw=2))
                # Lane and Key
                ax.plot([-80, -80], [0, 190], linewidth=2, color=color)
                ax.plot([80, 80], [0, 190], linewidth=2, color=color)
                ax.plot([-60, -60], [0, 190], linewidth=2, color=color)
                ax.plot([60, 60], [0, 190], linewidth=2, color=color)
                ax.plot([-80, 80], [190, 190], linewidth=2, color=color)
                ax.add_artist(mpl.patches.Circle((0, 190), 60, facecolor='none', edgecolor=color, lw=2))
                ax.plot([-250, 250], [0, 0], linewidth=4, color='white')
                # Rim
                ax.add_artist(mpl.patches.Circle((0, 60), 15, facecolor='none', edgecolor=color, lw=2))
                # Backboard
                ax.plot([-30, 30], [40, 40], linewidth=2, color=color)
                # Remove ticks
                ax.set_xticks([])
                ax.set_yticks([])
                # Set axis limits
                ax.set_xlim(-250, 250)
                ax.set_ylim(0, 470)
                return ax
        
        
        def frequency_chart(df: pd.DataFrame, name: str, season=None, extent=(-250, 250, 422.5, -47.5),
                                gridsize=25, cmap="viridis"):
                """ Create a shot chart of a player's shot frequency and accuracy
                """ 
                # create frequency of shots per hexbin zone
                shots_hex = plt.hexbin(
                df.LOC_X, df.LOC_Y + 60,
                extent=extent, cmap=cmap, gridsize=gridsize)
                plt.close()
                shots_hex_array = shots_hex.get_array()
                freq_by_hex = shots_hex_array / sum(shots_hex_array)
                
                # create field goal % per hexbin zone
                makes_df = df[df.SHOT_MADE_FLAG == 1] # filter dataframe for made shots
                makes_hex = plt.hexbin(makes_df.LOC_X, makes_df.LOC_Y + 60, cmap=cmap,
                                gridsize=gridsize, extent=extent) # create hexbins
                plt.close()
                pcts_by_hex = makes_hex.get_array() / shots_hex.get_array()
                pcts_by_hex[np.isnan(pcts_by_hex)] = 0  # convert NAN values to 0
                
                # filter data for zone with at least 5 shots made
                sample_sizes = shots_hex.get_array()
                filter_threshold = 5
                for i in range(len(pcts_by_hex)):
                        if sample_sizes[i] < filter_threshold:
                                pcts_by_hex[i] = 0
                x = [i[0] for i in shots_hex.get_offsets()]
                y = [i[1] for i in shots_hex.get_offsets()]
                z = pcts_by_hex
                sizes = freq_by_hex * 1000
                
                # Create figure and axes
                fig = plt.figure(figsize=(3.6, 3.6), facecolor='black', edgecolor='black', dpi=100)
                ax = fig.add_axes([0, 0, 1, 1], facecolor='black')
                plt.xlim(250, -250)
                plt.ylim(-47.5, 422.5)
                # Plot hexbins
                scatter = ax.scatter(x, y, c=z, cmap=cmap, marker='h', s=sizes)
                # Draw court
                ax = ShotCharts.create_court(ax)
                # Add legends
                max_freq = max(freq_by_hex)
                max_size = max(sizes)
                legend_acc = plt.legend(
                *scatter.legend_elements(num=5, fmt="{x:.0f}%",
                                        func=lambda x: x * 100),
                loc=[0.85,0.785], title='Shot %', fontsize=6)
                legend_freq = plt.legend(
                *scatter.legend_elements(
                        'sizes', num=5, alpha=0.8, fmt="{x:.1f}%"
                        , func=lambda s: s / max_size * max_freq * 100
                ),
                loc=[0.68,0.785], title='Freq %', fontsize=6)
                plt.gca().add_artist(legend_acc)
                # Add title
                plt.text(-250, 420, "Frequency and FG%", fontsize=12, color='white',
                        fontname='Franklin Gothic Book')
                season = f"{season[0][:4]}-{season[-1][-2:]}"
                plt.text(-250, -20, season, fontsize=8, color='white')
                

                return fig
        
        def volume_chart(df: pd.DataFrame, name: str, season=None, 
                        RA=True,
                        extent=(-250, 250, 422.5, -47.5),
                        gridsize=25, cmap="plasma"):
                fig = plt.figure(figsize=(3.6, 3.6), facecolor='black', edgecolor='black', dpi=100)
                ax = fig.add_axes([0, 0, 1, 1], facecolor='black')

                # Plot hexbin of shots
                if RA == True:
                        x = df.LOC_X
                        y = df.LOC_Y + 60
                        # Annotate player name and season
                        season = f"{season[0][:4]}-{season[-1][-2:]}"
                        plt.text(-250, -20, season, fontsize=8, color='white')
                else:
                        cond = ~((-45 < df.LOC_X) & (df.LOC_X < 45) & (-40 < df.LOC_Y) & (df.LOC_Y < 45))
                        x = df.LOC_X[cond]
                        y = df.LOC_Y[cond] + 60
                        # Annotate player name and season
                        plt.text(-250, 410, "Shot Volume", fontsize=12, color='white',
                                fontname='Franklin Gothic Book')
                        plt.text(-250, 385, "(w/o restricted area)", fontsize=10, color='red')
                        season = f"{season[0][:4]}-{season[-1][-2:]}"
                        plt.text(-250, -20, season, fontsize=8, color='white')
                        
                hexbin = ax.hexbin(x, y, cmap=cmap,
                        bins="log", gridsize=25, mincnt=2, extent=(-250, 250, 422.5, -47.5))

                # Draw court
                ax = ShotCharts.create_court(ax, 'white')

                # add colorbar
                im = load_image_from_github("https://github.com/ubiratanfilho/HotShot/blob/main/images/Colorbar%20Shotcharts.png?raw=true")
                newax = fig.add_axes([0.56, 0.6, 0.45, 0.4], anchor='NE', zorder=1)
                newax.xaxis.set_visible(False)
                newax.yaxis.set_visible(False)
                newax.imshow(im)
                

                return fig
        
        def makes_misses_chart(df: pd.DataFrame, name: str, season=None):
                # Create figure and axes
                fig = plt.figure(figsize=(3.6, 3.6), facecolor='black', edgecolor='black', dpi=100)
                ax = fig.add_axes([0, 0, 1, 1], facecolor='black')

                plt.text(-250, 425, "Misses", fontsize=12, color='red',
                        fontname='Franklin Gothic Book')
                plt.text(-170, 425, "&", fontsize=12, color='white',
                        fontname='Franklin Gothic Book')
                plt.text(-150, 425, "Buckets", fontsize=12, color='green',
                        fontname='Franklin Gothic Book')
                season = f"{season[0][:4]}-{season[-1][-2:]}"
                plt.text(-250, -20, season, fontsize=8, color='white')

                ax = ShotCharts.create_court(ax, 'white')
                sc = ax.scatter(df.LOC_X, df.LOC_Y + 60, c=df.SHOT_MADE_FLAG, cmap='RdYlGn', s=12)
                

                return fig

def load_eppm_data():
    data = pd.read_csv("pages/lineup_evals_10_min.csv", engine="pyarrow")

    return data[["LINEUP_ID", "PLAYER_NAMES", "E_VAL_PER_MIN", "PTS_PER_MIN"]]

def compare_league_average_shot_data(shot_data, league_avg_data):
    shot_point_vals = shot_data[["SHOT_TYPE", "SHOT_MADE_FLAG"]]
    shot_point_vals["SHOT_TYPE"] = shot_point_vals["SHOT_TYPE"].str[0].astype(int)

    three_p_att = shot_point_vals[shot_point_vals["SHOT_TYPE"] == 3]
    two_p_att = shot_point_vals[shot_point_vals["SHOT_TYPE"] == 2]

    three_p_m = three_p_att[three_p_att["SHOT_MADE_FLAG"] == 1]
    two_p_m = two_p_att[two_p_att["SHOT_MADE_FLAG"] == 1]

    league_avg_vals = league_avg_data[["SHOT_TYPE", "SHOT_MADE_FLAG"]]
    league_avg_vals["SHOT_TYPE"] = league_avg_vals["SHOT_TYPE"].str[0].astype(int)

    return None


    
          
def get_all_lineup_strings(eppm_data):
    lineup_strings = eppm_data["PLAYER_NAMES"].tolist()
    lineup_ids = eppm_data[["PLAYER_NAMES", "LINEUP_ID"]]
    cleaned = [i.replace("'","") for i in lineup_strings]
    lineup_ids["PLAYER_NAMES"] = cleaned
    return cleaned, lineup_ids

def get_lineup_id_from_players(player_string, lineup_ids):
    matches = lineup_ids[lineup_ids["PLAYER_NAMES"] == player_string]
    if len(matches) == 0:
        raise Exception("No matching lineup")
    else:
        return matches["LINEUP_ID"].tolist()[0]
    
def load_all_team_abbrevs():
    all_teams = teams.get_teams()

    return [i["abbreviation"] for i in all_teams]

def render_team_person_selection():
    eppm_data = load_eppm_data()
    lineup_options, lineup_ids = get_all_lineup_strings(eppm_data)
    lineup_options.append("All")
    lineup = st.selectbox("Lineup: ", lineup_options, index=len(lineup_options)-1)

    return lineup, eppm_data, lineup_ids

def render_all_lineups(eppm_data):
    st.header("All Lineups")
    eppm_data = load_eppm_data()
    st.subheader("Expected Point Production")
    render_combined_histogram_no_highlight(eppm_data)
    st.write(eppm_data)

def get_lineup_shot_data(lineup_id):
    data = shotchartlineupdetail.ShotChartLineupDetail(context_measure_detailed="PTS", group_id=lineup_id, season="2023-24")

    return data.get_data_frames()[0], data.get_data_frames()[1]

def render_shot_data(lineup_string, lineup_id, shot_data):
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Shot Volume")
        chart1 = ShotCharts.volume_chart(shot_data, lineup_string, ["2023-24"])
        st.pyplot(chart1)
    with col2:
        st.subheader("Raw Shot Data")
        st.write(shot_data)

def render_lineup_eppm(lineup_id, eppm_data):
    matching_val = eppm_data[eppm_data["LINEUP_ID"] == lineup_id]["E_VAL_PER_MIN"]

    if len(matching_val) == 0:
        st.text("No data available for this lineup.")
    else:
        highlight_value = matching_val.tolist()[0]

        fig = go.Figure()
        data = eppm_data["E_VAL_PER_MIN"]
        fig.add_trace(go.Histogram(x=data, nbinsx=30, marker_color='green', opacity=0.7, name='# Lineups'))
        fig.add_trace(go.Scatter(x=[highlight_value, highlight_value], y=[0, max(np.histogram(data, bins=10)[0])],
                                mode='lines', name='Lineup ePPM', line=dict(color='red', dash='dash', width=2)))

        fig.update_layout(title_text='Distribution of estimated points per minute (ePPM) relative to league average', xaxis_title='ePPM', yaxis_title='# of lineups',
                        showlegend=True)

    # Display the figure
    st.plotly_chart(fig, use_container_width=True)

def render_lineup_ppm(lineup_id, eppm_data):
    matching_val = eppm_data[eppm_data["LINEUP_ID"] == lineup_id]["E_VAL_PER_MIN"]
    if len(matching_val) == 0:
        st.text("No data available for this lineup.")
    else:
        highlight_value = matching_val.tolist()[0]

        fig = go.Figure()
        data = eppm_data["PTS_PER_MIN"]
        fig.add_trace(go.Histogram(x=data, nbinsx=30, marker_color='green', opacity=0.7, name='# Lineups'))
        fig.add_trace(go.Scatter(x=[highlight_value, highlight_value], y=[0, max(np.histogram(data, bins=10)[0])],
                                mode='lines', name='Lineup PPM', line=dict(color='red', dash='dash', width=2)))

        fig.update_layout(title_text='Distribution of points per minute (PPM)', xaxis_title='PPM', yaxis_title='# of lineups',
                        showlegend=True)

    # Display the figure
    st.plotly_chart(fig, use_container_width=True)
    
def render_combined_histogram(lineup_id, lineup_string, eppm_data):
    fig = go.Figure()

    for metric_column, color, highlight_color, title, xaxis_title in [("E_VAL_PER_MIN", 'blue', 'red', 'ePPM', 'ePPM'),
                                                                       ("PTS_PER_MIN", 'green', 'orange', 'PPM', 'PPM')]:
        matching_val = eppm_data[eppm_data["LINEUP_ID"] == lineup_id][metric_column]

        if len(matching_val) == 0:
            st.text(f"No data available for {title} in this lineup.")
        else:
            highlight_value = matching_val.tolist()[0]

            data = eppm_data[metric_column]
            fig.add_trace(go.Histogram(x=data, nbinsx=30, marker_color=color, opacity=0.7, name=f'{title} - All Lineups'))
            fig.add_trace(go.Scatter(x=[highlight_value, highlight_value], y=[0, max(np.histogram(data, bins=10)[0])],
                                    mode='lines', name=f'{title} - Lineup', line=dict(color=highlight_color, dash='dash', width=2)))

    fig.update_layout(title_text='Distribution of points per minute and estimated points per minute relative to league average', xaxis_title='Metric Values',
                      yaxis_title='# of lineups', showlegend=True)

    # Display the figure
    st.plotly_chart(fig, use_container_width=True)

def render_combined_histogram_no_highlight(eppm_data):
    fig = go.Figure()

    for metric_column, color, title, xaxis_title in [("E_VAL_PER_MIN", 'blue', 'ePPM', 'ePPM'),
                                                      ("PTS_PER_MIN", 'green', 'PPM', 'PPM')]:
        data = eppm_data[metric_column]
        fig.add_trace(go.Histogram(x=data, nbinsx=30, marker_color=color, opacity=0.7, name=f'{title} - All Lineups'))

    fig.update_layout(title_text='Distribution of ePPM and PPM relative to league average', xaxis_title='Metric Values',
                      yaxis_title='# of lineups', showlegend=True)

    # Display the figure
    st.plotly_chart(fig, use_container_width=True)


st.header("Lineup Dashboard")

lineup, eppm_data, lineup_ids = render_team_person_selection()

if lineup == "All":
    render_all_lineups(eppm_data)
else:
    lineup_id = get_lineup_id_from_players(lineup, lineup_ids)
    shot_data, league_avg_data = get_lineup_shot_data(lineup_id)

    st.header("Expected Point Production")
    render_combined_histogram(lineup_id, lineup, eppm_data)

    render_shot_data(lineup, lineup_id, shot_data)


