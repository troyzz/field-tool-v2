import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os

st.set_page_config(page_title="Field Mapper PRO", layout="wide")

# --- 1. DATA & PHOTO STORAGE ---
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

# Dictionary to store photos: { "Ticket_123": [photo1, photo2] }
if 'photo_storage' not in st.session_state:
    st.session_state.photo_storage = {}

if 'selected_id' not in st.session_state:
    st.session_state.selected_id = None

df = st.session_state.df

# --- 2. THE MAP ---
st.title("🛰️ Field Navigator & Gallery")
v_lat, v_lon = df['lat'].mean(), df['lon'].mean()
m = folium.Map(location=[v_lat, v_lon], zoom_start=14)
folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                 attr='Esri', name='Satellite', overlay=False).add_to(m)

for _, row in df.iterrows():
    t_id = str(row['Ticket'])
    is_sel = (t_id == str(st.session_state.selected_id))
    color = "orange" if is_sel else ("green" if row['status'] == 'Completed' else "blue")
    icon = "star" if is_sel else ("check" if row['status'] == 'Completed' else "camera")
    
    folium.Marker([row['lat'], row['lon']], popup=f"ID:{t_id}",
                  icon=folium.Icon(color=color, icon=icon)).add_to(m)

map_data = st_folium(m, width=None, height=450, returned_objects=["last_object_clicked_popup"], key="pro_map")

# --- 3. HANDLE CLICKS & SIDEBAR ---
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
    
    st.sidebar.write("---")
    
    # MULTI-PHOTO UPLOAD
    # accept_multiple_files=True allows you to pick several from your gallery
    uploaded_photos = st.sidebar.file_uploader("Upload Site Photos", 
                                              type=["jpg", "png", "jpeg"], 
                                              accept_multiple_files=True,
                                              key=f"files_{t_id}")
    
    if uploaded_photos:
        st.session_state.photo_storage[t_id] = uploaded_photos
        st.sidebar.success(f"{len(uploaded_photos)} photo(s) linked to Ticket {t_id}")
        # Show mini-previews with the new names
        for i, p in enumerate(uploaded_photos):
            st.sidebar.image(p, caption=f"Saved as: {t_id}_{i+1}.jpg", width=150)

    if st.sidebar.button("✅ Confirm Site Completion"):
        st.session_state.df.loc[st.session_state.df['Ticket'].astype(str) == t_id, 'status'] = 'Completed'
        st.session_state.selected_id = None
        st.rerun()

# --- 4. END OF DAY EXPORT ---
st.sidebar.write("---")
if st.sidebar.button("💾 Export Work Log (CSV)"):
    df.to_csv("completed_work.csv", index=False)
    st.sidebar.success("Work log saved!")
