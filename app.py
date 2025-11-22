import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from scipy.stats import norm
from datetime import datetime
import plotly.graph_objects as go

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
    .nav-btn {
        width: 100%; padding: 15px; border: 1px solid #444; background: #000;
        color: white; border-radius: 8px; margin-bottom: 5px; text-align: left;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE NAVIGATION ---
if 'page' not in st.session_state: st.session_state.page = 'home'

def set_page(page_name):
    st.session_state.page = page_name
import requests # Make sure this is imported

# --- SMART SEARCH HELPER ---
@st.cache_data(ttl=86400) # Cache results for 24h
def lookup_ticker(query):
    """
    Translates 'Apple' -> 'AAPL' using Yahoo's Autocomplete API.
    """
    query = query.strip().upper()
    
    # 1. Check if it's already a valid ticker (Fast Check)
    # If the user types 'AAPL', we don't need to search
    try:
        t = yf.Ticker(query)
        if not t.history(period="1d").empty:
            return query
    except:
        pass

    # 2. Use Yahoo Autocomplete API
    try:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}"
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()
        
        if 'quotes' in data and len(data['quotes']) > 0:
            # Get the first result that is an EQUITY
            for quote in data['quotes']:
                if quote.get('quoteType') == 'EQUITY':
                    return quote['symbol']
            # Fallback to first result
            return data['quotes'][0]['symbol']
    except Exception as e:
        print(f"Search Error: {e}")
        
    return query # Return original if search fails
