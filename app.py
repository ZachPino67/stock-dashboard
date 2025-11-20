<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
  <meta http-equiv="Content-Style-Type" content="text/css">
  <title></title>
  <meta name="Generator" content="Cocoa HTML Writer">
  <meta name="CocoaVersion" content="2685.2">
  <style type="text/css">
    p.p1 {margin: 0.0px 0.0px 0.0px 0.0px; font: 12.0px Helvetica}
    p.p2 {margin: 0.0px 0.0px 0.0px 0.0px; font: 12.0px Helvetica; min-height: 14.0px}
  </style>
</head>
<body>
<p class="p1">import streamlit as st</p>
<p class="p1">import yfinance as yf</p>
<p class="p1">import pandas as pd</p>
<p class="p1">import pandas_ta as ta</p>
<p class="p1">from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer</p>
<p class="p1">import feedparser</p>
<p class="p1">import datetime</p>
<p class="p2"><br></p>
<p class="p1"># --- PAGE CONFIG ---</p>
<p class="p1">st.set_page_config(page_title="Mag7 Insider", page_icon="🚀", layout="wide")</p>
<p class="p2"><br></p>
<p class="p1">st.title("🚀 The Magnificent 7: AI Insider Dashboard")</p>
<p class="p1">st.markdown("Scanning **Price**, **RSI**, and **News Sentiment** in real-time.")</p>
<p class="p2"><br></p>
<p class="p1"># --- SIDEBAR ---</p>
<p class="p1">st.sidebar.header("Configuration")</p>
<p class="p1">tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA']</p>
<p class="p1">selected_ticker = st.sidebar.selectbox("Drill Down into Stock:", tickers)</p>
<p class="p2"><br></p>
<p class="p1"># --- LOGIC (Hidden from user) ---</p>
<p class="p1">analyzer = SentimentIntensityAnalyzer()</p>
<p class="p1">financial_lexicon = {</p>
<p class="p1"><span class="Apple-converted-space">    </span>'beat': 2.0, 'missed': -2.0, 'record': 1.5, 'growth': 1.5,<span class="Apple-converted-space"> </span></p>
<p class="p1"><span class="Apple-converted-space">    </span>'slump': -2.0, 'layoffs': -1.5, 'lawsuit': -2.0, 'buyback': 2.0,</p>
<p class="p1"><span class="Apple-converted-space">    </span>'volatile': -1.0, 'uncertainty': -1.0, 'risk': -1.5,</p>
<p class="p1"><span class="Apple-converted-space">    </span>'fine': -2.0, 'investigation': -2.0</p>
<p class="p1">}</p>
<p class="p1">analyzer.lexicon.update(financial_lexicon)</p>
<p class="p2"><br></p>
<p class="p1">@st.cache_data(ttl=300) # Cache data for 5 mins to save speed</p>
<p class="p1">def get_data(ticker_list):</p>
<p class="p1"><span class="Apple-converted-space">    </span>results = []</p>
<p class="p1"><span class="Apple-converted-space">    </span>for ticker in ticker_list:</p>
<p class="p1"><span class="Apple-converted-space">        </span>try:</p>
<p class="p1"><span class="Apple-converted-space">            </span># 1. Price &amp; Technicals</p>
<p class="p1"><span class="Apple-converted-space">            </span>stock = yf.Ticker(ticker)</p>
<p class="p1"><span class="Apple-converted-space">            </span>df = stock.history(period="60d")</p>
<p class="p1"><span class="Apple-converted-space">            </span>if df.empty: continue</p>
<p class="p2"><span class="Apple-converted-space">            </span></p>
<p class="p1"><span class="Apple-converted-space">            </span>current_price = df['Close'].iloc[-1]</p>
<p class="p1"><span class="Apple-converted-space">            </span>df['RSI'] = ta.rsi(df['Close'], length=14)</p>
<p class="p1"><span class="Apple-converted-space">            </span>rsi = df['RSI'].iloc[-1] if not df['RSI'].empty else 50</p>
<p class="p2"><span class="Apple-converted-space">            </span></p>
<p class="p1"><span class="Apple-converted-space">            </span># 2. News Sentiment</p>
<p class="p1"><span class="Apple-converted-space">            </span>rss_url = f'https://finance.yahoo.com/rss/headline?s={ticker}'</p>
<p class="p1"><span class="Apple-converted-space">            </span>feed = feedparser.parse(rss_url)</p>
<p class="p1"><span class="Apple-converted-space">            </span>news_score = 0</p>
<p class="p2"><span class="Apple-converted-space">            </span></p>
<p class="p1"><span class="Apple-converted-space">            </span>if feed.entries:</p>
<p class="p1"><span class="Apple-converted-space">                </span>scores = [analyzer.polarity_scores(e.title)['compound'] for e in feed.entries[:5]]</p>
<p class="p1"><span class="Apple-converted-space">                </span>news_score = sum(scores) / len(scores) if scores else 0</p>
<p class="p2"><br></p>
<p class="p1"><span class="Apple-converted-space">            </span># 3. Verdict</p>
<p class="p1"><span class="Apple-converted-space">            </span>verdict = "WAIT"</p>
<p class="p1"><span class="Apple-converted-space">            </span>if rsi &lt; 30:<span class="Apple-converted-space"> </span></p>
<p class="p1"><span class="Apple-converted-space">                </span>verdict = "BUY DIP"</p>
<p class="p1"><span class="Apple-converted-space">                </span>if news_score &gt; 0: verdict = "STRONG BUY"</p>
<p class="p1"><span class="Apple-converted-space">            </span>elif rsi &gt; 70:</p>
<p class="p1"><span class="Apple-converted-space">                </span>verdict = "SELL RIP"</p>
<p class="p2"><span class="Apple-converted-space">                </span></p>
<p class="p1"><span class="Apple-converted-space">            </span>results.append({</p>
<p class="p1"><span class="Apple-converted-space">                </span>"Ticker": ticker,</p>
<p class="p1"><span class="Apple-converted-space">                </span>"Price": current_price,</p>
<p class="p1"><span class="Apple-converted-space">                </span>"RSI": rsi,</p>
<p class="p1"><span class="Apple-converted-space">                </span>"Sentiment": news_score,</p>
<p class="p1"><span class="Apple-converted-space">                </span>"Verdict": verdict</p>
<p class="p1"><span class="Apple-converted-space">            </span>})</p>
<p class="p1"><span class="Apple-converted-space">        </span>except:</p>
<p class="p1"><span class="Apple-converted-space">            </span>continue</p>
<p class="p1"><span class="Apple-converted-space">    </span>return pd.DataFrame(results)</p>
<p class="p2"><br></p>
<p class="p1"># --- RUN ANALYSIS ---</p>
<p class="p1">if st.button("🔄 Refresh Data"):</p>
<p class="p1"><span class="Apple-converted-space">    </span>st.cache_data.clear()</p>
<p class="p2"><br></p>
<p class="p1">df = get_data(tickers)</p>
<p class="p2"><br></p>
<p class="p1"># --- DISPLAY LEADERBOARD ---</p>
<p class="p1">st.subheader("🏆 Market Leaderboard")</p>
<p class="p1"># Style the dataframe: Green text for Buy, Red for Sell</p>
<p class="p1">def color_verdict(val):</p>
<p class="p1"><span class="Apple-converted-space">    </span>color = 'white'</p>
<p class="p1"><span class="Apple-converted-space">    </span>if 'BUY' in val: color = '#4CAF50' # Green</p>
<p class="p1"><span class="Apple-converted-space">    </span>elif 'SELL' in val: color = '#FF5252' # Red</p>
<p class="p1"><span class="Apple-converted-space">    </span>return f'color: {color}; font-weight: bold'</p>
<p class="p2"><br></p>
<p class="p1">st.dataframe(</p>
<p class="p1"><span class="Apple-converted-space">    </span>df.style.map(color_verdict, subset=['Verdict'])</p>
<p class="p1"><span class="Apple-converted-space">    </span>.format({"Price": "${:.2f}", "RSI": "{:.1f}", "Sentiment": "{:.2f}"}),</p>
<p class="p1"><span class="Apple-converted-space">    </span>use_container_width=True</p>
<p class="p1">)</p>
<p class="p2"><br></p>
<p class="p1"># --- DRILL DOWN SECTION ---</p>
<p class="p1">st.divider()</p>
<p class="p1">st.subheader(f"🔍 Deep Dive: {selected_ticker}")</p>
<p class="p2"><br></p>
<p class="p1"># Get Drill Down Data</p>
<p class="p1">stock = yf.Ticker(selected_ticker)</p>
<p class="p1">hist = stock.history(period="6mo")</p>
<p class="p2"><br></p>
<p class="p1"># Chart 1: Price</p>
<p class="p1">st.line_chart(hist['Close'])</p>
<p class="p2"><br></p>
<p class="p1"># News Feed</p>
<p class="p1">st.subheader("Latest Headlines")</p>
<p class="p1">rss_url = f'https://finance.yahoo.com/rss/headline?s={selected_ticker}'</p>
<p class="p1">feed = feedparser.parse(rss_url)</p>
<p class="p1">for entry in feed.entries[:3]:</p>
<p class="p1"><span class="Apple-converted-space">    </span>score = analyzer.polarity_scores(entry.title)['compound']</p>
<p class="p1"><span class="Apple-converted-space">    </span>emoji = "⚪"</p>
<p class="p1"><span class="Apple-converted-space">    </span>if score &gt; 0.05: emoji = "🟢"</p>
<p class="p1"><span class="Apple-converted-space">    </span>if score &lt; -0.05: emoji = "🔴"</p>
<p class="p1"><span class="Apple-converted-space">    </span>st.write(f"{emoji} **{entry.title}**")</p>
</body>
</html>
