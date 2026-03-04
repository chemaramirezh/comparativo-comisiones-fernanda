import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Comparador de Comisiones", layout="wide")

st.title("Comparador de Comisiones")

st.header("Seleccionar fechas de corte")

col1, col2 = st.columns(2)

with col1:
    fecha1 = st.date_input("Primer corte")

with col2:
    fecha2 = st.date_input("Segundo corte")

archivo1 = st.file_uploader("Archivo primer corte", type=["xlsx"])
archivo2 = st.file_uploader("Archivo segundo corte", type=["xlsx"])

def generar_excel(df):

    buffer = BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Comparativo")

    return buffer.getvalue()


if archivo1 and archivo2 and fecha1 and fecha2:

    if fecha2 <= fecha1:
        st.error("El segundo corte debe ser posterior al primero")
        st.stop()

    mes = fecha2.month

    df1 = pd.read_excel(archivo1, header=1)
    df2 = pd.read_excel(archivo2, header=1)

    df1 = df1[df1.iloc[:,0].notna()]
    df2 = df2[df2.iloc[:,0].notna()]

    base = df2.iloc[:,0:7].copy()
    base.rename(columns={base.columns[0]: "Clave"}, inplace=True)

    col_inicio = 8 + (mes-1)*3
    col_comision = col_inicio + 1

    corte1 = pd.DataFrame({
        "Clave": df1.iloc[:,0],
        "1er Corte": pd.to_numeric(df1.iloc[:,col_comision], errors="coerce").fillna(0)
    })

    corte2 = pd.DataFrame({
        "Clave": df2.iloc[:,0],
        "2do Corte": pd.to_numeric(df2.iloc[:,col_comision], errors="coerce").fillna(0)
    })

    resultado = base.merge(corte1, on="Clave", how="left")
    resultado = resultado.merge(corte2, on="Clave", how="left")

    resultado["1er Corte"] = resultado["1er Corte"].fillna(0)
    resultado["2do Corte"] = resultado["2do Corte"].fillna(0)

    resultado["Comisiones pagadas"] = np.minimum(
        resultado["1er Corte"], resultado["2do Corte"]
    )

    resultado["Cobro corte"] = np.maximum(
        resultado["2do Corte"] - resultado["1er Corte"], 0
    )

    def obs(row):
        if row["2do Corte"] < row["1er Corte"]:
            return "Ajuste en contra"
        return ""

    resultado["Observaciones"] = resultado.apply(obs, axis=1)

    # ==========================
    # FILA DE TOTALES
    # ==========================

    totales = resultado[[
        "1er Corte",
        "2do Corte",
        "Comisiones pagadas",
        "Cobro corte"
    ]].sum()

    fila_total = {col: "" for col in resultado.columns}

    fila_total["Clave"] = "TOTAL"
    fila_total["1er Corte"] = totales["1er Corte"]
    fila_total["2do Corte"] = totales["2do Corte"]
    fila_total["Comisiones pagadas"] = totales["Comisiones pagadas"]
    fila_total["Cobro corte"] = totales["Cobro corte"]

    resultado_final = pd.concat(
        [resultado, pd.DataFrame([fila_total])],
        ignore_index=True
    )

    # ==========================
    # RESUMEN
    # ==========================

    st.header("Resumen")

    colA, colB, colC = st.columns(3)

    colA.metric(
        "Total pagado previamente",
        f"${totales['Comisiones pagadas']:,.2f}"
    )

    colB.metric(
        "Cobro del corte",
        f"${totales['Cobro corte']:,.2f}"
    )

    colC.metric(
        "Pólizas analizadas",
        len(resultado)
    )

    # ==========================
    # VISTA PREVIA COMPLETA
    # ==========================

    st.subheader("Vista previa del comparativo")

    st.write(f"Total de filas: {len(resultado_final)}")

    st.dataframe(
        resultado_final,
        use_container_width=True,
        height=500
    )

    # ==========================
    # DESCARGA DE EXCEL
    # ==========================

    excel_file = generar_excel(resultado_final)

    st.download_button(
        label="📥 Descargar Excel",
        data=excel_file,
        file_name=f"Comparativo_{fecha1.strftime('%d%b')}_{fecha2.strftime('%d%b')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:

    st.info(
        "Selecciona las fechas de corte y sube ambos archivos para generar el comparativo."
    )
