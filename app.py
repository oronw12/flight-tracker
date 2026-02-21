import streamlit as st
import requests
import pandas as pd
import pydeck as pdk

st.set_page_config(layout="wide", page_title="Live Flight Tracker")

@st.cache_data(ttl=15)
def fetch_flight_data():
    url = "https://opensky-network.org/api/states/all"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        columns = [
            "icao24", "callsign", "origin_country", "time_position", "last_contact", 
            "longitude", "latitude", "baro_altitude", "on_ground", "velocity", 
            "true_track", "sensors", "geo_altitude", "squawk", "spi", "position_source"
        ]
        df = pd.DataFrame(data['states'], columns=columns)
        
        df = df.dropna(subset=['longitude', 'latitude', 'true_track'])
        df = df[df['on_ground'] == False]
        
        # בניית מילון הגדרות האייקון לכל שורה (נדרש על ידי PyDeck IconLayer)
        # שימוש באייקון מטוס גנרי מ-Wikimedia המצביע צפונה (0 מעלות)
        icon_data = {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/17/Plane_icon_nose_up.svg/512px-Plane_icon_nose_up.svg.png",
            "width": 512,
            "height": 512,
            "anchorY": 256
        }
        df['icon_data'] = [icon_data] * len(df)
        
        # המרת True Track לזווית ש-Deck.GL מבין.
        # באווירונאוטיקה 90 מעלות זה מזרח (בכיוון השעון). Deck.GL לרוב מצפה לזווית זהה, 
        # אך במקרה של סטייה תלוי באייקון - לעיתים נדרש להכפיל במינוס או להוסיף אופסט.
        df['angle'] = df['true_track'] 
        
        return df
    except Exception as e:
        st.error(f"API Error: {e}")
        return pd.DataFrame()

st.title("Global Flight Tracker - Live")

df = fetch_flight_data()

if not df.empty:
    st.write(f"Active flights tracked: {len(df)}")
    
    # החלפת ScatterplotLayer ב-IconLayer
    layer = pdk.Layer(
        type='IconLayer',
        data=df,
        get_icon='icon_data',
        get_size=4,
        size_scale=15,
        get_position='[longitude, latitude]',
        get_angle='angle', 
        get_color='[255, 200, 0, 255]', # צבע צהוב בולט על מפה כהה
        pickable=True
    )
    
    view_state = pdk.ViewState(
        latitude=32.0,
        longitude=34.8,
        zoom=5,
        pitch=45 # זווית ראייה תלת ממדית
    )
    
    r = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        map_style='mapbox://styles/mapbox/dark-v10',
        tooltip={"text": "Callsign: {callsign}\nCountry: {origin_country}\nAltitude: {baro_altitude}m\nSpeed: {velocity}m/s\nHeading: {true_track}°"}
    )
    
    st.pydeck_chart(r)
    
    if st.button("Refresh"):
        st.rerun()
