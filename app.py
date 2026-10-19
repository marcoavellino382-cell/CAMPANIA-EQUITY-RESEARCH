import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# Configurazione pagina
st.set_page_config(page_title="Campania Finance Dashboard", page_icon="📊", layout="wide")

st.title("📊 Osservatorio Finanziario: Aziende della Campania")
st.markdown("Analisi quantitativa in tempo reale per lo **Starting Finance Club**.")

# 1. Watchlist Aziende
aziende_campane = {
    'ZEST.MI': 'Zest (Ex Digital Magics)',
    'DHH.MI': 'DHH',
    'CLE.MI': 'Class Editori',
    'GIB.MI': 'Gibus'
}
tickers = list(aziende_campane.keys())

# 2. Funzione unica per scaricare i dati storici (Molto più stabile su Cloud)
@st.cache_data(ttl=1800)
def load_all_market_data(tickers):
    # Scarichiamo la serie storica degli ultimi 2 anni
    df_storico = yf.download(tickers, period='2y')['Close']
    
    # Gestione multi-index per yfinance
    if isinstance(df_storico.columns, pd.MultiIndex):
        df_storico.columns = df_storico.columns.get_level_values(1)
    
    # Pulizia dati storici da eventuali buchi giornalieri
    df_storico = df_storico.ffill().bfill()
    
    # Estraiamo l'ultimo prezzo disponibile in assoluto (ultima riga del dataset)
    ultimi_prezzi = df_storico.iloc[-1]
    
    # Calcolo del rendimento cumulativo degli ultimi 2 anni
    rendimenti_2a = ((df_storico.iloc[-1] / df_storico.iloc[0]) - 1) * 100
    
    # Calcolo della volatilità annualizzata
    volatilita = df_storico.pct_change().dropna().std() * np.sqrt(252) * 100
    
    # Costruiamo la tabella finale usando solo dati matematici estratti dai prezzi storici
    rows = []
    for t in tickers:
        prezzo_attuale = ultimi_prezzi.get(t, 0.0)
        rend_titolo = rendimenti_2a.get(t, 0.0)
        vol_titolo = volatilita.get(t, 0.0)
        
        rows.append({
            'Ticker': t,
            'Azienda': aziende_campane[t],
            'Prezzo Ultimo (€)': round(prezzo_attuale, 2),
            'Rendimento 2A (%)': round(rend_titolo, 2),
            'Volatilità Ann. (%)': round(vol_titolo, 2)
        })
        
    return pd.DataFrame(rows), df_storico

# Caricamento dei dati sicuri
with st.spinner("Estrazione e calcolo metriche quantitative in corso..."):
    df_fondamentali, df_prezzi = load_all_market_data(tickers)

# --- SEZIONE 1: KPIs DI SINTESI ---
st.subheader("📌 Panoramica di Mercato (Prezzi Live)")
cols = st.columns(len(tickers))
for i, row in df_fondamentali.iterrows():
    with cols[i]:
        st.metric(
            label=row['Azienda'], 
            value=f"€ {row['Prezzo Ultimo (€)']:.2f}", 
            delta=f"Rendimento: {row['Rendimento 2A (%)']}%"
        )

st.divider()

# --- SEZIONE 2: GRAFICI INTERATTIVI ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📈 Trend Storico Normalizzato (Base 100)")
    if not df_prezzi.empty:
        df_normalizzato = (df_prezzi / df_prezzi.iloc[0]) * 100
        st.line_chart(df_normalizzato)
        st.caption("Andamento degli ultimi 2 anni riscalato a base 100 per facilitare il confronto.")
    else:
        st.info("Dati storici non disponibili.")

with col_right:
    st.subheader("📊 Rischio vs Rendimento: Volatilità a Confronto")
    # Mostriamo un grafico della volatilità delle aziende per dare un taglio quantitativo da Analyst
    df_vol = df_fondamentali[['Azienda', 'Volatilità Ann. (%)']]
    st.bar_chart(df_vol.set_index('Azienda'))
    st.caption("Volatilità annualizzata calcolata sugli ultimi 2 anni. Più è alta, più il titolo è rischioso.")

st.divider()

# --- SEZIONE 3: TABELLA DATI COMPLETA ---
st.subheader("🗂️ Dettaglio Analisi Quantitativa")
st.dataframe(df_fondamentali.set_index('Ticker'), use_container_width=True)

# Bottone di Download CSV
csv = df_fondamentali.to_csv(index=False).encode('utf-8')
st.download_button("📥 Scarica Report Quantitativo", data=csv, file_name="report_quant_campania.csv", mime="text/csv")
