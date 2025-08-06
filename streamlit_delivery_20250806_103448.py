import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

st.set_page_config(page_title="Avanzamento Produzione Delivery", layout="wide")

# Logo Euroirte
st.image("LogoEuroirte.jpg", width=200)

st.title("Avanzamento Produzione Delivery - Euroirte s.r.l.")

# --- Funzione per caricare e pulire i dati ---
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

    df["Reparto"] = df["CodCliente"].map({500100: "OLO", 400340: "TIM"})

    mesi_italiani = {
        1: "Gennaio", 2: "Febbraio", 3: "Marzo", 4: "Aprile",
        5: "Maggio", 6: "Giugno", 7: "Luglio", 8: "Agosto",
        9: "Settembre", 10: "Ottobre", 11: "Novembre", 12: "Dicembre"
    }
    df["Mese"] = df["Data"].dt.month.map(mesi_italiani)

    return df

# --- Funzione per calcolare riepilogo ---
def calcola_riepilogo(gruppo):
    def calcola_blocco(df_blocco):
        gestiti_ftth = df_blocco[df_blocco["TipoImpianto"] == "FTTH"].shape[0]
        espletati_ftth = df_blocco[(df_blocco["TipoImpianto"] == "FTTH") & (df_blocco["Causale"] == "COMPLWR")].shape[0]
        resa_ftth = np.nan if gestiti_ftth == 0 else espletati_ftth / gestiti_ftth

        gestiti_altro = df_blocco[df_blocco["TipoImpianto"] != "FTTH"].shape[0]
        espletati_altro = df_blocco[(df_blocco["TipoImpianto"] != "FTTH") & (df_blocco["Causale"] == "COMPLWR")].shape[0]
        resa_altro = np.nan if gestiti_altro == 0 else espletati_altro / gestiti_altro

        return pd.Series({
            "Impianti gestiti FTTH": gestiti_ftth,
            "Impianti espletati FTTH": espletati_ftth,
            "Resa FTTH": resa_ftth,
            "Impianti gestiti ≠ FTTH": gestiti_altro,
            "Impianti espletati ≠ FTTH": espletati_altro,
            "Resa ≠ FTTH": resa_altro
        })

    return gruppo.apply(calcola_blocco).reset_index()

# --- Caricamento dati ---
df = load_data()

# --- Filtro reparto, tecnico, mese ---
mese_selezionato = st.selectbox("Seleziona un mese", ["Tutti"] + sorted(df["Mese"].dropna().unique()))
tecnico_selezionato = st.selectbox("Seleziona un tecnico", ["Tutti"] + sorted(df["Tecnico"].dropna().unique()))
reparto_selezionato = st.selectbox("Seleziona un reparto", ["Tutti"] + sorted(df["Reparto"].dropna().unique()))

# --- Filtro applicato ---
df_filtrato = df.copy()
if mese_selezionato != "Tutti":
    df_filtrato = df_filtrato[df_filtrato["Mese"] == mese_selezionato]
if tecnico_selezionato != "Tutti":
    df_filtrato = df_filtrato[df_filtrato["Tecnico"] == tecnico_selezionato]
if reparto_selezionato != "Tutti":
    df_filtrato = df_filtrato[df_filtrato["Reparto"] == reparto_selezionato]

# --- Ultima data aggiornamento ---
ultima_data = df["Data"].max()
if pd.notna(ultima_data):
    st.markdown(f"📅 **Dati aggiornati al: {ultima_data.strftime('%d/%m/%Y')}**")

# --- Riepilogo Mensile ---
st.subheader("📊 Riepilogo Mensile")
df_mensile = calcola_riepilogo(df_filtrato.groupby("Tecnico"))
st.dataframe(df_mensile, use_container_width=True, hide_index=True)

# --- Dettaglio Giornaliero ---
st.subheader("📅 Dettaglio Giornaliero")
df_giornaliero = calcola_riepilogo(df_filtrato.groupby(["Data", "Tecnico"]))
st.dataframe(df_giornaliero, use_container_width=True, hide_index=True)
