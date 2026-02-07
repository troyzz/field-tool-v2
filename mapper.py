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

# Initialize selection state
if 'selected_id' not in st.session_state:
    st.session_state.selected_id = None

df = st.session_state.df

# --- 2. THE MAP LOGIC ---
st.title("🛰️ Field Navigator")

# Center calculation
v_lat, v_lon = df['lat'].mean(), df['lon'].mean()
m = folium.Map(location=[v_lat, v_lon], zoom_start=14)
folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                 attr='Esri', name='Satellite', overlay=False).add_to(m)

for _, row in df.iterrows():
    # REFINED COLOR LOGIC
    current_ticket = str(row['Ticket'])
    is_selected = (current_ticket == str(st.session_state.selected_id))
    
    if is_selected:
        color = "orange"  # This is our Yellow/Selection color
        icon_type = "star"
    elif row['status'] == 'Completed':
        color = "green"
        icon_type = "check"
    else:
        color = "blue"
        icon_type = "camera"
        
    folium.Marker(
        [row['lat'], row['lon']],
        popup=f"ID:{current_ticket}",
        icon=folium.Icon(color=color, icon=icon_type)
    ).add_to(m)

# Render Map
map_data = st_folium(m, width=None, height=450, returned_objects=["last_object_clicked_popup"], key="pro_map")

# --- 3. HANDLE CLICKS & SIDEBAR ---
# Check if a new pin was clicked
if map_data and map_data.get("last_object_clicked_popup"):
    new_id = map_data["last_object_clicked_popup"].split(":")[1]
    if st.session_state.selected_id != new_id:
        st.session_state.selected_id = new_id
        st.rerun() # Force the map to redraw with the orange pin

if st.session_state.selected_id:
    t_id = st.session_state.selected_id
    selected_row = df[df['Ticket'].astype(str) == t_id].iloc[0]
    
    st.sidebar.markdown(f"## 📍 Selected: {t_id}")
    
    # NAVIGATION: Direct "Turn-by-Turn" Link
    # This specific format is best for Android/Google Maps App
    nav_url = f"https://www.google.com/maps/dir/?api=1&destination={selected_row['lat']},{selected_row['lon']}&travelmode=driving"
    st.sidebar.link_button("🚗 Start Google Maps Nav", nav_url)
    
    st.sidebar.markdown("---")
    
    # UPLOAD FROM NATIVE CAMERA
    st.sidebar.write("📸 **Capture Site:** Take photo with your phone app, then upload below:")
    uploaded_photo = st.sidebar.file_uploader("Choose Photo", type=["jpg", "jpeg", "png"], key=f"file_{t_id}")
    
    if st.sidebar.button("✅ Confirm Completion"):
        st.session_state.df.loc[st.session_state.df['Ticket'].astype(str) == t_id, 'status'] = 'Completed'
        st.session_state.selected_id = None
        st.rerun()

if st.sidebar.button("🗑️ Reset Map"):
    st.session_state.clear()
    st.rerun()
