import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os

st.set_page_config(page_title="Field Mapper PRO", layout="wide")

# --- 1. DATA LOADING ---
uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])

if uploaded_file:
    try:
        # Read the file
        df = pd.read_csv(uploaded_file)
        
        # CLEANING: Remove any rows that are completely empty
        df = df.dropna(how='all')
        
        # POSITION FIX: Force the first 3 columns to be our data
        df.columns.values[0] = "Ticket"
        df.columns.values[1] = "lat"
        df.columns.values[2] = "lon"
        
        # CONVERT TO NUMBERS: This is the critical part
        df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
        df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
        
        # DROP BAD DATA: Remove rows where Lat or Lon failed to convert
        df = df.dropna(subset=['lat', 'lon'])
        
        if df.empty:
            st.error("Wait! After cleaning, no valid coordinates were found. Check your CSV format.")
            st.stop()

        st.sidebar.success(f"Loaded {len(df)} locations!")
        st.sidebar.write("Preview:", df[['Ticket', 'lat', 'lon']].head(3))
        
        # --- 2. THE MAP ---
        st.title("🛰️ Satellite Field View")
        
        # Center the map on the first pin
        m = folium.Map(location=[df['lat'].iloc[0], df['lon'].iloc[0]], zoom_start=15)
        
        # Add Satellite Layer
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Satellite',
            overlay=False
        ).add_to(m)

        for _, row in df.iterrows():
            folium.Marker(
                [row['lat'], row['lon']],
                popup=f"Ticket: {row['Ticket']}",
                icon=folium.Icon(color="blue", icon="info-sign")
            ).add_to(m)

        st_folium(m, width="100%", height=600)

    except Exception as e:
        st.error(f"Critical Error: {e}")
else:
    st.info("Please upload your CSV file in the sidebar to begin.")
