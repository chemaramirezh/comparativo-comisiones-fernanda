import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import re
from datetime import datetime

st.set_page_config(page_title="Comparador de Comisiones", layout="wide")

st.title("Comparador de Comisiones")

st.header("Seleccionar fechas de corte")

col1, col2 = st.columns(2)

with col1:
    fecha1 = st.date_input("Primer corte")

with col2:
    fecha2 = st.date_input("Segundo corte")

if fecha1 and fecha2:

    if fecha2 <= fecha1:
        st.error("El segundo corte debe ser posterior al primero")
        st.stop()

    mes = fecha2.month

    archivo1 = st.file_uploader("Archivo primer corte", type=["xlsx"])
    archivo2 = st.file_uploader("Archivo segundo corte", type=["xlsx"])

    if archivo1 and archivo2:

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

        st.header("Resumen")

        total_pagado = resultado["Comisiones pagadas"].sum()
        total_cobro = resultado["Cobro corte"].sum()

        colA, colB = st.columns(2)

        colA.metric("Total pagado previamente", f"${total_pagado:,.2f}")
        colB.metric("Cobro del corte", f"${total_cobro:,.2f}")

        st.dataframe(resultado.head(50))

        st.download_button(
            "Descargar Excel",
            resultado.to_csv(index=False),
            file_name="comparativo_comisiones.csv"
        )

st.header("Dashboard histórico")

archivos = st.file_uploader(
    "Subir archivos históricos",
    type=["xlsx"],
    accept_multiple_files=True
)

if archivos:

    registros = []
    ranking = {}

    for file in archivos:

        nombre = file.name

        fecha_match = re.search(r"\d{4}-\d{2}-\d{2}", nombre)

        if fecha_match:
            fecha = datetime.strptime(fecha_match.group(), "%Y-%m-%d")
        else:
            continue

        df = pd.read_excel(file, header=1)

        df = df[df.iloc[:,0].notna()]

        mes = fecha.month
        col_inicio = 8 + (mes-1)*3
        col_comision = col_inicio + 1

        df["comision"] = pd.to_numeric(df.iloc[:,col_comision], errors="coerce").fillna(0)

        total = df["comision"].sum()

        for i,row in df.iterrows():

            poliza = row.iloc[0]
            valor = row["comision"]

            ranking[poliza] = ranking.get(poliza,0) + valor

        registros.append({
            "fecha": fecha,
            "total": total
        })

    cortes = pd.DataFrame(registros)

    cortes = cortes.sort_values("fecha")

    cortes["Ingreso"] = cortes["total"].diff()

    cortes = cortes.dropna()

    fig1 = px.bar(cortes,x="fecha",y="Ingreso",title="Ingreso por corte")

    st.plotly_chart(fig1, use_container_width=True)

    cortes["acumulado"] = cortes["Ingreso"].cumsum()

    fig2 = px.line(cortes,x="fecha",y="acumulado",title="Ingreso acumulado")

    st.plotly_chart(fig2, use_container_width=True)

    ingreso_total = cortes["Ingreso"].sum()

    st.metric("Ingreso total analizado",f"${ingreso_total:,.2f}")

    ranking_df = pd.DataFrame(
        ranking.items(),
        columns=["Poliza","Comision"]
    )

    ranking_df = ranking_df.sort_values(
        "Comision",
        ascending=False
    ).head(10)

    st.subheader("Top 10 pólizas por comisión")

    fig3 = px.bar(
        ranking_df,
        x="Poliza",
        y="Comision",
        title="Ranking de pólizas"
    )

    st.plotly_chart(fig3, use_container_width=True)
