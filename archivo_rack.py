import streamlit as st
import pandas as pd
import math

# ================= CONFIGURACIÓN FÍSICA =================
CAPACIDAD_CAJA = 300
CAJAS_POR_NIVEL = 2
NIVELES_POR_RACK = 5
CAJAS_POR_RACK = CAJAS_POR_NIVEL * NIVELES_POR_RACK
COMPS_POR_RACK = CAJAS_POR_RACK * CAPACIDAD_CAJA

# ================= STREAMLIT =================
st.set_page_config(page_title="AppArchivo", layout="wide")
st.title("📦 AppArchivo – Organización de Archivo Físico")
st.caption("Nivel 01 abajo (más pesado / más viejo)")

# ================= CARGA DE EXCEL =================
archivo = st.file_uploader(
    "Subí tu Excel (Col A: Número | Col B: Tipo PX / PU / PH)",
    type=["xlsx", "xlsm"]
)

if archivo is None:
    st.stop()

df = pd.read_excel(archivo)
df = df.iloc[:, :2]
df.columns = ["numero", "tipo"]
df = df[df["tipo"].isin(["PX", "PU", "PH"])]

# ================= ORGANIZACIÓN =================
df = df.sort_values(by=["tipo", "numero"], ascending=[True, True])

registros = []
rack_actual = 1
nivel_actual = 1
caja_en_nivel = 1
contador_caja = 0
caja_id = 1

for _, row in df.iterrows():
    if contador_caja == CAPACIDAD_CAJA:
        contador_caja = 0
        caja_en_nivel += 1
        caja_id += 1

        if caja_en_nivel > CAJAS_POR_NIVEL:
            caja_en_nivel = 1
            nivel_actual += 1

        if nivel_actual > NIVELES_POR_RACK:
            nivel_actual = 1
            rack_actual += 1

    contador_caja += 1

    registros.append({
        "tipo": row["tipo"],
        "numero": row["numero"],
        "rack": f"Rack-{rack_actual}",
        "nivel": nivel_actual,
        "caja": f"Caja-{caja_id:02d}"
    })

df_org = pd.DataFrame(registros)

# ================= RESÚMENES =================
resumen = (
    df_org
    .groupby(["rack", "nivel", "caja"])
    .size()
    .reset_index(name="comprobantes")
    .sort_values(["rack", "nivel", "caja"])
)

racks_necesarios = df_org["rack"].nunique()

# ================= INDICADORES =================
st.subheader("📊 Capacidad")

c1, c2, c3 = st.columns(3)
c1.metric("📄 Comprobantes", len(df_org))
c2.metric("📦 Cajas", df_org["caja"].nunique())
c3.metric("🏗️ Racks", racks_necesarios)

ocupacion = int((len(df_org) / COMPS_POR_RACK) * 100)
st.progress(min(ocupacion / 100, 1.0))

if ocupacion >= 90:
    st.error("🚨 Rack casi lleno – planificar expansión")
elif ocupacion >= 70:
    st.warning("⚠️ Rack al 70% – seguimiento recomendado")
else:
    st.success("✅ Capacidad OK")

# ================= DISTRIBUCIÓN =================
st.subheader("🧱 Distribución por Rack")

for rack in resumen["rack"].unique():
    st.markdown(f"### {rack}")
    rack_df = resumen[resumen["rack"] == rack]

    for nivel in sorted(rack_df["nivel"].unique()):
        nivel_df = rack_df[rack_df["nivel"] == nivel]
        cajas = [
            f"{r['caja']} ({r['comprobantes']})"
            for _, r in nivel_df.iterrows()
        ]
        st.write(f"Nivel {nivel}: " + " | ".join(cajas))

# ================= BÚSQUEDA INDIVIDUAL =================
st.subheader("🔍 Buscar comprobante")

buscar = st.text_input("Número de comprobante")

if buscar:
    res = df_org[df_org["numero"].astype(str) == buscar]
    if not res.empty:
        r = res.iloc[0]
        st.success(
            f"📍 {r['tipo']} {r['numero']} → "
            f"{r['rack']} · Nivel {r['nivel']} · {r['caja']}"
        )
    else:
        st.error("No encontrado")

# ================= BÚSQUEDA MÚLTIPLE =================
st.subheader("🧾 Buscar lista de comprobantes (optimizado)")

lista_txt = st.text_area(
    "Pegá números (uno por línea o separados por coma)",
    height=120
)

if lista_txt:
    lista = lista_txt.replace(",", "\n").splitlines()
    lista = [x.strip() for x in lista if x.strip()]

    encontrados = df_org[df_org["numero"].astype(str).isin(lista)]

    if encontrados.empty:
        st.error("No se encontraron comprobantes")
    else:
        encontrados = encontrados.sort_values(
            by=["rack", "nivel", "caja"]
        )

        st.success(f"Encontrados {len(encontrados)} comprobantes")

        st.dataframe(
            encontrados[["tipo", "numero", "rack", "nivel", "caja"]],
            use_container_width=True
        )

        st.subheader("🧱 Orden óptimo de recorrido")

        resumen_busqueda = (
            encontrados
            .groupby(["rack", "nivel", "caja"])
            .size()
            .reset_index(name="cantidad")
            .sort_values(["rack", "nivel"])
        )

        for _, r in resumen_busqueda.iterrows():
            st.write(
                f"📍 {r['rack']} · Nivel {r['nivel']} · "
                f"{r['caja']} → {r['cantidad']} comprobantes"
            )
