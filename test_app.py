import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="TEST", layout="wide")
st.title("TEST: st_folium SIN GeoJSON")

df = pd.read_csv("restaurantes_calgary_api.csv")
df.columns = [c.strip().lower() for c in df.columns]

rename_map = {
    "dirección":"direccion", "address":"direccion",
    "lat":"latitud", "latitude":"latitud",
    "lng":"longitud", "lon":"longitud", "longitude":"longitud",
}
df = df.rename(columns=rename_map)

df["latitud"] = pd.to_numeric(df.get("latitud"), errors="coerce")
df["longitud"] = pd.to_numeric(df.get("longitud"), errors="coerce")
df = df.dropna(subset=["latitud","longitud"])

st.write("Filas con coords:", len(df))

m = folium.Map(location=[51.0447, -114.0719], zoom_start=12, tiles="cartodbpositron")

# 100 puntos max para que sea liviano
for _, r in df.head(100).iterrows():
    folium.CircleMarker(
        location=[r["latitud"], r["longitud"]],
        radius=4,
        fill=True,
        popup=str(r.get("nombre","")),
    ).add_to(m)

st_folium(m, use_container_width=True, height=720, key="test_map")
