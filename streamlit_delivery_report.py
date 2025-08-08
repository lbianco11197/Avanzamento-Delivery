
import streamlit as st
import pandas as pd
from datetime import datetime
import os

def load_data():
    df = pd.read_excel("delivery.xlsx", usecols=[
        "Data Esec. Lavoro", "Tecnico Assegnato", "Tipo Impianto", "Causale Chiusura", "Reparto"
    ])
    
    df.rename(columns={
        "Data Esec. Lavoro": "Data",
        "Tecnico Assegnato": "Tecnico",
        "Tipo Impianto": "TipoImpianto",
        "Causale Chiusura": "Causale",
        "Reparto": "Reparto"
    }, inplace=True)

    df.dropna(subset=["Data"], inplace=True)
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df.dropna(subset=["Data"], inplace=True)
    df["DataStr"] = df["Data"].dt.strftime("%d/%m/%Y")
    df["Mese"] = df["Data"].dt.month

    mesi_italiani = {
        1: "Gennaio", 2: "Febbraio", 3: "Marzo", 4: "Aprile",
        5: "Maggio", 6: "Giugno", 7: "Luglio", 8: "Agosto",
        9: "Settembre", 10: "Ottobre", 11: "Novembre", 12: "Dicembre"
    }
    df["MeseNome"] = df["Mese"].map(mesi_italiani)
    return df

df = load_data()
st.write(df)
