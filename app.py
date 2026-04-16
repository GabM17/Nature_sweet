import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(layout="wide", page_title="Dashboard NatureSweet")

st.title("📊 Dashboard de Ventas")

# ==============================
# 1. Cargar archivo
# ==============================
uploaded_file = st.file_uploader("Sube tu archivo de Excel (Base de Datos Agrupada)", type=["xlsx"])

if uploaded_file is not None:
    try:
        # Cargamos el archivo
        df = pd.read_excel(uploaded_file, sheet_name="Agrupado")
        
        # ==============================
        # 2. Limpieza básica
        # ==============================
        df.columns = df.columns.str.strip()
        df["Fecha"] = pd.to_datetime(df["Fecha"], dayfirst=True)

        # ==============================
        # 3. Sidebar filtros
        # ==============================
        st.sidebar.header("Filtros")

        metrica = st.sidebar.radio(
            "Selecciona la métrica:",
            ["Cajas", "Pesos"],
            horizontal=True
        )

        col_ventas = "Ventas en cajas" if metrica == "Cajas" else "Ventas en Pesos"
        titulo = "cajas" if metrica == "Cajas" else "pesos"

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

        # Rango de fechas
        min_fecha = df["Fecha"].min()
        max_fecha = df["Fecha"].max()
        rango_fecha = st.sidebar.date_input("Rango de fechas", [min_fecha, max_fecha])

        # ==============================
        # 4. Aplicar filtros
        # ==============================
        df_filtrado = df.copy()

        if cliente:
            df_filtrado = df_filtrado[df_filtrado["CLIENTE"].isin(cliente)]
        if cedis:
            df_filtrado = df_filtrado[df_filtrado["CEDIS"].isin(cedis)]
        if producto:
            df_filtrado = df_filtrado[df_filtrado["PRODUCTO"].isin(producto)]
        
        # Validar que el rango de fechas tenga inicio y fin antes de filtrar
        if len(rango_fecha) == 2:
            df_filtrado = df_filtrado[
                (df_filtrado["Fecha"] >= pd.to_datetime(rango_fecha[0])) &
                (df_filtrado["Fecha"] <= pd.to_datetime(rango_fecha[1]))
            ]

        # ==============================
        # 5. Visualización (KPIs y Gráficos)
        # ==============================
        col1, col2, col3 = st.columns(3)
        col1.metric(f"Ventas totales ({titulo})", f"{int(df_filtrado[col_ventas].sum()):,}")
        col2.metric("Clientes únicos", df_filtrado["CLIENTE"].nunique())
        col3.metric("Productos únicos", df_filtrado["PRODUCTO"].nunique())

        # Ventas por MES
        df_filtrado["MES"] = df_filtrado["Fecha"].dt.to_period("M").dt.to_timestamp()
        ventas_mes = df_filtrado.groupby("MES")[col_ventas].sum().reset_index()
        fig = px.line(ventas_mes, x="MES", y=col_ventas, markers=True, title=f"Ventas mensuales ({titulo})")
        st.plotly_chart(fig, use_container_width=True)

        # Ventas por producto
        ventas_mes_producto = df_filtrado.groupby(["MES", "PRODUCTO"])[col_ventas].sum().reset_index()
        fig3 = px.line(ventas_mes_producto, x="MES", y=col_ventas, color="PRODUCTO", title=f"Ventas por producto")
        st.plotly_chart(fig3, use_container_width=True)

        # Ranking CEDIS con Mapa
        st.subheader("🗺️ Análisis por CEDIS")
        
        ciudades_coords = {
            "TIJUANA": (32.5149, -117.0382), "CULIACÁN": (24.8091, -107.3940),
            "GUADALAJARA": (20.6597, -103.3496), "ESTADO DE MÉXICO": (19.4969, -99.7233),
            "VILLAHERMOSA": (17.9892, -92.9475), "HERMOSILLO": (29.0729, -110.9559),
            "MONTERREY": (25.6866, -100.3161), "TEPEJI": (19.9040, -99.3420),
            "CIUDAD DE MÉXICO": (19.4326, -99.1332), "DURANGO": (24.0277, -104.6532),
            "CIUDAD JUÁREZ": (31.6904, -106.4245), "REYNOSA": (26.0927, -98.2773)
        }

        df_filtrado["LAT"] = df_filtrado["CEDIS"].map(lambda x: ciudades_coords.get(x, (None, None))[0])
        df_filtrado["LON"] = df_filtrado["CEDIS"].map(lambda x: ciudades_coords.get(x, (None, None))[1])

        mapa_df = df_filtrado.groupby(["CEDIS", "LAT", "LON"])[col_ventas].sum().reset_index()
        
        fig_map = px.density_mapbox(mapa_df, lat="LAT", lon="LON", z=col_ventas, radius=35,
                                    center=dict(lat=23, lon=-102), zoom=4,
                                    mapbox_style="carto-positron", title="Mapa de Calor")
        st.plotly_chart(fig_map, use_container_width=True)

        st.subheader("📋 Datos filtrados")
        st.dataframe(df_filtrado)

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("Por favor, sube el archivo de Excel para comenzar.")
