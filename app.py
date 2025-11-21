import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import feedparser
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests

# --- PAGE CONFIG ---
st.set_page_config(page_title="ProQuant Dashboard", page_icon="📈", layout="wide")

# --- SIDEBAR ---
st.sidebar.header("⚙️ Control Panel")
tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA']
selected_ticker = st.sidebar.selectbox("Select Asset", tickers)
timeframe = st.sidebar.selectbox("Timeframe", ["60d", "1y", "max"], index=0)

# --- UTILS & LOGIC ---
analyzer = SentimentIntensityAnalyzer()
financial_lexicon = {
    'beat': 2.0, 'missed': -2.0, 'record': 1.5, 'growth': 1.5, 
    'slump': -2.0, 'layoffs': -1.5, 'lawsuit': -2.0, 'buyback': 2.0,
    'volatile': -1.0, 'uncertainty': -1.0, 'risk': -1.5,
    'fine': -2.0, 'investigation': -2.0
}
analyzer.lexicon.update(financial_lexicon)

@st.cache_data(ttl=300)
def get_market_mood():
    """Scrapes CNN Fear & Greed Index (Simulated for stability)"""
    # In a real app, you'd scrape CNN. 
    # For this demo, we use VIX (Volatility Index) as a proxy because it's free/stable.
    vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
    
    mood = "Neutral"
    color = "gray"
    if vix < 15: 
        mood = "Greed (Risk On)"
        color = "green"
    elif vix > 25: 
        mood = "Fear (Risk Off)"
        color = "red"
        
    return mood, color, round(vix, 2)

def get_fundamentals(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    return {
        "P/E Ratio": info.get('trailingPE', 'N/A'),
        "Market Cap": info.get('marketCap', 'N/A'),
        "Revenue Growth": info.get('revenueGrowth', 'N/A'),
        "Debt To Equity": info.get('debtToEquity', 'N/A')
    }

# --- MAIN LAYOUT ---
# 1. HEADER & MACRO CONTEXT
mood, mood_color, vix_val = get_market_mood()
c1, c2 = st.columns([3, 1])
with c1:
    st.title(f"📊 {selected_ticker} Pro-Terminal")
with c2:
    st.markdown(f"### Market Mood: :{mood_color}[{mood}]")
    st.caption(f"VIX Level: {vix_val}")

st.divider()

# 2. DATA FETCHING
stock = yf.Ticker(selected_ticker)
df = stock.history(period=timeframe)

# Add Indicators
df['RSI'] = ta.rsi(df['Close'], length=14)
df['SMA_50'] = ta.sma(df['Close'], length=50)
df['SMA_200'] = ta.sma(df['Close'], length=200)

# 3. THE INTERACTIVE CHART (Plotly)
# This replaces the static image with a zoomable, hoverable chart
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                    vertical_spacing=0.1, row_heights=[0.7, 0.3])

# Candlestick
fig.add_trace(go.Candlestick(x=df.index,
                open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'],
                name="Price"), row=1, col=1)

# Moving Averages
fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], 
                         line=dict(color='orange', width=1), name="SMA 50"), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['SMA_200'], 
                         line=dict(color='blue', width=1), name="SMA 200"), row=1, col=1)

# RSI
fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], 
                         line=dict(color='purple', width=2), name="RSI"), row=2, col=1)
# RSI Zones
fig.add_hline(y=70, line_dash="dot", row=2, col=1, annotation_text="Overbought")
fig.add_hline(y=30, line_dash="dot", row=2, col=1, annotation_text="Oversold")

fig.update_layout(xaxis_rangeslider_visible=False, height=600, margin=dict(l=0, r=0, t=0, b=0))
st.plotly_chart(fig, use_container_width=True)

# 4. FUNDAMENTALS & NEWS TABS
tab1, tab2 = st.tabs(["💰 Fundamentals", "📰 AI News Analysis"])

with tab1:
    fund_data = get_fundamentals(selected_ticker)
    fc1, fc2, fc3, fc4 = st.columns(4)
    fc1.metric("P/E Ratio", fund_data["P/E Ratio"])
    
    # Format Market Cap to Billions/Trillions
    mcap = fund_data["Market Cap"]
    if mcap != 'N/A':
        mcap_str = f"${mcap / 1e12:.2f}T" if mcap > 1e12 else f"${mcap / 1e9:.2f}B"
    else:
        mcap_str = "N/A"
    fc2.metric("Market Cap", mcap_str)
    
    fc3.metric("Rev Growth", f"{fund_data['Revenue Growth'] * 100:.1f}%" if fund_data['Revenue Growth'] != 'N/A' else "N/A")
    fc4.metric("Debt/Equity", fund_data['Debt To Equity'])

with tab2:
    rss_url = f'https://finance.yahoo.com/rss/headline?s={selected_ticker}'
    feed = feedparser.parse(rss_url)
    
    if feed.entries:
        for entry in feed.entries[:5]:
            score = analyzer.polarity_scores(entry.title)['compound']
            emoji = "⚪"
            if score > 0.05: emoji = "🟢"
            if score < -0.05: emoji = "🔴"
            
            with st.expander(f"{emoji} {entry.title}"):
                st.write(f"**AI Score:** {score}")
                st.write(f"[Read Full Article]({entry.link})")
    else:
        st.write("No recent news found.")
