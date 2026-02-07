import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Field Mapper", layout="wide")

st.title("📍 Field Photo Mapper")

# 1. SIMPLE UPLOADER
uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])

if uploaded_file:
    # Read data
    df = pd.read_csv(uploaded_file)
    
    # --- THE "NO-FAIL" RENAME ---
    # We rename columns by their POSITION (0, 1, 2)
    # This ignores whatever names are actually in the file
    try:
        df.columns.values[0] = "ticket"
        df.columns.values[1] = "lat"
        df.columns.values[2] = "lon"
        
        # Force to numbers
        df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
        df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
        df = df.dropna(subset=['lat', 'lon'])
        
        st.success(f"✅ Loaded {len(df)} Pins")

        # 2. THE MAP
        # Center on the first valid pin
        m = folium.Map(location=[df['lat'].iloc[0], df['lon'].iloc[0]], zoom_start=12)
        
        for _, row in df.iterrows():
            folium.Marker(
                [row['lat'], row['lon']], 
                popup=str(row['ticket'])
            ).add_to(m)
        
        st_folium(m, width="100%", height=600)
        
    except Exception as e:
        st.error(f"Mapping failed. Error: {e}")
        st.write("Current Columns:", list(df.columns))
else:
    st.info("Please upload your CSV in the sidebar.")