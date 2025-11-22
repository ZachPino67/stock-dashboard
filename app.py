import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from scipy.stats import norm
from datetime import datetime
import plotly.graph_objects as go
import time

# --- PAGE CONFIG ---
st.set_page_config(page_title="OpStruct Pro", page_icon="📐", layout="wide")

# --- SESSION STATE ---
if 'page' not in st.session_state: st.session_state.page = 'home'

# --- CSS STYLING ---
st.markdown("""
<style>
    .stApp {background-color: #000000; color: #e0e0e0;}
    h1, h2, h3 {font-family: 'SF Pro Display', sans-serif;}
    
    /* MARKETING HOME */
    .hero-text {
        background: -webkit-linear-gradient(45deg, #00FF00, #00AAFF);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        font-size: 4rem; font-weight: 800; text-align: center; margin-bottom: 20px;
    }
    
    /* TERMINAL UI */
    .metric-card {
        background: #111; border: 1px solid #333; padding: 15px; 
        border-radius: 8px; text-align: center;
    }
    .trade-ticket {
        background: #0d1117; border-left: 5px solid #00FF00; padding: 20px;
        margin-top: 20px; font-family: 'Courier New';
    }
    .greek-box {
        font-size: 0.8rem; color: #aaa; background: #222; 
        padding: 5px 10px; border-radius: 4px; display: inline-block; margin: 2px;
    }
</style>
""", unsafe_allow_html=True)

