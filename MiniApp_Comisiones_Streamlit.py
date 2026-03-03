
import streamlit as st
import pandas as pd
import numpy as np

st.title("Mini App Comparativo de Comisiones")

st.write("Sube los archivos del día 5 y día 20 y selecciona el mes.")

meses = {
    "Enero":1,"Febrero":2,"Marzo":3,"Abril":4,"Mayo":5,"Junio":6,
    "Julio":7,"Agosto":8,"Septiembre":9,"Octubre":10,"Noviembre":11,"Diciembre":12
}

mes_nombre = st.selectbox("Selecciona el mes:", list(meses.keys()))
mes_num = meses[mes_nombre]

file_5 = st.file_uploader("Sube archivo día 5", type=["xlsx"])
file_20 = st.file_uploader("Sube archivo día 20", type=["xlsx"])

if file_5 and file_20:
    df5 = pd.read_excel(file_5, header=1)
    df20 = pd.read_excel(file_20, header=1)

    # Eliminar filas sin clave válida
    df5 = df5[df5.iloc[:,0].notna()]
    df5 = df5[df5.iloc[:,0] != 0]
    df20 = df20[df20.iloc[:,0].notna()]
    df20 = df20[df20.iloc[:,0] != 0]

    base_20 = df20.iloc[:,0:7].copy()
    base_20.rename(columns={base_20.columns[0]:"Clave"}, inplace=True)

    # Parametrización mensual
    col_inicio = 8 + (mes_num - 1) * 3
    col_inicio_py = col_inicio - 1
    col_comision = col_inicio_py + 2

    df5_comm = pd.DataFrame({
        "Clave": df5.iloc[:,0],
        "Comision_5": pd.to_numeric(df5.iloc[:,col_comision], errors="coerce").fillna(0)
    })

    df20_comm = pd.DataFrame({
        "Clave": df20.iloc[:,0],
        "Comision_20": pd.to_numeric(df20.iloc[:,col_comision], errors="coerce").fillna(0)
    })

    df_final = base_20.merge(df5_comm, on="Clave", how="left")
    df_final = df_final.merge(df20_comm, on="Clave", how="left")

    df_final["Comision_5"] = df_final["Comision_5"].fillna(0)
    df_final["Comision_20"] = df_final["Comision_20"].fillna(0)

    df_final["Comisiones pagadas"] = np.minimum(df_final["Comision_5"], df_final["Comision_20"])

    df_final["Comisiones cobro efectivo dia 20"] = np.where(
        df_final["Comision_20"] > df_final["Comision_5"],
        df_final["Comision_20"] - df_final["Comision_5"],
        0
    )

    def observacion(row):
        c5 = row["Comision_5"]
        c20 = row["Comision_20"]
        if c5 > 0 and c20 > 0:
            if c20 > c5:
                return f"Diferencia a favor +{round(c20-c5,2)}"
            elif c5 > c20:
                return f"Diferencia en contra -{round(c5-c20,2)}"
            else:
                return "Pagada previamente"
        elif c5 > 0 and c20 == 0:
            return "Pagada el día 5"
        elif c5 == 0 and c20 > 0:
            return "Se cobra el día 20"
        else:
            return ""

    df_final["Observaciones"] = df_final.apply(observacion, axis=1)

    # Totales
    numeric_cols = ["Comision_5","Comision_20",
                    "Comisiones pagadas",
                    "Comisiones cobro efectivo dia 20"]

    totals = df_final[numeric_cols].sum()

    total_row = {col:"" for col in df_final.columns}
    total_row["Clave"] = "TOTAL"
    for col in numeric_cols:
        total_row[col] = totals[col]

    df_final = pd.concat([df_final, pd.DataFrame([total_row])], ignore_index=True)

    st.success("Comparativo generado correctamente")
    st.dataframe(df_final)

    csv = df_final.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Descargar Excel (CSV)",
        data=csv,
        file_name=f"Comparativo_{mes_nombre}.csv",
        mime="text/csv"
    )
