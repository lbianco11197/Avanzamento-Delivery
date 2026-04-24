import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from pathlib import Path

def set_page_background(image_path: str):
    """Imposta un'immagine di sfondo full-screen come background dell'app Streamlit."""
    p = Path(image_path)
    if not p.exists():
        st.warning(f"Background non trovato: {image_path}")
        return
    encoded = base64.b64encode(p.read_bytes()).decode()
    css = f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background: url("data:image/png;base64,{encoded}") center/cover no-repeat fixed;
    }}
    [data-testid="stHeader"], [data-testid="stSidebar"] {{
        background-color: rgba(255,255,255,0.0) !important;
    }}
    html, body, [data-testid="stApp"] {{
        color: #0b1320 !important;
    }}
    .stDataFrame, .stTable, .stSelectbox div[data-baseweb="select"],
    .stTextInput, .stNumberInput, .stDateInput, .stMultiSelect,
    .stRadio, .stCheckbox, .stSlider, .stFileUploader, .stTextArea {{
        background-color: rgba(255,255,255,0.88) !important;
        border-radius: 10px;
        backdrop-filter: blur(0.5px);
        border: 1px solid #ddd !important;
    }}
    .stDataFrame table, .stDataFrame th, .stDataFrame td {{
        color: #0b1320 !important;
        background-color: rgba(255,255,255,0.0) !important;
    }}
    .stButton > button, .stDownloadButton > button, .stLinkButton > a {{
        background-color: #ffffff !important;
        color: #0b1320 !important;
        border: 1px solid #ddd !important;
        border-radius: 8px;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

st.set_page_config(layout="wide")
set_page_background("sfondo.png")

st.title("📊 Avanzamento Produzione Delivery - Euroirte s.r.l.")
st.image("LogoEuroirte.png", width=180)
st.link_button("🏠 Torna alla Home", url="https://homeeuroirte.streamlit.app/")

def pulisci_tecnici(df):
    """Rimuove righe senza tecnico e normalizza i nomi"""
    df["Tecnico"] = (
        df["Tecnico"]
        .astype(str)
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
        .str.upper()
    )
    df = df[df["Tecnico"].notna() & (df["Tecnico"] != "") & (df["Tecnico"] != "NAN")]
    return df

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
    df["Data"] = pd.to_datetime(df["Data"], dayfirst=True, errors="coerce")
    df.dropna(subset=["Data"], inplace=True)
    df["DataStr"] = df["Data"].dt.strftime("%d/%m/%Y")
    df = pulisci_tecnici(df)

    df["Tecnico"] = (
        df["Tecnico"]
        .astype(str)
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
        .str.upper()
    )

    df["Mese"] = pd.to_datetime(df["Data"]).dt.month
    mesi_italiani = {
        1: "Gennaio", 2: "Febbraio", 3: "Marzo", 4: "Aprile",
        5: "Maggio", 6: "Giugno", 7: "Luglio", 8: "Agosto",
        9: "Settembre", 10: "Ottobre", 11: "Novembre", 12: "Dicembre"
    }
    df["MeseNome"] = df["Mese"].map(mesi_italiani)

    df["Reparto"] = df["Reparto"].map({400340: "TIM", 500100: "OLO"})

    return df

def load_resa_data():
    df = pd.read_excel("resa.xlsx", usecols=[
        "Data Inizio Appuntamento", "Tipo Impianto", "Causale Chiusura", "Reparto","Stato"
    ])

    df.rename(columns={
        "Data Inizio Appuntamento": "Data",
        "Tipo Impianto": "TipoImpianto",
        "Causale Chiusura": "Causale",
        "Reparto": "Reparto"
    }, inplace=True)

    # parsing data + ORA → teniamo solo la data
    df["Data"] = pd.to_datetime(df["Data"], dayfirst=True, errors="coerce")
    df.dropna(subset=["Data"], inplace=True)
    df["Data"] = df["Data"].dt.normalize()  # 👉 rimuove l'ora

    # filtro reparto corretto
    df["Reparto"] = df["Reparto"].astype(str).str.strip()
    df = df[df["Reparto"] == "400340"]

    # filtro stato diverso da 50
    #df["Stato"] = df["Stato"].astype(str).str.strip()
    #df = df[df["Stato"] != "50 - Annullata"]

    # normalizzazione
    df["TipoImpianto"] = df["TipoImpianto"].astype(str).str.strip().str.upper()

    # ⚠️ QUI LA CORREZIONE IMPORTANTE
    # NON trasformiamo in stringa vuota → lasciamo i NaN
    df["Causale"] = df["Causale"].astype(str).str.strip().str.upper()
    df["Causale"] = df["Causale"].replace("NAN", pd.NA)

    df["DataStr"] = df["Data"].dt.strftime("%d/%m/%Y")
    df["Mese"] = df["Data"].dt.month

    mesi_italiani = {
        1: "Gennaio", 2: "Febbraio", 3: "Marzo", 4: "Aprile",
        5: "Maggio", 6: "Giugno", 7: "Luglio", 8: "Agosto",
        9: "Settembre", 10: "Ottobre", 11: "Novembre", 12: "Dicembre"
    }
    df["MeseNome"] = df["Mese"].map(mesi_italiani)

    return df

def filtra_resa_per_periodo(df_resa, tmese, giorno_sel):
    df_filtrato = df_resa.copy()

    if tmese != "Tutti":
        df_filtrato = df_filtrato[df_filtrato["MeseNome"] == tmese]

    if giorno_sel != "Tutti":
        df_filtrato = df_filtrato[df_filtrato["DataStr"] == giorno_sel]

    return df_filtrato

def calcola_tabella_resa(df, tipo_label):
    if tipo_label.upper() == "FTTH":
        df_tipo = df[df["TipoImpianto"] == "FTTH"].copy()
    else:
        df_tipo = df[df["TipoImpianto"] == "FTTC"].copy()

    totale = len(df_tipo)
    ok = df_tipo["Causale"].eq("COMPLWR").sum()
    ko = totale - ok
    resa = (ok / totale * 100) if totale > 0 else 0

    if totale == 0:
        data_label = "-"
    else:
        date_uniche = df_tipo["Data"].dt.normalize().nunique()
        mesi_unici = df_tipo["Data"].dt.to_period("M").nunique()

        if date_uniche == 1:
            data_label = df_tipo["Data"].iloc[0].strftime("%d/%m/%Y")
        elif mesi_unici == 1:
            data_label = df_tipo["MeseNome"].iloc[0]
        else:
            data_label = "Totale"

    tabella = pd.DataFrame([{
        "Data": data_label,
        "Ok": int(ok),
        "Ko": int(ko),
        "Totale complessivo": int(totale),
        "Resa": round(resa)
    }])

    return tabella

def colore_resa(v):
    if pd.isna(v):
        return ""
    if v > 64:
        return "background-color: #ccffcc"
    elif v >= 55:
        return "background-color: #fff3b0"
    else:
        return "background-color: #ff9999"

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

file_path = "delivery.xlsx"
df = load_data()
df_resa = load_resa_data()
st.markdown(f"🗓️ **Dati aggiornati al:** {df['Data'].max().strftime('%d/%m/%Y')}")

ordine_mesi = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
               "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]

mesi_presenti = [m for m in ordine_mesi if m in df["MeseNome"].unique()]
mesi = ["Tutti"] + mesi_presenti
tecnici = ["Tutti"] + sorted(df["Tecnico"].dropna().unique())
reparti = ["Tutti"] + sorted(df["Reparto"].dropna().unique())

riga1_col1, riga1_col2 = st.columns(2)
riga2_col1, riga2_col2 = st.columns(2)

tmese = riga1_col1.selectbox("📆 Seleziona un mese", mesi)
df_filtrato_temp = df[df["MeseNome"] == tmese] if tmese != "Tutti" else df

giorni = ["Tutti"] + sorted(df_filtrato_temp["DataStr"].dropna().unique(), key=lambda x: datetime.strptime(x, "%d/%m/%Y"))
giorno_sel = riga1_col2.selectbox("📆 Seleziona un giorno", giorni)

reparto = riga2_col1.selectbox("🧑‍🔧 Seleziona un reparto", reparti)
tecnico = riga2_col2.selectbox("🧑‍🔧 Seleziona un tecnico", tecnici)

df_filtrato_temp = df[df["MeseNome"] == tmese] if tmese != "Tutti" else df

df_filtrato = df.copy()
if tmese != "Tutti":
    df_filtrato = df_filtrato[df_filtrato["MeseNome"] == tmese]
if tecnico != "Tutti":
    df_filtrato = df_filtrato[df_filtrato["Tecnico"] == tecnico]
if reparto != "Tutti":
    df_filtrato = df_filtrato[df_filtrato["Reparto"] == reparto]

st.subheader("📆 Dettaglio Giornaliero")
if giorno_sel != "Tutti":
    df_det_giornaliero = df_filtrato[df_filtrato["DataStr"] == giorno_sel]
else:
    df_det_giornaliero = df_filtrato.copy()

df_giornaliero = calcola_riepilogo(df_det_giornaliero.groupby(["Data", "Tecnico"])).reset_index(drop=True)
df_giornaliero["Data"] = df_giornaliero["Data"].dt.strftime("%d/%m/%Y")

for col in ["Impianti gestiti FTTH", "Impianti espletati FTTH", "Impianti gestiti ≠ FTTH", "Impianti espletati ≠ FTTH"]:
    df_giornaliero[col] = df_giornaliero[col].astype("Int64")
for col in ["Resa FTTH", "Resa ≠ FTTH"]:
    df_giornaliero[col] = df_giornaliero[col].round(0).astype("Int64")

st.dataframe(
    df_giornaliero.style
    .map(
        lambda v: "background-color: #ccffcc" if pd.notna(v) and v >= 70
        else ("background-color: #ff9999" if pd.notna(v) and v < 70 else ""),
        subset=["Resa FTTH", "Resa ≠ FTTH"]
    )
    .format({"Resa FTTH": "{:.0f}%", "Resa ≠ FTTH": "{:.0f}%"})
    .hide(axis="index"),
    use_container_width=True
)

st.subheader("📆 Riepilogo Mensile per Tecnico")
df_mensile = calcola_riepilogo(df_filtrato.groupby(["MeseNome", "Tecnico"]))
for col in ["Impianti gestiti FTTH", "Impianti espletati FTTH", "Impianti gestiti ≠ FTTH", "Impianti espletati ≠ FTTH"]:
    df_mensile[col] = df_mensile[col].astype("Int64")
for col in ["Resa FTTH", "Resa ≠ FTTH"]:
    df_mensile[col] = df_mensile[col].round(0).astype("Int64")

st.dataframe(
    df_mensile.style
    .map(
        lambda v: "background-color: #ccffcc" if pd.notna(v) and v >= 70
        else ("background-color: #ff9999" if pd.notna(v) and v < 70 else ""),
        subset=["Resa FTTH", "Resa ≠ FTTH"]
    )
    .format({"Resa FTTH": "{:.0f}%", "Resa ≠ FTTH": "{:.0f}%"})
    .hide(axis="index"),
    use_container_width=True
)

st.subheader("📊 Resa FTTH e FTTC")

df_resa_filtrato = filtra_resa_per_periodo(df_resa, tmese, giorno_sel)

tabella_resa_ftth = calcola_tabella_resa(df_resa_filtrato, "FTTH")
tabella_resa_fttc = calcola_tabella_resa(df_resa_filtrato, "FTTC")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Resa FTTH")
    st.dataframe(
        tabella_resa_ftth.style
        .map(colore_resa, subset=["Resa"])
        .format({"Resa": "{:.0f}%"}),
        use_container_width=True,
        hide_index=True
    )

with col2:
    st.markdown("### Resa FTTC")
    st.dataframe(
        tabella_resa_fttc.style
        .map(colore_resa, subset=["Resa"])
        .format({"Resa": "{:.0f}%"}),
        use_container_width=True,
        hide_index=True
    )