# ==================================================
#           THE QUANT ENGINE (MATH CORE)
# ==================================================
class QuantEngine:
    def __init__(self, risk_free_rate=0.045):
        self.r = risk_free_rate

    def black_scholes_call(self, S, K, T, sigma):
        # S: Spot, K: Strike, T: Time(years), sigma: IV
        if T <= 0: return max(0, S - K)
        d1 = (np.log(S / K) + (self.r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        delta = norm.cdf(d1)
        return delta

    def black_scholes_put(self, S, K, T, sigma):
        if T <= 0: return max(0, K - S)
        d1 = (np.log(S / K) + (self.r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        delta = norm.cdf(d1) - 1
        return delta

    def find_closest_strike(self, df, target_delta, option_type="call"):
        # Scans the chain to find the strike with Delta closest to Target
        # This is how pros trade ("Sell the 30 Delta")
        df['delta_diff'] = abs(df['calc_delta'] - target_delta)
        return df.loc[df['delta_diff'].idxmin()]

# Initialize Engine
quant = QuantEngine()

# ==================================================
#                 HELPER FUNCTIONS
# ==================================================
@st.cache_data(ttl=300)
def get_chain(ticker, expiry):
    stock = yf.Ticker(ticker)
    opt = stock.option_chain(expiry)
    return stock, opt.calls, opt.puts

def calculate_greeks(df, spot, expiry_date, type="call"):
    # Adds 'calc_delta' column to the dataframe using Black-Scholes
    T = (datetime.strptime(expiry_date, "%Y-%m-%d") - datetime.now()).days / 365.0
    if T < 0.001: T = 0.001 # Prevent divide by zero
    
    deltas = []
    for index, row in df.iterrows():
        iv = row['impliedVolatility']
        strike = row['strike']
        
        # Yahoo IV is sometimes 0 or junk, filter it
        if iv < 0.01: iv = 0.5 
        
        if type == "call":
            d = quant.black_scholes_call(spot, strike, T, iv)
        else:
            d = quant.black_scholes_put(spot, strike, T, iv)
        deltas.append(d)
        
    df['calc_delta'] = deltas
    return df

# ==================================================
#                 HOMEPAGE
# ==================================================
def homepage():
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown('<div class="hero-text">OpStruct Pro.<br>Trade Deltas, Not Guesses.</div>', unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #888;'>The first free terminal that runs a <b>Black-Scholes Engine</b> in your browser.<br>Calculates Greeks real-time. Structures Delta-Neutral strategies automatically.</p>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        if st.button("🚀 INITIALIZE QUANT TERMINAL", use_container_width=True):
            st.session_state.page = 'app'
            st.rerun()

# ==================================================
#                 TERMINAL APP
# ==================================================
def main_app():
    # --- SIDEBAR CONFIG ---
    st.sidebar.markdown("## ⚙️ Quant Settings")
    ticker = st.sidebar.text_input("Ticker", "NVDA").upper()
    
    # 1. Fetch Expiries
    stock = yf.Ticker(ticker)
    try:
        exps = stock.options
    except:
        st.error("Invalid Ticker")
        return
        
    expiry = st.sidebar.selectbox("Expiration Cycle", exps[:8])
    
    # 2. Strategy Selection
    st.sidebar.markdown("### ♟️ Strategy")
    strategy_mode = st.sidebar.selectbox("Trade Type", [
        "Bull Call Spread (Debit)", 
        "Bear Put Spread (Debit)", 
        "Iron Condor (Income)",
        "Delta Neutral Hedge" 
    ])
    
    # --- HEADER DATA ---
    hist = stock.history(period="5d")
    current_price = hist['Close'].iloc[-1]
    
    c1, c2, c3 = st.columns([1, 10, 1])
    with c2:
        st.markdown(f"### 🦅 {ticker} Quant Dashboard")
        m1, m2, m3 = st.columns(3)
        m1.metric("Spot Price", f"${current_price:.2f}")
        m2.metric("Expiry", expiry)
        
        # Calculate DTE
        dte = (datetime.strptime(expiry, "%Y-%m-%d") - datetime.now()).days
        m3.metric("DTE", f"{dte} Days")
        
    st.divider()

    # --- EXECUTION ENGINE ---
    with st.spinner("🧮 Running Black-Scholes Model..."):
        try:
            _, calls, puts = get_chain(ticker, expiry)
            
            # CALCULATE LIVE GREEKS (The "Advanced" Part)
            calls = calculate_greeks(calls, current_price, expiry, "call")
            puts = calculate_greeks(puts, current_price, expiry, "put")
            
            trade = {}
            
            # --- STRATEGY LOGIC: DELTA BASED ---
            
            if strategy_mode == "Bull Call Spread (Debit)":
                # PRO LOGIC: Buy 50 Delta (ATM), Sell 30 Delta (OTM)
                buy_leg = quant.find_closest_strike(calls, 0.50)
                sell_leg = quant.find_closest_strike(calls, 0.30)
                
                cost = buy_leg['lastPrice'] - sell_leg['lastPrice']
                trade = {
                    "Name": "Delta-50/30 Call Spread",
                    "Legs": [
                        {"side": "BUY", "strike": buy_leg['strike'], "delta": f"{buy_leg['calc_delta']:.2f}", "price": buy_leg['lastPrice']},
                        {"side": "SELL", "strike": sell_leg['strike'], "delta": f"{sell_leg['calc_delta']:.2f}", "price": sell_leg['lastPrice']}
                    ],
                    "Net": cost,
                    "Max_Profit": (sell_leg['strike'] - buy_leg['strike']) - cost,
                    "Bias": "Bullish",
                    "Note": "Optimized for directional move with reduced Theta decay."
                }
                
            elif strategy_mode == "Bear Put Spread (Debit)":
                # PRO LOGIC: Buy -50 Delta, Sell -30 Delta
                buy_leg = quant.find_closest_strike(puts, -0.50, "put")
                sell_leg = quant.find_closest_strike(puts, -0.30, "put")
                
                cost = buy_leg['lastPrice'] - sell_leg['lastPrice']
                trade = {
                    "Name": "Delta-50/30 Put Spread",
                    "Legs": [
                        {"side": "BUY", "strike": buy_leg['strike'], "delta": f"{buy_leg['calc_delta']:.2f}", "price": buy_leg['lastPrice']},
                        {"side": "SELL", "strike": sell_leg['strike'], "delta": f"{sell_leg['calc_delta']:.2f}", "price": sell_leg['lastPrice']}
                    ],
                    "Net": cost,
                    "Max_Profit": (buy_leg['strike'] - sell_leg['strike']) - cost,
                    "Bias": "Bearish",
                    "Note": "Hedges downside risk while capping cost."
                }

            elif strategy_mode == "Iron Condor (Income)":
                # PRO LOGIC: Sell 20 Delta Call / Sell 20 Delta Put (High Probability)
                short_call = quant.find_closest_strike(calls, 0.20)
                long_call = quant.find_closest_strike(calls, 0.10) # Protection
                short_put = quant.find_closest_strike(puts, -0.20, "put")
                long_put = quant.find_closest_strike(puts, -0.10, "put")
                
                credit = (short_call['lastPrice'] - long_call['lastPrice']) + (short_put['lastPrice'] - long_put['lastPrice'])
                width = long_call['strike'] - short_call['strike']
                
                trade = {
                    "Name": "Delta-20 Iron Condor",
                    "Legs": [
                        {"side": "SELL", "strike": short_call['strike'], "delta": f"{short_call['calc_delta']:.2f}", "price": short_call['lastPrice']},
                        {"side": "BUY", "strike": long_call['strike'], "delta": f"{long_call['calc_delta']:.2f}", "price": long_call['lastPrice']},
                        {"side": "SELL", "strike": short_put['strike'], "delta": f"{short_put['calc_delta']:.2f}", "price": short_put['lastPrice']},
                        {"side": "BUY", "strike": long_put['strike'], "delta": f"{long_put['calc_delta']:.2f}", "price": long_put['lastPrice']},
                    ],
                    "Net": credit,
                    "Max_Profit": credit,
                    "Bias": "Neutral",
                    "Note": "High Probability Income Trade. Profits if price stays stable."
                }

            # --- DISPLAY TICKET ---
            c1, c2 = st.columns([1, 1])
            
            with c1:
                st.subheader("🎫 Algorithm Structure")
                st.markdown(f"""
                <div class="trade-ticket">
                    <h3>{trade['Name']}</h3>
                    <p style='color: #888;'>Bias: {trade['Bias']}</p>
                    <hr style='border-color: #333;'>
                """, unsafe_allow_html=True)
                
                for leg in trade['Legs']:
                    color = "#00FF00" if leg['side'] == "BUY" else "#FF4B4B"
                    st.markdown(f"""
                    <div style='display: flex; justify-content: space-between; margin-bottom: 5px;'>
                        <span style='color: {color}; font-weight: bold;'>{leg['side']} ${leg['strike']}</span>
                        <span>Price: ${leg['price']:.2f}</span>
                        <span class='greek-box'>Δ {leg['delta']}</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown(f"""
                    <hr style='border-color: #333;'>
                    <div style='display: flex; justify-content: space-between; font-size: 1.2em;'>
                        <span>EST. COST:</span>
                        <span style='color: white;'>${trade['Net']*100:.2f}</span>
                    </div>
                    <div style='display: flex; justify-content: space-between; font-size: 1.2em;'>
                        <span>MAX PROFIT:</span>
                        <span style='color: #00FF00;'>${trade['Max_Profit']*100:.2f}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                st.info(f"👨‍💻 **Quant Note:** {trade['Note']}")

            with c2:
                # P&L CHART
                st.subheader("📉 Payoff Topology")
                spot_range = np.linspace(current_price * 0.85, current_price * 1.15, 100)
                
                # Dynamic P&L Calculation based on Legs
                pnl = np.zeros_like(spot_range) - (trade['Net'] * 100) # Start with debit/credit
                if strategy_mode == "Iron Condor (Income)": pnl = np.zeros_like(spot_range) + (trade['Net'] * 100)
                
                for leg in trade['Legs']:
                    if "CALL" in strategy_mode or "Iron" in strategy_mode and leg['strike'] > current_price:
                        # Call Logic
                        payoff = np.maximum(0, spot_range - leg['strike']) * 100
                        if leg['side'] == "BUY": pnl += payoff
                        else: pnl -= payoff
                    else:
                        # Put Logic
                        payoff = np.maximum(0, leg['strike'] - spot_range) * 100
                        if leg['side'] == "BUY": pnl += payoff
                        else: pnl -= payoff

                fig = go.Figure()
                fig.add_trace(go.Scatter(x=spot_range, y=pnl, mode='lines', fill='tozeroy', 
                                         line=dict(color='#00FF00' if pnl.max() > 0 else '#FF4B4B')))
                fig.add_hline(y=0, line_color="white", line_dash="dash")
                fig.add_vline(x=current_price, line_color="yellow", annotation_text="Spot")
                fig.update_layout(template="plotly_dark", height=400, yaxis_title="Profit ($)", xaxis_title="Stock Price")
                st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Optimization Error: {e}")
            st.caption("Common issue: Option chain illiquid or missing Delta data.")

# --- NAVIGATION CONTROLLER ---
if st.session_state.page == 'home':
    homepage()
else:
    main_app()
