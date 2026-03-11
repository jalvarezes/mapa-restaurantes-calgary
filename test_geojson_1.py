import json
import streamlit as st
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="TEST GEOJSON 1", layout="wide")
st.title("TEST: st_folium + GeoJSON (1 feature)")

with open("community_boundaries.geojson", "r", encoding="utf-8") as f:
    geo = json.load(f)

# agarramos SOLO 1 feature para que sea liviano
one = {"type": "FeatureCollection", "features": [geo["features"][0]]}

m = folium.Map(location=[51.0447, -114.0719], zoom_start=12, tiles="cartodbpositron")

# OJO: SIN tooltip (porque el tooltip vacío puede romper el JS)
folium.GeoJson(
    one,
    name="one",
    style_function=lambda feature: {
        "fillColor": "purple",
        "color": "purple",
        "weight": 2,
        "fillOpacity": 0.25,
    },
).add_to(m)

folium.LayerControl().add_to(m)

st_folium(m, use_container_width=True, height=720, key="geo1")
