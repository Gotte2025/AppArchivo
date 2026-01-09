import streamlit as st
import pandas as pd
import math

# ---------------- CONFIGURACIÓN ----------------
CAPACIDAD_CAJA = 300
RACK = "A"

st.set_page_config(
    page_title="AppArchivo",
    layout="wide"
)

st.title("📦 AppArchivo – Sistema de Archivo")
st.info("Subí un Excel para comenzar")

# ---------------- CARGA DE DATOS ----------------
def cargar_excel(archivo):
    df = pd.read_excel(archivo)
    df = df.iloc[:, :2]
    df.columns = ["numero", "tipo"]
    return df

def organizar(df):
    df = df[df["tipo"].isin(["PX", "PU", "PH"])]
    df = df.sort_values(by=["tipo", "numero"], ascending=[True, False])

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

    ocupacion = (
        df.groupby("caja")
        .size()
        .reset_index(name="cantidad")
        .sort_values("cantidad", ascending=False)
        .reset_index(drop=True)
    )

    ocupacion["nivel"] = ocupacion.index + 1
    df = df.merge(ocupacion[["caja", "nivel"]], on="caja", how="left")

    return df

def construir_rack(df):
    rack = {}
    for _, r in df.iterrows():
        rack.setdefault(r["nivel"], set()).add(r["caja"])
    return rack

# ---------------- INTERFAZ ----------------
archivo = st.file_uploader(
    "Subí tu Excel",
    type=["xlsx", "xlsm"]
)

if archivo is None:
    st.stop()

df = cargar_excel(archivo)
df = organizar(df)
rack = construir_rack(df)

st.subheader("🧱 Vista del Rack (nivel por nivel)")

for nivel in sorted(rack.keys(), reverse=True):
    cols = st.columns(len(rack[nivel]))
    for i, caja in enumerate(sorted(rack[nivel])):
        with cols[i]:
            tipo = caja[:2]
            color = {
                "PX": "#AED6F1",
                "PU": "#ABEBC6",
                "PH": "#FAD7A0"
            }[tipo]

            ocupacion = len(df[df["caja"] == caja])
            porcentaje = int((ocupacion / CAPACIDAD_CAJA) * 100)

            st.markdown(
                f"""
                <div style="
                    background-color:{color};
                    padding:10px;
                    border-radius:8px;
                    text-align:center;
                    border:1px solid #555;
                ">
                <b>{caja}</b><br>
                Nivel {nivel}<br>
                {ocupacion} comps<br>
                {porcentaje}%
                </div>
                """,
                unsafe_allow_html=True
            )

st.subheader("🔍 Buscar comprobante")
buscar = st.text_input("Ingresá número de comprobante")

if buscar:
    res = df[df["numero"].astype(str) == buscar]
    if not res.empty:
        r = res.iloc[0]
        st.success(
            f"📍 {r['tipo']} {r['numero']} → Rack {r['rack']} / Nivel {r['nivel']} / Caja {r['caja']}"
        )
    else:
        st.error("Comprobante no encontrado")

