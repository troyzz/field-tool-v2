import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os

st.set_page_config(page_title="Troy's Map", layout="centered")

SAVED_DATA = "permanent_work_log.csv"

# Initialize photo storage in session if not there
if 'all_photos' not in st.session_state:
    st.session_state.all_photos = {}

if 'df' not in st.session_state:
    st.title("🛰️ Troy's Fielding Tool")
    if os.path.exists(SAVED_DATA):
        st.session_state.df = pd.read_csv(SAVED_DATA)
        st.rerun()

    uploaded_file = st.file_uploader("Upload CSV (Ticket, Lat, Lon, Notes)", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        df.columns.values[0] = 'Ticket'
        df.columns.values[1] = 'lat'
        df.columns.values[2] = 'lon'
        df.columns.values[3] = 'Notes' if len(df.columns) >= 4 else 'Notes'
        if 'Notes' not in df.columns: df['Notes'] = "No notes."
        
        df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
        df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
        df = df.dropna(subset=['lat', 'lon'])
        df['status'] = 'Pending'
        st.session_state.df = df
        df.to_csv(SAVED_DATA, index=False)
        st.rerun()
    st.stop()

df = st.session_state.df

# --- THE MAP ---
avg_lat, avg_lon = df['lat'].mean(), df['lon'].mean()
m = folium.Map(location=[avg_lat, avg_lon], zoom_start=13, tiles="OpenStreetMap")

for i, row in df.iterrows():
    t_id = str(row['Ticket'])
    # Highlight logic
    is_sel = (str(st.session_state.get('selected_id')) == t_id)
    color = "orange" if is_sel else ("green" if row['status'] == 'Completed' else "blue")
    
    folium.Marker(
        [row['lat'], row['lon']],
        popup=f"ID:{t_id}",
        icon=folium.Icon(color=color, icon="camera" if not is_sel else "star")
    ).add_to(m)

st.subheader("Field Map")
# Returned_objects=['last_object_clicked_popup'] is what triggers the refresh
map_data = st_folium(m, height=350, width=None, key="troy_map", returned_objects=["last_object_clicked_popup"])

# --- SELECTION LOGIC ---
if map_data and map_data.get("last_object_clicked_popup"):
    clicked_id = map_data["last_object_clicked_popup"].split(":")[1]
    if str(st.session_state.get('selected_id')) != clicked_id:
        st.session_state.selected_id = clicked_id
        st.rerun()

# --- DETAILS, NOTES & CAMERA ---
if st.session_state.get('selected_id'):
    t_id = st.session_state.selected_id
    sel = df[df['Ticket'].astype(str) == t_id].iloc[0]
    
    st.divider()
    st.markdown(f"### 📍 Site: {t_id}")
    st.info(f"📝 **Field Notes:**\n\n{sel['Notes']}")

    # NAV BUTTON
    nav_url = f"google.navigation:q={sel['lat']},{sel['lon']}"
    st.link_button("🚗 Start Google Maps Nav", nav_url, use_container_width=True)
    
    # CAMERA / UPLOAD SECTION
    st.markdown("#### 📸 Capture Photos")
    photos = st.file_uploader("Tap to take photo or upload", accept_multiple_files=True, key=f"cam_{t_id}")
    if photos:
        st.session_state.all_photos[t_id] = photos
        st.success(f"Captured {len(photos)} photos for this site.")

    # COMPLETION BUTTON
    if st.button("✅ Confirm Completion", use_container_width=True):
        st.session_state.df.loc[st.session_state.df['Ticket'].astype(str) == t_id, 'status'] = 'Completed'
        st.session_state.selected_id = None # Deselect after finishing
        st.session_state.df.to_csv(SAVED_DATA, index=False)
        st.rerun()

if st.sidebar.button("🗑️ Reset Day"):
    if os.path.exists(SAVED_DATA): os.remove(SAVED_DATA)
    st.session_state.clear()
    st.rerun()
