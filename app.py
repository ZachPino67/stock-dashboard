import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests

# --- PAGE CONFIG ---
st.set_page_config(page_title="QUANT-X: Supply Chain Edition", page_icon="⛓️", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .stApp {background-color: #0e1117;}
    div.stButton > button:first-child {background-color: #00FF00; color: black;}
</style>
""", unsafe_allow_html=True)

# --- THE INTELLIGENCE DATABASE (RELATIONSHIPS) ---
# We map tickers to Human Names + The "Why"
RELATIONSHIPS = {
    'NVDA': [
        {'ticker': 'TSM', 'name': 'Taiwan Semi', 'role': 'Supplier (Foundry)', 'why': 'Manufactures 100% of Nvidia chips.'},
        {'ticker': 'SMCI', 'name': 'Super Micro', 'role': 'Customer/Partner', 'why': 'Builds the servers NVDA chips go into.'},
        {'ticker': 'VRT', 'name': 'Vertiv', 'role': 'Infrastructure', 'why': 'Cooling systems for AI Data Centers.'},
        {'ticker': 'AMD', 'name': 'AMD', 'role': 'Rival', 'why': 'Direct competitor in GPU market.'}
    ],
    'AAPL': [
        {'ticker': 'SWKS', 'name': 'Skyworks', 'role': 'Supplier (Radio)', 'why': 'Makes 5G/Antenna chips for iPhone.'},
        {'ticker': 'QCOM', 'name': 'Qualcomm', 'role': 'Supplier (Modem)', 'why': 'Provides 5G modems (Critical).'},
        {'ticker': 'CRUS', 'name': 'Cirrus Logic', 'role': 'Supplier (Audio)', 'why': 'Audio chips (80% rev comes from Apple).'},
        {'ticker': 'GLW', 'name': 'Corning', 'role': 'Supplier (Glass)', 'why': 'Makes the "Gorilla Glass" screens.'}
    ],
    'TSLA': [
        {'ticker': 'ALB', 'name': 'Albemarle', 'role': 'Supplier (Raw)', 'why': 'World largest Lithium miner (Batteries).'},
        {'ticker': 'RIVN', 'name': 'Rivian', 'role': 'Rival', 'why': 'High-end EV Truck competitor.'},
        {'ticker': 'BYDDF', 'name': 'BYD', 'role': 'Rival (Global)', 'why': 'Biggest EV rival in China.'}
    ],
    'MSFT': [
        {'ticker': 'CRWD', 'name': 'CrowdStrike', 'role': 'Partner/Risk', 'why': 'Deeply integrated into Windows Security.'},
        {'ticker': 'ORCL', 'name': 'Oracle', 'role': 'Rival (Cloud)', 'why': 'Competes with Azure for AI hosting.'},
        {'ticker': 'ADBE', 'name': 'Adobe', 'role': 'Partner (AI)', 'why': 'Integrating Copilot into Creative Cloud.'}
    ],
    'GOOGL': [
        {'ticker': 'META', 'name': 'Meta', 'role': 'Rival (Ads)', 'why': 'Competes for Digital Ad spend.'},
        {'ticker': 'TTD', 'name': 'Trade Desk', 'role': 'Rival (AdTech)', 'why': 'Open internet ad platform (Anti-Google).'},
        {'ticker': 'SNAP', 'name': 'Snap', 'role': 'Rival (Social)', 'why': 'Competes for Gen-Z eyeballs.'}
    ],
    'AMZN': [
        {'ticker': 'WMT', 'name': 'Walmart', 'role': 'Rival (Retail)', 'why': 'Biggest e-commerce competitor.'},
        {'ticker': 'SHOP', 'name': 'Shopify', 'role': 'Rival (Platform)', 'why': 'Empowers anti-Amazon independent stores.'},
        {'ticker': 'FDX', 'name': 'FedEx', 'role': 'Logistics', 'why': 'Shipping rival/partner ecosystem.'}
    ],
    'META': [
        {'ticker': 'PINS', 'name': 'Pinterest', 'role': 'Rival (Social)', 'why': 'Alternative for visual ad spend.'},
        {'ticker': 'RDDT', 'name': 'Reddit', 'role': 'Data Source', 'why': 'Data licensing for AI training.'}
    ]
}

# --- SIDEBAR ---
st.sidebar.title("⛓️ QUANT-X")
tickers = list(RELATIONSHIPS.keys())
selected_ticker = st.sidebar.selectbox("TARGET ASSET", tickers)
timeframe = st.sidebar.selectbox("Analysis Period", ["3mo", "6mo", "1y"], index=1)

# --- DATA ENGINE ---
@st.cache_data(ttl=60)
def get_data(ticker, period):
    stock = yf.Ticker(ticker)
    df = stock.history(period=period)
    # Basic Indicators
    df['RSI'] = df.ta.rsi(close='Close', length=14)
    # Z-Score
    df['Z_Score'] = (df['Close'] - df['Close'].rolling(20).mean()) / df['Close'].rolling(20).std()
    return df

# --- MAIN LAYOUT ---
df = get_data(selected_ticker, timeframe)
curr_price = df['Close'].iloc[-1]
rsi = df['RSI'].iloc[-1]

c1, c2, c3 = st.columns(3)
c1.metric("Target", selected_ticker, f"${curr_price:.2f}")
c2.metric("RSI Status", f"{rsi:.1f}", "Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral")

st.divider()

# --- THE NEW CORRELATION ENGINE ---
st.subheader(f"🧬 Supply Chain Intelligence: {selected_ticker}")
st.caption("Real-time correlation analysis of suppliers, customers, and rivals.")

# 1. Calculate Correlations
relations = RELATIONSHIPS[selected_ticker]
correlation_data = []

# Normalize Lead Asset for Charting
chart_data = pd.DataFrame()
chart_data[selected_ticker] = (df['Close'] / df['Close'].iloc[0] - 1) * 100

for item in relations:
    try:
        # Get Sympathy Data
        sym_df = yf.Ticker(item['ticker']).history(period=timeframe)
        
        # Sync dates (Critical for correlation)
        sym_df = sym_df['Close'].reindex(df.index, method='ffill')
        
        # Calculate Correlation (Math)
        corr = df['Close'].corr(sym_df)
        
        # Calculate Performance
        perf = (sym_df.iloc[-1] - sym_df.iloc[0]) / sym_df.iloc[0] * 100
        
        # Save for Table
        correlation_data.append({
            "Ticker": item['ticker'],
            "Company": item['name'],
            "Role": item['role'],
            "The Connection": item['why'],
            "Correlation": corr,
            "Performance": perf
        })
        
        # Save for Chart
        chart_data[item['ticker']] = (sym_df / sym_df.iloc[0] - 1) * 100
        
    except:
        continue

# 2. Display Intelligence Table
corr_df = pd.DataFrame(correlation_data)

# Sort by Highest Correlation first
corr_df = corr_df.sort_values(by="Correlation", ascending=False)

# CONFIGURING THE TABLE DISPLAY
st.dataframe(
    corr_df,
    column_config={
        "Correlation": st.column_config.ProgressColumn(
            "Correlation (0-1)",
            help="1.0 =
