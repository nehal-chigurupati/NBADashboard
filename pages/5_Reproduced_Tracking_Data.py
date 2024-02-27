import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import tempfile
import subprocess
import sys
from pages.components.sidebar import *
from pages.src.CourtVision.TrackProcessing import get_track_data, process_colors
from pages.src.CourtVision.TrackCollection import generate_tracking_data
from st_aggrid import AgGrid

st.set_page_config(layout="wide")
render_sidebar()

@st.cache_data(show_spinner=False, experimental_allow_widgets=True)
def analyze_video(video_buffer, video_out_path):
    #Save video file (streamlit has a weird buffer format)
    tfile = tempfile.NamedTemporaryFile(delete=False)
    tfile.write(video_buffer.read())
    return generate_tracking_data(tfile.name, with_video=True, video_out_path=video_out_path)

def display_json_data(json_out, display):
    if display:
        out_df = get_track_data(json_out)
        if out_df is not None:
            AgGrid(out_df[["TRACK_NUM", "X", "Y", "FRAME_NUM", "MODE_TEAM_ABBREV"]])

def convert_to_h264(input_path, output_path):
    # Load the video clip
    clip = VideoFileClip(input_path)

    # Set the codec to H.264
    codec = "libx264"

    # Write the video with the specified codec
    clip.write_videofile(output_path, codec=codec)

st.text("Note: I'm still improving these models. The current iteration tends to lose track of players behind screens.")
st.title("Reproduced Tracking Data")


st.subheader("Step 1: Upload Video")
centers = None
json_out = None
df = None
# Upload video file
video_file = st.file_uploader("Upload an MP4 file of game footage. The process works best on footage of singular possessions", type=["mp4"])
# Check if a video file is uploaded
if video_file is not None:
    # Display video information
    with st.expander("Original Video"):
        st.text(f"Filename: {video_file.name}")
        st.video(video_file)

    video_out_path="pages/src/CourtVision/temp_out_vid.mp4"
    json_out = analyze_video(video_file, video_out_path=video_out_path)
    data, centers, model = process_colors(json_out, 2)

if json_out is not None:

    st.subheader("Step 2: Associate jersey colors with teams")
    colors = np.array([centers[0], centers[1]]) / 255.0  # Normalize RGB values to [0, 1]
    plt.imshow([colors])
    plt.axis('off')
    st.pyplot(plt)

    label1 = st.selectbox(label="Enter a label for the left color: ", options=nba_team_abbreviations, index=None)

    if label1:
        label2 = st.selectbox(label="Enter a label for the right color: ", options=[i for i in nba_team_abbreviations if i != label1], index=None)

    if label1 and label2:
        team_df = pd.DataFrame({"TEAM_ABBREV": [label1, label2], "CLUSTER": [0, 1]})
        df = data.merge(team_df, on="CLUSTER")
        df['MODE_TEAM_ABBREV'] = df.groupby('TRACK_NUM')['TEAM_ABBREV'].transform(lambda x: x.mode().iloc[0])

        st.subheader("Step 3: Download Output")
        with open(video_out_path, "rb") as file:
            btn = st.download_button(
                label="Download Video",
                data=file,
                file_name="tracking.mp4"
            )
            st.video(file)
        st.dataframe(df[["CLUSTER", "TRACK_NUM", "X", "Y", "FRAME_NUM", "MODE_TEAM_ABBREV"]], use_container_width=True)