
import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(layout="wide")

# Titolo e logo
st.image("logo.png", width=150)
st.title("Avanzamento Produzione Delivery - Euroirte s.r.l.")

# Caricamento e pulizia dati
@st.cache_data
def load_data():
    df = pd.read_excel("delivery.xlsx", usecols=[
        "Data Esec. Lavoro",
        "Tecnico Assegnato",
        "Tipo Impianto",
        "Causale Chiusura",
        "Codice Cliente"
    ])
    df.rename(columns={
        "Data Esec. Lavoro": "Data",
        "Tecnico Assegnato": "Tecnico",
        "Tipo Impianto": "TipoImpianto",
        "Causale Chiusura": "Causale",
        "Codice Cliente": "CodCliente"
    }, inplace=True)
    df["Data"] = pd.to_datetime(df["Data"], format="%d/%m/%Y", errors="coerce")
    df = df.dropna(subset=["Data"])
    df["Reparto"] = df["Reparto"].map({500100: "OLO", 400340: "TIM"})
    mesi_italiani = {
        1: "Gennaio", 2: "Febbraio", 3: "Marzo", 4: "Aprile",
        5: "Maggio", 6: "Giugno", 7: "Luglio", 8: "Agosto",
        9: "Settembre", 10: "Ottobre", 11: "Novembre", 12: "Dicembre"
    }
    df["Mese"] = df["Data"].dt.month.map(mesi_italiani)
    return df
    
if "Tecnico" not in df.columns:
    st.error("La colonna 'Tecnico' non è stata trovata nel file Excel. Controlla i nomi delle colonne.")
    st.stop()
    
# Funzione riepilogo per tecnico
def calcola_riepilogo(gruppo):
    def calcola_blocco(df_blocco):
        gestiti_ftth = df_blocco[df_blocco["TipoImpianto"] == "FTTH"].shape[0]
        espletati_ftth = df_blocco[(df_blocco["TipoImpianto"] == "FTTH") & (df_blocco["Causale"] == "COMPLWR")].shape[0]
        resa_ftth = (espletati_ftth / gestiti_ftth) * 100 if gestiti_ftth > 0 else None

        gestiti_altro = df_blocco[df_blocco["TipoImpianto"] != "FTTH"].shape[0]
        espletati_altro = df_blocco[(df_blocco["TipoImpianto"] != "FTTH") & (df_blocco["Causale"] == "COMPLWR")].shape[0]
        resa_altro = (espletati_altro / gestiti_altro) * 100 if gestiti_altro > 0 else None

        return pd.Series({
            "Impianti gestiti FTTH": gestiti_ftth,
            "Impianti espletati FTTH": espletati_ftth,
            "Resa FTTH": resa_ftth,
            "Impianti gestiti ≠ FTTH": gestiti_altro,
            "Impianti espletati ≠ FTTH": espletati_altro,
            "Resa ≠ FTTH": resa_altro
        })

    return gruppo.apply(calcola_blocco).reset_index()

# Carica i dati
df = load_data()

# Filtro per mese, tecnico, reparto
st.markdown(f"📅 **Dati aggiornati al: {df['Data'].max().strftime('%d/%m/%Y')}**")

col1, col2, col3 = st.columns(3)
mese_sel = col1.selectbox("Seleziona un mese", options=["Tutti"] + sorted(df["Mese"].dropna().unique().tolist()))
tecnico_sel = col2.selectbox("Seleziona un tecnico", options=["Tutti"] + sorted(df["Tecnico"].dropna().unique().tolist()))
reparto_sel = col3.selectbox("Seleziona un reparto", options=["Tutti"] + sorted(df["Reparto"].dropna().unique().tolist()))

# Applica i filtri
if mese_sel != "Tutti":
    df = df[df["Mese"] == mese_sel]
if tecnico_sel != "Tutti":
    df = df[df["Tecnico"] == tecnico_sel]
if reparto_sel != "Tutti":
    df = df[df["Reparto"] == reparto_sel]

# Riepilogo mensile
st.subheader("📊 Riepilogo Mensile")
df_mensile = calcola_riepilogo(df.groupby("Tecnico"))

# Nascondi colonne FTTH se reparto è OLO
if reparto_sel == "OLO":
    df_mensile = df_mensile.drop(columns=["Impianti gestiti FTTH", "Impianti espletati FTTH", "Resa FTTH"])

st.dataframe(df_mensile)

# Riepilogo giornaliero
st.subheader("📅 Dettaglio Giornaliero")
df_giornaliero = calcola_riepilogo(df.groupby(["Data", "Tecnico"]))

if reparto_sel == "OLO":
    df_giornaliero = df_giornaliero.drop(columns=["Impianti gestiti FTTH", "Impianti espletati FTTH", "Resa FTTH"])

st.dataframe(df_giornaliero)
