import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os

st.set_page_config(page_title="Troy's Map", layout="centered")

SAVED_DATA = "permanent_work_log.csv"

if 'df' not in st.session_state:
    st.title("🛰️ Troy's Fielding Tool")
    
    if os.path.exists(SAVED_DATA):
        st.session_state.df = pd.read_csv(SAVED_DATA)
        st.rerun()

    uploaded_file = st.file_uploader("Upload CSV (Ticket, Lat, Lon, Notes)", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        
        # Standardize names
        df.columns.values[0] = 'Ticket'
        df.columns.values[1] = 'lat'
        df.columns.values[2] = 'lon'
        if len(df.columns) >= 4:
            df.columns.values[3] = 'Notes'
        else:
            df['Notes'] = "No notes."

        # THE FIX: Force Lat/Lon to numbers and drop broken rows
        df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
        df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
        df = df.dropna(subset=['lat', 'lon'])
            
        df['status'] = 'Pending'
        st.session_state.df = df
        df.to_csv(SAVED_DATA, index=False)
        st.rerun()
    st.stop()

df = st.session_state.df

# --- 3. THE MAP ---
# Safety check: if no valid coordinates, don't crash
if not df.empty:
    avg_lat = df['lat'].mean()
    avg_lon = df['lon'].mean()
    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=13, tiles="OpenStreetMap")

    for i, row in df.iterrows():
        t_id = str(row['Ticket'])
        is_sel = (st.session_state.get('selected_id') == t_id)
        color = "orange" if is_sel else ("green" if row['status'] == 'Completed' else "blue")
        
        folium.Marker(
            [row['lat'], row['lon']],
            popup=f"ID:{t_id}",
            icon=folium.Icon(color=color, icon="camera")
        ).add_to(m)

    st.subheader("Field Map")
    map_data = st_folium(m, height=350, width=None, key="troy_map")

    # --- 4. DETAILS & NOTES ---
    if map_data and map_data.get("last_object_clicked_popup"):
        t_id = map_data["last_object_clicked_popup"].split(":")[1]
        st.session_state.selected_id = t_id
        
        sel = df[df['Ticket'].astype(str) == t_id].iloc[0]
        st.markdown(f"### 📍 Site: {t_id}")
        
        # DISPLAY NOTES HERE
        st.info(f"📝 **Field Notes:**\n\n{sel['Notes']}")

        nav_url = f"google.navigation:q={sel['lat']},{sel['lon']}"
        st.link_button("🚗 Start Google Maps Nav", nav_url, use_container_width=True)
        
        if st.button("✅ Confirm Completion", use_container_width=True):
            st.session_state.df.loc[st.session_state.df['Ticket'].astype(str) == t_id, 'status'] = 'Completed'
            st.session_state.df.to_csv(SAVED_DATA, index=False)
            st.rerun()
else:
    st.error("No valid GPS coordinates found in your CSV. Please check columns 2 and 3.")

if st.sidebar.button("🗑️ Reset Day"):
    if os.path.exists(SAVED_DATA): os.remove(SAVED_DATA)
    st.session_state.clear()
    st.rerun()
