import streamlit as st
import pandas as pd
from datetime import datetime
import locale

# Imposta la pagina in orizzontale
st.set_page_config(layout="wide")

# Imposta la localizzazione italiana per la visualizzazione dei mesi
try:
    locale.setlocale(locale.LC_TIME, 'it_IT.utf8')
except:
    pass

# Logo
st.image("LogoEuroirte.jpg", width=150)

# Titolo
st.title("Avanzamento Produzione Delivery - Euroirte s.r.l.")

# Funzione per caricare i dati
@st.cache_data(ttl=0)
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
        "Reparto": "Reparto"
    }, inplace=True)

    df.dropna(subset=["Data"], inplace=True)
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df.dropna(subset=["Data"], inplace=True)
    df["Data"] = df["Data"].dt.strftime("%d/%m/%Y")

    df["Mese"] = pd.to_datetime(df["Data"], format="%d/%m/%Y").dt.month
    mesi_italiani = {
        1: "Gennaio", 2: "Febbraio", 3: "Marzo", 4: "Aprile",
        5: "Maggio", 6: "Giugno", 7: "Luglio", 8: "Agosto",
        9: "Settembre", 10: "Ottobre", 11: "Novembre", 12: "Dicembre"
    }
    df["MeseNome"] = df["Mese"].map(mesi_italiani)

    df["Reparto"] = df["Reparto"].map({400340: "TIM", 500100: "OLO"})

    return df

# Funzione per calcolo riepilogo
def calcola_riepilogo(gruppo):
    def calcola_blocco(df_blocco):
        gestiti_ftth = df_blocco[df_blocco["TipoImpianto"] == "FTTH"].shape[0]
        espletati_ftth = df_blocco[(df_blocco["TipoImpianto"] == "FTTH") & (df_blocco["Causale"] == "COMPLWR")].shape[0]
        resa_ftth = None if gestiti_ftth == 0 else int(round((espletati_ftth / gestiti_ftth) * 100))

        gestiti_non = df_blocco[df_blocco["TipoImpianto"] != "FTTH"].shape[0]
        espletati_non = df_blocco[(df_blocco["TipoImpianto"] != "FTTH") & (df_blocco["Causale"] == "COMPLWR")].shape[0]
        resa_non = None if gestiti_non == 0 else int(round((espletati_non / gestiti_non) * 100))

        return pd.Series({
            "Impianti gestiti FTTH": gestiti_ftth,
            "Impianti espletati FTTH": espletati_ftth,
            "Resa FTTH": resa_ftth,
            "Impianti gestiti ≠ FTTH": gestiti_non,
            "Impianti espletati ≠ FTTH": espletati_non,
            "Resa ≠ FTTH": resa_non
        })

    return gruppo.apply(calcola_blocco)

# Carica i dati
df = load_data()

# Mostra la data di aggiornamento
ultima_data = pd.to_datetime(df["Data"], format="%d/%m/%Y").max().strftime("%d/%m/%Y")
st.markdown(f"<div style='color: #6c757d; font-weight: 500;'>🗓️ Dati aggiornati al: {ultima_data}</div>", unsafe_allow_html=True)

# Sidebar filtri
ordine_mesi = [
    "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
    "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
]

# Filtra solo i mesi presenti nei dati
mesi_presenti = [mese for mese in ordine_mesi if mese in df["MeseNome"].unique()]

mesi = ["Tutti"] + mesi_presenti
tecnici = ["Tutti"] + sorted(df["Tecnico"].dropna().unique())
reparti = ["Tutti"] + sorted(df["Reparto"].dropna().unique())

tmese = st.selectbox("Seleziona un mese", mesi)
tecnico = st.selectbox("Seleziona un tecnico", tecnici)
reparto = st.selectbox("Seleziona un reparto", reparti)

# Applica i filtri se selezionati
df_filtrato = df.copy()
if tmese != "Tutti":
    df_filtrato = df_filtrato[df_filtrato["MeseNome"] == tmese]
if tecnico != "Tutti":
    df_filtrato = df_filtrato[df_filtrato["Tecnico"] == tecnico]
if reparto != "Tutti":
    df_filtrato = df_filtrato[df_filtrato["Reparto"] == reparto]

# --- Dettaglio Giornaliero ---
st.subheader("📅 Dettaglio Giornaliero")

# Filtro per mese e data
mese_giornaliero = st.selectbox("Seleziona un mese per il dettaglio giornaliero", mesi_presenti)
giorni_disponibili = sorted(df[df["MeseNome"] == mese_giornaliero]["Data"].unique().tolist())
giorno_giornaliero = st.selectbox("Seleziona un giorno", ["Tutti"] + giorni_disponibili)

df_det_giornaliero = df[df["MeseNome"] == mese_giornaliero]
if giorno_giornaliero != "Tutti":
    df_det_giornaliero = df_det_giornaliero[df_det_giornaliero["Data"] == giorno_giornaliero]

df_giornaliero = calcola_riepilogo(df_det_giornaliero.groupby(["Data", "Tecnico"])).reset_index()

st.dataframe(
    df_giornaliero.style
    .format({
        "Resa FTTH": "{:.0f}%",
        "Resa ≠ FTTH": "{:.0f}%"
    })
    .applymap(
        lambda v: "background-color: #d4f4dd" if pd.notna(v) and v >= 70
        else ("background-color: #f4cccc" if pd.notna(v) and v < 70 else ""),
        subset=["Resa FTTH", "Resa ≠ FTTH"]
    ),
    use_container_width=True
)

# --- Andamento Mensile ---
st.subheader("📅 Andamento Mensile")
df_mensile = calcola_riepilogo(df_filtrato.groupby(["MeseNome", "Tecnico"])).reset_index()

# Colorazione semaforica
def color_map(val):
    if pd.isna(val):
        return ""
    return "background-color: #d4edda;" if val >= 70 else "background-color: #f8d7da;"

st.dataframe(df_mensile.style.format({
    "Resa FTTH": "{}%",
    "Resa ≠ FTTH": "{}%",
    "Impianti gestiti FTTH": "{:.0f}",
    "Impianti espletati FTTH": "{:.0f}",
    "Impianti gestiti ≠ FTTH": "{:.0f}",
    "Impianti espletati ≠ FTTH": "{:.0f}"
}).applymap(color_map, subset=["Resa FTTH", "Resa ≠ FTTH"]))


