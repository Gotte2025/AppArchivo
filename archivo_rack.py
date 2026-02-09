import streamlit as st
import pandas as pd
import math

st.set_page_config(layout="wide")

st.title("📦 Sistema de Archivo por Rack")

# ================= CONFIGURACIÓN FÍSICA =================

COMPROBANTES_POR_CAJA = 300
POSICIONES_POR_NIVEL = 10
NIVELES_POR_RACK = 5

CAJAS_POR_LADO_RACK = POSICIONES_POR_NIVEL * NIVELES_POR_RACK
CAPACIDAD_LADO = CAJAS_POR_LADO_RACK * COMPROBANTES_POR_CAJA
CAPACIDAD_TOTAL_RACK = CAPACIDAD_LADO * 2

# ================= CARGA DE ARCHIVO =================

archivo = st.file_uploader(
    "Subí el Excel / CSV de comprobantes",
    type=["xlsx","xlsm","csv"]
)

if archivo:

    # Leer archivo
    if archivo.name.endswith(".csv"):
        df = pd.read_csv(archivo)
    else:
        df = pd.read_excel(archivo)

    df = df.iloc[:, :2]
    df.columns = ["numero","tipo"]

    # Filtrar tipos válidos
    df = df[df["tipo"].isin(["PX","PU","PH"])]

    # Separar
    px = df[df["tipo"] == "PX"].sort_values("numero")
    otros = df[df["tipo"].isin(["PU","PH"])].sort_values("numero")

    px = px.reset_index(drop=True)
    otros = otros.reset_index(drop=True)

    # ================= FUNCIÓN UBICAR =================

    def ubicar(df_tipo, lado):

        ubicaciones = []

        for i in range(len(df_tipo)):

            caja_global = i // COMPROBANTES_POR_CAJA

            rack = (caja_global // CAJAS_POR_LADO_RACK) + 1

            dentro_rack = caja_global % CAJAS_POR_LADO_RACK

            nivel = (dentro_rack // POSICIONES_POR_NIVEL) + 1

            posicion = (dentro_rack % POSICIONES_POR_NIVEL) + 1

            ubicaciones.append([
                rack,
                nivel,
                posicion,
                lado,
                caja_global + 1
            ])

        return pd.DataFrame(
            ubicaciones,
            columns=[
                "rack","nivel","posicion","lado","caja"
            ]
        )

    # Asignar ubicaciones
    if len(px) > 0:
        px[[
            "rack","nivel","posicion","lado","caja"
        ]] = ubicar(px,"Frente")

    if len(otros) > 0:
        otros[[
            "rack","nivel","posicion","lado","caja"
        ]] = ubicar(otros,"Fondo")

    # Unir
    df_final = pd.concat([px,otros])
    df_final = df_final.sort_values(
        ["rack","nivel","posicion","lado"]
    )

    # ================= MÉTRICAS =================

    st.subheader("📊 Capacidad y Proyección")

    racks_px = math.ceil(len(px) / CAPACIDAD_LADO)
    racks_otros = math.ceil(len(otros) / CAPACIDAD_LADO)

    col1,col2,col3 = st.columns(3)

    col1.metric("Racks PX", racks_px)
    col2.metric("Racks PU/PH", racks_otros)
    col3.metric(
        "Capacidad por Rack",
        f"{CAPACIDAD_TOTAL_RACK:,}"
    )

    # ================= BUSCADOR =================

    st.subheader("🔍 Buscar comprobante")

    num_buscar = st.text_input("Número")

    if st.button("Buscar"):

        resultado = df_final[
            df_final["numero"].astype(str) == num_buscar
        ]

        if not resultado.empty:

            r = resultado.iloc[0]

            st.success("Ubicación encontrada")

            c1,c2,c3,c4 = st.columns(4)

            c1.metric("Rack", r["rack"])
            c2.metric("Nivel", r["nivel"])
            c3.metric("Posición", r["posicion"])
            c4.metric("Lado", r["lado"])

        else:
            st.error("No encontrado")

    # ================= RECORRIDO ÓPTIMO =================

    st.subheader("🧭 Recorrido óptimo por lista")

    lista = st.text_area(
        "Pegá números (uno por línea)"
    )

    if st.button("Calcular recorrido"):

        numeros = [
            x.strip()
            for x in lista.split("\n")
            if x.strip() != ""
        ]

        df_busqueda = df_final[
            df_final["numero"].astype(str).isin(numeros)
        ]

        if df_busqueda.empty:

            st.warning("No se encontraron")

        else:

            recorrido = df_busqueda.sort_values(
                by=["rack","nivel","posicion","lado"]
            )

            st.success(
                f"{len(recorrido)} comprobantes encontrados"
            )

            st.dataframe(
                recorrido[
                    [
                        "numero",
                        "tipo",
                        "rack",
                        "nivel",
                        "posicion",
                        "lado"
                    ]
                ]
            )

            csv_recorrido = recorrido.to_csv(
                index=False
            ).encode("utf-8")

            st.download_button(
                "📥 Descargar recorrido",
                csv_recorrido,
                "recorrido_optimo.csv",
                "text/csv"
            )

    # ================= DESCARGA LAYOUT =================

    st.subheader("📥 Descargar layout completo")

    csv_layout = df_final.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "Descargar layout",
        csv_layout,
        "layout_rack.csv",
        "text/csv"
    )
