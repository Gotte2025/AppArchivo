import streamlit as st
import pandas as pd
import math

# ---------------- CONFIGURACIÓN FÍSICA REAL ----------------
CAPACIDAD_CAJA = 300
CAJAS_POR_NIVEL = 2
NIVELES_POR_RACK = 5
CAJAS_POR_RACK = CAJAS_POR_NIVEL * NIVELES_POR_RACK
COMPS_POR_RACK = CAJAS_POR_RACK * CAPACIDAD_CAJA
RACK = "A"

# ---------------- STREAMLIT ----------------
st.set_page_config(page_title="AppArchivo", layout="wide")
st.title("📦 AppArchivo – Archivo físico inteligente")
st.caption("Nivel 01 abajo (más pesado) · Proyección y alertas automáticas")

# ---------------- CARGA DE DATOS ----------------
def cargar_excel(archivo):
    df = pd.read_excel(archivo)
    df = df.iloc[:, :2]
    df.columns = ["numero", "tipo"]
    return df

def organizar(df):
    df = df[df["tipo"].isin(["PX", "PU", "PH"])]
    df = df.sort_values(by=["tipo", "numero"], ascending=[True, True])

    cajas = []
    racks = []
    contador = {}
    caja_actual = {}

    for _, row in df.iterrows():
        tipo = row["tipo"]

        if tipo not in contador:
            contador[tipo] = 0
            caja_actual[tipo] = 1

        contador[tipo] += 1

        if contador[tipo] > CAPACIDAD_CAJA:
            caja_actual[tipo] += 1
            contador[tipo] = 1

        cajas.append(f"{tipo}-{caja_actual[tipo]:02d}")
        racks.append(RACK)

    df["caja"] = cajas
    df["rack"] = racks

    ocupacion = df.groupby("caja").size().reset_index(name="cantidad")
    ocupacion = ocupacion.sort_values("cantidad", ascending=False).reset_index(drop=True)
    ocupacion["nivel"] = ocupacion.index + 1

    df = df.merge(ocupacion[["caja", "nivel"]], on="caja", how="left")
    return df, ocupacion

# ---------------- INTERFAZ ----------------
archivo = st.file_uploader(
    "Subí tu Excel (Col A: número | Col B: tipo PX / PU / PH)",
    type=["xlsx", "xlsm"]
)

if archivo is None:
    st.stop()

df = cargar_excel(archivo)
df, ocupacion = organizar(df)

# ---------------- INDICADORES CLAVE ----------------
st.subheader("📊 Estado del archivo")

total_comprobantes = len(df)
cajas_usadas = df["caja"].nunique()
racks_usados = math.ceil(cajas_usadas / CAJAS_POR_RACK)
porcentaje_rack = int((cajas_usadas / CAJAS_POR_RACK) * 100)

c1, c2, c3 = st.columns(3)
c1.metric("📦 Comprobantes totales", total_comprobantes)
c2.metric("🧱 Cajas usadas", cajas_usadas)
c3.metric("🏗️ Racks ocupados", racks_usados)

st.progress(min(porcentaje_rack / 100, 1.0))

# ---------------- ALERTAS ----------------
if porcentaje_rack >= 90:
    st.error("🚨 Rack casi lleno – Planificar nuevo rack URGENTE")
elif porcentaje_rack >= 70:
    st.warning("⚠️ Rack al 70% – Evaluar crecimiento")
else:
    st.success("✅ Capacidad de rack en nivel seguro")

# ---------------- PROYECCIÓN ----------------
st.subheader("📈 Proyección anual")

promedio_mensual = st.number_input(
    "Promedio mensual de comprobantes",
    min_value=1,
    value=300,
    step=50
)

proy_anual = promedio_mensual * 12
racks_anuales = math.ceil(proy_anual / COMPS_POR_RACK)

st.info(
    f"""
    📅 Proyección anual: **{proy_anual} comprobantes**  
    🏗️ Racks necesarios en 12 meses: **{racks_anuales}**
    """
)

# ---------------- VISTA DEL RACK ----------------
st.subheader("🧱 Vista del rack (Nivel 01 abajo)")

rack_vista = {}
for _, r in ocupacion.iterrows():
    rack_vista.setdefault(r["nivel"], []).append(r)

for nivel in sorted(rack_vista.keys()):
    cols = st.columns(CAJAS_POR_NIVEL)
    for i, r in enumerate(rack_vista[nivel][:CAJAS_POR_NIVEL]):
        with cols[i]:
            tipo = r["caja"][:2]
            color = {"PX": "#AED6F1", "PU": "#ABEBC6", "PH": "#FAD7A0"}[tipo]
            porcentaje = int((r["cantidad"] / CAPACIDAD_CAJA) * 100)

            st.markdown(
                f"""
                <div style="
                    background-color:{color};
                    padding:12px;
                    border-radius:8px;
                    text-align:center;
                    border:1px solid #555;
                ">
                <b>{r['caja']}</b><br>
                Nivel {nivel}<br>
                {r['cantidad']} comps<br>
                {porcentaje}%
                </div>
                """,
                unsafe_allow_html=True
            )

# ---------------- BÚSQUEDA ----------------
st.subheader("🔍 Buscar comprobante")

buscar = st.text_input("Ingresá número de comprobante")

if buscar:
    res = df[df["numero"].astype(str) == buscar]
    if not res.empty:
        r = res.iloc[0]
        st.success(
            f"📍 {r['tipo']} {r['numero']} → "
            f"Rack {r['rack']} · Nivel {r['nivel']} · Caja {r['caja']}"
        )
    else:
        st.error("Comprobante no encontrado")

# ---------------- BÚSQUEDA MÚLTIPLE ----------------
st.subheader("🧾 Buscar lista de comprobantes (optimizado)")

st.caption(
    "Pegá una lista de números (uno por línea o separados por coma). "
    "El sistema agrupa para minimizar recorridos físicos."
)

lista_texto = st.text_area(
    "Lista de comprobantes",
    height=150,
    placeholder="10234\n10235\n20456\n30567"
)

if lista_texto:
    # Normalizar lista
    lista = (
        lista_texto
        .replace(",", "\n")
        .splitlines()
    )
    lista = [x.strip() for x in lista if x.strip()]

    # Buscar
    encontrados = df[df["numero"].astype(str).isin(lista)].copy()
    encontrados["numero"] = encontrados["numero"].astype(str)

    if encontrados.empty:
        st.error("No se encontraron comprobantes de la lista")
    else:
        # Orden óptimo de recorrido
        encontrados = encontrados.sort_values(
            by=["rack", "nivel", "caja"]
        )

        st.success(f"✅ Encontrados {len(encontrados)} comprobantes")

        # Mostrar tabla
        st.dataframe(
            encontrados[
                ["tipo", "numero", "rack", "nivel", "caja"]
            ],
            use_container_width=True
        )

        # ---------------- RESUMEN FÍSICO ----------------
        st.subheader("🧱 Resumen para búsqueda física")

        resumen = (
            encontrados
            .groupby(["rack", "nivel", "caja"])
            .size()
            .reset_index(name="cantidad")
            .sort_values(["rack", "nivel"])
        )

        for _, r in resumen.iterrows():
            st.write(
                f"📍 Rack {r['rack']} · Nivel {r['nivel']} · "
                f"Caja {r['caja']} → {r['cantidad']} comprobantes"
            )
