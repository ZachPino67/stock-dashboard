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
    
    # 1. MACD (Momentum)
    macd = df.ta.macd(close='Close', fast=12, slow=26, signal=9)
    df = pd.concat([df, macd], axis=1)
    
    # 2. BOLLINGER BANDS (Volatility)
    bb = df.ta.bbands(close='Close', length=20, std=2)
    df = pd.concat([df, bb], axis=1)
    
    # 3. Z-SCORE (Statistical Outlier Detection)
    # (Price - Mean) / StdDev
    df['Z_Score'] = (df['Close'] - df['Close'].rolling(20).mean()) / df['Close'].rolling(20).std()
    
    # 4. RSI
    df['RSI'] = df.ta.rsi(close='Close', length=14)
    
    return df

# --- LAYOUT ---
df = get_quant_data(selected_ticker, timeframe)
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
c3.metric("Z-SCORE (20d)", f
