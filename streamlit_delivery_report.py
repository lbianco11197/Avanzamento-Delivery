
import pandas as pd
import streamlit as st
from datetime import datetime

# --- Funzione per caricare e pulire i dati ---
@st.cache_data
def load_data():
    df = pd.read_excel("delivery.xlsx", usecols=[
        "Data Esec. Lavoro",
        "Tecnico",
        "Tipo Impianto",
        "Causale Chiusura",
        "Reparto"
    ])

    df.rename(columns={
        "Data Esec. Lavoro": "Data",
        "Tecnico": "Tecnico",
        "Tipo Impianto": "TipoImpianto",
        "Causale Chiusura": "Causale",
        "Reparto": "CodReparto"
    }, inplace=True)

    df = df.dropna(subset=["Data"])
    df["Data"] = pd.to_datetime(df["Data"]).dt.date
    df["Data"] = pd.to_datetime(df["Data"].astype(str), format="%Y-%m-%d").dt.strftime("%d/%m/%Y")

    df["Reparto"] = df["CodReparto"].map({500100: "OLO", 400340: "TIM"})
    df["Mese"] = pd.to_datetime(df["Data"], format="%d/%m/%Y").dt.month
    df["MeseNome"] = pd.to_datetime(df["Data"], format="%d/%m/%Y").dt.strftime("%B")

    return df


# --- Funzione per calcolare il riepilogo ---
def calcola_blocco(df_blocco):
    gestiti_ftth = df_blocco[df_blocco["TipoImpianto"] == "FTTH"].shape[0]
    espletati_ftth = df_blocco[(df_blocco["TipoImpianto"] == "FTTH") & (df_blocco["Causale"] == "COMPLWR")].shape[0]
    resa_ftth = (espletati_ftth / gestiti_ftth * 100) if gestiti_ftth > 0 else None

    gestiti_non_ftth = df_blocco[df_blocco["TipoImpianto"] != "FTTH"].shape[0]
    espletati_non_ftth = df_blocco[(df_blocco["TipoImpianto"] != "FTTH") & (df_blocco["Causale"] == "COMPLWR")].shape[0]
    resa_non_ftth = (espletati_non_ftth / gestiti_non_ftth * 100) if gestiti_non_ftth > 0 else None

    return pd.Series({
        "Impianti gestiti FTTH": gestiti_ftth,
        "Impianti espletati FTTH": espletati_ftth,
        "Resa FTTH": resa_ftth,
        "Impianti gestiti ≠ FTTH": gestiti_non_ftth,
        "Impianti espletati ≠ FTTH": espletati_non_ftth,
        "Resa ≠ FTTH": resa_non_ftth
    })


def calcola_riepilogo(df_grouped):
    return df_grouped.apply(calcola_blocco).reset_index()


# --- Funzione per colorare le celle ---
def color_cells(val, col_name):
    if pd.isna(val):
        return ""
    if "FTTH" in col_name and "Resa" in col_name:
        return "background-color: #c6f6c6" if val >= 75 else "background-color: #f6c6c6"
    if "≠ FTTH" in col_name and "Resa" in col_name:
        return "background-color: #c6f6c6" if val >= 70 else "background-color: #f6c6c6"
    return ""


def apply_color(df):
    return df.style.applymap(lambda val: color_cells(val, "Resa FTTH"), subset=["Resa FTTH"]) \
                   .applymap(lambda val: color_cells(val, "Resa ≠ FTTH"), subset=["Resa ≠ FTTH"])


# --- MAIN APP ---
st.set_page_config(layout="wide")
st.image("LogoEuroirte.jpg", width=150)
st.title("Avanzamento Produzione Delivery - Euroirte s.r.l.")
st.markdown(f"🗓️ **Dati aggiornati al: {datetime.now().strftime('%d/%m/%Y')}**")

df = load_data()

# --- FILTRI ---
mesi_unici = ["Tutti"] + sorted(df["MeseNome"].unique(), key=lambda m: datetime.strptime(m, "%B").month)
tecnici_unici = ["Tutti"] + sorted(df["Tecnico"].dropna().unique())
reparti_unici = ["Tutti"] + sorted(df["Reparto"].dropna().unique())
date_uniche = ["Tutte"] + sorted(df["Data"].unique(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"))

col1, col2, col3, col4 = st.columns(4)
mese_selezionato = col1.selectbox("Seleziona un mese", mesi_unici)
tecnico_selezionato = col2.selectbox("Seleziona un tecnico", tecnici_unici)
reparto_selezionato = col3.selectbox("Seleziona un reparto", reparti_unici)
data_selezionata = col4.selectbox("Seleziona una data (opzionale)", date_uniche)

# --- FILTRA I DATI ---
if mese_selezionato != "Tutti":
    df = df[df["MeseNome"] == mese_selezionato]
if tecnico_selezionato != "Tutti":
    df = df[df["Tecnico"] == tecnico_selezionato]
if reparto_selezionato != "Tutti":
    df = df[df["Reparto"] == reparto_selezionato]
if data_selezionata != "Tutte":
    df = df[df["Data"] == data_selezionata]

# --- CALCOLA E MOSTRA RIEPILOGHI ---
st.subheader("📆 Andamento Mensile")
df_mensile = calcola_riepilogo(df.groupby(["MeseNome", "Tecnico"]))
st.dataframe(apply_color(df_mensile), use_container_width=True)

st.subheader("📅 Dettaglio Giornaliero")
df_giornaliero = calcola_riepilogo(df.groupby(["Data", "Tecnico"]))
st.dataframe(apply_color(df_giornaliero), use_container_width=True)
