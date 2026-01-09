# 📦 Sistema de Archivo de Comprobantes

Aplicación web desarrollada en **Python + Streamlit** para administrar y
visualizar el archivo físico de comprobantes (PX, PU, PH).

## 🚀 Funcionalidades
- Asignación automática de cajas
- Visualización del rack por niveles
- Búsqueda individual de comprobantes
- Búsqueda múltiple con recorrido optimizado
- Checklist de retiro
- Compatible con uso en celular

## 📂 Formato del Excel
El archivo debe tener:
- Columna A: Número de comprobante
- Columna B: Tipo (PX, PU, PH)

## ▶️ Ejecución local
```bash
pip install -r requirements.txt
streamlit run archivo_rack.py
