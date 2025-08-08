import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(layout="wide")

# Imposta sfondo bianco e testo nero
st.markdown("""
    <style>
    /* Sfondo e testo di base */
    html, body, [data-testid="stApp"] {
        background-color: white !important;
        color: black !important;
    }

    /* RADIO BUTTON - Forza etichette nere */
    .stRadio div[role="radiogroup"] label span {
        color: black !important;
        font-weight: 500 !important;
    }

    /* RADIO BUTTON - Mobile layout più leggibile */
    @media only screen and (max-width: 768px) {
        .stRadio > div {
            flex-direction: row !important;
            justify-content: space-evenly;
            gap: 10px;
        }
        .stRadio div[role="radiogroup"] label span {
            font-size: 15px !important;
        }
    }

    /* Pulsanti */
    .stButton > button {
        background-color: white !important;
        color: black !important;
        border: 1px solid #ccc !important;
        border-radius: 6px !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- Autenticazione per upload file Excel ---
#st.sidebar.markdown("## 🔒 Area Amministratore")
#password = st.sidebar.text_input("Inserisci la password per caricare il file", type="password")
#
#if password == "Euroirte111927":  # Cambia questa password come preferisci
#    uploaded_file = st.sidebar.file_uploader("📂 Carica nuovo file 'delivery.xlsx'", type=["xlsx"])
#    if uploaded_file:
#        with open("delivery.xlsx", "wb") as f:
#            f.write(uploaded_file.getbuffer())
#        st.sidebar.success("✅ File aggiornato correttamente!")
#else:
#    st.sidebar.info("Solo gli utenti autorizzati possono aggiornare i dati.")

# --- Titolo ---
st.title("📊 Avanzamento Produzione Delivery - Euroirte s.r.l.")

# Intestazione con logo e bottone
# Logo in alto
st.image("LogoEuroirte.jpg", width=180)

# Bottone sotto il logo
st.link_button("🏠 Torna alla Home", url="https://homeeuroirte.streamlit.app/")

# --- Caricamento dati ---
@st.cache_data(show_spinner=False)

def load_data(file_updated_time):
    df = pd.read_excel("delivery.xlsx", usecols=[
        "Data Esec. Lavoro", "Tecnico", "Tipo Impianto", "Causale Chiusura", "Reparto"
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
    df["DataStr"] = df["Data"].dt.strftime("%d/%m/%Y")

    df["Mese"] = pd.to_datetime(df["Data"]).dt.month
    mesi_italiani = {
        1: "Gennaio", 2: "Febbraio", 3: "Marzo", 4: "Aprile",
        5: "Maggio", 6: "Giugno", 7: "Luglio", 8: "Agosto",
        9: "Settembre", 10: "Ottobre", 11: "Novembre", 12: "Dicembre"
    }
    df["MeseNome"] = df["Mese"].map(mesi_italiani)

    df["Reparto"] = df["Reparto"].map({400340: "TIM", 500100: "OLO"})

    return df

def calcola_blocco(df_blocco):
    gestiti_ftth = df_blocco[df_blocco["TipoImpianto"] == "FTTH"].shape[0]
    espletati_ftth = df_blocco[(df_blocco["TipoImpianto"] == "FTTH") & (df_blocco["Causale"] == "COMPLWR")].shape[0]
    resa_ftth = (espletati_ftth / gestiti_ftth * 100) if gestiti_ftth else None

    gestiti_altro = df_blocco[df_blocco["TipoImpianto"] != "FTTH"].shape[0]
    espletati_altro = df_blocco[(df_blocco["TipoImpianto"] != "FTTH") & (df_blocco["Causale"] == "COMPLWR")].shape[0]
    resa_altro = (espletati_altro / gestiti_altro * 100) if gestiti_altro else None

    return pd.Series({
        "Impianti gestiti FTTH": gestiti_ftth,
        "Impianti espletati FTTH": espletati_ftth,
        "Resa FTTH": resa_ftth,
        "Impianti gestiti ≠ FTTH": gestiti_altro,
        "Impianti espletati ≠ FTTH": espletati_altro,
        "Resa ≠ FTTH": resa_altro
    })

def calcola_riepilogo(gruppo):
    return gruppo.apply(calcola_blocco).reset_index()

# --- Avvia app ---
file_path = "delivery.xlsx"
file_updated_time = os.path.getmtime(file_path)
df = load_data(file_updated_time)
st.markdown(f"🗓️ **Dati aggiornati al:** {df['Data'].max().strftime('%d/%m/%Y')}")

# --- Sidebar Filtri ---
ordine_mesi = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
               "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]

mesi_presenti = [m for m in ordine_mesi if m in df["MeseNome"].unique()]
mesi = ["Tutti"] + mesi_presenti
tecnici = ["Tutti"] + sorted(df["Tecnico"].dropna().unique())
reparti = ["Tutti"] + sorted(df["Reparto"].dropna().unique())

# Layout due righe di colonne: riga 1 mese e giorno, riga 2 reparto e tecnico
riga1_col1, riga1_col2 = st.columns(2)
riga2_col1, riga2_col2 = st.columns(2)

tmese = riga1_col1.selectbox("📆 Seleziona un mese", mesi)
df_filtrato_temp = df[df["MeseNome"] == tmese] if tmese != "Tutti" else df

giorni = ["Tutti"] + sorted(df_filtrato_temp["DataStr"].dropna().unique(), key=lambda x: datetime.strptime(x, "%d/%m/%Y"))
giorno_sel = riga1_col2.selectbox("📆 Seleziona un giorno", giorni)

reparto = riga2_col1.selectbox("🧑‍🔧 Seleziona un reparto", reparti)
tecnico = riga2_col2.selectbox("🧑‍🔧 Seleziona un tecnico", tecnici)


# Filtro iniziale per selezionare i giorni del mese corrente
df_filtrato_temp = df[df["MeseNome"] == tmese] if tmese != "Tutti" else df


# --- Applica filtri ---
df_filtrato = df.copy()
if tmese != "Tutti":
    df_filtrato = df_filtrato[df_filtrato["MeseNome"] == tmese]
if tecnico != "Tutti":
    df_filtrato = df_filtrato[df_filtrato["Tecnico"] == tecnico]
if reparto != "Tutti":
    df_filtrato = df_filtrato[df_filtrato["Reparto"] == reparto]

# --- Dettaglio Giornaliero ---
st.subheader("📆 Dettaglio Giornaliero")
if giorno_sel != "Tutti":
    df_det_giornaliero = df_filtrato[df_filtrato["DataStr"] == giorno_sel]
else:
    df_det_giornaliero = df_filtrato.copy()

df_giornaliero = calcola_riepilogo(df_det_giornaliero.groupby(["Data", "Tecnico"])).reset_index()
df_giornaliero["Data"] = df_giornaliero["Data"].dt.strftime("%d/%m/%Y")

for col in ["Impianti gestiti FTTH", "Impianti espletati FTTH", "Impianti gestiti ≠ FTTH", "Impianti espletati ≠ FTTH"]:
    df_giornaliero[col] = df_giornaliero[col].astype("Int64")
for col in ["Resa FTTH", "Resa ≠ FTTH"]:
    df_giornaliero[col] = df_giornaliero[col].round(0).astype("Int64")

st.dataframe(
    df_giornaliero.style
    .applymap(lambda v: "background-color: #ccffcc" if pd.notna(v) and v >= 70 else ("background-color: #ff9999" if pd.notna(v) and v < 70 else ""), subset=["Resa FTTH", "Resa ≠ FTTH"]),
    use_container_width=True
)

# --- Andamento Mensile ---
st.subheader("📆 Riepilogo Mensile per Tecnico")
df_mensile = calcola_riepilogo(df_filtrato.groupby(["MeseNome", "Tecnico"]))
for col in ["Impianti gestiti FTTH", "Impianti espletati FTTH", "Impianti gestiti ≠ FTTH", "Impianti espletati ≠ FTTH"]:
    df_mensile[col] = df_mensile[col].astype("Int64")
for col in ["Resa FTTH", "Resa ≠ FTTH"]:
    df_mensile[col] = df_mensile[col].round(0).astype("Int64")

st.dataframe(
    df_mensile.style
    .applymap(lambda v: "background-color: #ccffcc" if pd.notna(v) and v >= 70 else ("background-color: #ff9999" if pd.notna(v) and v < 70 else ""), subset=["Resa FTTH", "Resa ≠ FTTH"]),
    use_container_width=True
)
