import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# Configurazione pagina Streamlit
st.set_page_config(page_title="Campania Finance Dashboard", page_icon="📊", layout="wide")

st.title("📊 Osservatorio Finanziario: Aziende della Campania")
st.markdown("Analisi quantitativa e fondamentale in tempo reale per lo **Starting Finance Club**.")

# 1. Definizione della Watchlist Campana
aziende_campane = {
    'DM.MI': 'Digital Magics',
    'DHH.MI': 'DHH',
    'CLE.MI': 'Class Editori',
    'HI.MI': 'Health Italia'
}
tickers = list(aziende_campane.keys())

# Cache dei dati per evitare di bloccare l'app a ogni clic
@st.cache_data(ttl=3600)
def load_financial_data(tickers):
    data = []
    for t in tickers:
        stock = yf.Ticker(t)
        info = stock.info
        data.append({
            'Ticker': t,
            'Azienda': aziende_campane[t],
            'Settore': info.get('sector', 'N/A'),
            'Prezzo (€)': info.get('currentPrice', info.get('previousClose', 0)),
            'Market Cap (€M)': round(info.get('marketCap', 0) / 1e6, 2) if info.get('marketCap') else 0,
            'P/E Trailing': info.get('trailingPE', np.nan),
            'EV/EBITDA': info.get('enterpriseToEbitda', np.nan)
        })
    return pd.DataFrame(data)

@st.cache_data(ttl=3600)
def load_historical_data(tickers):
    prices = yf.download(tickers, period='2y')['Close']
    # Gestione formati multi-index delle versioni recenti di yfinance
    if isinstance(prices.columns, pd.MultiIndex):
        prices.columns = prices.columns.get_level_values(1)
    return prices

# Caricamento effettivo dei dati
with st.spinner("Estrazione dati da Yahoo Finance in corso..."):
    df_fondamentali = load_financial_data(tickers)
    df_prezzi = load_historical_data(tickers)

# --- SEZIONE 1: KPIs DI SINTESI ---
st.subheader("📌 Panoramica di Mercato")
cols = st.columns(len(tickers))
for i, row in df_fondamentali.iterrows():
    with cols[i]:
        st.metric(
            label=row['Azienda'], 
            value=f"€ {row['Prezzo (€)']:.2f}", 
            delta=f"Cap: € {row['Market Cap (€M)']}M"
        )

st.divider()

# --- SEZIONE 2: GRAFICI INTERATTIVI ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📈 Trend Storico Normalizzato (Base 100)")
    # Normalizzazione per confrontare i trend indipendentemente dal prezzo nominale
    df_normalizzato = (df_prezzi / df_prezzi.iloc[0]) * 100
    st.line_chart(df_normalizzato)
    st.caption("Andamento degli ultimi 2 anni riscalato a base 100 per facilitare il confronto.")

with col_right:
    st.subheader("📊 Multipli di Mercato a Confronto")
    # Grafico a barre dei P/E
    df_pe = df_fondamentali[['Azienda', 'P/E Trailing']].dropna()
    if not df_pe.empty:
        st.bar_chart(df_pe.set_index('Azienda'))
    else:
        st.info("Dati P/E non disponibili al momento per i ticker selezionati.")

st.divider()

# --- SEZIONE 3: TABELLA DATI COMPLETA ---
st.subheader("🗂️ Dettaglio Fondamentali")
st.dataframe(df_fondamentali.set_index('Ticker'), use_container_width=True)

# Bottone di download dei dati in CSV direttamente dalla dashboard
csv = df_fondamentali.to_csv(index=False).encode('utf-8')
st.download_button("📥 Scarica Report in CSV", data=csv, file_name="report_finanziario_campania.csv", mime="text/csv")

# Scarica l'indice di riferimento insieme ai titoli
benchmark = yf.download('FTSEMIB.MI', period='2y')['Close']
rendimenti_benchmark = benchmark.pct_change().dropna()

# Calcolo del Beta per ciascun titolo (da inserire nel loop dei ticker)
varianza_mercato = rendimenti_benchmark.var()
covarianza = rendimenti_titolo.cov(rendimenti_benchmark)
beta = covarianza / varianza_mercato
