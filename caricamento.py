import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(layout="wide")

st.image("LogoEuroirte.jpg", width=180)
st.title("Modulo di aggiornamento dati - Delivery")

# --- Autenticazione semplice ---
PASSWORD = "euroirte2025"
password_input = st.text_input("Inserisci la password per modificare i dati", type="password")

if password_input != PASSWORD:
    st.warning("Accesso limitato. Inserisci la password corretta per continuare.")
    st.stop()

st.success("Accesso autorizzato!")

# --- Caricamento file esistente ---
file_path = "delivery.xlsx"
if not os.path.exists(file_path):
    st.error("Il file delivery.xlsx non esiste nel progetto.")
    st.stop()

try:
    df = pd.read_excel(file_path)
except Exception as e:
    st.error(f"Errore nel caricamento del file: {e}")
    st.stop()

st.markdown("### Aggiungi nuove righe manualmente")

with st.form("manual_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        data_esec = st.date_input("Data Esec. Lavoro", value=datetime.today())
        causale = st.text_input("Causale Chiusura")
    with col2:
        tecnico = st.text_input("Tecnico Assegnato")
        reparto = st.selectbox("Reparto", [400340, 500100])
    with col3:
        tipo_impianto = st.text_input("Tipo Impianto")

    submitted = st.form_submit_button("Aggiungi riga")
    if submitted:
        nuova_riga = {
            "Data Esec. Lavoro": pd.to_datetime(data_esec),
            "Tecnico Assegnato": tecnico,
            "Tipo Impianto": tipo_impianto,
            "Causale Chiusura": causale,
            "Reparto": reparto
        }
        df = pd.concat([df, pd.DataFrame([nuova_riga])], ignore_index=True)
        df.to_excel(file_path, index=False)
        st.success("Nuova riga aggiunta con successo!")

# --- Upload massivo ---
st.markdown("### Oppure carica più righe da un file Excel")
uploaded_file = st.file_uploader("Carica un file Excel con le nuove righe", type=["xlsx"])
if uploaded_file is not None:
    try:
        new_data = pd.read_excel(uploaded_file)
        expected_cols = ["Data Esec. Lavoro", "Tecnico Assegnato", "Tipo Impianto", "Causale Chiusura", "Reparto"]
        if not all(col in new_data.columns for col in expected_cols):
            st.error(f"Il file deve contenere le seguenti colonne: {expected_cols}")
        else:
            df = pd.concat([df, new_data], ignore_index=True)
            df.to_excel(file_path, index=False)
            st.success("File caricato e righe aggiunte con successo!")
    except Exception as e:
        st.error(f"Errore durante il caricamento del file: {e}")

# --- Mostra le ultime righe aggiornate ---
st.markdown("### Anteprima degli ultimi dati")
st.dataframe(df.tail(10), use_container_width=True)