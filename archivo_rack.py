import streamlit as st
import pandas as pd
import math

st.title("📦 Layout de Archivo por Rack")

# ================= CONFIGURACIÓN =================

COMPROBANTES_POR_CAJA = 300
POSICIONES_POR_NIVEL = 10
NIVELES_POR_RACK = 5

CAJAS_POR_LADO_RACK = POSICIONES_POR_NIVEL * NIVELES_POR_RACK
CAPACIDAD_LADO = CAJAS_POR_LADO_RACK * COMPROBANTES_POR_CAJA

# ================= CARGA =================

archivo = st.file_uploader(
    "Subí el Excel",
    type=["xlsx", "xlsm", "csv"]
)

if archivo:

    if archivo.name.endswith(".csv"):
        df = pd.read_csv(archivo)
    else:
        df = pd.read_excel(archivo)

    df = df.iloc[:, :2]
    df.columns = ["numero", "tipo"]

    # Separar tipos
    px = df[df["tipo"] == "PX"].sort_values("numero")
    otros = df[df["tipo"].isin(["PU", "PH"])].sort_values("numero")

    # ================= FUNCIÓN UBICAR =================

    def ubicar(df_tipo, lado):

        ubicaciones = []

        for i in range(len(df_tipo)):

            caja_global = math.floor(i / COMPROBANTES_POR_CAJA)

            rack = math.floor(
                caja_global / CAJAS_POR_LADO_RACK
            ) + 1

            dentro_rack = caja_global % CAJAS_POR_LADO_RACK

            nivel = math.floor(
                dentro_rack / POSICIONES_POR_NIVEL
            ) + 1

            posicion = (
                dentro_rack % POSICIONES_POR_NIVEL
            ) + 1

            ubicaciones.append([
                rack,
                nivel,
                posicion,
                lado,
                caja_global + 1
            ])

        return ubicaciones

    # Asignar ubicaciones
    px[[
        "rack","nivel","posicion","lado","caja"
    ]] = ubicar(px, "Frente")

    otros[[
        "rack","nivel","posicion","lado","caja"
    ]] = ubicar(otros, "Fondo")

    # Unir
    df_final = pd.concat([px, otros])
    df_final = df_final.sort_values(
        ["rack","nivel","posicion","lado"]
    )

    # ================= RESULTADOS =================

    st.success("Layout generado")

    st.dataframe(df_final.head(50))

    # ================= MÉTRICAS =================

    racks_px = math.ceil(len(px) / CAPACIDAD_LADO)
    racks_otros = math.ceil(len(otros) / CAPACIDAD_LADO)

    st.subheader("📊 Proyección")

    col1, col2 = st.columns(2)

    col1.metric(
        "Racks PX",
        racks_px
    )

    col2.metric(
        "Racks PU/PH",
        racks_otros
    )

    st.metric(
        "Capacidad por Rack",
        f"{CAPACIDAD_LADO*2:,} comprobantes"
    )

    # ================= DESCARGA =================

    csv = df_final.to_csv(index=False).encode("utf-8")

    st.download_button(
        "📥 Descargar layout",
        csv,
        "layout_archivo.csv",
        "text/csv"
    )
