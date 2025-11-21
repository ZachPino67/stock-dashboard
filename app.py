import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import feedparser
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# --- PAGE CONFIG ---
st.set_page_config(page_title="QUANT-X Terminal", page_icon="☢️", layout="wide")

# --- CUSTOM CSS (HACKER MODE) ---
st.markdown("""
<style>
    .stApp {background-color: #0e1117;}
    div.stButton > button:first-child {background-color: #00FF00; color: black;}
    div[data-testid="stMetricValue"] {font-size: 24px;}
</style>
""", unsafe_allow_html=True)

# --- STRATEGY MAP ---
SYMPATHY_MAP = {
    'NVDA': {'tickers': ['TSM', 'SMCI', 'AMD', 'VRT'], 'role': 'AI Hardware & Power'},
    'AAPL': {'tickers': ['SWKS', 'QCOM', 'CRUS', 'GLW'], 'role': 'iPhone Supply Chain'},
    'TSLA': {'tickers': ['ALB', 'BYDDF', 'RIVN'], 'role': 'Lithium & EV Rivals'},
    'MSFT': {'tickers': ['CRWD', 'PLTR', 'ADBE'], 'role': 'Enterprise SaaS & Cloud'},
    'GOOGL': {'tickers': ['META', 'TTD', 'SNAP'], 'role': 'Digital Ads'},
    'AMZN': {'tickers': ['WMT', 'SHOP', 'FDX', 'UPS'], 'role': 'E-Comm & Logistics'},
    'META': {'tickers': ['PINS', 'SNAP', 'RDDT'], 'role': 'Social Graph'}
}

# --- SIDEBAR ---
st.sidebar.title("☢️ QUANT-X")
tickers = list(SYMPATHY_MAP.keys())
selected_ticker = st.sidebar.selectbox("TARGET ASSET", tickers)
timeframe = st.sidebar.selectbox("Lookback", ["6mo", "1y", "2y"], index=0)

# --- DATA ENGINE ---
@st.cache_data(ttl=60)
def get_quant_data(ticker, period):
    stock = yf.Ticker(ticker)
    df = stock.history(period=period)
    
    if df.empty: return pd.DataFrame()
    
    # 1. MACD (Momentum)
    macd = df.ta.macd(close='Close', fast=12, slow=26, signal=9)
    if macd is not None:
        df = pd.concat([df, macd], axis=1)
    
    # 2. BOLLINGER BANDS (Volatility)
    bb = df.ta.bbands(close='Close', length=20, std=2)
    if bb is not None:
        df = pd.concat([df, bb], axis=1)
    
    # 3. Z-SCORE (Statistical Outlier Detection)
    # (Price - Mean) / StdDev
    df['Z_Score'] = (df['Close'] - df['Close'].rolling(20).mean()) / df['Close'].rolling(20).std()
    
    # 4. RSI
    df['RSI'] = df.ta.rsi(close='Close', length=14)
    
    return df

# --- LAYOUT ---
df = get_quant_data(selected_ticker, timeframe)

if df.empty:
    st.error("Error fetching data. Please reload.")
