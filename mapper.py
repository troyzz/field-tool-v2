import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os
import base64

st.set_page_config(page_title="Field Mapper PRO", layout="wide")

# --- 1. PERSISTENT STORAGE SETUP ---
# We use this file to "resume" work if the app refreshes
SAVED_DATA = "permanent_work_log.csv"

def save_progress():
    st.session_state.df.to_csv(SAVED_DATA, index=False)

# --- 2. DATA LOADING ---
if 'df' not in st.session_state:
    # Check if we have a saved session to resume
    if os.path.exists(SAVED_DATA):
        st.session_state.df = pd.read_csv(SAVED_DATA)
    else:
        uploaded_file = st.sidebar.file_uploader("Upload CSV to Start Day", type=["csv"])
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            df.columns.values[0], df.columns.values[1], df.columns.values[2] = "Ticket", "lat", "lon"
            df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
            df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
            df = df.dropna(subset=['lat', 'lon'])
            df['status'] = 'Pending'
            st.session_state.df = df
            save_progress()
            st.rerun()
        st.stop()

if 'selected_id' not in st.session_state:
    st.session_state.selected_id = None

df = st.session_state.df

# --- 3. THE MAP ---
st.title("🛰️ Field Navigator (Auto-Save ON)")
m = folium.Map(location=[df['lat'].mean(), df['lon'].mean()], zoom_start=14)
folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                 attr='Esri', name='Satellite', overlay=False).add_to(m)

for _, row in df.iterrows():
    t_id = str(row['Ticket'])
    is_sel = (t_id == str(st.session_state.selected_id))
    color = "orange" if is_sel else ("green" if row['status'] == 'Completed' else "blue")
    icon = "star" if is_sel else ("check" if row['status'] == 'Completed' else "camera")
    folium.Marker([row['lat'], row['lon']], popup=f"ID:{t_id}", icon=folium.Icon(color=color, icon=icon)).add_to(m)

map_data = st_folium(m, width=None, height=450, returned_objects=["last_object_clicked_popup"], key="pro_map")

# --- 4. HANDLE CLICKS & SIDEBAR ---
if map_data and map_data.get("last_object_clicked_popup"):
    new_id = map_data["last_object_clicked_popup"].split(":")[1]
    if st.session_state.selected_id != new_id:
        st.session_state.selected_id = new_id
        st.rerun()

if st.session_state.selected_id:
    t_id = st.session_state.selected_id
    sel_row = df[df['Ticket'].astype(str) == t_id].iloc[0]
    
    st.sidebar.header(f"📍 Ticket: {t_id}")
    nav_url = f"https://www.google.com/maps/dir/?api=1&destination={sel_row['lat']},{sel_row['lon']}&travelmode=driving"
    st.sidebar.link_button("🚗 Start Google Maps Nav", nav_url)
    
    uploaded_photos = st.sidebar.file_uploader("Upload Site Photos", accept_multiple_files=True, key=f"files_{t_id}")
    
    if st.sidebar.button("✅ Confirm Site Completion"):
        st.session_state.df.loc[st.session_state.df['Ticket'].astype(str) == t_id, 'status'] = 'Completed'
        st.session_state.selected_id = None
        save_progress() # This saves it to the hard drive
        st.rerun()

# --- 5. END OF DAY RESET ---
st.sidebar.write("---")
if st.sidebar.button("🗑️ Start New Day (Clear All)"):
    if os.path.exists(SAVED_DATA):
        os.remove(SAVED_DATA)
    st.session_state.clear()
    st.rerun()
