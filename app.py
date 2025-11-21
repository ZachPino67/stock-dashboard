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
st.set_page_config(page_title="AlphaStrike Terminal", page_icon="🦅", layout="wide")

# --- STRATEGY: THE KNOWLEDGE GRAPH (RELATIONSHIPS) ---
# This is the "Brain" that knows who supplies who.
SYMPATHY_MAP = {
    'NVDA': {'tickers': ['TSM', 'SMCI', 'AMD'], 'role': 'Foundry (TSM) & Server Integrator (SMCI)'},
    'AAPL': {'tickers': ['SWKS', 'QCOM', 'CRUS'], 'role': 'Chip Suppliers (Skyworks, Qualcomm)'},
    'TSLA': {'tickers': ['ALB', 'RIVN', 'BLNK'], 'role': 'Lithium (ALB) & EV Rivals'},
    'MSFT': {'tickers': ['CRWD', 'ORCL', 'ADBE'], 'role': 'Cloud Security & Enterprise Rivals'},
    'GOOGL': {'tickers': ['META', 'TTD', 'SNAP'], 'role': 'Ad-Tech Rivals'},
    'AMZN': {'tickers': ['WMT', 'SHOP', 'FDX'], 'role': 'Retail Rivals & Logistics'},
    'META': {'tickers': ['PINS', 'SNAP', 'TTD'], 'role': 'Social Media Ad Ecosystem'}
}

# --- SIDEBAR ---
st.sidebar.header("🦅 AlphaStrike Control")
tickers = list(SYMPATHY_MAP.keys())
selected_ticker = st.sidebar.selectbox("Select Lead Asset", tickers)
timeframe = st.sidebar.selectbox("Timeframe", ["60d", "6mo", "1y"], index=0)

# --- LOGIC & UTILS ---
analyzer = SentimentIntensityAnalyzer()
financial_lexicon = {
    'beat': 2.0, 'missed': -2.0, 'record': 1.5, 'growth': 1.5, 
    'slump': -2.0, 'layoffs': -1.5, 'lawsuit': -2.0, 'fine': -2.0
}
analyzer.lexicon.update(financial_lexicon)

@st.cache_data(ttl=300)
def get_market_mood():
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

@st.cache_data(ttl=300)
def get_sympathy_data(lead_ticker, sympathy_list, period):
    data = {}
    # Get Lead Data
    lead_hist = yf.Ticker(lead_ticker).history(period=period)['Close']
    # Normalize to % change starting at 0
    data[lead_ticker] = (lead_hist / lead_hist.iloc[0] - 1) * 100
    
    # Get Sympathy Data
    for sym in sympathy_list:
        try:
            hist = yf.Ticker(sym).history(period=period)['Close']
            # Reindex to match lead ticker dates
            hist = hist.reindex(lead_hist.index, method='ffill')
            data[sym] = (hist / hist.iloc[0] - 1) * 100
        except:
            continue
            
    return pd.DataFrame(data)

# --- LAYOUT ---
mood, mood_color, vix_val = get_market_mood()
c1, c2 = st.columns([3, 1])
with c1:
    st.title(f"🦅 {selected_ticker} Strategic Hub")
with c2:
    st.markdown(f"### Market Mood: :{mood_color}[{mood}]")
    st.caption(f"VIX: {vix_val}")

st.divider()

# --- SECTION 1: THE LEAD ASSET ---
stock = yf.Ticker(selected_ticker)
df = stock.history(period="1y") # Always fetch 1y for robust RSI
df['RSI'] = ta.rsi(df['Close'], length=14)

# Filter by user timeframe for display
days_map = {"60d": 60, "6mo": 180, "1y": 365}
df_display = df.tail(days_map[timeframe])

# Interactive Chart
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, row_heights=[0.7, 0.3])
fig.add_trace(go.Candlestick(x=df_display.index, open=df_display['Open'], high=df_display['High'],
                low=df_display['Low'], close=df_display['Close'], name="Price"), row=1, col=1)
fig.add_trace(go.Scatter(x=df_display.index, y=df_display['RSI'], line=dict(color='purple', width=2), name="RSI"), row=2, col=1)
fig.add_hline(y=30, line_dash="dot", row=2, col=1, annotation_text="Oversold")
fig.update_layout(xaxis_rangeslider_visible=False, height=500, margin=dict(l=0, r=0, t=0, b=0))
st.plotly_chart(fig, use_container_width=True)

# --- SECTION 2: THE SYMPATHY SCANNER (The New Alpha) ---
st.subheader("🔗 Supply Chain & Ripple Effects")
sympathy_info = SYMPATHY_MAP[selected_ticker]
st.info(f"**Strategy:** Watch {sympathy_info['tickers']} ({sympathy_info['role']}). Look for LAG.")

# Fetch and Normalize Data
sym_df = get_sympathy_data(selected_ticker, sympathy_info['tickers'], timeframe)

# 1. Performance Comparison Chart
st.markdown("##### Relative Performance (%)")
perf_fig = go.Figure()
colors = ['#00FF00', '#FF0000', '#0000FF', '#FFA500'] # Green, Red, Blue, Orange

for i, col in enumerate(sym_df.columns):
    # Make the Lead Asset thick and white, others colorful
    width = 4 if col == selected_ticker else 2
    color = 'white' if col == selected_ticker else colors[i % len(colors)]
    dash = 'solid' if col == selected_ticker else 'dot'
    
    perf_fig.add_trace(go.Scatter(x=sym_df.index, y=sym_df[col], mode='lines', 
                                  name=col, line=dict(width=width, color=color, dash=dash)))

perf_fig.update_layout(template="plotly_dark", hovermode="x unified", height=400)
st.plotly_chart(perf_fig, use_container_width=True)

# 2. Correlation Matrix
st.markdown("##### Correlation Matrix (Do they move together?)")
corr_matrix = sym_df.corr()
st.dataframe(corr_matrix.style.background_gradient(cmap="RdYlGn"), use_container_width=True)

# --- SECTION 3: AI NEWS ---
st.divider()
st.subheader("📰 Sentiment Analysis")
rss_url = f'https://finance.yahoo.com/rss/headline?s={selected_ticker}'
feed = feedparser.parse(rss_url)
cols = st.columns(3)
if feed.entries:
    for i, entry in enumerate(feed.entries[:6]):
        score = analyzer.polarity_scores(entry.title)['compound']
        emoji = "⚪"
        if score > 0.1: emoji = "🟢"
        if score < -0.1: emoji = "🔴"
        
        with cols[i % 3]:
            st.markdown(f"**{emoji} {entry.title}**")
            st.caption(f"Score: {score}")
            st.markdown(f"[Read]({entry.link})")
