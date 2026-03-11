import math
import re
import unicodedata

import pandas as pd
import streamlit as st
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Mapa Restaurantes Calgary", layout="wide")
st.title("Mapa Restaurantes - Potencial (Heatmap)")

CSV_PATH = "restaurantes_calgary_api.csv"

# =========================
# HELPERS
# =========================
def norm_text_series(s: pd.Series) -> pd.Series:
    s = s.fillna("").astype(str)
    s = s.map(lambda x: unicodedata.normalize("NFKD", x).encode("ascii", "ignore").decode("ascii"))
    s = s.str.lower().str.strip()
    s = s.str.replace(r"\s+", " ", regex=True)
    return s

GENERIC_TIPO_RE = re.compile(r"^\s*(?:restaurant|food|food court|bar|bistro|fine dining)\s*$", re.I)

ASIAN_RE = re.compile(
    r"\b(?:asian fusion|asian|chinese|szechuan|sichuan|cantonese|dim sum|hot pot|noodle|ramen|udon|pho|pad thai|thai|vietnamese|korean|japanese|sushi|izakaya|yakitori|bibimbap)\b",
    re.I,
)
INDIAN_RE = re.compile(
    r"\b(?:indian|hindu|curry|tandoor|tandoori|biryani|masala|naan|dosa|vindaloo|paneer)\b",
    re.I,
)
CHAIN_RE = re.compile(
    r"\b(?:mcdonald'?s|burger king|chipotle|domino'?s|pizza hut|kfc|subway|starbucks|tim hortons|wendy'?s|a&w|five guys|taco bell|popeyes|dairy queen)\b",
    re.I,
)

# =========================
# LOAD CSV
# =========================
df = pd.read_csv(CSV_PATH)
df.columns = [c.strip().lower() for c in df.columns]

rename_map = {
    "dirección": "direccion",
    "address": "direccion",
    "lat": "latitud",
    "latitude": "latitud",
    "lng": "longitud",
    "lon": "longitud",
    "longitude": "longitud",
    "reviews": "num_resenas",
    "review_count": "num_resenas",
    "review count": "num_resenas",
}
df = df.rename(columns=rename_map)

for col, default in {
    "nombre": "Sin nombre",
    "direccion": "",
    "latitud": None,
    "longitud": None,
    "zona": "Unknown",
    "rating": 0.0,
    "num_resenas": 0,
    "estatus": "prospecto",
    "tipo_cocina": "",
}.items():
    if col not in df.columns:
        df[col] = default

df["latitud"] = pd.to_numeric(df["latitud"], errors="coerce")
df["longitud"] = pd.to_numeric(df["longitud"], errors="coerce")
df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0.0)
df["num_resenas"] = pd.to_numeric(df["num_resenas"], errors="coerce").fillna(0).astype(int)

df["zona"] = df["zona"].astype(str).str.strip()
df["estatus"] = df["estatus"].astype(str).str.strip().str.lower()
df["tipo_cocina"] = df["tipo_cocina"].astype(str)

df = df.dropna(subset=["latitud", "longitud"]).copy()

# =========================
# FLAGS
# =========================
tn = norm_text_series(df["tipo_cocina"])
nn = norm_text_series(df["nombre"])
generic_tipo = tn.str.match(GENERIC_TIPO_RE) | (tn == "")

df["flag_asian"] = tn.str.contains(ASIAN_RE, na=False) | (generic_tipo & nn.str.contains(ASIAN_RE, na=False))
df["flag_indian"] = tn.str.contains(INDIAN_RE, na=False) | (generic_tipo & nn.str.contains(INDIAN_RE, na=False))
df["flag_chain"] = nn.str.contains(CHAIN_RE, na=False)

# =========================
# SCORE
# =========================
df["score"] = (
    (df["estatus"].eq("prospecto")).astype(int) * 1.0
    + 0.2 * df["rating"]
    + 0.3 * df["num_resenas"].apply(lambda x: math.log1p(max(int(x), 0)))
)

zona_scores = (
    df.groupby("zona", as_index=False)
    .agg(
        score_zona=("score", "sum"),
        prospectos=("estatus", lambda s: (s == "prospecto").sum()),
        total=("estatus", "count"),
    )
    .sort_values("score_zona", ascending=False)
)

st.subheader("Top zonas por potencial (score)")
st.dataframe(zona_scores.head(15), width="stretch")

# =========================
# SIDEBAR
# =========================
st.sidebar.header("Filtros")

zonas_all = sorted(df["zona"].unique().tolist())
estatus_all = sorted(df["estatus"].unique().tolist())

zonas = st.sidebar.multiselect("Zona", options=zonas_all, default=zonas_all)
estatus_filtro = st.sidebar.multiselect(
    "Estatus",
    options=estatus_all,
    default=["prospecto"] if "prospecto" in estatus_all else estatus_all,
)

