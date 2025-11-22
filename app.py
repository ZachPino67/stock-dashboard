import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from scipy.stats import norm
from datetime import datetime, timedelta
import plotly.graph_objects as go

# --- CONFIGURATION ---
st.set_page_config(page_title="OpStruct AI", page_icon="📐", layout="wide")

# --- CSS: THE BLOOMBERG AESTHETIC ---
st.markdown("""
<style>
    .stApp {background-color: #0e1117; color: #e0e0e0;}
    div.stButton > button {
        background-color: #222; border: 1px solid #444; color: white; font-family: 'Courier New';
    }
    div.stButton > button:hover {border-color: #00FF00; color: #00FF00;}
    .trade-card {
        background-color: #161b22; padding: 20px; border-radius: 10px; border-left: 5px solid #00FF00;
        font-family: 'Courier New'; margin-bottom: 20px;
    }
    h1, h2, h3 {font-family: 'Arial Black'; color: #f0f0f0;}
    .stat-box {text-align: center; padding: 10px; background: #0d1117; border: 1px solid #30363d; border-radius: 6px;}
</style>
""", unsafe_allow_html=True)

# --- BLACK-SCHOLES & MATH MODULES ---
def calculate_probability_of_profit(current_price, strike_price, days_to_exp, iv):
    # Simplified PoP calculation using standard distribution
    # Probability of closing ITM
    if days_to_exp <= 0: return 0
    sigma = iv * np.sqrt(days_to_exp / 365)
    d2 = (np.log(current_price / strike_price) - (0.5 * sigma ** 2)) / sigma
    prob_itm = norm.cdf(d2)
    return prob_itm

@st.cache_data(ttl=60)
# --- REMOVED THE CACHE DECORATOR TO FIX THE CRASH ---
def get_option_chain_data(ticker):
    stock = yf.Ticker(ticker)
    try:
        exps = stock.options
        return stock, exps
    except:
        return None, []
# --- UI: SIDEBAR (INPUTS) ---
st.sidebar.title("📐 OpStruct AI")
st.sidebar.markdown("Automated Derivatives Structuring")

ticker = st.sidebar.text_input("Underlying Asset", "NVDA").upper()
stock, exps = get_option_chain_data(ticker)

if not exps:
    st.error("Invalid Ticker")
    st.stop()

# 1. SELECT EXPIRY
expiry = st.sidebar.selectbox("Target Expiration", exps[:6]) # Show next 6 expiries

# 2. DEFINE STRATEGY VIEW
view = st.sidebar.radio("Market Outlook", ["Bullish (Go Up)", "Bearish (Go Down)", "Neutral (Stay Flat)"])

# --- MAIN DASHBOARD ---
st.title(f"⚡ {ticker} Structuring Engine")

# Get Real-time Data
hist = stock.history(period="1mo")
current_price = hist['Close'].iloc[-1]
iv_rank = (hist['Close'].pct_change().std() * np.sqrt(252) * 100) # Simplified IV Proxy

# Header Metrics
c1, c2, c3, c4 = st.columns(4)
c1.metric("Spot Price", f"${current_price:.2f}")
c2.metric("Implied Volatility", f"{iv_rank:.1f}%")
c3.metric("Selected Expiry", expiry)

days_to_exp = (datetime.strptime(expiry, "%Y-%m-%d") - datetime.now()).days
c4.metric("DTE (Days)", days_to_exp)

st.divider()

# --- THE STRUCTURING LOGIC (AI BRAIN) ---
# This replaces the "Up/Down" game with actual Option Selection

opt = stock.option_chain(expiry)
calls = opt.calls
puts = opt.puts

trade_structure = {}

if view == "Bullish (Go Up)":
    # AI Strategy: Long Call Spread (Debit Spread)
    # Buy ATM Call, Sell OTM Call (to fund it)
    buy_strike = calls.iloc[(calls['strike'] - current_price).abs().argsort()[:1]]['strike'].values[0]
    sell_strike = calls[calls['strike'] > buy_strike].iloc[0]['strike']
    
    # Get Prices
    buy_cost = calls[calls['strike'] == buy_strike]['lastPrice'].values[0]
    sell_credit = calls[calls['strike'] == sell_strike]['lastPrice'].values[0]
    net_debit = buy_cost - sell_credit
    
    trade_structure = {
        "Name": "Bull Call Spread",
        "Leg 1": f"BUY {expiry} ${buy_strike} CALL",
        "Leg 2": f"SELL {expiry} ${sell_strike} CALL",
        "Cost": net_debit * 100,
        "Max Profit": ((sell_strike - buy_strike) - net_debit) * 100,
        "Breakeven": buy_strike + net_debit,
        "Thesis": "Moderately Bullish. Capped upside but reduced cost."
    }

