import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from scipy.stats import norm
from datetime import datetime, timedelta
import plotly.graph_objects as go
import requests
import textwrap
import time

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="OpStruct Pro",
    page_icon="♟️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- MOBILE-OPTIMIZED CSS STYLING ---
st.markdown("""
<style>
    /* GLOBAL THEME */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=JetBrains+Mono:wght@400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background-color: #0B0E11; /* Deep Charcoal */
        color: #E0E0E0;
    }
    
    /* HEADERS */
    h1, h2, h3 {
        font-weight: 600;
        letter-spacing: -0.5px;
    }

    /* HERO TITLE CLASS */
    .hero-title {
        font-size: 4.5rem;
        background: -webkit-linear-gradient(45deg, #00FF88, #00A3FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
        line-height: 1.1;
    }
    
    /* TERMINAL FONT */
    .mono {
        font-family: 'JetBrains Mono', monospace;
    }
    
    /* CUSTOM CARDS */
    .concept-card {
        background: rgba(30, 35, 45, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 24px;
        border-radius: 12px;
        margin-bottom: 20px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .concept-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
        border-color: rgba(0, 255, 136, 0.3);
    }
    
    .concept-title {
        color: #00FF88;
        font-weight: 700;
        font-size: 1.3rem;
        margin-bottom: 8px;
    }

    /* TRADE TICKET STYLES */
    .trade-ticket {
        background: #151920; 
        border: 1px solid #333; 
        border-radius: 12px; 
        padding: 24px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        font-family: 'Inter', sans-serif;
    }
    .ticket-header {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #888;
        border-bottom: 1px solid #333;
        padding-bottom: 10px;
        margin-bottom: 15px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .leg-row {
        display: flex; 
        justify-content: space-between;
        align-items: center;
        padding: 12px 0; 
        border-bottom: 1px solid #2a2e35;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.95rem;
        flex-wrap: wrap;
    }
    .leg-buy { color: #00FF88; background: rgba(0, 255, 136, 0.1); padding: 2px 6px; border-radius: 4px; white-space: nowrap; }
    .leg-sell { color: #FF4B4B; background: rgba(255, 75, 75, 0.1); padding: 2px 6px; border-radius: 4px; white-space: nowrap; }
    
    .ticket-footer {
        margin-top: 20px;
        padding-top: 15px;
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
    }
    .cost-val {
        font-size: 1.8rem;
        font-weight: 700;
        color: #fff;
    }
    
    /* METRIC CONTAINERS */
    div[data-testid="stMetric"] {
        background-color: #161B22;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #30363D;
    }
    
    /* SIDEBAR BUTTONS */
    section[data-testid="stSidebar"] button {
        width: 100%;
        text-align: left;
        padding-left: 20px;
        border: none;
        background: transparent;
        color: #ccc;
    }
    section[data-testid="stSidebar"] button:hover {
        color: #fff;
        background: #1F2530;
    }

    /* MOBILE OVERRIDES */
    @media only screen and (max-width: 600px) {
        .hero-title { font-size: 2.8rem !important; }
        .concept-card, .trade-ticket { padding: 16px !important; }
        .cost-val { font-size: 1.4rem !important; }
        div.block-container { padding-top: 2rem !important; }
    }
</style>
""", unsafe_allow_html=True)

# --- NAVIGATION STATE ---
if 'page' not in st.session_state: st.session_state.page = 'home'
if 'user_level' not in st.session_state: st.session_state.user_level = 'Rookie'

def set_page(page_name):
    st.session_state.page = page_name

