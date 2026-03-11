import streamlit as st
import folium
from streamlit_folium import st_folium

st.title("TEST MAP")

m = folium.Map(location=[51.0447, -114.0719], zoom_start=12)

folium.CircleMarker(
    location=[51.0447, -114.0719],
    radius=8,
    popup="Calgary test"
).add_to(m)

st_folium(m, use_container_width=True, height=700)