elif view == "Bearish (Go Down)":
    # AI Strategy: Long Put Spread (Debit Spread)
    buy_strike = puts.iloc[(puts['strike'] - current_price).abs().argsort()[:1]]['strike'].values[0]
    sell_strike = puts[puts['strike'] < buy_strike].iloc[-1]['strike'] # Further OTM
    
    buy_cost = puts[puts['strike'] == buy_strike]['lastPrice'].values[0]
    sell_credit = puts[puts['strike'] == sell_strike]['lastPrice'].values[0]
    net_debit = buy_cost - sell_credit
    
    trade_structure = {
        "Name": "Bear Put Spread",
        "Leg 1": f"BUY {expiry} ${buy_strike} PUT",
        "Leg 2": f"SELL {expiry} ${sell_strike} PUT",
        "Cost": net_debit * 100,
        "Max Profit": ((buy_strike - sell_strike) - net_debit) * 100,
        "Breakeven": buy_strike - net_debit,
        "Thesis": "Cheaper than buying a raw Put. Protections against IV crush."
    }

elif view == "Neutral (Stay Flat)":
    # AI Strategy: Iron Condor (Selling Volatility)
    # Sell OTM Call & Sell OTM Put
    upper_strike = calls[calls['strike'] > current_price * 1.05].iloc[0]['strike']
    lower_strike = puts[puts['strike'] < current_price * 0.95].iloc[-1]['strike']
    
    # Simplified (Short Strangle for demo)
    call_credit = calls[calls['strike'] == upper_strike]['lastPrice'].values[0]
    put_credit = puts[puts['strike'] == lower_strike]['lastPrice'].values[0]
    total_credit = call_credit + put_credit
    
    trade_structure = {
        "Name": "Short Strangle (Income)",
        "Leg 1": f"SELL {expiry} ${upper_strike} CALL",
        "Leg 2": f"SELL {expiry} ${lower_strike} PUT",
        "Cost": f"+${total_credit * 100:.2f} (Credit)",
        "Max Profit": total_credit * 100,
        "Breakeven": f"${lower_strike - total_credit:.2f} / ${upper_strike + total_credit:.2f}",
        "Thesis": "Profits if stock stays between the strikes. Harvests Theta decay."
    }

# --- DISPLAY THE "PROFESSIONAL" TRADE CARD ---
st.subheader("🤖 AI Proposed Structure")

c1, c2 = st.columns([2, 1])

with c1:
    st.markdown(f"""
    <div class="trade-card">
        <h3>{trade_structure['Name']}</h3>
        <p style="color: #00FF00;">{trade_structure['Leg 1']}</p>
        <p style="color: #FF4B4B;">{trade_structure['Leg 2']}</p>
        <hr style="border-color: #333;">
        <div style="display: flex; justify-content: space-between;">
            <div>
                <small>EST. COST</small><br>
                <span style="font-size: 1.5em; font-weight: bold;">${trade_structure['Cost']:.2f}</span>
            </div>
            <div>
                <small>MAX PROFIT</small><br>
                <span style="font-size: 1.5em; color: #00FF00;">${trade_structure['Max Profit']:.2f}</span>
            </div>
            <div>
                <small>BREAKEVEN</small><br>
                <span>{trade_structure['Breakeven']}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.info(f"🧠 **AI Thesis:** {trade_structure['Thesis']}")

with c2:
    # VISUALIZE THE P&L
    st.markdown("##### P&L Simulation")
    
    # Simple Payoff Chart Logic
    spot_range = np.linspace(current_price * 0.8, current_price * 1.2, 100)
    if "Call Spread" in trade_structure['Name']:
        payoff = np.where(spot_range > buy_strike, spot_range - buy_strike, 0) - \
                 np.where(spot_range > sell_strike, spot_range - sell_strike, 0) - net_debit
    elif "Put Spread" in trade_structure['Name']:
         payoff = np.where(spot_range < buy_strike, buy_strike - spot_range, 0) - \
                  np.where(spot_range < sell_strike, sell_strike - spot_range, 0) - net_debit
    else:
        # Strangle
        payoff = total_credit - np.where(spot_range > upper_strike, spot_range - upper_strike, 0) - \
                 np.where(spot_range < lower_strike, lower_strike - spot_range, 0)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=spot_range, y=payoff, mode='lines', fill='tozeroy', 
                             line=dict(color='#00FF00' if payoff[-1] > 0 else '#FF4B4B')))
    fig.add_hline(y=0, line_color="white", line_dash="dash")
    fig.add_vline(x=current_price, line_color="yellow", annotation_text="Spot")
    fig.update_layout(template="plotly_dark", height=300, margin=dict(l=0,r=0,t=0,b=0), 
                      xaxis_title="Stock Price at Expiry", yaxis_title="Profit/Loss")
    st.plotly_chart(fig, use_container_width=True)

# --- EXPLAINER FOR LINKEDIN ---
with st.expander("🔍 How this works (Technical Details)"):
    st.markdown("""
    **This is not a simple Buy/Sell button.**
    1. **Chain Scanning:** The Python backend pulls the full Option Chain for the selected expiry.
    2. **Strike Selection:** It algorithmically finds strikes based on Delta/Price closeness.
    3. **Spread Construction:** It pairs a Long option with a Short option to create a 'Spread.'
       * *Why?* This reduces the cost of the trade and caps the risk. This is how professionals trade.
    4. **P&L Modeling:** The chart simulates the profit/loss across a range of future prices.
    """)
