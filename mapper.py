import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium, folium_static  # Added folium_static
import os

st.set_page_config(page_title="Field Mapper PRO", layout="wide")

# --- 1. DATA LOADING ---
uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        df.columns.values[0], df.columns.values[1], df.columns.values[2] = "Ticket", "lat", "lon"
        df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
        df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
        df = df.dropna(subset=['lat', 'lon'])

        st.sidebar.success(f"Loaded {len(df)} locations")
        
        # --- 2. MOBILE OPTIMIZATION SETTINGS ---
        st.sidebar.title("📱 Mobile Settings")
        use_static = st.sidebar.checkbox("Use Static Map (Fastest for Phone)", value=False)

        # --- 3. THE MAP ---
        st.title("🛰️ Satellite Field View")
        
        # Center the map
        m = folium.Map(location=[df['lat'].mean(), df['lon'].mean()], zoom_start=13)
        
        # Satellite Layer
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri', name='Satellite', overlay=False
        ).add_to(m)

        for _, row in df.iterrows():
            folium.Marker(
                [row['lat'], row['lon']],
                popup=f"Ticket: {row['Ticket']}",
                icon=folium.Icon(color="blue", icon="info-sign")
            ).add_to(m)

        # --- 4. RENDER LOGIC ---
        if use_static:
            # This is the 'light' version for older phones
            folium_static(m, width=350, height=500)
        else:
            # This is the 'pro' version - width=None is the mobile fix
            st_folium(m, width=None, height=500, key="field_map")

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("Please upload your CSV in the sidebar.")