# ==================================================
#                 PAGE 1: HOMEPAGE
# ==================================================
def page_home():
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown('<h1 style="text-align: center; font-size: 4rem; background: -webkit-linear-gradient(45deg, #00FF00, #00AAFF); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">OpStruct.</h1>', unsafe_allow_html=True)
    st.markdown('<h3 style="text-align: center; color: #888;">Master the Mathematics of Risk.</h3>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    c1, c2, c3 = st.columns(3)
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
#                 PAGE 2: THE ACADEMY (ELI5)
# ==================================================
def page_academy():
    st.title("🎓 The Options Academy")
    st.markdown("Everything explained simply. No math degrees required.")
    
    tab1, tab2, tab3 = st.tabs(["🟢 The Basics (Calls/Puts)", "⚠ Risk (Naked vs Covered)", "Greek Alphabet 101"])
    
    # --- TAB 1: BASICS ---
    with tab1:
        st.header("What is an Option?")
        st.info("💡 **Analogy:** Think of an Option like a **Coupon** or **Car Insurance**.")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("""
            <div class="concept-card" style="border-left: 5px solid #00FF00;">
                <span class="concept-title">📞 The CALL Option</span>
                <p><b>"The Coupon"</b></p>
                <p>You pay $5 today for a coupon that lets you buy a TV for $500 next month.</p>
                <ul>
                    <li><b>If TV price goes to $600:</b> You use the coupon. You buy at $500, sell at $600. You make $100 (minus the $5 coupon cost).</li>
                    <li><b>If TV price drops to $400:</b> You throw the coupon in the trash. You only lost the $5.</li>
                </ul>
                <p><b>TL;DR:</b> You want the price to go 🚀 <b>UP</b>.</p>
            </div>
            """, unsafe_allow_html=True)
            
        with c2:
            st.markdown("""
            <div class="concept-card" style="border-left: 5px solid #FF4B4B;">
                <span class="concept-title">📉 The PUT Option</span>
                <p><b>"The Insurance"</b></p>
                <p>You pay $100 to insure your car (stock) for its current value of $20,000.</p>
                <ul>
                    <li><b>If the car crashes (Stock drops to $0):</b> The insurance pays you $20,000. You are saved.</li>
                    <li><b>If the car is fine (Stock stays up):</b> The insurance expires. You lose the $100 premium.</li>
                </ul>
                <p><b>TL;DR:</b> You want the price to go 📉 <b>DOWN</b>.</p>
            </div>
            """, unsafe_allow_html=True)

    # --- TAB 2: RISK ---
    with tab2:
        st.header("Naked vs. Covered (How to not go broke)")
        st.warning("⚠️ **Crucial Lesson:** Selling options is like being the Casino. Buying options is like being the Gambler.")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### 🍑 Naked (Undefined Risk)")
            st.error("""
            **Selling Naked Calls** is the most dangerous trade in finance.
            * **Scenario:** You promise to sell Apple shares at $200, but you *don't own them*.
            * **Disaster:** Apple goes to $1,000. You *must* buy them at $1,000 and sell at $200.
            * **Loss:** Unlimited. You can go bankrupt in 10 minutes.
            """)
            
        with c2:
            st.markdown("### 🛡️ Covered / Spreads (Defined Risk)")
            st.success("""
            **Covered Calls** are safe.
            * **Scenario:** You own 100 shares of Apple. You promise to sell them at $200.
            * **Outcome:** If Apple goes to $1,000, you just sell your shares. You miss the profit, but you **don't lose money**.
            
            **Vertical Spreads:**
            * Buying one option and Selling another to "cap" your risk. This is how Pros trade.
            """)

    # --- TAB 3: GREEKS ---
    with tab3:
        st.header("The Greeks (The Dashboard of your Car)")
        st.markdown("Options change price based on math variables. We call them Greeks.")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Δ Delta", "Speed", "Direction")
            st.caption("How much the option price moves for every $1 the stock moves. (Also roughly the % probability of profit).")
        with col2:
            st.metric("Θ Theta", "Time", "Decay")
            st.caption("How much value the option loses every single day. Like an ice cube melting.")
        with col3:
            st.metric("Γ Gamma", "Accel", "Risk")
            st.caption("How fast Delta changes. Gamma explodes near expiration. This is the 'Turbo' button.")
        with col4:
            st.metric("ν Vega", "Fear", "Volatility")
            st.caption("How much the price changes when the market gets scared (Volatility).")
# ==================================================
#                 PAGE 3: THE TERMINAL (PRO)
# ==================================================
def page_terminal():
    # --- REUSING THE QUANT ENGINE ---
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

        def find_closest_strike(self, df, target_delta, option_type="call"):
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
    st.markdown("Institutional-grade trade structuring.")
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        # 1. INPUT: Allow raw text
        raw_input = st.text_input("Company or Ticker", "Apple").strip()
        
        # 2. SMART LOOKUP: Convert "Apple" -> "AAPL"
        ticker = lookup_ticker(raw_input)
        
        # Show the user what we found
        if ticker != raw_input.upper():
            st.caption(f"✅ Found: **{ticker}**")
    
    # --- ERROR HANDLING WRAPPER (Prevents Crash) ---
    try:
        stock = yf.Ticker(ticker)
        
        # CHECK 1: Does history exist?
        hist = stock.history(period="5d")
        if hist.empty:
            st.error(f"❌ Could not find data for '{ticker}'. Please try another name.")
            return # STOP HERE if no data
        
        # CHECK 2: Do options exist?
        exps = stock.options
        if not exps:
            st.warning(f"⚠️ '{ticker}' has no options chain available.")
            return # STOP HERE if no options

        with c2: expiry = st.selectbox("Expiration", exps[:6])
        with c3: view = st.selectbox("Strategy", ["Bullish (Call Spread)", "Bearish (Put Spread)", "Neutral (Income Strangle)"])

        # Run Engine
        with st.spinner(f"Structuring trades for {ticker}..."):
            current_price = hist['Close'].iloc[-1]
            
            # Calculate Greeks
            _, calls, puts = get_chain(ticker, expiry)
            calls = calculate_greeks(calls, current_price, expiry, "call")
            puts = calculate_greeks(puts, current_price, expiry, "put")
            
            st.metric("Spot Price", f"${current_price:.2f}", f"{(datetime.strptime(expiry, '%Y-%m-%d') - datetime.now()).days} DTE")
            
            # --- STRATEGY LOGIC ---
            trade = {}
            
            if "Bullish" in view:
                buy_leg = quant.find_closest_strike(calls, 0.50)
                sell_leg = quant.find_closest_strike(calls, 0.30)
                buy_leg['side'] = "BUY"; sell_leg['side'] = "SELL"
                buy_leg['type'] = "call"; sell_leg['type'] = "call"
                trade = {"Legs": [buy_leg, sell_leg], "Type": "Call Debit Spread (Bullish)"}

            elif "Bearish" in view:
                buy_leg = quant.find_closest_strike(puts, -0.50, "put")
                sell_leg = quant.find_closest_strike(puts, -0.30, "put")
                buy_leg['side'] = "BUY"; sell_leg['side'] = "SELL"
                buy_leg['type'] = "put"; sell_leg['type'] = "put"
                trade = {"Legs": [buy_leg, sell_leg], "Type": "Put Debit Spread (Bearish)"}

            elif "Neutral" in view:
                call_leg = quant.find_closest_strike(calls, 0.20)
                put_leg = quant.find_closest_strike(puts, -0.20, "put")
                call_leg['side'] = "SELL"; put_leg['side'] = "SELL"
                call_leg['type'] = "call"; put_leg['type'] = "put"
                trade = {"Legs": [call_leg, put_leg], "Type": "Short Strangle (Income)"}
            
            # --- RENDERER ---
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
                st.subheader("🧪 Simulation Lab")
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
                    if leg['type'] == "call": new_price = quant.black_scholes_call(spot_range, leg['strike'], sim_T, sim_sigma)
                    else: new_price = quant.black_scholes_put(spot_range, leg['strike'], sim_T, sim_sigma)
                    
                    if leg['side'] == "BUY": pnl_simulated += (new_price * 100)
                    else: pnl_simulated -= (new_price * 100)

                fig = go.Figure()
                fig.add_trace(go.Scatter(x=spot_range, y=pnl_simulated, mode='lines', name='Simulated P&L', fill='tozeroy', line=dict(color='#00FF00' if pnl_simulated.max() > 0 else '#FF4B4B')))
                fig.add_hline(y=0, line_color="gray", line_dash="dash")
                fig.add_vline(x=current_price, line_color="yellow")
                fig.update_layout(template="plotly_dark", height=400, title="Projected Outcome", yaxis_title="P/L ($)")
                st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Analysis Error: {e}")
        st.caption("Common causes: Invalid ticker, no options chain, or API timeout.")
            
            # ==================================================
            #           THE SIMULATION LAB (NEW)
            # ==================================================
            st.subheader("🧪 Simulation Lab (The 'What If' Machine)")
            st.caption("Options change price before expiration. Use the sliders to simulate Time Decay and Volatility Shocks.")
            
            sim_col1, sim_col2 = st.columns(2)
            with sim_col1:
                days_forward = st.slider("⏳ Time Travel (Days Passed)", 0, 30, 0)
            with sim_col2:
                vol_adjust = st.slider("⚡ Volatility Adjustment (%)", -50, 50, 0)

            # --- SIMULATION ENGINE ---
            spot_range = np.linspace(current_price * 0.85, current_price * 1.15, 100)
            
            # 1. P&L at Expiration (Static)
            pnl_expiration = np.zeros_like(spot_range) - (total_price * 100)
            for leg in trade['Legs']:
                if leg['type'] == "call":
                    payoff = np.maximum(0, spot_range - leg['strike']) * 100
                else:
                    payoff = np.maximum(0, leg['strike'] - spot_range) * 100
                    
                if leg['side'] == "BUY": pnl_expiration += payoff
                else: pnl_expiration -= payoff
                
            # 2. P&L Now (Simulated Black-Scholes)
            pnl_simulated = np.zeros_like(spot_range) - (total_price * 100)
            
            # Calculate T (Time remaining after sliding days forward)
            total_days = (datetime.strptime(expiry, "%Y-%m-%d") - datetime.now()).days
            sim_T = max(0.001, (total_days - days_forward) / 365.0)
            
            for leg in trade['Legs']:
                # Adjust IV
                sim_sigma = (leg['impliedVolatility'] * (1 + vol_adjust/100))
                if sim_sigma < 0.01: sim_sigma = 0.01
                
                # Re-Price Option using Black-Scholes
                if leg['type'] == "call":
                    new_price = quant.black_scholes_call(spot_range, leg['strike'], sim_T, sim_sigma)
                else:
                    new_price = quant.black_scholes_put(spot_range, leg['strike'], sim_T, sim_sigma)
                
                if leg['side'] == "BUY": pnl_simulated += (new_price * 100)
                else: pnl_simulated -= (new_price * 100)

            # --- PLOTTING ---
            fig = go.Figure()
            
            # Plot Expiration (Dotted)
            fig.add_trace(go.Scatter(x=spot_range, y=pnl_expiration, mode='lines', 
                                     name='At Expiration', line=dict(color='white', dash='dot')))
            
            # Plot Simulated (Solid Color)
            fig.add_trace(go.Scatter(x=spot_range, y=pnl_simulated, mode='lines', 
                                     name=f'Simulated (T+{days_forward})', fill='tozeroy',
                                     line=dict(color='#00FF00' if pnl_simulated.max() > 0 else '#FF4B4B')))
            
            fig.add_hline(y=0, line_color="gray", line_width=1)
            fig.add_vline(x=current_price, line_color="yellow", annotation_text="Spot Price")
            
            fig.update_layout(template="plotly_dark", height=500, 
                              title="P&L: Expiration vs. Simulation",
                              xaxis_title="Stock Price", yaxis_title="Profit/Loss ($)")
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.info("""
            **How to read this:**
            * **Dotted Line:** What you make if you hold until the very end.
            * **Colored Area:** What you make **on that specific day**.
            * **Tip:** Notice how 'Time Travel' shrinks the curve (Theta Decay) and 'Volatility' expands/contracts it.
            """)
# ==================================================
#                 MAIN CONTROLLER
# ==================================================
with st.sidebar:
    st.title("OpStruct")
    if st.button("🏠 Home", use_container_width=True): set_page('home')
    if st.button("🎓 Academy", use_container_width=True): set_page('academy')
    if st.button("📐 Terminal", use_container_width=True): set_page('terminal')

if st.session_state.page == 'home': page_home()      # <--- The fix: changed 'homepage()' to 'page_home()'
elif st.session_state.page == 'academy': page_academy()
elif st.session_state.page == 'terminal': page_terminal()
