import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium


st.set_page_config(page_title="Mapa Restaurantes Calgary", layout="wide")
st.title("Mapa de Restaurantes - Calgary")

# Cargar datos desde el CSV
df = pd.read_csv("restaurantes.csv")

# Crear mapa centrado en Calgary
m = folium.Map(location=[51.0447, -114.0719], zoom_start=12)

# Agregar marcadores al mapa
for _, row in df.iterrows():
    estatus = str(row["estatus"]).strip().lower()
    color = "green" if estatus == "cliente" else "red"

    notas = str(row.get("notas", "")).strip()

    popup = f"""
    <b>Nombre:</b> {row['nombre']}<br>
    <b>Dirección:</b> {row['direccion']}<br>
    <b>Estatus:</b> {row['estatus']}<br>
    """
    if notas:
        popup += f"<b>Notas:</b> {notas}"

    folium.Marker(
        location=[row["latitud"], row["longitud"]],
        popup=popup,
        icon=folium.Icon(color=color, icon="info-sign")
    ).add_to(m)

# Mostrar el mapa dentro de Streamlit
st_folium(m, width=1200, height=700)