rating_floor = float(df["rating"].min()) if len(df) else 0.0
rating_ceiling = float(df["rating"].max()) if len(df) else 5.0
rating_floor = round(rating_floor, 1)
rating_ceiling = round(rating_ceiling, 1)

rating_min = st.sidebar.slider(
    "Rating mínimo",
    min_value=rating_floor,
    max_value=rating_ceiling,
    value=rating_floor,
    step=0.1,
)

resenas_min = st.sidebar.slider("N° reseñas mínimo", 0, int(df["num_resenas"].max() or 5000), 0)

show_points = st.sidebar.checkbox("Mostrar puntos", value=True)
show_heat = st.sidebar.checkbox("Mostrar heatmap", value=True)

ex_asian = st.sidebar.checkbox("Excluir Asian/Chinese (difícil)", value=False)
ex_indian = st.sidebar.checkbox("Excluir Indian/Hindu (difícil)", value=False)
show_chains = st.sidebar.checkbox("Mostrar cadenas (solo puntos)", value=False)

# =========================
# FILTERED DATA
# =========================
df_base = df[
    (df["zona"].isin(zonas)) &
    (df["estatus"].isin(estatus_filtro)) &
    (df["rating"] >= rating_min) &
    (df["num_resenas"] >= resenas_min)
].copy()

# Heatmap: siempre sin cadenas
df_heat = df_base[~df_base["flag_chain"]].copy()
if ex_asian:
    df_heat = df_heat[~df_heat["flag_asian"]]
if ex_indian:
    df_heat = df_heat[~df_heat["flag_indian"]]

# Puntos normales
df_points = df_base[~df_base["flag_chain"]].copy()

if ex_asian:
    df_points = df_points[~df_points["flag_asian"]]

if ex_indian:
    df_points = df_points[~df_points["flag_indian"]]

# Cadenas solo si activas checkbox
df_chains = df_base[df_base["flag_chain"]].copy() if show_chains else df_base.iloc[0:0].copy()

if ex_asian:
    df_chains = df_chains[~df_chains["flag_asian"]]

if ex_indian:
    df_chains = df_chains[~df_chains["flag_indian"]]

st.caption(
    f"Base: {len(df_base)} | Heatmap usa: {len(df_heat)} | "
    f"Puntos visibles: {len(df_points)} | Cadenas visibles: {len(df_chains)}"
)

# =========================
# MAP
# =========================
m = folium.Map(
    location=[51.0447, -114.0719],
    zoom_start=12,
    tiles="cartodbpositron",
    control_scale=True,
)

# Heatmap
if show_heat and len(df_heat) > 0:
    heat_data = [[r.latitud, r.longitud, float(r.score)] for r in df_heat.itertuples()]
    HeatMap(
        heat_data,
        name="Heatmap potencial",
        radius=18,
        blur=22,
        min_opacity=0.2,
        max_zoom=13,
    ).add_to(m)

# Puntos normales
if show_points and len(df_points) > 0:
    for _, r in df_points.iterrows():
        popup = f"""
        <b>{r.get('nombre','')}</b><br>
        {r.get('direccion','')}<br>
        <b>Zona:</b> {r.get('zona','')}<br>
        <b>Estatus:</b> {r.get('estatus','')}<br>
        <b>Tipo:</b> {r.get('tipo_cocina','')}<br>
        <b>Rating:</b> {r.get('rating',0)} | <b>Reseñas:</b> {r.get('num_resenas',0)}<br>
        <b>Score:</b> {round(float(r.get('score',0)), 2)}
        """
        folium.CircleMarker(
            location=[r["latitud"], r["longitud"]],
            radius=5,
            fill=True,
            fill_opacity=0.7,
            popup=folium.Popup(popup, max_width=350),
        ).add_to(m)

# Cadenas
if show_points and len(df_chains) > 0:
    for _, r in df_chains.iterrows():
        popup = f"""
        <b>[CADENA] {r.get('nombre','')}</b><br>
        {r.get('direccion','')}<br>
        <b>Zona:</b> {r.get('zona','')}<br>
        <b>Estatus:</b> {r.get('estatus','')}<br>
        <b>Tipo:</b> {r.get('tipo_cocina','')}<br>
        <b>Rating:</b> {r.get('rating',0)} | <b>Reseñas:</b> {r.get('num_resenas',0)}<br>
        <b>Score:</b> {round(float(r.get('score',0)), 2)}
        """
        folium.CircleMarker(
            location=[r["latitud"], r["longitud"]],
            radius=6,
            fill=True,
            fill_opacity=0.9,
            color="black",
            weight=2,
            popup=folium.Popup(popup, max_width=350),
        ).add_to(m)

folium.LayerControl(collapsed=True).add_to(m)

# SOLO un render
st_folium(m, width="stretch", height=720, key="mapa")