
import streamlit as st
import pandas as pd

st.set_page_config(layout="wide", page_title="Avanzamento Produzione Delivery - Euroirte s.r.l.")

# Logo e titolo
st.image("LogoEuroirte.jpg", width=200)
st.title("Avanzamento Produzione Delivery - Euroirte s.r.l.")

# Caricamento file Excel
file_path = "delivery.xlsx"
df = pd.read_excel(file_path)

# Conversione colonna data
df["Data Esec. Lavoro"] = pd.to_datetime(df["Data Esec. Lavoro"], dayfirst=True, errors="coerce")
df["Data"] = df["Data Esec. Lavoro"]

# Mappatura reparto
df["Reparto"] = df["Codice Cliente"].map({500100: "OLO", 400340: "TIM"})

# Selettori
reparti = ["Tutti"] + sorted(df["Reparto"].dropna().unique())
tecnici = ["Tutti"] + sorted(df["Tecnico Assegnato"].dropna().unique())
date = ["Tutti"] + sorted(df["Data"].dropna().dt.strftime("%d/%m/%Y").unique())

col1, col2 = st.columns(2)
reparto_sel = col1.selectbox("Filtro Reparto", reparti)
tecnico_sel = col2.selectbox("Filtro Tecnico", tecnici)
data_sel = st.selectbox("Filtro per Data", date)

# Filtro dinamico
if reparto_sel != "Tutti":
    df = df[df["Reparto"] == reparto_sel]
if tecnico_sel != "Tutti":
    df = df[df["Tecnico Assegnato"] == tecnico_sel]
if data_sel != "Tutti":
    data_filter = pd.to_datetime(data_sel, format="%d/%m/%Y", dayfirst=True)
    df = df[df["Data"] == data_filter]

# Indicatori
tabella = []

for tecnico in df["Tecnico Assegnato"].dropna().unique():
    df_tecnico = df[df["Tecnico Assegnato"] == tecnico]
    gestiti = len(df_tecnico)
    espletati = len(df_tecnico[df_tecnico["Causale Chiusura"] == "COMPLWR"])
    ftth = df_tecnico[df_tecnico["Tipo Impianto"] == "FTTH"]
    non_ftth = df_tecnico[df_tecnico["Tipo Impianto"] != "FTTH"]
    resa_ftth = (len(ftth[ftth["Causale Chiusura"] == "COMPLWR"]) / len(ftth) * 100) if len(ftth) else 0
    resa_non_ftth = (len(non_ftth[non_ftth["Causale Chiusura"] == "COMPLWR"]) / len(non_ftth) * 100) if len(non_ftth) else 0

    tabella.append({
        "Tecnico": tecnico,
        "Impianti Gestiti": gestiti,
        "Impianti Espletati": espletati,
        "Resa FTTH (%)": resa_ftth,
        "Resa ≠ FTTH (%)": resa_non_ftth
    })

df_out = pd.DataFrame(tabella)

# Colorazione condizionale
def color_ftth(val):
    return "background-color: lightgreen" if val >= 75 else "background-color: salmon"

def color_non_ftth(val):
    return "background-color: lightgreen" if val >= 70 else "background-color: salmon"

st.dataframe(df_out.style
    .format({"Resa FTTH (%)": "{:.1f}%", "Resa ≠ FTTH (%)": "{:.1f}%"})
    .applymap(color_ftth, subset=["Resa FTTH (%)"])
    .applymap(color_non_ftth, subset=["Resa ≠ FTTH (%)"])
)

# Ultima data aggiornamento
ultima_data = df["Data"].max()
if pd.notna(ultima_data):
    st.markdown(f"🗓️ **Dati aggiornati al: {ultima_data.strftime('%d/%m/%Y')}**")
