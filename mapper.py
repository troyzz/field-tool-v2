import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os

st.set_page_config(page_title="Field Mapper PRO", layout="wide")

# --- 1. DATA LOADING ---
if 'df' not in st.session_state:
    uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        df.columns.values[0], df.columns.values[1], df.columns.values[2] = "Ticket", "lat", "lon"
        df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
        df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
        df = df.dropna(subset=['lat', 'lon'])
        df['status'] = 'Pending'
        st.session_state.df = df
        st.rerun()
    st.stop()

# Track which pin is currently tapped
if 'selected_id' not in st.session_state:
    st.session_state.selected_id = None

df = st.session_state.df

# --- 2. THE MAP ---
st.title("🛰️ Field Navigator & Mapper")

# Center the map
v_lat, v_lon = df['lat'].mean(), df['lon'].mean()
m = folium.Map(location=[v_lat, v_lon], zoom_start=14)
folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                 attr='Esri', name='Satellite', overlay=False).add_to(m)

for _, row in df.iterrows():
    # COLOR LOGIC: Green if done, Yellow if selected, Blue if pending
    if str(row['Ticket']) == str(st.session_state.selected_id):
        color = "orange" # Yellow/Orange for selection
    else:
        color = "green" if row['status'] == 'Completed' else "blue"
        
    folium.Marker(
        [row['lat'], row['lon']],
        popup=f"ID:{row['Ticket']}",
        icon=folium.Icon(color=color, icon="camera" if color != "orange" else "star")
    ).add_to(m)

map_data = st_folium(m, width=None, height=450, returned_objects=["last_object_clicked_popup"], key="pro_map")

# --- 3. SIDEBAR: NAVIGATION & CAMERA ---
if map_data and map_data.get("last_object_clicked_popup"):
    t_id = map_data["last_object_clicked_popup"].split(":")[1]
    st.session_state.selected_id = t_id # Set the yellow state
    
    row = df[df['Ticket'].astype(str) == t_id].iloc[0]
    
    st.sidebar.markdown(f"## 📍 Site: {t_id}")
    
    # NAVIGATION BUTTON
    # This creates a special link that forces the Google Maps app to open
    nav_url = f"https://www.google.com/maps/dir/?api=1&destination={row['lat']},{row['lon']}&travelmode=driving"
    st.sidebar.link_button("🚗 Open Google Maps Nav", nav_url)
    
    st.sidebar.markdown("---")
    
    # PHOTO LOGIC
    st.sidebar.write("📸 **Take Photo:** Use your native camera app, then upload here for full quality/zoom:")
    uploaded_photo = st.sidebar.file_uploader("Upload Site Photo", type=["jpg", "png", "jpeg"], key=f"file_{t_id}")
    
    if st.sidebar.button("✅ Mark as Completed"):
        st.session_state.df.loc[st.session_state.df['Ticket'].astype(str) == t_id, 'status'] = 'Completed'
        st.session_state.selected_id = None # Clear selection
        st.rerun()

if st.sidebar.button("🗑️ Reset"):
    st.session_state.clear()
    st.rerun()
