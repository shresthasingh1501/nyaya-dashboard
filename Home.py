import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from folium import IFrame
import pydeck as pdk
import numpy as np
import plotly.express as px
import os
import csv
from PIL import Image
import google.generativeai as genai
import google.ai.generativelanguage as glm
	
API_KEY = 'AIzaSyAv7RXj23iVkQ6ZMjbTLLu5v1-_J1v09vY'
genai.configure(api_key=API_KEY)

# Set page configuration
st.set_page_config(
    page_title="Nyaya Vikas Project Verification",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Function to create the CSV file if it doesn't exist
def create_csv_if_not_exists(file_path='map.csv'):
    if not os.path.exists(file_path):
        columns = [
            'project_name', 'project_status', 'project_description',
            'ai_review', 'ai_reason', 'latitude', 'longitude', 'image_path'
        ]
        df = pd.DataFrame(columns=columns)
        df.to_csv(file_path, index=False)

# Call the function to ensure the CSV file exists
create_csv_if_not_exists()

def load_data():
    data = pd.read_csv('map.csv')
    return data

data = load_data()

# Ensure ai_review column is of type string
if not data.empty:
    data['ai_review'] = data['ai_review'].astype(str)
    data['project_status'] = data['project_status'].astype(float)

# Sidebar with statistics
st.sidebar.header("Statistics")
if not data.empty:
    st.sidebar.metric("Total Projects", len(data))
    verified_count = data[data['ai_review'] == '1'].shape[0]
    unverified_count = data[data['ai_review'] != '1'].shape[0]
    st.sidebar.metric("Verified Projects", verified_count)
    st.sidebar.metric("Unverified Projects", unverified_count)

st.sidebar.header("Contact")
st.sidebar.info(
    """
    **Contact Us:**
    [Email](mailto:shelp-nyayavikas@gov.in) | [Website](https://bhuvan-nyayavikas.nrsc.gov.in/dashboard/index.php)
    """
)

# Function to create a 2D Folium map
def create_folium_map(data):
    m = folium.Map(location=[20.5937, 78.9629], zoom_start=5)
    for i, row in data.iterrows():
        html = f"""
        <div id="popup-{i}" style="width: 300px; height: 200px;">
            <strong>Project Name:</strong> {row['project_name']}<br>
            <strong>Project Status:</strong> {row['project_status']}%<br>
            <strong>AI Review:</strong> {'Qualified' if row['ai_review'] == '1' else 'Disqualified'}<br>
            <strong>AI Reason:</strong> {row['ai_reason']}
        </div>
        """
        iframe = IFrame(html, width=300, height=200)
        popup = folium.Popup(iframe, max_width=300)
        color = 'blue' if row['ai_review'] == '1' else 'red'
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=popup,
            tooltip=row['project_name'],
            icon=folium.Icon(color=color)
        ).add_to(m)
    return m

# Function to create a 3D PyDeck map
def create_pydeck_map(data):
    view_state = pdk.ViewState(
        latitude=np.mean(data['latitude']),
        longitude=np.mean(data['longitude']),
        zoom=5,
        pitch=50,
    )
    layer = pdk.Layer(
        'ColumnLayer',
        data=data,
        get_position=['longitude', 'latitude'],
        get_elevation='project_status',
        height=200,
        width=1000,
        elevation_scale=100,
        radius=100,
        get_fill_color=['ai_review == "1" ? 0 : 255', 'ai_review == "1" ? 0 : 0', 'ai_review == "1" ? 255 : 0'],
        pickable=True,
        auto_highlight=True,
    )
    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={
            'html': '<b>Project Name:</b> {project_name}<br><b>Claimed Project Status:</b> {project_status}%<br><b>AI Review:</b> {ai_review}',
            'style': {'color': 'white'}
        }
    )
    return deck

# Toggle for map type
map_type = st.sidebar.radio("Select Map Type", ("2D Map", "3D Map"))

# Main content
st.title("Nyaya Vikas AI Verification System")

# Create two columns for the map and the graphs
col1, col2 = st.columns([3, 1])

# Display map in the first column
with col1:
    if map_type == "2D Map":
        m = create_folium_map(data)
        folium_static(m, width=1000, height=950)
    else:
        deck = create_pydeck_map(data)
        st.pydeck_chart(deck, use_container_width=True)

# Display graphs in the second column
with col2:
    st.subheader("Project Verification Status")
    fig = px.pie(
        names=['Qualified', 'Disqualified'],
        values=[verified_count, unverified_count],
        color=['blue', 'red']
    )
    fig.update_traces(marker=dict(colors=['blue', 'red']))
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Project Status Distribution")
    st.bar_chart(data['project_status'])

# Legend at the bottom of the sidebar
st.sidebar.markdown("""
<style>
.legend {
    border: 1px solid #ccc;
    padding: 10px;
    font-size: 14px;
    color: black;
    background-color: white;
}
.legend i {
    width: 18px;
    height: 18px;
    float: left;
    margin-right: 8px;
    opacity: 0.7;
}
</style>
<div class="legend">
    <div><i style="background: blue"></i>Qualified</div>
    <div><i style="background: red"></i>Disqualified</div>
</div>
""", unsafe_allow_html=True)