# --- INSTITUTIONAL GRADE MATH ENGINE ---
class VectorizedQuantEngine:
    def __init__(self):
        # DYNAMIC RISK FREE RATE: Fetch 13-Week Treasury Bill Yield
        # This is critical for accurate Theta and Rho pricing
        try:
            tnx = yf.Ticker("^IRX")
            hist = tnx.history(period="1d")
            if not hist.empty:
                # Ticker returns yield as whole number (e.g., 4.5), convert to decimal
                self.r = hist['Close'].iloc[-1] / 100
            else:
                self.r = 0.045 # Fallback to 4.5%
        except:
            self.r = 0.045

    def calculate_greeks_vectorized(self, df, S, T, sigma_col='impliedVolatility', type='call'):
        """
        Vectorized Black-Scholes-Merton implementation.
        Calculates Delta, Theta, Vega, and Theoretical Price instantly for whole chains.
        """
        # Handle missing IVs by using a reasonable default (0.40) to prevent crashes
        sigma = df[sigma_col].replace(0, np.nan).fillna(0.40) 
        K = df['strike']
        
        # Prevent divide by zero for 0DTE options (set min time to ~4 hours)
        T = np.maximum(T, 0.001) 

        d1 = (np.log(S / K) + (self.r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        # Standard Normal Probability Density Function (PDF) and CDF
        pdf_d1 = norm.pdf(d1)
        cdf_d1 = norm.cdf(d1)
        cdf_d2 = norm.cdf(d2)
        cdf_neg_d1 = norm.cdf(-d1)
        cdf_neg_d2 = norm.cdf(-d2)

        if type == 'call':
            df['theo_price'] = S * cdf_d1 - K * np.exp(-self.r * T) * cdf_d2
            df['delta'] = cdf_d1
            
            # THETA CALCULATION (The "Bleed")
            # Theta = -(S*sigma*pdf(d1)) / (2*sqrt(T)) - r*K*exp(-rT)*N(d2)
            term1 = -(S * sigma * pdf_d1) / (2 * np.sqrt(T))
            term2 = self.r * K * np.exp(-self.r * T) * cdf_d2
            df['theta'] = (term1 - term2) / 365.0 # Annualized -> Daily
            
        else: # PUT
            df['theo_price'] = K * np.exp(-self.r * T) * cdf_neg_d2 - S * cdf_neg_d1
            df['delta'] = cdf_d1 - 1
            
            # THETA CALCULATION
            term1 = -(S * sigma * pdf_d1) / (2 * np.sqrt(T))
            term2 = self.r * K * np.exp(-self.r * T) * cdf_neg_d2
            df['theta'] = (term1 + term2) / 365.0

        # VEGA: Sensitivity to 1% change in IV
        df['vega'] = (S * pdf_d1 * np.sqrt(T)) / 100 
        
        return df

    def find_closest_strike(self, df, target_delta):
        # Drop NaNs to ensure we pick valid liquid strikes
        df_clean = df.dropna(subset=['delta'])
        if df_clean.empty: return df.iloc[0]
        idx = (np.abs(df_clean['delta'] - target_delta)).argmin()
        return df_clean.iloc[idx]

    def black_scholes_single(self, S, K, T, sigma, type="call"):
        """ Helper for the P&L Simulator Loop (Numpy Array Compatible) """
        T = np.maximum(T, 0.001)
        d1 = (np.log(S / K) + (self.r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        if type == "call": 
            return S * norm.cdf(d1) - K * np.exp(-self.r * T) * norm.cdf(d2)
        else: 
            return K * np.exp(-self.r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

# --- HELPER: SMART TICKER SEARCH ---
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

# --- EDUCATIONAL CONTENT (FULL) ---
ACADEMY_CONTENT = {
    "101": {
        "title": "Module 101: The Option Contract",
        "levels": {
            "Rookie": {"Call": "Discount Coupon.", "Put": "Car Insurance.", "Key": "Options give rights, not obligations."},
            "Trader": {"Call": "Bullish Leverage. Delta > 0.", "Put": "Bearish Protection. Delta < 0.", "Key": "Leverage cuts both ways."},
            "Quant": {"Call": "Asymmetric payoff. Positive Convexity.", "Put": "Hedging instrument. Skewed IV.", "Key": "Payoff = max(S-K, 0)."}
        }
    },
    "201": {
        "title": "Module 201: The Casino Rule",
        "levels": {
            "Rookie": {"Buy": "Lottery Ticket.", "Sell": "The Casino.", "Key": "The house always wins."},
            "Trader": {"Buy": "Long Vol (Debit).", "Sell": "Short Vol (Credit).", "Key": "Professionals sell Theta."},
            "Quant": {"Buy": "Long Gamma/Vega.", "Sell": "Harvest VRP (Variance Risk Premium).", "Key": "IV > RV systematically."}
        }
    },
    "301": {
        "title": "Module 301: The Greeks",
        "levels": {
            "Rookie": {"Delta": "Speed/Direction.", "Theta": "Time Decay.", "Vega": "Panic.", "Key": "Greeks explain P&L movement."},
            "Trader": {"Delta": "Probability ITM.", "Theta": "Daily Bill.", "Vega": "Vol Sensitivity.", "Key": "Sell Vega when high, Buy when low."},
            "Quant": {"Delta": "d1 First Derivative.", "Theta": "Time Derivative.", "Vega": "Vol Derivative.", "Key": "Sensitivities of the BSM equation."}
        }
    },
    "401": {
        "title": "Module 401: Spreads",
        "levels": {
            "Rookie": {"Concept": "The Combo Meal.", "Benefit": "Cheaper & Safer.", "Key": "Don't bet the farm on one trade."},
            "Trader": {"Concept": "Vertical Spreads.", "Benefit": "Defined Risk / Higher POP.", "Key": "Capped upside for sleep-at-night risk."},
            "Quant": {"Concept": "Factor Isolation.", "Benefit": "Margin Efficiency.", "Key": "Isolating Delta while neutralizing Vega."}
        }
    }
}

QUIZ_BANK = {
    "Rookie": [
        {"q": "A Call Option gives you the right, but not the...?", "options": ["Obligation", "Speed", "Guarantee"], "a": "Obligation"},
        {"q": "Buying a Put is like...?", "options": ["Lottery", "Insurance", "Loan"], "a": "Insurance"},
    ],
    "Trader": [
        {"q": "Which Greek measures Time Decay?", "options": ["Delta", "Theta", "Vega"], "a": "Theta"},
        {"q": "If Long Options, Theta is...?", "options": ["Friend", "Enemy", "Neutral"], "a": "Enemy"},
    ],
    "Quant": [
         {"q": "Positive Gamma implies your P&L curve is...?", "options": ["Convex", "Concave", "Linear"], "a": "Convex"},
         {"q": "To isolate Delta and neutralize Vega, you use a...?", "options": ["Vertical Spread", "Calendar Spread", "Strangle"], "a": "Vertical Spread"}
    ]
}

# ==================================================
#                  PAGE 1: HOMEPAGE
# ==================================================
def page_home():
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style="text-align: center;">
            <h1 class="hero-title">OpStruct.</h1>
            <h3 style="color: #8899A6; font-weight: 400; margin-top: 10px;">Master the Mathematics of Risk.</h3>
        </div>
        """, 
        unsafe_allow_html=True
    )
    st.markdown("---")
    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown("""
        <div class="concept-card">
            <div class="concept-emoji">🎓</div>
            <div class="concept-title">The University</div>
            <p class="card-text">Gamified learning path. Start as a Rookie, pass exams, and unlock Quant clearance.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Enter University →", key="btn_academy", use_container_width=True): set_page('academy')
    with col2:
        st.markdown("""
        <div class="concept-card">
            <div class="concept-emoji">📐</div>
            <div class="concept-title">The Terminal</div>
            <p class="card-text">Institutional-grade structuring engine. <b>Visualize P&L, POP, and Greeks</b> in real-time.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Launch Terminal →", key="btn_terminal", use_container_width=True): set_page('terminal')

# ==================================================
#                  PAGE 2: ACADEMY
# ==================================================
def page_academy():
    current_level = st.session_state.user_level
    lvl_map = {"Rookie": 0, "Trader": 50, "Quant": 100}
    
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown(f"## 🎓 Clearance: <span style='color:#00FF88'>{current_level.upper()}</span>", unsafe_allow_html=True)
        st.progress(lvl_map.get(current_level, 0))
    with c2:
        st.markdown(f"### Level {int(lvl_map.get(current_level)/50 + 1)}")

    st.markdown("---")
    tabs = st.tabs(["101: Contracts", "201: Casino Rule", "301: Greeks", "401: Spreads"])
    
    with tabs[0]:
        content = ACADEMY_CONTENT["101"]["levels"][current_level]
        st.subheader(ACADEMY_CONTENT["101"]["title"])
        c_a, c_b = st.columns(2)
        c_a.info(f"**CALL**: {content['Call']}")
        c_b.error(f"**PUT**: {content['Put']}")
        st.success(f"💡 {content['Key']}")

    with tabs[1]:
        content = ACADEMY_CONTENT["201"]["levels"][current_level]
        st.subheader(ACADEMY_CONTENT["201"]["title"])
        c_a, c_b = st.columns(2)
        c_a.error(f"**BUY**: {content['Buy']}")
        c_b.success(f"**SELL**: {content['Sell']}")
        st.info(f"💡 {content['Key']}")

    with tabs[2]:
        content = ACADEMY_CONTENT["301"]["levels"][current_level]
        st.subheader(ACADEMY_CONTENT["301"]["title"])
        c1, c2, c3 = st.columns(3)
        c1.metric("Delta", "Price", delta_color="normal"); c1.write(content['Delta'])
        c2.metric("Theta", "Time", delta_color="inverse"); c2.write(content['Theta'])
        c3.metric("Vega", "Vol", delta_color="off"); c3.write(content['Vega'])
        st.success(f"💡 {content['Key']}")

    with tabs[3]:
        content = ACADEMY_CONTENT["401"]["levels"][current_level]
        st.subheader(ACADEMY_CONTENT["401"]["title"])
        st.info(f"**Concept**: {content['Concept']}")
        st.success(f"**Benefit**: {content['Benefit']}")
        st.caption(f"💡 {content['Key']}")

    st.markdown("---")
    if current_level == "Quant":
        st.balloons()
        st.success("🎉 You are a certified Quantitative Structurer.")
        if st.button("Reset"): 
            st.session_state.user_level = 'Rookie'
            st.rerun()
    else:
        with st.expander(f"📝 Take {current_level} Exam", expanded=False):
            with st.form(key=f"quiz_{current_level}"):
                score = 0
                quiz_data = QUIZ_BANK[current_level]
                for i, q in enumerate(quiz_data):
                    st.markdown(f"**Q{i+1}: {q['q']}**")
                    ans = st.radio(f"A{i}", q['options'], key=f"q_{current_level}_{i}", label_visibility="collapsed")
                    if ans == q['a']: score += 1
                    st.divider()
                if st.form_submit_button("Submit"):
                    if score == len(quiz_data):
                        st.success("PERFECT SCORE!")
                        st.session_state.user_level = "Trader" if current_level == "Rookie" else "Quant"
                        st.rerun()
                    else:
                        st.error("Failed. Try again.")

# ==================================================
#                  PAGE 3: TERMINAL (UPGRADED)
# ==================================================
def page_terminal():
    quant = VectorizedQuantEngine()

    # IV RANK UTILITY
    def get_iv_rank(stock_obj):
        try:
            hist = stock_obj.history(period="1y")
            if hist.empty: return 0, 0
            hist['Log_Ret'] = np.log(hist['Close'] / hist['Close'].shift(1))
            hist['Volatility'] = hist['Log_Ret'].rolling(window=30).std() * np.sqrt(252) * 100
            vol_data = hist['Volatility'].dropna()
            current_vol = vol_data.iloc[-1]
            mn, mx = vol_data.min(), vol_data.max()
            iv_rank = (current_vol - mn) / (mx - mn) * 100 if mx != mn else 0
            return current_vol, iv_rank
        except: return 0, 0

    @st.cache_data(ttl=300)
    def get_chain_and_greeks(ticker, expiry, current_price):
        stock = yf.Ticker(ticker)
        try:
            opt = stock.option_chain(expiry)
            calls, puts = opt.calls, opt.puts
        except: return None, None
        
        T = (datetime.strptime(expiry, "%Y-%m-%d") - datetime.now()).days / 365.0
        calls = quant.calculate_greeks_vectorized(calls, current_price, T, type='call')
        puts = quant.calculate_greeks_vectorized(puts, current_price, T, type='put')
        return calls, puts

    st.markdown("## 📐 OpStruct Pro Terminal")
    
    # INPUTS
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        raw_input = st.text_input("Ticker", "SPY").strip()
        ticker = lookup_ticker(raw_input)
    
    stock = yf.Ticker(ticker)
    try: exps = stock.options
    except: exps = []
    
    if not exps:
        st.warning("No options data found.")
        return

    with c2: expiry = st.selectbox("Expiry", exps[:12])
    with c3: view = st.selectbox("Strategy", ["Bullish (Call Debit)", "Bearish (Put Debit)", "Neutral (Strangle)"])

    if st.button("Initialize Terminal", type="primary", use_container_width=True):
        with st.spinner(f"Calculating Greeks for {ticker}..."):
            hist = stock.history(period="5d")
            if hist.empty: return
            current_price = hist['Close'].iloc[-1]
            curr_vol, iv_rank = get_iv_rank(stock)
            calls, puts = get_chain_and_greeks(ticker, expiry, current_price)
            
            if calls is None: return
            dte = (datetime.strptime(expiry, '%Y-%m-%d') - datetime.now()).days

            # AUTO STRUCTURING
            trade = {}
            if "Bullish" in view:
                buy_leg = quant.find_closest_strike(calls, 0.50)
                sell_leg = quant.find_closest_strike(calls, 0.30)
                if buy_leg['strike'] > sell_leg['strike']: sell_leg = quant.find_closest_strike(calls, 0.20)
                buy_leg['side'] = "BUY"; sell_leg['side'] = "SELL"
                buy_leg['type'] = "call"; sell_leg['type'] = "call"
                trade = {"Legs": [buy_leg, sell_leg], "Type": "Call Debit Spread"}
            elif "Bearish" in view:
                buy_leg = quant.find_closest_strike(puts, -0.50)
                sell_leg = quant.find_closest_strike(puts, -0.30)
                buy_leg['side'] = "BUY"; sell_leg['side'] = "SELL"
                buy_leg['type'] = "put"; sell_leg['type'] = "put"
                trade = {"Legs": [buy_leg, sell_leg], "Type": "Put Debit Spread"}
            elif "Neutral" in view:
                call_leg = quant.find_closest_strike(calls, 0.20)
                put_leg = quant.find_closest_strike(puts, -0.20)
                call_leg['side'] = "SELL"; put_leg['side'] = "SELL"
                call_leg['type'] = "call"; put_leg['type'] = "put"
                trade = {"Legs": [call_leg, put_leg], "Type": "Short Strangle"}

            st.session_state['terminal_data'] = {
                "ticker": ticker, "current_price": current_price,
                "iv_rank": iv_rank, "curr_vol": curr_vol,
                "calls": calls, "puts": puts, "trade": trade, "dte": dte
            }

    # RENDER TERMINAL
    if 'terminal_data' in st.session_state:
        data = st.session_state['terminal_data']
        if 'calls' not in data or data['calls'] is None:
            st.warning("Data outdated. Re-initialize."); return

        # DASHBOARD
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Price", f"${data['current_price']:.2f}")
        m2.metric("IV Rank", f"{data['iv_rank']:.0f}%")
        m3.metric("Implied Vol", f"{data['curr_vol']:.1f}%")
        m4.metric("Risk Free Rate", f"{quant.r*100:.2f}%")

        # VOL SKEW CHART
        with st.expander("Volatility Surface Analysis", expanded=True):
            skew_fig = go.Figure()
            # Filter noise
            c_view = data['calls'][ (data['calls']['strike'] > data['current_price']*0.8) & (data['calls']['strike'] < data['current_price']*1.2) ]
            p_view = data['puts'][ (data['puts']['strike'] > data['current_price']*0.8) & (data['puts']['strike'] < data['current_price']*1.2) ]
            
            skew_fig.add_trace(go.Scatter(x=c_view['strike'], y=c_view['impliedVolatility']*100, mode='lines', name='Call IV', line=dict(color='#00FF88')))
            skew_fig.add_trace(go.Scatter(x=p_view['strike'], y=p_view['impliedVolatility']*100, mode='lines', name='Put IV', line=dict(color='#FF4B4B')))
            skew_fig.update_layout(template="plotly_dark", height=250, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(skew_fig, use_container_width=True)

        st.divider()
        
        # TICKET & SIMULATION
        trade = data['trade']
        if trade:
            c_left, c_right = st.columns([1, 2])
            
            with c_left:
                st.subheader("Trade Structure")
                total_price = 0
                rows = ""
                for leg in trade['Legs']:
                    price = leg.get('lastPrice', leg.get('theo_price', 0))
                    side = leg['side']
                    if side == "BUY": total_price += price
                    else: total_price -= price
                    
                    css = "leg-buy" if side == "BUY" else "leg-sell"
                    rows += f"""<div class="leg-row"><span class="mono"><b class="{css}">{side}</b> {leg['strike']} {leg['type'].upper()}</span><span class="mono" style="color:#888;">Δ {leg['delta']:.2f} | ${price:.2f}</span></div>"""
                
                net_cost = total_price * 100
                lbl = f"Debit: ${net_cost:.2f}" if total_price > 0 else f"Credit: ${abs(net_cost):.2f}"
                
                # PROBABILITY OF PROFIT (POP) LOGIC
                pop = 50.0
                if "Debit" in trade['Type']:
                    long_leg = trade['Legs'][0]
                    vol_annual = data['curr_vol'] / 100
                    time_annual = data['dte'] / 365.0
                    expected_move = data['current_price'] * vol_annual * np.sqrt(time_annual)
                    
                    if expected_move > 0:
                        if "Call" in trade['Type']:
                            breakeven = long_leg['strike'] + total_price
                            z = (breakeven - data['current_price']) / expected_move
                            pop = norm.sf(z) * 100
                        else:
                            breakeven = long_leg['strike'] - total_price
                            z = (data['current_price'] - breakeven) / expected_move
                            pop = norm.sf(z) * 100

                st.markdown(f"""
                <div class="trade-ticket">
                    <div class="ticket-header"><span>{trade['Type']}</span></div>
                    {rows}
                    <div class="ticket-footer">
                        <div class="cost-display"><div class="cost-val">{lbl}</div></div>
                    </div>
                    <div style="margin-top: 15px; padding: 8px; background: rgba(255,255,255,0.05); border-radius: 4px; display: flex; justify-content: space-between;">
                        <span style="color: #888;">Est. Probability (POP)</span>
                        <span style="color: #00FF88; font-weight: bold;">{pop:.1f}%</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with c_right:
                st.subheader("Profit/Loss Simulation")
                l1, l2 = st.columns(2)
                days_fwd = l1.slider("⏳ Days Forward", 0, max(1, data['dte']), 0)
                vol_adj = l2.slider("⚡ Vol Adjust (%)", -50, 50, 0)
                
                # SIMULATION LOOP
                spot_range = np.linspace(data['current_price'] * 0.75, data['current_price'] * 1.25, 100)
                sim_T = max(0.001, (data['dte'] - days_fwd) / 365.0)
                pnl_sim = np.zeros_like(spot_range) - (total_price * 100)
                
                for leg in trade['Legs']:
                    sim_sigma = max(0.01, leg['impliedVolatility'] * (1 + vol_adj/100))
                    leg_prices = quant.black_scholes_single(spot_range, leg['strike'], sim_T, sim_sigma, leg['type'])
                    if leg['side'] == "BUY": pnl_sim += (leg_prices * 100)
                    else: pnl_sim -= (leg_prices * 100)

                # PLOTLY CHART WITH ZONES
                fig = go.Figure()
                pos_mask = pnl_sim >= 0
                neg_mask = pnl_sim < 0
                
                fig.add_trace(go.Scatter(x=spot_range[pos_mask], y=pnl_sim[pos_mask], mode='lines', name='Profit', line=dict(color='#00FF88', width=0), fill='tozeroy', fillcolor='rgba(0, 255, 136, 0.2)'))
                fig.add_trace(go.Scatter(x=spot_range[neg_mask], y=pnl_sim[neg_mask], mode='lines', name='Loss', line=dict(color='#FF4B4B', width=0), fill='tozeroy', fillcolor='rgba(255, 75, 75, 0.2)'))
                fig.add_trace(go.Scatter(x=spot_range, y=pnl_sim, mode='lines', line=dict(color='white', width=2)))
                
                fig.add_vline(x=data['current_price'], line_dash="dash", line_color="#F4D03F")
                fig.add_hline(y=0, line_color="#555")
                fig.update_layout(template="plotly_dark", height=350, margin=dict(l=10, r=10, t=30, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

# --- MAIN CONTROLLER ---
with st.sidebar:
    st.title("OpStruct")
    if st.button("🏠 Home"): set_page('home')
    if st.button("🎓 Academy"): set_page('academy')
    if st.button("📐 Terminal"): set_page('terminal')
    st.markdown("---")
    st.caption("Educational Prototype v3.0")

if st.session_state.page == 'home': page_home()
elif st.session_state.page == 'academy': page_academy()
elif st.session_state.page == 'terminal': page_terminal()
