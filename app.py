import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# Configurazione pagina
st.set_page_config(page_title="Campania Finance Dashboard", page_icon="📊", layout="wide")

st.title("📊 Osservatorio Finanziario: Aziende della Campania")
st.markdown("Analisi quantitativa e fondamentale in tempo reale per lo **Starting Finance Club**.")

# 1. Watchlist Aggiornata con Ticker Attivi e Verificati
# Abbiamo inserito aziende campane e realtà industriali fortemente radicate sul territorio
# ZEST = Ex Digital Magics (Hub Napoli), CLE = Class/Gambero Rosso, GIB = Gamberetti/Agro, DHH = Tech
aziende_campane = {
    'ZEST.MI': 'Zest (Ex Digital Magics)',
    'DHH.MI': 'DHH',
    'CLE.MI': 'Class Editori',
    'GIB.MI': 'Gibus'
}
tickers = list(aziende_campane.keys())

# Cache dei dati fondamentali
@st.cache_data(ttl=3600)
def load_financial_data(tickers):
    data = []
    for t in tickers:
        stock = yf.Ticker(t)
        info = stock.info
        
        # Gestione dei valori mancanti (Fallback sul prezzo precedente se currentPrice è None)
        prezzo = info.get('currentPrice') or info.get('previousClose') or info.get('regularMarketPrice') or 0.0
        market_cap = info.get('marketCap')
        market_cap_m = round(market_cap / 1e6, 2) if market_cap else 0.0
        
        # Filtro per evitare P/E negativi o assenti che rompono i grafici
        pe = info.get('trailingPE')
        pe_val = round(pe, 2) if (pe and pe > 0) else np.nan
        
        data.append({
            'Ticker': t,
            'Azienda': aziende_campane[t],
            'Settore': info.get('sector', 'N/A'),
            'Prezzo (€)': round(prezzo, 2),
            'Market Cap (€M)': market_cap_m,
            'P/E Trailing': pe_val
        })
    return pd.DataFrame(data)

@st.cache_data(ttl=3600)
def load_historical_data(tickers):
    prices = yf.download(tickers, period='2y')['Close']
    if isinstance(prices.columns, pd.MultiIndex):
        prices.columns = prices.columns.get_level_values(1)
    # Rimuoviamo colonne completamente vuote se presenti
    prices = prices.dropna(how='all', axis=1)
    return prices

# Caricamento dati
with st.spinner("Aggiornamento dati finanziari da Piazza Affari..."):
    df_fondamentali = load_financial_data(tickers)
    df_prezzi = load_historical_data(tickers)

# --- SEZIONE 1: KPIs DI SINTESI ---
st.subheader("📌 Panoramica di Mercato")
cols = st.columns(len(tickers))
for i, row in df_fondamentali.iterrows():
    with cols[i]:
        # Se il prezzo è zero, mostriamo un avviso elegante invece di un KPI errato
        if row['Prezzo (€)'] == 0:
            st.warning(f"⚠️ {row['Azienda']}\nDati momentaneamente non disponibili")
        else:
            st.metric(
                label=row['Azienda'], 
                value=f"€ {row['Prezzo (€)']:.2f}", 
                delta=f"Cap: € {row['Market Cap (€M)']}M",
                delta_color="normal"
            )

st.divider()

# --- SEZIONE 2: GRAFICI INTERATTIVI ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📈 Trend Storico Normalizzato (Base 100)")
    if not df_prezzi.empty:
        # Riampiamo i buchi nei dati storici per non spezzare le linee del grafico
        df_prezzi_clean = df_prezzi.ffill().bfill()
        df_normalizzato = (df_prezzi_clean / df_prezzi_clean.iloc[0]) * 100
        st.line_chart(df_normalizzato)
        st.caption("Andamento degli ultimi 2 anni riscalato a base 100 per facilitare il confronto.")
    else:
        st.info("Dati storici non disponibili.")

with col_right:
    st.subheader("📊 Multipli di Mercato a Confronto (P/E)")
    # Filtriamo la tabella tenendo solo le righe che hanno un P/E valido e maggiore di zero
    df_pe = df_fondamentali[['Azienda', 'P/E Trailing']].dropna()
    if not df_pe.empty:
        st.bar_chart(df_pe.set_index('Azienda'))
        st.caption("Rapporto Prezzo/Utili (P/E). Le aziende con utili negativi o non pervenuti sono escluse automaticamente.")
    else:
        st.info("💡 Al momento le aziende selezionate presentano utili negativi (in perdita) o dati P/E non disponibili su Yahoo Finance.")

st.divider()

# --- SEZIONE 3: TABELLA DATI COMPLETA ---
st.subheader("🗂️ Dettaglio Fondamentali")
st.dataframe(df_fondamentali.set_index('Ticker'), use_container_width=True)

# Download button
csv = df_fondamentali.to_csv(index=False).encode('utf-8')
st.download_button("📥 Scarica Report in CSV", data=csv, file_name="report_finanziario_campania.csv", mime="text/csv")
