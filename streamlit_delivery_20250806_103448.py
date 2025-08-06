import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(layout="wide", page_title="Avanzamento Produzione Delivery - Euroirte s.r.l.")

# Logo e intestazione
st.image("LogoEuroirte.jpg", width=180)
st.title("Avanzamento Produzione Delivery - Euroirte s.r.l.")

# Caricamento file Excel
file_path = "delivery.xlsx"
df = pd.read_excel(file_path)

# Conversione data e aggiunta colonna mese
df["Data Esec. Lavoro"] = pd.to_datetime(df["Data Esec. Lavoro"], dayfirst=True, errors="coerce")
df["Mese"] = df["Data Esec. Lavoro"].dt.strftime("%B %Y")
df["Reparto"] = df["Codice Cliente"].map({500100: "OLO", 400340: "TIM"})

# Filtri interattivi
col1, col2, col3 = st.columns(3)
mese_sel = col1.selectbox("Seleziona un mese", ["Tutti"] + sorted(df["Mese"].dropna().unique()))
tecnico_sel = col2.selectbox("Seleziona un tecnico", ["Tutti"] + sorted(df["Tecnico Assegnato"].dropna().unique()))
reparto_sel = col3.selectbox("Seleziona un reparto", ["Tutti"] + sorted(df["Reparto"].dropna().unique()))

# Applica filtri
if mese_sel != "Tutti":
    df = df[df["Mese"] == mese_sel]
if tecnico_sel != "Tutti":
    df = df[df["Tecnico Assegnato"] == tecnico_sel]
if reparto_sel != "Tutti":
    df = df[df["Reparto"] == reparto_sel]

# Calcolo per ogni tecnico
tabella = []
for tecnico in df["Tecnico Assegnato"].dropna().unique():
    df_tecnico = df[df["Tecnico Assegnato"] == tecnico]
    ftth = df_tecnico[df_tecnico["Tipo Impianto"] == "FTTH"]
    non_ftth = df_tecnico[df_tecnico["Tipo Impianto"] != "FTTH"]

    gestiti_ftth = len(ftth)
    espletati_ftth = len(ftth[ftth["Causale Chiusura"] == "COMPLWR"])
    resa_ftth = (espletati_ftth / gestiti_ftth * 100) if gestiti_ftth else np.nan

    gestiti_non = len(non_ftth)
    espletati_non = len(non_ftth[non_ftth["Causale Chiusura"] == "COMPLWR"])
    resa_non = (espletati_non / gestiti_non * 100) if gestiti_non else np.nan

    tabella.append({
        "Tecnico": tecnico,
        "Impianti gestiti FTTH": gestiti_ftth,
        "Impianti espletati FTTH": espletati_ftth,
        "Resa FTTH": resa_ftth,
        "Impianti gestiti ≠ FTTH": gestiti_non,
        "Impianti espletati ≠ FTTH": espletati_non,
        "Resa ≠ FTTH": resa_non
    })

df_out = pd.DataFrame(tabella)

# Rimuovi FTTH se OLO
if reparto_sel == "OLO":
    df_out.drop(columns=["Impianti gestiti FTTH", "Impianti espletati FTTH", "Resa FTTH"], inplace=True)

# Colori semaforici
def color_resa_ftth(val):
    if pd.isna(val): return ""
    return "background-color: lightgreen" if val >= 75 else "background-color: salmon"

def color_resa_non(val):
    if pd.isna(val): return ""
    return "background-color: lightgreen" if val >= 70 else "background-color: salmon"

# Visualizza tabella con formattazione
st.dataframe(df_out.style
    .format({
        "Resa FTTH": "{:.1f}%",
        "Resa ≠ FTTH": "{:.1f}%"
    }, na_rep="")
    .applymap(color_resa_ftth, subset=["Resa FTTH"] if "Resa FTTH" in df_out.columns else [])
    .applymap(color_resa_non, subset=["Resa ≠ FTTH"])
)

# Mostra data aggiornamento
ultima_data = df["Data Esec. Lavoro"].max()
if pd.notna(ultima_data):
    st.markdown(f"🗓️ **Dati aggiornati al: {ultima_data.strftime('%d/%m/%Y')}**")
