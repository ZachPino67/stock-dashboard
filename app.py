import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- PAGE CONFIG ---
st.set_page_config(page_title="QUANT-X: Fusion Terminal", page_icon="🦅", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .stApp {background-color: #0e1117;}
    div.stButton > button:first-child {background-color: #00FF00; color: black;}
</style>
""", unsafe_allow_html=True)

# --- INTELLIGENCE DATABASE ---
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
st.sidebar.title("🦅 QUANT-X")
tickers = list(RELATIONSHIPS.keys())
selected_ticker = st.sidebar.selectbox("TARGET ASSET", tickers)
timeframe = st.sidebar.selectbox("Timeframe", ["6mo", "1y", "2y"], index=1)

# --- DATA ENGINE (DEEP DIVE) ---
@st.cache_data(ttl=60)
def get_quant_data(ticker, period):
    stock = yf.Ticker(ticker)
    df = stock.history(period=period)
    
    if df.empty: return pd.DataFrame()
    
    # 1. MACD
    macd = df.ta.macd(close='Close', fast=12, slow=26, signal=9)
    if macd is not None: df = pd.concat([df, macd], axis=1)
    
    # 2. BOLLINGER BANDS
    bb = df.ta.bbands(close='Close', length=20, std=2)
    if bb is not None: df = pd.concat([df, bb], axis=1)
    
    # 3. Z-SCORE
    df['Z_Score'] = (df['Close'] - df['Close'].rolling(20).mean()) / df['Close'].rolling(20).std()
    
    # 4. RSI
    df['RSI'] = df.ta.rsi(close='Close', length=14)
    
    return df

# --- MAIN LAYOUT ---
df = get_quant_data(selected_ticker, timeframe)
curr_price = df['Close'].iloc[-1]
rsi = df['RSI'].iloc[-1]
z_score = df['Z_Score'].iloc[-1]

# --- SECTION 1: HEADS UP DISPLAY ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("PRICE", f"${curr_price:.2f}")
c2.metric("RSI", f"{rsi:.1f}", "Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral")

z_col = "normal"
if z_score > 2: z_col = "inverse"
c3.metric("Z-SCORE", f"{z_score:.2f}", "Sigma Dev", delta_color=z_col)

signal = "WAIT"
if rsi < 30 and z_score < -2: signal = "💎 STRONG BUY"
elif rsi > 70 and z_score > 2: signal = "🔥 STRONG SELL"
c4.metric("QUANT SIGNAL", signal)

# --- SECTION 2: THE MASTER CHART (RESTORED) ---
st.markdown("### 🔭 Technical Deep Dive")

fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                    vertical_spacing=0.05, row_heights=[0.6, 0.2, 0.2])

# Candles & BB
fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'], name="Price"), row=1, col=1)
if 'BBU_20_2.0' in df.columns:
    fig.add_trace(go.Scatter(x=df.index, y=df['BBU_20_2.0'], 
                            line=dict(color='rgba(0, 255, 255, 0.3)', width=1), name="Upper BB"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['BBL_20_2.0'], 
                            line=dict(color='rgba(0, 255, 255, 0.3)', width=1), fill='tonexty', name="Lower BB"), row=1, col=1)

# MACD
if 'MACDh_12_26_9' in df.columns:
    fig.add_trace(go.Bar(x=df.index, y=df['MACDh_12_26_9'], marker_color='cyan', name="MACD Hist"), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD_12_26_9'], line=dict(color='white', width=1), name="MACD"), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MACDs_12_26_9'], line=dict(color='orange', width=1), name="Signal"), row=2, col=1)

# Z-Score
fig.add_trace(go.Scatter(x=df.index, y=df['Z_Score'], line=dict(color='yellow', width=2), name="Z-Score"), row=3, col=1)
fig.add_hline(y=2, line_dash="dot", line_color="red", row=3, col=1)
fig.add_hline(y=-2, line_dash="dot", line_color="green", row=3, col=1)

fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=700, margin=dict(l=0, r=0, t=0, b=0))
st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- SECTION 3: SUPPLY CHAIN INTELLIGENCE ---
st.subheader(f"🧬 Supply Chain Intelligence: {selected_ticker}")

relations = RELATIONSHIPS[selected_ticker]
correlation_data = []
chart_data = pd.DataFrame()
chart_data[selected_ticker] = (df['Close'] / df['Close'].iloc[0] - 1) * 100

for item in relations:
    try:
        sym_df = yf.Ticker(item['ticker']).history(period=timeframe)
        sym_df = sym_df['Close'].reindex(df.index, method='ffill')
        
        corr = df['Close'].corr(sym_df)
        perf = (sym_df.iloc[-1] - sym_df.iloc[0]) / sym_df.iloc[0] * 100
        
        correlation_data.append({
            "Ticker": item['ticker'],
            "Company": item['name'],
            "Role": item['role'],
            "Connection": item['why'],
            "Correlation": corr,
            "Performance": perf
        })
        chart_data[item['ticker']] = (sym_df / sym_df.iloc[0] - 1) * 100
    except: continue

# Correlation Table
corr_df = pd.DataFrame(correlation_data).sort_values(by="Correlation", ascending=False)

st.dataframe(
    corr_df,
    column_config={
        "Correlation": st.column_config.ProgressColumn(
            "Correlation (0-1)",
            help="1.0 = Moves Identically. 0.0 = No Relation.",
            min_value=-1, max_value=1, format="%.2f",
        ),
        "Performance": st.column_config.NumberColumn("Return (%)", format="%.2f%%")
    },
    hide_index=True, use_container_width=True
)

# Relative Perf Chart
st.markdown("### 📈 Ecosystem Performance")
perf_fig = go.Figure()
perf_fig.add_trace(go.Scatter(x=chart_data.index, y=chart_data[selected_ticker], mode='lines', name=selected_ticker, line=dict(color='white', width=4)))
colors = ['#00FF00', '#FF0000', '#0088FF', '#FFA500', '#FF00FF']
for i, row in corr_df.iterrows():
    perf_fig.add_trace(go.Scatter(x=chart_data.index, y=chart_data[row['Ticker']], mode='lines', name=row['Ticker'], line=dict(width=2, color=colors[i % len(colors)])))

perf_fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0, r=0, t=0, b=0))
st.plotly_chart(perf_fig, use_container_width=True)
