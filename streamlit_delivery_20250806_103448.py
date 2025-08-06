import streamlit as st
import pandas as pd
import numpy as np
import locale

@st.cache_data
def load_data():
    df = pd.read_excel("delivery.xlsx", usecols=[
        "Data Esec. Lavoro",
        "Tecnico Assegnato",
        "Tipo Impianto",
        "Causale Chiusura",
        "Codice Cliente"
    ])

    # Rinomina colonne per uniformità
    df.rename(columns={
        "Data Esec. Lavoro": "Data",
        "Tecnico Assegnato": "Tecnico",
        "Tipo Impianto": "TipoImpianto",
        "Causale Chiusura": "Causale",
        "Codice Cliente": "CodCliente"
    }, inplace=True)

    # Conversione data e rimozione righe senza data
    df["Data"] = pd.to_datetime(df["Data"], format="%d/%m/%Y", errors="coerce")
    df = df.dropna(subset=["Data"])

    # Creazione colonna Reparto
    df["Reparto"] = df["CodCliente"].map({500100: "OLO", 400340: "TIM"})

    # Colonna mese (in italiano, senza locale)
    mesi_italiani = {
        1: "Gennaio", 2: "Febbraio", 3: "Marzo", 4: "Aprile",
        5: "Maggio", 6: "Giugno", 7: "Luglio", 8: "Agosto",
        9: "Settembre", 10: "Ottobre", 11: "Novembre", 12: "Dicembre"
    }
    df["Mese"] = df["Data"].dt.month.map(mesi_italiani)

    # Colonna "Ultimo aggiornamento"
    ultima_data = df["Data"].max()
    if pd.notna(ultima_data):
        st.markdown(f"📅 **Dati aggiornati al: {ultima_data.strftime('%d/%m/%Y')}**")

    return df
    
# Imposta la lingua italiana per i mesi
try:
    locale.setlocale(locale.LC_TIME, 'it_IT.UTF-8')
except locale.Error:
    pass  # Locale non disponibile, usa default

st.set_page_config(layout="wide", page_title="Avanzamento Produzione Delivery - Euroirte s.r.l.")

# Logo e intestazione
st.image("LogoEuroirte.jpg", width=180)
st.title("Avanzamento Produzione Delivery - Euroirte s.r.l.")

# Carica file Excel
file_path = "delivery.xlsx"
df = pd.read_excel(file_path)

# Gestione date e mese in italiano
df["Data Esec. Lavoro"] = pd.to_datetime(df["Data Esec. Lavoro"], dayfirst=True, errors="coerce")
df["Mese"] = df["Data Esec. Lavoro"].dt.strftime("%B %Y").str.capitalize()
df["Giorno"] = df["Data Esec. Lavoro"].dt.strftime("%d/%m/%Y")
df["Reparto"] = df["Reparto"].map({500100: "OLO", 400340: "TIM"})

# Mostra data aggiornamento subito sotto il titolo
ultima_data = df["Data Esec. Lavoro"].max()
if pd.notna(ultima_data):
    st.markdown(f"🗓️ **Dati aggiornati al: {ultima_data.strftime('%d/%m/%Y')}**")

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

# Funzione calcolo riepilogo
def calcola_riepilogo(df_grouped):
    tabella = []
    for (tecnico, chiave), df_tecnico in df_grouped:
        ftth = df_tecnico[df_tecnico["Tipo Impianto"] == "FTTH"]
        non_ftth = df_tecnico[df_tecnico["Tipo Impianto"] != "FTTH"]

        gestiti_ftth = len(ftth)
        espletati_ftth = len(ftth[ftth["Causale Chiusura"] == "COMPLWR"])
        resa_ftth = (espletati_ftth / gestiti_ftth * 100) if gestiti_ftth else np.nan

        gestiti_non = len(non_ftth)
        espletati_non = len(non_ftth[non_ftth["Causale Chiusura"] == "COMPLWR"])
        resa_non = (espletati_non / gestiti_non * 100) if gestiti_non else np.nan

        record = {
            "Tecnico": tecnico,
            "Impianti gestiti FTTH": gestiti_ftth,
            "Impianti espletati FTTH": espletati_ftth,
            "Resa FTTH": resa_ftth,
            "Impianti gestiti ≠ FTTH": gestiti_non,
            "Impianti espletati ≠ FTTH": espletati_non,
            "Resa ≠ FTTH": resa_non
        }

        if isinstance(chiave, str):  # Giornaliero
            record["Giorno"] = chiave

        tabella.append(record)

    return pd.DataFrame(tabella)

# Tabella mensile (per tecnico)
df_mensile = calcola_riepilogo(df.groupby("Tecnico"))

# Tabella giornaliera (per tecnico e giorno)
df_giornaliero = calcola_riepilogo(df.groupby(["Tecnico", "Giorno"]))

# Rimuove colonne FTTH se OLO
def filtra_colonne(df_tab):
    if reparto_sel == "OLO":
        return df_tab.drop(columns=["Impianti gestiti FTTH", "Impianti espletati FTTH", "Resa FTTH"], errors='ignore')
    return df_tab

df_mensile = filtra_colonne(df_mensile)
df_giornaliero = filtra_colonne(df_giornaliero)

# Colorazione condizionale
def color_resa_ftth(val):
    if pd.isna(val): return ""
    return "background-color: lightgreen" if val >= 75 else "background-color: salmon"

def color_resa_non(val):
    if pd.isna(val): return ""
    return "background-color: lightgreen" if val >= 70 else "background-color: salmon"

# Mostra riepilogo mensile
st.subheader("📊 Riepilogo Mensile per Tecnico")
st.dataframe(df_mensile.style
    .format({
        "Resa FTTH": "{:.1f}%",
        "Resa ≠ FTTH": "{:.1f}%"
    }, na_rep="")
    .applymap(color_resa_ftth, subset=["Resa FTTH"] if "Resa FTTH" in df_mensile.columns else [])
    .applymap(color_resa_non, subset=["Resa ≠ FTTH"])
)

# Mostra riepilogo giornaliero
st.subheader("📅 Riepilogo Giornaliero per Tecnico")
st.dataframe(df_giornaliero.style
    .format({
        "Resa FTTH": "{:.1f}%",
        "Resa ≠ FTTH": "{:.1f}%"
    }, na_rep="")
    .applymap(color_resa_ftth, subset=["Resa FTTH"] if "Resa FTTH" in df_giornaliero.columns else [])
    .applymap(color_resa_non, subset=["Resa ≠ FTTH"])
)
