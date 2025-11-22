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
    
    /* ACADEMY STYLING */
    .lesson-box {
        background: #1f1f1f; padding: 20px; border-radius: 10px; border-left: 4px solid #00AAFF; margin-bottom: 20px;
    }
    .analogy-text { font-style: italic; color: #aaa; }
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
            <div class="concept-title">The University</div>
            <p>From "Zero" to "Hedge Fund" in 4 modules. Learn the logic, not just the definitions.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Enter University ->", key="home_academy"): set_page('academy')
        
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
#                 PAGE 2: THE ACADEMY (DEEP DIVE)
# ==================================================
def page_academy():
    st.title("🎓 OpStruct University")
    st.caption("A comprehensive guide to derivatives trading.")
    
    tab1, tab2, tab3, tab4 = st.tabs(["101: The Contract", "201: The Casino Rule", "301: The Greeks", "401: Spreads"])
    
    # --- MODULE 1: THE CONTRACT ---
    with tab1:
        st.header("The Foundation")
        st.markdown("An Option is simply a contract that gives you a **Superpower** for a specific amount of time.")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### 📞 The CALL Option (Bullish)")
            st.info("The Right to BUY.")
            st.markdown("""
            **The Analogy: The Real Estate Deposit**
            
            Imagine you want to buy a house listed for **$500,000**, but you don't have the money yet.
            You pay the owner **$5,000** (Premium) to hold the house for you for **30 Days**.
            
            * **Scenario A:** A new highway is built nearby, and the house value shoots to **$600,000**.
                * You exercise your contract. You buy it at the locked price of $500k.
                * You immediately sell it for $600k.
                * **Profit:** $100,000 - $5,000 (Cost) = **$95,000**.
            
            * **Scenario B:** The house value drops to **$400,000**.
                * You are not forced to buy it. You walk away.
                * **Loss:** Only the **$5,000** deposit.
            """)
            
        with c2:
            st.markdown("### 📉 The PUT Option (Bearish)")
            st.info("The Right to SELL.")
            st.markdown("""
            **The Analogy: Car Insurance**
            
            You own a Ferrari worth **$200,000**. You are worried about crashing.
            You pay Geico **$1,000** (Premium) for a policy that guarantees the value at $200k for **1 Year**.
            
            * **Scenario A:** You crash the car. It is now worth **$0**.
                * Geico pays you the full **$200,000**.
                * You avoided financial ruin.
            
            * **Scenario B:** You drive safely. The car is fine.
                * The policy expires.
                * **Loss:** Only the **$1,000** premium.
            """)

    # --- MODULE 2: BUYING VS SELLING ---
    with tab2:
        st.header("Who makes the money?")
        st.markdown("Every trade has a Buyer and a Seller. Their odds are different.")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 👤 The Buyer (The Gambler)")
            st.write("You pay a Premium to own the contract.")
            st.markdown("""
            * **Risk:** Limited (You can only lose what you paid).
            * **Reward:** Unlimited (The stock can go to the moon).
            * **Win Rate:** **LOW.** (Most options expire worthless).
            * **Enemy:** Time. Every day the stock doesn't move, you lose money.
            """)
            
        with col2:
            st.markdown("### 🏦 The Seller (The Casino)")
            st.write("You collect the Premium and take on the obligation.")
            st.markdown("""
            * **Risk:** potentially UNLIMITED (unless hedged).
            * **Reward:** Limited (You keep the premium).
            * **Win Rate:** **HIGH.** (You win if the stock does nothing).
            * **Ally:** Time. You get paid for every day the stock sits still.
            """)
            
        st.divider()
        st.warning("🚀 **OpStruct Philosophy:** We want the Win Rate of the Casino, but with the Safety of the Gambler. That is why we use **Spreads** (Tab 4).")

    # --- MODULE 3: THE GREEKS ---
    with tab3:
        st.header("The Greeks (The Dashboard)")
        st.markdown("Options prices aren't random. They are driven by 4 variables.")
        
        with st.expander("Δ DELTA (Speed & Probability)", expanded=True):
            st.markdown("""
            **What it is:** How much the option price moves for every $1 the stock moves.
            
            * **The Cheat Code:** Delta is roughly the **% Probability** the option will win.
            * **Example:** A `0.30 Delta` option has a ~30% chance of expiring in the money.
            * **Use it for:** Choosing your risk level.
            """)
            
        with st.expander("Θ THETA (Time Decay)"):
            st.markdown("""
            **What it is:** How much value the option loses **every single day**.
            
            * **The Analogy:** An Ice Cube melting.
            * **For Buyers:** Theta is your enemy. You are racing against the melt.
            * **For Sellers:** Theta is your friend. You are collecting the 'melt' as income.
            """)
            
        with st.expander("ν VEGA (Fear / Volatility)"):
            st.markdown("""
            **What it is:** Sensitivity to Volatility (Implied Volatility).
            
            * **The Analogy:** The 'Panic' Tax.
            * **High Vega:** When the market crashes, fear spikes. Options become incredibly expensive (like buying water in a desert).
            * **Strategy:** Sell High Vega (when everyone is scared). Buy Low Vega (when everyone is calm).
            """)
            
        with st.expander("Γ GAMMA (Acceleration)"):
            st.markdown("""
            **What it is:** How fast Delta changes.
            * **The Danger Zone:** Gamma explodes in the last week before expiration. It turns small moves into massive P&L swings. This is why trading 0-Day options (0DTE) is like juggling dynamite.
            """)

    # --- MODULE 4: STRATEGIES ---
    with tab4:
        st.header("Structuring the Trade")
        st.markdown("Never trade 'Naked' (Buy/Sell single options). Use 'Spreads' to engineer your edge.")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### 🐂 The Vertical Spread")
            st.write("**Strategy:** Buy an Expensive Option, Sell a Cheaper Option.")
            st.markdown("""
            * **Why?** The option you SELL pays for part of the option you BUY.
            * **Benefit:** It lowers your cost and raises your Breakeven price.
            * **Tradeoff:** You cap your maximum profit. (But we don't care about hitting home runs; we want base hits).
            """)
            
        with c2:
            st.markdown("### 🦅 The Iron Condor")
            st.write("**Strategy:** Sell a Call above the price, Sell a Put below the price.")
            st.markdown("""
            * **Why?** You are betting the stock will stay in a "Range."
            * **Benefit:** You collect rent (Theta) from both sides.
            * **Tradeoff:** If the stock explodes Up or Down, you lose. Best for boring markets.
            """)

# ==================================================
#                 PAGE 3: THE TERMINAL (PRO)
# ==================================================
def page_terminal():
    # --- QUANT ENGINE (FIXED: VECTOR SAFE) ---
    class QuantEngine:
        def __init__(self, risk_free_rate=0.045):
            self.r = risk_free_rate

        def black_scholes_call(self, S, K, T, sigma):
            # Using np.maximum for vector operations
            if isinstance(T, float) and T <= 0.001: return max(0.0, S - K)
            
            d1 = (np.log(S / K) + (self.r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
            d2 = d1 - sigma * np.sqrt(T)
            return S * norm.cdf(d1) - K * np.exp(-self.r * T) * norm.cdf(d2)

        def black_scholes_put(self, S, K, T, sigma):
            if isinstance(T, float) and T <= 0.001: return max(0.0, K - S)
            
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

        with c2: expiry = st.selectbox("Expiration", exps[:12])
        with c3: view = st.selectbox("Strategy", ["Bullish (Call Spread)", "Bearish (Put Spread)", "Neutral (Income Strangle)"])

        with st.spinner(f"Structuring trades for {ticker}..."):
            current_price = hist['Close'].iloc[-1]
            
            # GREEKS CALCULATION
            _, calls, puts = get_chain(ticker, expiry)
            calls = calculate_greeks(calls, current_price, expiry, "call")
            puts = calculate_greeks(puts, current_price, expiry, "put")
            
            # CALC DAYS TO EXPIRY
            dte = (datetime.strptime(expiry, '%Y-%m-%d') - datetime.now()).days
            st.metric("Spot Price", f"${current_price:.2f}", f"{dte} DTE")
            
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
                
                # SIMULATION LAB
                st.divider()
                st.subheader("🧪 Casino Probability Lab")
                st.caption("Advanced Risk Analysis using Monte Carlo approximations.")
                
                sim_col1, sim_col2 = st.columns(2)
                with sim_col1: 
                    slider_max = dte if dte > 0 else 1
                    days_forward = st.slider("⏳ Time Travel (Days Passed)", 0, slider_max, 0)
                with sim_col2: 
                    vol_adjust = st.slider("⚡ Volatility Adjustment (%)", -80, 300, 0)

                # MATH ENGINE (VECTORIZED)
                spot_range = np.linspace(current_price * 0.7, current_price * 1.3, 200)
                
                pnl_expiration = np.zeros_like(spot_range) - (total_price * 100)
                for leg in trade['Legs']:
                    if leg['type'] == "call":
                        payoff = np.maximum(0, spot_range - leg['strike']) * 100
                    else:
                        payoff = np.maximum(0, leg['strike'] - spot_range) * 100
                    
                    if leg['side'] == "BUY": pnl_expiration += payoff
                    else: pnl_expiration -= payoff

                pnl_simulated = np.zeros_like(spot_range) - (total_price * 100)
                sim_T = max(0.001, (dte - days_forward) / 365.0)
                
                for leg in trade['Legs']:
                    sim_sigma = (leg['impliedVolatility'] * (1 + vol_adjust/100))
                    if sim_sigma < 0.01: sim_sigma = 0.01
                    
                    if leg['type'] == "call":
                        new_price = quant.black_scholes_call(spot_range, leg['strike'], sim_T, sim_sigma)
                    else:
                        new_price = quant.black_scholes_put(spot_range, leg['strike'], sim_T, sim_sigma)
                    
                    if leg['side'] == "BUY": pnl_simulated += (new_price * 100)
                    else: pnl_simulated -= (new_price * 100)

                # CALCULATE PROBABILITY & EV
                sigma_now = trade['Legs'][0]['impliedVolatility']
                T_full = max(0.001, dte / 365.0)
                pdf = norm.pdf(np.log(spot_range / current_price), loc=(0.045 - 0.5 * sigma_now**2) * T_full, scale=sigma_now * np.sqrt(T_full))
                pdf = pdf / pdf.sum()
                
                expected_value = np.sum(pnl_expiration * pdf)
                prob_profit = np.sum(pdf[pnl_expiration > 0]) * 100
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Win Probability (PoP)", f"{prob_profit:.1f}%")
                ev_color = "normal" if expected_value > 0 else "inverse"
                m2.metric("Expected Value (EV)", f"${expected_value:.2f}", "Avg return per trade", delta_color=ev_color)
                
                max_loss = np.min(pnl_expiration)
                max_win = np.max(pnl_expiration)
                m3.metric("Max Risk / Reward", f"${max_loss:.0f} / ${max_win:.0f}")

                fig = go.Figure()
                fig.add_trace(go.Scatter(x=spot_range, y=pnl_expiration, mode='lines', 
                                         name='Expiration P&L', line=dict(color='white', dash='dot')))
                fig.add_trace(go.Scatter(x=spot_range, y=pnl_simulated, mode='lines', 
                                         name=f'Simulated (T+{days_forward})', fill='tozeroy', 
                                         line=dict(color='#00FF00' if expected_value > 0 else '#FF4B4B')))
                
                fig.add_hline(y=0, line_color="gray", line_width=1)
                fig.add_vline(x=current_price, line_color="yellow", annotation_text="Spot")
                fig.update_layout(template="plotly_dark", height=500, title="Probability-Weighted Outcome", yaxis_title="P/L ($)")
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
