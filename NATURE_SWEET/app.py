import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(layout="wide")

st.title("📊 Dashboard de Ventas")

# ==============================
# Cargar archivo
# ==============================




# 1. Obtenemos la ruta absoluta de la carpeta donde está este script (app.py)
# Esto resuelve el problema de las subcarpetas en Streamlit Cloud
base_path = os.path.dirname(__file__)

# 2. Construimos la ruta al Excel de forma dinámica
file_path = os.path.join(base_path, "Base de Datos NatureSweet Agrupada.xlsx")

# 3. Cargamos el archivo
try:
    df = pd.read_excel(file_path, sheet_name="Agrupado")
except FileNotFoundError:
    # Este bloque es por si acaso algo falla, para que la app te diga qué ve el servidor
    import streamlit as st
    st.error(f"No encontré el archivo en: {file_path}")
    st.write("Archivos disponibles en esta carpeta:", os.listdir(base_path))
df = pd.read_excel(file_path, sheet_name="Agrupado")

# ==============================
# Limpieza básica
# ==============================
df.columns = df.columns.str.strip()
df["Fecha"] = pd.to_datetime(df["Fecha"], dayfirst=True)


# ==============================
# Sidebar filtros
# ==============================
st.sidebar.header("Filtros")

st.sidebar.markdown("Cajas o en Pesos")
metrica = st.radio(
    "Selecciona la métrica:",
    ["Cajas", "Pesos"],
    horizontal=True
)

if metrica == "Cajas":
    col_ventas = "Ventas en cajas"
    titulo = "cajas"
else:
    col_ventas = "Ventas en Pesos"
    titulo = "pesos"

cliente = st.sidebar.multiselect(
    "Cliente",
    options=sorted(df["CLIENTE"].dropna().unique()),
    placeholder="Selecciona cliente(s)"
)

cedis = st.sidebar.multiselect(
    "CEDIS",
    options=sorted(df["CEDIS"].dropna().unique()),
    placeholder="Selecciona CEDIS"
)

producto = st.sidebar.multiselect(
    "Producto",
    options=sorted(df["PRODUCTO"].dropna().unique()),
    placeholder="Selecciona producto(s)"
)

fecha = st.sidebar.date_input(
    "Rango de fechas",
    [df["Fecha"].min(), df["Fecha"].max()]
)

# ==============================
# Aplicar filtros
# ==============================
df_filtrado = df.copy()

if cliente:
    df_filtrado = df_filtrado[df_filtrado["CLIENTE"].isin(cliente)]

if cedis:
    df_filtrado = df_filtrado[df_filtrado["CEDIS"].isin(cedis)]

if producto:
    df_filtrado = df_filtrado[df_filtrado["PRODUCTO"].isin(producto)]

df_filtrado = df_filtrado[
    (df_filtrado["Fecha"] >= pd.to_datetime(fecha[0])) &
    (df_filtrado["Fecha"] <= pd.to_datetime(fecha[1]))
]

# ==============================
# KPIs
# ==============================
col1, col2, col3 = st.columns(3)

col1.metric(
    f"Ventas totales ({titulo})",
    f"{int(df_filtrado[col_ventas].sum()):,}"
)

col2.metric(
    "Clientes únicos",
    df_filtrado["CLIENTE"].nunique()
)

col3.metric(
    "Productos únicos",
    df_filtrado["PRODUCTO"].nunique()
)

# ==============================
# Ventas por MES
# ==============================
df_filtrado["MES"] = df_filtrado["Fecha"].dt.to_period("M").dt.to_timestamp()

ventas_mes = (
    df_filtrado
    .groupby("MES")[col_ventas]
    .sum()
    .reset_index()
)

fig = px.line(
    ventas_mes,
    x="MES",
    y=col_ventas,
    markers=True,
    title=f"Ventas mensuales ({titulo})"
)

st.plotly_chart(fig, use_container_width=True)

# ==============================
# Ventas por producto en el tiempo
# ==============================
ventas_mes_producto = (
    df_filtrado
    .groupby(["MES", "PRODUCTO"])[col_ventas]
    .sum()
    .reset_index()
)

fig3 = px.line(
    ventas_mes_producto,
    x="MES",
    y=col_ventas,
    color="PRODUCTO",
    title=f"Ventas mensuales por producto ({titulo})"
)

st.plotly_chart(fig3, use_container_width=True)

# ==============================
# Top productos
# ==============================
top_productos = (
    df_filtrado.groupby("PRODUCTO")[col_ventas]
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
)

fig2 = px.bar(
    top_productos,
    x="PRODUCTO",
    y=col_ventas,
    title=f"Top 10 Productos ({titulo})"
)

st.plotly_chart(fig2, use_container_width=True)

# ==============================
# Ranking CEDIS
# ==============================
st.subheader("🏆 Ranking de CEDIS")

ranking_cedis = (
    df_filtrado
    .groupby("CEDIS")[col_ventas]
    .sum()
    .sort_values(ascending=False)
    .reset_index()
)

total = ranking_cedis[col_ventas].sum()
ranking_cedis["% Participación"] = (ranking_cedis[col_ventas] / total * 100).round(2)

fig4 = px.bar(
    ranking_cedis.head(10),
    x="CEDIS",
    y=col_ventas,
    text="% Participación",
    title=f"Top 10 CEDIS ({titulo})"
)

st.plotly_chart(fig4, use_container_width=True)
# ==============================
# MAPA DE CALOR GEOESPACIAL
# ==============================
st.subheader("🗺️ Mapa de calor por CEDIS")

# Coordenadas de ciudades
ciudades_coords = {
    "TIJUANA": (32.5149, -117.0382),
    "CULIACÁN": (24.8091, -107.3940),
    "GUADALAJARA": (20.6597, -103.3496),
    "ESTADO DE MÉXICO": (19.4969, -99.7233),
    "VILLAHERMOSA": (17.9892, -92.9475),
    "HERMOSILLO": (29.0729, -110.9559),
    "MONTERREY": (25.6866, -100.3161),
    "TEPEJI": (19.9040, -99.3420),
    "CIUDAD DE MÉXICO": (19.4326, -99.1332),
    "DURANGO": (24.0277, -104.6532),
    "CIUDAD JUÁREZ": (31.6904, -106.4245),
    "REYNOSA": (26.0927, -98.2773)
}

# Mapear coordenadas
df_filtrado["LAT"] = df_filtrado["CEDIS"].map(lambda x: ciudades_coords.get(x, (None, None))[0])
df_filtrado["LON"] = df_filtrado["CEDIS"].map(lambda x: ciudades_coords.get(x, (None, None))[1])

# Agrupar por ciudad
mapa_df = (
    df_filtrado
    .groupby(["CEDIS", "LAT", "LON"])[col_ventas]
    .sum()
    .reset_index()
)

# Heatmap
fig_map = px.density_mapbox(
    mapa_df,
    lat="LAT",
    lon="LON",
    z=col_ventas,
    radius=35,
    center=dict(lat=23, lon=-102),
    zoom=4,
    mapbox_style="carto-positron",
    title=f"Mapa de calor de ventas ({titulo})"
)

st.plotly_chart(fig_map, use_container_width=True)
# ==============================
# Tabla
# ==============================
st.subheader("📋 Datos filtrados")
st.dataframe(df_filtrado)