else:
    curr_price = df['Close'].iloc[-1]
    price_chg = (curr_price - df['Close'].iloc[-2]) / df['Close'].iloc[-2] * 100
    z_score = df['Z_Score'].iloc[-1]
    rsi = df['RSI'].iloc[-1]

    # HEADER METRICS
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("PRICE", f"${curr_price:.2f}", f"{price_chg:.2f}%")
    c2.metric("RSI (14)", f"{rsi:.1f}", delta_color="inverse")

    # Z-Score Coloring
    z_color = "off"
    if z_score > 2: z_color = "inverse" # Red (Sell)
    elif z_score < -2: z_color = "normal" # Green (Buy)
    
    # --- THE LINE THAT WAS BROKEN ---
    c3.metric("Z-SCORE (20d)", f"{z_score:.2f}", "Sigma Deviation", delta_color=z_color)
    # --------------------------------

    # Volatility Check (Bandwidth)
    # We check if columns exist to avoid errors
    bandwidth = 0
    if 'BBP_20_2.0' in df.columns:
        bandwidth = df['BBP_20_2.0'].iloc[-1] # %B
    c4.metric("BOLLINGER %B", f"{bandwidth:.2f}", "Range Position")

    # Signal Logic
    signal = "WAIT"
    if rsi < 30 and z_score < -2: signal = "💎 STRONG BUY"
    elif rsi > 70 and z_score > 2: signal = "🔥 STRONG SELL"
    elif bandwidth > 1.0: signal = "⚠️ BREAKOUT"
    c5.metric("QUANT SIGNAL", signal)

    st.divider()

    # --- MASTER CHART (THE BLOOMBERG VIEW) ---
    # Row 1: Price + Bollinger Bands
    # Row 2: MACD (Momentum)
    # Row 3: Z-Score (Mean Reversion)

    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.05, row_heights=[0.6, 0.2, 0.2])

    # 1. CANDLES & BOLLINGER BANDS
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'],
                    low=df['Low'], close=df['Close'], name="Price"), row=1, col=1)

    # Upper Band
    if 'BBU_20_2.0' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['BBU_20_2.0'], 
                                line=dict(color='rgba(0, 255, 255, 0.3)', width=1), name="Upper BB"), row=1, col=1)
    # Lower Band
    if 'BBL_20_2.0' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['BBL_20_2.0'], 
                                line=dict(color='rgba(0, 255, 255, 0.3)', width=1), fill='tonexty', name="Lower BB"), row=1, col=1)

    # 2. MACD
    if 'MACDh_12_26_9' in df.columns:
        fig.add_trace(go.Bar(x=df.index, y=df['MACDh_12_26_9'], marker_color='cyan', name="MACD Hist"), row=2, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MACD_12_26_9'], line=dict(color='white', width=1), name="MACD"), row=2, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MACDs_12_26_9'], line=dict(color='orange', width=1), name="Signal"), row=2, col=1)

    # 3. Z-SCORE
    fig.add_trace(go.Scatter(x=df.index, y=df['Z_Score'], line=dict(color='yellow', width=2), name="Z-Score"), row=3, col=1)
    # Add Sigma Lines
    fig.add_hline(y=2, line_dash="dot", line_color="red", row=3, col=1, annotation_text="+2 Sigma (Sell)")
    fig.add_hline(y=-2, line_dash="dot", line_color="green", row=3, col=1, annotation_text="-2 Sigma (Buy)")
    fig.add_hline(y=0, line_color="gray", row=3, col=1)

    fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=800, title=f"{selected_ticker} QUANTITATIVE ANALYSIS")
    st.plotly_chart(fig, use_container_width=True)

    # --- SYMPATHY MATRIX ---
    st.subheader("🔗 Supply Chain Correlation")
    sympathy_list = SYMPATHY_MAP[selected_ticker]['tickers']

    # Normalize Data
    norm_data = pd.DataFrame()
    norm_data[selected_ticker] = (df['Close'] / df['Close'].iloc[0] - 1) * 100
    for sym in sympathy_list:
        try:
            sym_hist = yf.Ticker(sym).history(period=timeframe)['Close']
            sym_hist = sym_hist.reindex(df.index, method='ffill')
            norm_data[sym] = (sym_hist / sym_hist.iloc[0] - 1) * 100
        except: pass

    # Chart
    perf_fig = go.Figure()
    for col in norm_data.columns:
        width = 4 if col == selected_ticker else 1
        perf_fig.add_trace(go.Scatter(x=norm_data.index, y=norm_data[col], name=col, line=dict(width=width)))
    perf_fig.update_layout(template="plotly_dark", height=300, margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(perf_fig, use_container_width=True)
