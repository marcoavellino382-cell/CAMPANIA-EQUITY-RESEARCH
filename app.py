import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# Configurazione della pagina
st.set_page_config(page_title="Campania Finance Dashboard", page_icon="📊", layout="wide")

st.title("📊 Osservatorio Finanziario: Aziende della Campania")
st.markdown("Analisi quantitativa in tempo reale per lo **Starting Finance Club**.")

# 1. Watchlist Aziende Campane con Ticker ad alta liquidità
aziende_campane = {
    'ZEST.MI': 'Zest (Ex Digital Magics)',
    'DHH.MI': 'DHH',
    'CLE.MI': 'Class Editori',
    'SCK.MI': 'Sciuker Frames'
}
tickers = list(aziende_campane.keys())

# 2. Funzione di scaricamento ottimizzata per la struttura MultiIndex
@st.cache_data(ttl=600)  # Ridotto il tempo di cache per evitare blocchi temporanei
def load_all_market_data(tickers):
    # Scarichiamo i dati esplicitando l'argomento group_by per controllare la struttura
    df_raw = yf.download(tickers, period='2y', group_by='ticker')
    
    rows = []
    df_prezzi_chiusura = pd.DataFrame()
    
    for t in tickers:
        try:
            # Estrazione sicura della serie storiche di chiusura dal MultiIndex di yfinance
            if t in df_raw.columns.get_level_values(0):
                serie_titolo = df_raw[t]['Close'].dropna()
            else:
                # Fallback se yfinance restituisce un formato piatto flat
                serie_titolo = df_raw['Close'][t].dropna() if t in df_raw['Close'].columns else pd.Series()
            
            if not serie_titolo.empty:
                # Applichiamo una pulizia immediata sulla serie del singolo titolo
                serie_titolo = serie_titolo.ffill().bfill()
                
                # Salviamo la serie pulita nel dataframe per i grafici
                df_prezzi_chiusura[t] = serie_titolo
                
                prezzo_attuale = float(serie_titolo.iloc[-1])
                prezzo_iniziale = float(serie_titolo.iloc[0])
                
                rend_titolo = ((prezzo_attuale / prezzo_iniziale) - 1) * 100
                vol_titolo = serie_titolo.pct_change().dropna().std() * np.sqrt(252) * 100
            else:
                prezzo_attuale, rend_titolo, vol_titolo = 0.0, 0.0, 0.0
        except Exception:
            prezzo_attuale, rend_titolo, vol_titolo = 0.0, 0.0, 0.0
            
        rows.append({
            'Ticker': t,
            'Azienda': aziende_campane[t],
            'Prezzo Ultimo (€)': round(prezzo_attuale, 2),
            'Rendimento 2A (%)': round(rend_titolo, 2),
            'Volatilità Ann. (%)': round(vol_titolo, 2)
        })
        
    return pd.DataFrame(rows), df_prezzi_chiusura

# Caricamento dei dati puliti
with st.spinner("Estrazione e calcolo delle metriche quantitative di Piazza Affari..."):
    df_fondamentali, df_prezzi = load_all_market_data(tickers)

# --- SEZIONE 1: KPIs DI SINTESI ---
st.subheader("📌 Panoramica di Mercato (Prezzi Live)")
cols = st.columns(len(tickers))
for i, row in df_fondamentali.iterrows():
    with cols[i]:
        st.metric(
            label=row['Azienda'], 
            value=f"€ {row['Prezzo Ultimo (€)']:.2f}", 
            delta=f"Rendimento: {row['Rendimento 2A (%)']:.2f}%"
        )

st.divider()

# --- SEZIONE 2: GRAFICI INTERATTIVI ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📈 Trend Storico Normalizzato (Base 100)")
    if not df_prezzi.empty:
        # Normalizzazione in base 100 partendo dal primo dato disponibile
        df_normalizzato = (df_prezzi / df_prezzi.iloc[0]) * 100
        st.line_chart(df_normalizzato)
        st.caption("Andamento degli ultimi 2 anni riscalato a base 100 per facilitare il confronto.")
    else:
        st.info("Attesa sincronizzazione dati storici.")

with col_right:
    st.subheader("📊 Rischio vs Rendimento: Volatilità a Confronto")
    # Filtro stringente per assicurarci che vengano passati solo dati numerici reali al grafico a barre
    df_vol = df_fondamentali[df_fondamentali['Volatilità Ann. (%)'] > 0][['Azienda', 'Volatilità Ann. (%)']]
    if not df_vol.empty:
        st.bar_chart(df_vol.set_index('Azienda'))
        st.caption("Volatilità annualizzata calcolata sugli ultimi 2 anni. Più è alta, più il titolo è rischioso.")
    else:
        st.info("Grafico della volatilità temporaneamente non disponibile.")

st.divider()

# --- SEZIONE 3: TABELLA DATI COMPLETA ---
st.subheader("🗂️ Dettaglio Analisi Quantitativa")
st.dataframe(df_fondamentali.set_index('Ticker'), use_container_width=True)

# Bottone di Download CSV
csv = df_fondamentali.to_csv(index=False).encode('utf-8')
st.download_button("📥 Scarica Report Quantitativo", data=csv, file_name="report_quant_campania.csv", mime="text/csv")
