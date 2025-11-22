import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from scipy.stats import norm
from datetime import datetime, timedelta
import plotly.graph_objects as go
import requests
import time

# --- PAGE CONFIG ---
st.set_page_config(page_title="OpStruct Academy", page_icon="🎓", layout="wide")

# --- CSS & STYLING ---
st.markdown("""
<style>
    .stApp {background-color: #0e1117; color: #e0e0e0;}
    h1, h2, h3 {font-family: 'SF Pro Display', sans-serif;}
    
    /* CARDS */
    .concept-card {
        background: #161b22; border: 1px solid #30363d; padding: 20px; 
        border-radius: 10px; margin-bottom: 15px;
    }
    .concept-title {color: #00FF00; font-weight: bold; font-size: 1.2rem;}
    .concept-emoji {font-size: 2rem;}
    
    /* NAVIGATION */
    div.stButton > button {
        width: 100%; border-radius: 8px; font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE NAVIGATION ---
if 'page' not in st.session_state: st.session_state.page = 'home'

def set_page(page_name):
    st.session_state.page = page_name

# --- HELPER: SMART SEARCH ---
@st.cache_data(ttl=86400)
def lookup_ticker(query):
    query = query.strip().upper()
    try:
        t = yf.Ticker(query)
        if not t.history(period="1d").empty: return query
    except: pass

    try:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()
        if 'quotes' in data and len(data['quotes']) > 0:
            return data['quotes'][0]['symbol']
    except: pass
    return query

# ==================================================
#                 PAGE 1: HOMEPAGE
# ==================================================
def page_home():
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown('<h1 style="text-align: center; font-size: 4rem; background: -webkit-linear-gradient(45deg, #00FF00, #00AAFF); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">OpStruct.</h1>', unsafe_allow_html=True)
    st.markdown('<h3 style="text-align: center; color: #888;">Master the Mathematics of Risk.</h3>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div class="concept-card">
            <div class="concept-emoji">🎓</div>
            <div class="concept-title">The Academy</div>
            <p>Learn Options like a 5-year-old. No jargon. Just logic.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Enter Academy ->", key="home_academy"): set_page('academy')
        
    with c2:
        st.markdown("""
        <div class="concept-card">
            <div class="concept-emoji">📐</div>
            <div class="concept-title">The Terminal</div>
            <p>Institutional-grade structuring engine powered by Black-Scholes.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Launch Terminal ->", key="home_terminal"): set_page('terminal')

# ==================================================
#                 PAGE 2: THE ACADEMY
# ==================================================
def page_academy():
    st.title("🎓 The Options Academy")
    tab1, tab2, tab3 = st.tabs(["🟢 The Basics", "⚠ Risk", "Greeks 101"])
    
    with tab1:
        st.info("💡 **Analogy:** Options are like **Coupons** (Calls) or **Insurance** (Puts).")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### 📞 CALL = The Coupon")
            st.write("You pay $5 for a coupon to buy a TV at $500. If the price goes to $600, you save $100.")
        with c2:
            st.markdown("### 📉 PUT = The Insurance")
            st.write("You pay $100 to insure your car. If it crashes (stock drops), you get paid.")

    with tab2:
        st.error("⚠️ **Golden Rule:** Buying Options = Limited Loss. Selling Naked Options = Unlimited Loss.")
        st.write("OpStruct only builds **Spreads** (Buying one + Selling one) to cap your risk.")

    with tab3:
        st.metric("Δ Delta", "Speed/Prob", "Direction")
        st.metric("Θ Theta", "Time Decay", "Ice Cube Melting")

# ==================================================
#                 PAGE 3: THE TERMINAL (PRO)
# ==================================================
def page_terminal():
    # --- QUANT ENGINE ---
    class QuantEngine:
        def __init__(self, risk_free_rate=0.045):
            self.r = risk_free_rate
        def black_scholes_call(self, S, K, T, sigma):
            if T <= 0.001: return max(0, S - K)
            d1 = (np.log(S / K) + (self.r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
            d2 = d1 - sigma * np.sqrt(T)
            return S * norm.cdf(d1) - K * np.exp(-self.r * T) * norm.cdf(d2)
        def black_scholes_put(self, S, K, T, sigma):
            if T <= 0.001: return max(0, K - S)
            d1 = (np.log(S / K) + (self.r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
            d2 = d1 - sigma * np.sqrt(T)
            return K * np.exp(-self.r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        
        def get_delta(self, S, K, T, sigma, type="call"):
            if T <= 0.001: return 0
            d1 = (np.log(S / K) + (self.r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
            if type == "call": return norm.cdf(d1)
            else: return norm.cdf(d1) - 1

        def find_closest_strike(self, df, target_delta):
            df['delta_diff'] = abs(df['calc_delta'] - target_delta)
            return df.loc[df['delta_diff'].idxmin()]

    quant = QuantEngine()

    def get_chain(ticker, expiry):
        stock = yf.Ticker(ticker)
        opt = stock.option_chain(expiry)
        return stock, opt.calls, opt.puts

    def calculate_greeks(df, spot, expiry_date, type="call"):
        T = (datetime.strptime(expiry_date, "%Y-%m-%d") - datetime.now()).days / 365.0
        if T < 0.001: T = 0.001
        deltas = []
        for index, row in df.iterrows():
            iv = row['impliedVolatility'] if row['impliedVolatility'] > 0.01 else 0.5
            if type == "call": d = quant.get_delta(spot, row['strike'], T, iv, "call")
            else: d = quant.get_delta(spot, row['strike'], T, iv, "put")
            deltas.append(d)
        df['calc_delta'] = deltas
        return df

    st.title("📐 OpStruct Pro Terminal")
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        raw_input = st.text_input("Company or Ticker", "Apple").strip()
        ticker = lookup_ticker(raw_input)
        if ticker != raw_input.upper(): st.caption(f"✅ Found: **{ticker}**")
    
    # ERROR HANDLING WRAPPER
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d")
        if hist.empty:
            st.error(f"❌ Could not find data for '{ticker}'.")
            return
        
        exps = stock.options
        if not exps:
            st.warning(f"⚠️ '{ticker}' has no options chain.")
            return

        with c2: expiry = st.selectbox("Expiration", exps[:6])
        with c3: view = st.selectbox("Strategy", ["Bullish (Call Spread)", "Bearish (Put Spread)", "Neutral (Income Strangle)"])

        with st.spinner(f"Structuring trades for {ticker}..."):
            current_price = hist['Close'].iloc[-1]
            
            # GREEKS CALCULATION
            _, calls, puts = get_chain(ticker, expiry)
            calls = calculate_greeks(calls, current_price, expiry, "call")
            puts = calculate_greeks(puts, current_price, expiry, "put")
            
            st.metric("Spot Price", f"${current_price:.2f}", f"{(datetime.strptime(expiry, '%Y-%m-%d') - datetime.now()).days} DTE")
            
            # STRATEGY LOGIC
            trade = {}
            if "Bullish" in view:
                buy_leg = quant.find_closest_strike(calls, 0.50)
                sell_leg = quant.find_closest_strike(calls, 0.30)
                buy_leg['side'] = "BUY"; sell_leg['side'] = "SELL"
                buy_leg['type'] = "call"; sell_leg['type'] = "call"
                trade = {"Legs": [buy_leg, sell_leg], "Type": "Call Debit Spread (Bullish)"}

            elif "Bearish" in view:
                buy_leg = quant.find_closest_strike(puts, -0.50)
                sell_leg = quant.find_closest_strike(puts, -0.30)
                buy_leg['side'] = "BUY"; sell_leg['side'] = "SELL"
                buy_leg['type'] = "put"; sell_leg['type'] = "put"
                trade = {"Legs": [buy_leg, sell_leg], "Type": "Put Debit Spread (Bearish)"}

            elif "Neutral" in view:
                call_leg = quant.find_closest_strike(calls, 0.20)
                put_leg = quant.find_closest_strike(puts, -0.20)
                call_leg['side'] = "SELL"; put_leg['side'] = "SELL"
                call_leg['type'] = "call"; put_leg['type'] = "put"
                trade = {"Legs": [call_leg, put_leg], "Type": "Short Strangle (Income)"}
            
            # RENDERER
            if trade:
                st.subheader(f"🤖 Generated: {trade['Type']}")
                total_price = 0
                legs_html = ""
                
                for leg in trade['Legs']:
                    price = leg['lastPrice']
                    strike = leg['strike']
                    delta = leg['calc_delta']
                    side = leg['side']
                    
                    if side == "BUY": total_price += price
                    else: total_price -= price
                    
                    color = "🟢" if side == "BUY" else "🔴"
                    legs_html += f"<p>{color} <b>{side}</b> ${strike} (Delta: {delta:.2f}) - ${price:.2f}</p>"

                cost_label = f"Est. Debit: ${total_price*100:.2f}" if total_price > 0 else f"Est. Credit: ${abs(total_price)*100:.2f} (Income)"

                st.markdown(f"""
                <div style="background: #111; padding: 20px; border-left: 5px solid #00FF00; border-radius: 10px;">
                    {legs_html}
                    <hr style="border-color: #444;">
                    <h3>{cost_label}</h3>
                </div>
                """, unsafe_allow_html=True)
                
                # SIMULATION LAB (INDENTATION FIXED HERE)
                st.divider()
                st.subheader("🧪 Simulation Lab (The 'What If' Machine)")
                st.caption("Options change price before expiration. Use the sliders to simulate Time Decay and Volatility Shocks.")
                
                sim_col1, sim_col2 = st.columns(2)
                with sim_col1: days_forward = st.slider("⏳ Time Travel (Days Passed)", 0, 30, 0)
                with sim_col2: vol_adjust = st.slider("⚡ Volatility Adjustment (%)", -50, 50, 0)

                spot_range = np.linspace(current_price * 0.85, current_price * 1.15, 100)
                
                # Simulated P&L
                pnl_simulated = np.zeros_like(spot_range) - (total_price * 100)
                total_days = (datetime.strptime(expiry, "%Y-%m-%d") - datetime.now()).days
                sim_T = max(0.001, (total_days - days_forward) / 365.0)
                
                for leg in trade['Legs']:
                    sim_sigma = (leg['impliedVolatility'] * (1 + vol_adjust/100))
                    if sim_sigma < 0.01: sim_sigma = 0.01
                    
                    if leg['type'] == "call":
                        new_price = quant.black_scholes_call(spot_range, leg['strike'], sim_T, sim_sigma)
                    else:
                        new_price = quant.black_scholes_put(spot_range, leg['strike'], sim_T, sim_sigma)
                    
                    if leg['side'] == "BUY": pnl_simulated += (new_price * 100)
                    else: pnl_simulated -= (new_price * 100)

                fig = go.Figure()
                fig.add_trace(go.Scatter(x=spot_range, y=pnl_simulated, mode='lines', 
                                         name='Simulated P&L', fill='tozeroy', 
                                         line=dict(color='#00FF00' if pnl_simulated.max() > 0 else '#FF4B4B')))
                fig.add_hline(y=0, line_color="gray", line_dash="dash")
                fig.add_vline(x=current_price, line_color="yellow")
                fig.update_layout(template="plotly_dark", height=400, title="Projected Outcome", yaxis_title="P/L ($)")
                st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Analysis Error: {e}")

# ==================================================
#                 MAIN CONTROLLER
# ==================================================
with st.sidebar:
    st.title("OpStruct")
    if st.button("🏠 Home", use_container_width=True): set_page('home')
    if st.button("🎓 Academy", use_container_width=True): set_page('academy')
    if st.button("📐 Terminal", use_container_width=True): set_page('terminal')

if st.session_state.page == 'home': page_home()
elif st.session_state.page == 'academy': page_academy()
elif st.session_state.page == 'terminal': page_terminal()
