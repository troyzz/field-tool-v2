import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os
import zipfile
from io import BytesIO

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Troy's Fielding Tool", page_icon="🛰️", layout="wide")

# This is the "Ghost File" that usually lives on the server's hidden memory
SAVED_DATA = "permanent_work_log.csv"

if 'all_photos' not in st.session_state:
    st.session_state.all_photos = {}
if 'selected_id' not in st.session_state:
    st.session_state.selected_id = None

# --- 2. DATA LOADING (Force Reset Version) ---
# If the phone is crashing, we want to clear the 'df' from memory
if 'df' not in st.session_state:
    # Try to load, but if it fails or doesn't exist, we move to Uploader
    if os.path.exists(SAVED_DATA):
        try:
            st.session_state.df = pd.read_csv(SAVED_DATA)
        except:
            if os.path.exists(SAVED_DATA): os.remove(SAVED_DATA)
    
    if 'df' not in st.session_state:
        st.title("📂 Upload Your Daily Route")
        st.write("Please upload your 4-column CSV (Ticket, Lat, Lon, Notes) to begin.")
        uploaded_file = st.file_uploader("Choose CSV File", type=["csv"])
        
        if uploaded_file:
            try:
                raw_df = pd.read_csv(uploaded_file).dropna(how='all')
                clean_df = pd.DataFrame()
                
                # Assign columns by position to avoid header naming issues
                clean_df['Ticket'] = raw_df.iloc[:, 0].astype(str)
                clean_df['lat'] = pd.to_numeric(raw_df.iloc[:, 1], errors='coerce')
                clean_df['lon'] = pd.to_numeric(raw_df.iloc[:, 2], errors='coerce')
                clean_df['Notes'] = raw_df.iloc[:, 3].fillna("No notes.") if len(raw_df.columns) >= 4 else "No notes."
                
                clean_df = clean_df.dropna(subset=['lat', 'lon'])
                clean_df['status'] = 'Pending'
                
                st.session_state.df = clean_df
                clean_df.to_csv(SAVED_DATA, index=False)
                st.rerun()
            except Exception as e:
                st.error(f"CSV Error: {e}")
        st.stop() # Prevents the rest of the app from running until CSV is uploaded

# Shortcut for the data
df = st.session_state.df

# --- 3. THE SIDEBAR ---
st.sidebar.title("🔍 Search & Tools")
search_query = st.sidebar.text_input("Enter Ticket Number")

if st.sidebar.button("🗑️ RESET ALL DATA"):
    if os.path.exists(SAVED_DATA): os.remove(SAVED_DATA)
    st.session_state.clear()
    st.rerun()

# --- 4. MAP LOGIC ---
m = folium.Map()

if search_query:
    match = df[df['Ticket'].astype(str).str.contains(search_query, na=False)]
    if not match.empty:
        st.session_state.selected_id = str(match.iloc[0]['Ticket'])
        m = folium.Map(location=[match.iloc[0]['lat'], match.iloc[0]['lon']], zoom_start=18)
else:
    sw, ne = df[['lat', 'lon']].min().values.tolist(), df[['lat', 'lon']].max().values.tolist()
    m.fit_bounds([sw, ne])

folium.TileLayer(
    tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attr='Esri', name='Satellite', overlay=False
).add_to(m)

for _, row in df.iterrows():
    t_id = str(row['Ticket'])
    is_sel = (t_id == str(st.session_state.selected_id))
    color = "orange" if is_sel else ("green" if row['status'] == 'Completed' else "blue")
    folium.Marker(
        [row['lat'], row['lon']], 
        icon=folium.Icon(color=color, icon="camera" if not is_sel else "star")
    ).add_to(m)

st.title("🛰️ Troy's Fielding Tool")
map_data = st_folium(m, width=None, height=450, key="main_map")

# --- 5. SITE DETAILS ---
if st.session_state.selected_id:
    t_id = st.session_state.selected_id
    sel_row = df[df['Ticket'].astype(str) == t_id].iloc[0]
    
    st.markdown(f"### 📍 Site: {t_id}")
    st.info(f"**Notes:** {sel_row['Notes']}")
    
    col1, col2 = st.columns(2)
    with col1:
        nav_url = f"https://www.google.com/maps/dir/?api=1&destination={sel_row['lat']},{sel_row['lon']}&travelmode=driving"
        st.link_button("🚗 Start Nav", nav_url, use_container_width=True)
    with col2:
        if st.button("✅ Mark Complete", use_container_width=True):
            st.session_state.df.loc[st.session_state.df['Ticket'].astype(str) == t_id, 'status'] = 'Completed'
            st.session_state.selected_id = None
            st.session_state.df.to_csv(SAVED_DATA, index=False)
            st.rerun()

    st.file_uploader("📸 Upload Photos", accept_multiple_files=True, key=f"photo_{t_id}")

# --- 6. EXPORT ---
st.sidebar.markdown("---")
if st.session_state.all_photos:
    st.sidebar.subheader("📦 Export")
    # (ZIP logic would go here if needed, keeping it light for the test)
