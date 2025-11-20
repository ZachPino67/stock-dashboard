import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import feedparser
import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Mag7 Insider", page_icon="🚀", layout="wide")

st.title("🚀 The Magnificent 7: AI Insider Dashboard")
st.markdown("Scanning **Price**, **RSI**, and **News Sentiment** in real-time.")

# --- SIDEBAR ---
st.sidebar.header("Configuration")
tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA']
selected_ticker = st.sidebar.selectbox("Drill Down into Stock:", tickers)

# --- LOGIC (Hidden from user) ---
analyzer = SentimentIntensityAnalyzer()
financial_lexicon = {
    'beat': 2.0, 'missed': -2.0, 'record': 1.5, 'growth': 1.5, 
    'slump': -2.0, 'layoffs': -1.5, 'lawsuit': -2.0, 'buyback': 2.0,
    'volatile': -1.0, 'uncertainty': -1.0, 'risk': -1.5,
    'fine': -2.0, 'investigation': -2.0
}
analyzer.lexicon.update(financial_lexicon)

@st.cache_data(ttl=300) # Cache data for 5 mins to save speed
def get_data(ticker_list):
    results = []
    for ticker in ticker_list:
        try:
            # 1. Price & Technicals
            stock = yf.Ticker(ticker)
            df = stock.history(period="60d")
            if df.empty: continue
            
            current_price = df['Close'].iloc[-1]
            df['RSI'] = ta.rsi(df['Close'], length=14)
            rsi = df['RSI'].iloc[-1] if not df['RSI'].empty else 50
            
            # 2. News Sentiment
            rss_url = f'https://finance.yahoo.com/rss/headline?s={ticker}'
            feed = feedparser.parse(rss_url)
            news_score = 0
            
            if feed.entries:
                scores = [analyzer.polarity_scores(e.title)['compound'] for e in feed.entries[:5]]
                news_score = sum(scores) / len(scores) if scores else 0

            # 3. Verdict
            verdict = "WAIT"
            if rsi < 30: 
                verdict = "BUY DIP"
                if news_score > 0: verdict = "STRONG BUY"
            elif rsi > 70:
                verdict = "SELL RIP"
                
            results.append({
                "Ticker": ticker,
                "Price": current_price,
                "RSI": rsi,
                "Sentiment": news_score,
                "Verdict": verdict
            })
        except:
            continue
    return pd.DataFrame(results)

# --- RUN ANALYSIS ---
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()

df = get_data(tickers)

# --- DISPLAY LEADERBOARD ---
st.subheader("🏆 Market Leaderboard")
# Style the dataframe: Green text for Buy, Red for Sell
def color_verdict(val):
    color = 'white'
    if 'BUY' in val: color = '#4CAF50' # Green
    elif 'SELL' in val: color = '#FF5252' # Red
    return f'color: {color}; font-weight: bold'

st.dataframe(
    df.style.map(color_verdict, subset=['Verdict'])
    .format({"Price": "${:.2f}", "RSI": "{:.1f}", "Sentiment": "{:.2f}"}),
    use_container_width=True
)

# --- DRILL DOWN SECTION ---
st.divider()
st.subheader(f"🔍 Deep Dive: {selected_ticker}")

# Get Drill Down Data
stock = yf.Ticker(selected_ticker)
hist = stock.history(period="6mo")

# Chart 1: Price
st.line_chart(hist['Close'])

# News Feed
st.subheader("Latest Headlines")
rss_url = f'https://finance.yahoo.com/rss/headline?s={selected_ticker}'
feed = feedparser.parse(rss_url)
if feed.entries:
    for entry in feed.entries[:3]:
        score = analyzer.polarity_scores(entry.title)['compound']
        emoji = "⚪"
        if score > 0.05: emoji = "🟢"
        if score < -0.05: emoji = "🔴"
        st.write(f"{emoji} **{entry.title}**")
else:
    st.write("No recent news found.")
