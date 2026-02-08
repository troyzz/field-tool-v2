import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os

# 1. SETUP
st.set_page_config(page_title="Troy's Tool", layout="wide")

SAVED_DATA = "permanent_work_log.csv"

# Initialize session states
if 'all_photos' not in st.session_state: st.session_state.all_photos = {}
if 'selected_id' not in st.session_state: st.session_state.selected_id = None

# 2. DATA LOADING
if 'df' not in st.session_state:
    st.title("🛰️ Troy's Fielding Tool")
    if os.path.exists(SAVED_DATA):
        st.session_state.df = pd.read_csv(SAVED_DATA)
        st.rerun()

    uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        # Ensure column naming is consistent
        df.columns.values[0], df.columns.values[1], df.columns.values[2] = 'Ticket', 'lat', 'lon'
        df['Notes'] = df.iloc[:, 3].fillna("No notes.") if len(df.columns) >= 4 else "No notes."
        df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
        df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
        df = df.dropna(subset=['lat', 'lon'])
        df['status'] = 'Pending'
        st.session_state.df = df
        df.to_csv(SAVED_DATA, index=False)
        st.rerun()
    st.stop()

df = st.session_state.df

# 3. THE MAP (Restoring the original working color-change logic)
m = folium.Map(location=[df['lat'].mean(), df['lon'].mean()], zoom_start=13)

for i, row in df.iterrows():
    t_id = str(row['Ticket'])
    # This is the specific logic that makes pins turn orange
    is_sel = (str(st.session_state.selected_id) == t_id)
    color = "orange" if is_sel else ("green" if row['status'] == 'Completed' else "blue")
    
    folium.Marker(
        [row['lat'], row['lon']],
        popup=f"ID:{t_id}",
        icon=folium.Icon(color=color, icon="camera" if not is_sel else "star")
    ).add_to(m)

st.subheader("Field Map")
# THE KEY: 'last_object_clicked_popup' must be in returned_objects for colors to update
map_data = st_folium(m, height=400, width=None, key="troy_map", returned_objects=["last_object_clicked_popup"])

# 4. SELECTION TRIGGER
if map_data and map_data.get("last_object_clicked_popup"):
    clicked_id = map_data["last_object_clicked_popup"].split(":")[1]
    if st.session_state.selected_id != clicked_id:
        st.session_state.selected_id = clicked_id
        st.rerun()

# 5. SIDEBAR: TICKET INFO, CAMERA, AND LARGE NOTES
st.sidebar.title("📍 Site Control")

# Search/Select Box (Restored)
ticket_options = ["Select a Site"] + df['Ticket'].astype(str).tolist()
choice = st.sidebar.selectbox("Search/Pick Ticket", options=ticket_options, index=0)

if choice != "Select a Site" and choice != st.session_state.selected_id:
    st.session_state.selected_id = choice
    st.rerun()

if st.session_state.selected_id:
    t_id = st.session_state.selected_id
    sel = df[df['Ticket'].astype(str) == t_id].iloc[0]
    
    st.sidebar.markdown(f"## Ticket: {t_id}")
    
    # Nav and Camera
    nav_url = f"google.navigation:q={sel['lat']},{sel['lon']}"
    st.sidebar.link_button("🚗 Start Nav", nav_url, use_container_width=True)
    
    # RESTORED CAMERA
    photos = st.sidebar.file_uploader("📸 Capture Photo", accept_multiple_files=True, key=f"cam_{t_id}")
    if photos:
        st.session_state.all_photos[t_id] = photos

    if st.sidebar.button("✅ Confirm Completion", use_container_width=True):
        st.session_state.df.loc[st.session_state.df['Ticket'].astype(str) == t_id, 'status'] = 'Completed'
        st.session_state.selected_id = None
        st.session_state.df.to_csv(SAVED_DATA, index=False)
        st.rerun()

    # LARGE NOTES BOX AT THE BOTTOM
    st.sidebar.markdown("---")
    st.sidebar.subheader("📋 Field Notes")
    st.sidebar.info(sel['Notes'])

st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Reset Day", use_container_width=True):
    if os.path.exists(SAVED_DATA): os.remove(SAVED_DATA)
    st.session_state.clear()
    st.rerun()
