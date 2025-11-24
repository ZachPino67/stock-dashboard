import streamlit as st
import yfinance as yf
import numpy as np
import plotly.graph_objects as go
import requests
from datetime import datetime
from scipy.stats import norm

# --- MVC IMPORTS ---
# Logic: The "Brain"
from quant_engine import VectorizedQuantEngine
# Data: The "Assets"
from academy_data import APP_STYLE, ACADEMY_CONTENT, QUIZ_BANK

# --- CONFIGURATION ---
st.set_page_config(
    page_title="OpStruct Pro",
    page_icon="♟️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# INJECT GLOBAL CSS
st.markdown(APP_STYLE, unsafe_allow_html=True)

# --- SESSION STATE MANAGEMENT ---
if 'page' not in st.session_state: st.session_state.page = 'home'
if 'user_level' not in st.session_state: st.session_state.user_level = 'Rookie'

def set_page(page_name):
    st.session_state.page = page_name

# --- CACHED UTILITIES ---
@st.cache_data(ttl=86400, show_spinner=False)
def lookup_ticker(query):
    """Resolves company names to tickers (e.g. 'Apple' -> 'AAPL')."""
    query = query.strip().upper()
    # 1. Try direct hit
    try:
        t = yf.Ticker(query)
        if not t.history(period="1d").empty: return query
    except: pass
    # 2. Try Search API
    try:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()
        if 'quotes' in data and len(data['quotes']) > 0:
            return data['quotes'][0]['symbol']
    except: pass
    return query

@st.cache_data(ttl=300, show_spinner=False)
def fetch_market_data(ticker, expiry, current_price):
    """
    Fetches option chain and runs the Vectorized Quant Engine.
    Cached for 5 minutes to prevent API rate limits.
    """
    # Instantiate engine locally to avoid pickling issues with cache
    engine = VectorizedQuantEngine()
    stock = yf.Ticker(ticker)
    
    try:
        opt = stock.option_chain(expiry)
        calls, puts = opt.calls, opt.puts
    except Exception as e:
        return None, None, None

    # Calculate Time to Expiry (Annualized)
    T = (datetime.strptime(expiry, "%Y-%m-%d") - datetime.now()).days / 365.0
    
    # Run the Math
    calls = engine.calculate_greeks_vectorized(calls, current_price, T, type='call')
    puts = engine.calculate_greeks_vectorized(puts, current_price, T, type='put')
    
    return calls, puts, engine.r # Return Risk-Free Rate too

# ==================================================
#                  VIEW: HOMEPAGE
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
            <p class="card-text">Gamified learning path. Start as a <b>Rookie</b>, pass exams, and unlock <b>Quant</b> clearance.</p>
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
#                  VIEW: ACADEMY
# ==================================================
def page_academy():
    current_level = st.session_state.user_level
    lvl_map = {"Rookie": 0, "Trader": 50, "Quant": 100}
    
    # Progress Header
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown(f"## 🎓 Clearance: <span style='color:#00FF88'>{current_level.upper()}</span>", unsafe_allow_html=True)
        st.progress(lvl_map.get(current_level, 0))
    with c2:
        st.markdown(f"### Level {int(lvl_map.get(current_level)/50 + 1)}")

    st.markdown("---")
    
    # Dynamic Tabs based on imported Data
    module_keys = list(ACADEMY_CONTENT.keys())
    tabs = st.tabs([ACADEMY_CONTENT[k]["title"] for k in module_keys])
    
    for i, key in enumerate(module_keys):
        with tabs[i]:
            module = ACADEMY_CONTENT[key]
            content = module["levels"][current_level]
            
            st.subheader(module["title"])
            
            # Custom Layouts for specific modules for better UX
            if key == "101": # Contracts
                c_a, c_b = st.columns(2)
                c_a.info(f"**CALL**: {content['Call']}")
                c_b.error(f"**PUT**: {content['Put']}")
            elif key == "201": # Casino Rule
                c_a, c_b = st.columns(2)
                c_a.error(f"**BUY**: {content['Buy']}")
                c_b.success(f"**SELL**: {content['Sell']}")
            elif key == "301": # Greeks
                c1, c2, c3 = st.columns(3)
                c1.metric("Delta", "Price", delta_color="normal"); c1.write(content['Delta'])
                c2.metric("Theta", "Time", delta_color="inverse"); c2.write(content['Theta'])
                c3.metric("Vega", "Vol", delta_color="off"); c3.write(content['Vega'])
            else: # Spreads (401) or others
                st.info(f"**Concept**: {content.get('Concept', '')}")
                st.success(f"**Benefit**: {content.get('Benefit', '')}")

            if 'Key' in content:
                st.caption(f"💡 Alpha Note: {content['Key']}")

    st.markdown("---")
    
    # Exam Logic
    if current_level == "Quant":
        st.balloons()
        st.success("🎉 You are a certified Quantitative Structurer.")
        if st.button("Reset Progress"): 
            st.session_state.user_level = 'Rookie'
            st.rerun()
    else:
        with st.expander(f"📝 Take {current_level} Exam", expanded=False):
            with st.form(key=f"quiz_{current_level}"):
                score = 0
                questions = QUIZ_BANK.get(current_level, [])
                
                for idx, q in enumerate(questions):
                    st.markdown(f"**Q{idx+1}: {q['q']}**")
                    ans = st.radio(f"Select Answer {idx}", q['options'], key=f"q_{current_level}_{idx}", label_visibility="collapsed")
                    if ans == q['a']: score += 1
                    st.divider()
                
                if st.form_submit_button("Submit Exam"):
                    if score == len(questions):
                        st.success(f"PASSED! ({score}/{len(questions)})")
                        # Level Up Logic
                        new_level = "Trader" if current_level == "Rookie" else "Quant"
                        st.session_state.user_level = new_level
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"FAILED ({score}/{len(questions)}). Review the modules and try again.")

# ==================================================
#                  VIEW: TERMINAL
# ==================================================
def page_terminal():
    st.markdown("## 📐 OpStruct Pro Terminal")
    
    # 1. Search & Config Row
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        raw_input = st.text_input("Ticker", "SPY").strip()
        ticker = lookup_ticker(raw_input)
    
    # Quick Stock Data Fetch (Lightweight)
    stock = yf.Ticker(ticker)
    try: 
        exps = stock.options
        if not exps: raise ValueError("No chain")
    except: 
        st.warning(f"No options data found for {ticker}. Try SPY, NVDA, or AAPL.")
        return

    with c2: expiry = st.selectbox("Expiry", exps[:12])
    with c3: view = st.selectbox("Strategy", ["Bullish (Call Debit)", "Bearish (Put Debit)", "Neutral (Strangle)"])

    # 2. Initialize / Refresh Button
    if st.button("Initialize Analysis", type="primary", use_container_width=True):
        with st.spinner(f"Crunching Volatility Surface for {ticker}..."):
            # Fetch Historical for Context
            hist = stock.history(period="5d")
            if hist.empty: 
                st.error("Market data unavailable.")
                return
                
            current_price = hist['Close'].iloc[-1]
            
            # Get IV Rank (Simplified)
            try:
                hist_yr = stock.history(period="1y")
                vol = np.log(hist_yr['Close']/hist_yr['Close'].shift(1)).rolling(30).std() * np.sqrt(252) * 100
                curr_vol = vol.iloc[-1]
                min_vol, max_vol = vol.min(), vol.max()
                iv_rank = (curr_vol - min_vol) / (max_vol - min_vol) * 100
            except:
                curr_vol, iv_rank = 0, 0

            # Heavy Lifting (Cached)
            calls, puts, rf_rate = fetch_market_data(ticker, expiry, current_price)
            
            if calls is None:
                st.error("Failed to calculate Greeks.")
                return

            # 3. Auto-Structure Trade based on View
            engine = VectorizedQuantEngine() # Helper for finding strikes
            trade = {}
            
            if "Bullish" in view:
                # Buy 50 Delta Call, Sell 30 Delta Call
                buy_leg = engine.find_closest_strike(calls, 0.50)
                sell_leg = engine.find_closest_strike(calls, 0.30)
                # Sanity Check: Debit spread must buy low, sell high
                if buy_leg['strike'] > sell_leg['strike']: 
                    sell_leg = engine.find_closest_strike(calls, 0.20)
                
                buy_leg['side'] = "BUY"; sell_leg['side'] = "SELL"
                buy_leg['type'] = "call"; sell_leg['type'] = "call"
                trade = {"Legs": [buy_leg, sell_leg], "Type": "Call Debit Spread"}
                
            elif "Bearish" in view:
                # Buy 50 Delta Put, Sell 30 Delta Put
                buy_leg = engine.find_closest_strike(puts, -0.50)
                sell_leg = engine.find_closest_strike(puts, -0.30)
                
                buy_leg['side'] = "BUY"; sell_leg['side'] = "SELL"
                buy_leg['type'] = "put"; sell_leg['type'] = "put"
                trade = {"Legs": [buy_leg, sell_leg], "Type": "Put Debit Spread"}
                
            elif "Neutral" in view:
                # Sell 20 Delta Call, Sell 20 Delta Put
                call_leg = engine.find_closest_strike(calls, 0.20)
                put_leg = engine.find_closest_strike(puts, -0.20)
                
                call_leg['side'] = "SELL"; put_leg['side'] = "SELL"
                call_leg['type'] = "call"; put_leg['type'] = "put"
                trade = {"Legs": [call_leg, put_leg], "Type": "Short Strangle"}

            # Save to Session State (Persistence)
            dte = (datetime.strptime(expiry, '%Y-%m-%d') - datetime.now()).days
            st.session_state['terminal_data'] = {
                "ticker": ticker, "current_price": current_price,
                "iv_rank": iv_rank, "curr_vol": curr_vol, "rf_rate": rf_rate,
                "calls": calls, "puts": puts, "trade": trade, "dte": dte
            }

    # 4. Render Dashboard (If data exists)
    if 'terminal_data' in st.session_state:
        data = st.session_state['terminal_data']
        
        # Stale Data Check
        if data['ticker'] != ticker:
            st.warning("⚠️ Inputs changed. Click 'Initialize Analysis' to update.")

        # Metrics Row
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Spot Price", f"${data['current_price']:.2f}")
        m2.metric("IV Rank", f"{data['iv_rank']:.0f}%", 
                  delta="High" if data['iv_rank']>50 else "Low", 
                  delta_color="inverse" if data['iv_rank']<50 else "normal")
        m3.metric("Implied Vol", f"{data['curr_vol']:.1f}%")
        m4.metric("Risk Free Rate", f"{data['rf_rate']*100:.2f}%")

        # Charts & Ticket
        st.divider()
        c_left, c_right = st.columns([1, 2])

        with c_left:
            st.subheader("Trade Structure")
            trade = data['trade']
            if trade:
                total_price = 0
                rows = ""
                for leg in trade['Legs']:
                    # Pricing fallback
                    price = leg.get('lastPrice', leg.get('theo_price', 0))
                    if leg['side'] == "BUY": total_price += price
                    else: total_price -= price
                    
                    # HTML Construction
                    css = "leg-buy" if leg['side'] == "BUY" else "leg-sell"
                    rows += f"""
                    <div class="leg-row">
                        <span class="mono"><b class="{css}">{leg['side']}</b> {leg['strike']} {leg['type'].upper()}</span>
                        <span class="mono" style="color:#888;">Δ {leg['delta']:.2f} | ${price:.2f}</span>
                    </div>"""

                net_cost = total_price * 100
                label = f"Debit: ${net_cost:.2f}" if total_price > 0 else f"Credit: ${abs(net_cost):.2f}"
                
                # POP Calculation
                pop = 50.0
                engine = VectorizedQuantEngine() # Helper
                # Logic: Z-Score distance to breakeven
                if "Debit" in trade['Type']:
                    long_leg = trade['Legs'][0]
                    vol_annual = data['curr_vol'] / 100
                    time_annual = data['dte'] / 365.0
                    # Expected Move (1 Std Dev)
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
                        <div class="cost-display"><div class="cost-val">{label}</div></div>
                    </div>
                    <div style="margin-top: 15px; padding: 8px; background: rgba(255,255,255,0.05); border-radius: 4px; display: flex; justify-content: space-between;">
                        <span style="color: #888;">Est. Probability (POP)</span>
                        <span style="color: #00FF88; font-weight: bold;">{pop:.1f}%</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        with c_right:
            st.subheader("Profit/Loss Simulation")
            
            # Sliders
            l1, l2 = st.columns(2)
            days_fwd = l1.slider("⏳ Days Forward (Theta Burn)", 0, max(1, data['dte']), 0)
            vol_adj = l2.slider("⚡ IV Shock (%)", -50, 50, 0)
            
            # Simulator Logic (Re-using Engine Helper)
            engine = VectorizedQuantEngine()
            engine.r = data['rf_rate'] # Ensure consistent rate
            
            spot_range = np.linspace(data['current_price'] * 0.8, data['current_price'] * 1.2, 100)
            sim_T = max(0.001, (data['dte'] - days_fwd) / 365.0)
            
            # Base P&L is negative entry cost
            pnl_sim = np.zeros_like(spot_range) - (total_price * 100)
            
            for leg in trade['Legs']:
                sim_sigma = max(0.01, leg['impliedVolatility'] * (1 + vol_adj/100))
                leg_prices = engine.black_scholes_single(spot_range, leg['strike'], sim_T, sim_sigma, leg['type'])
                
                if leg['side'] == "BUY": pnl_sim += (leg_prices * 100)
                else: pnl_sim -= (leg_prices * 100)

            # Plotly Chart
            fig = go.Figure()
            
            # Zones
            pos_mask = pnl_sim >= 0
            neg_mask = pnl_sim < 0
            
            fig.add_trace(go.Scatter(x=spot_range[pos_mask], y=pnl_sim[pos_mask], mode='lines', name='Profit', line=dict(color='#00FF88', width=0), fill='tozeroy', fillcolor='rgba(0, 255, 136, 0.2)'))
            fig.add_trace(go.Scatter(x=spot_range[neg_mask], y=pnl_sim[neg_mask], mode='lines', name='Loss', line=dict(color='#FF4B4B', width=0), fill='tozeroy', fillcolor='rgba(255, 75, 75, 0.2)'))
            fig.add_trace(go.Scatter(x=spot_range, y=pnl_sim, mode='lines', line=dict(color='white', width=2)))
            
            fig.add_vline(x=data['current_price'], line_dash="dash", line_color="#F4D03F", annotation_text="Spot")
            fig.add_hline(y=0, line_color="#555")
            
            fig.update_layout(
                template="plotly_dark", 
                height=350, 
                margin=dict(l=10, r=10, t=30, b=20), 
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)', 
                showlegend=False,
                xaxis_title="Stock Price at T+" + str(days_fwd),
                yaxis_title="P&L ($)"
            )
            st.plotly_chart(fig, use_container_width=True)

# --- MAIN CONTROLLER ROUTER ---
import time # Lazy import for exam delay

with st.sidebar:
    st.title("OpStruct")
    st.caption("Institutional Grade v4.1")
    st.markdown("---")
    if st.button("🏠 Home", use_container_width=True): set_page('home')
    if st.button("🎓 Academy", use_container_width=True): set_page('academy')
    if st.button("📐 Terminal", use_container_width=True): set_page('terminal')
    st.markdown("---")

if st.session_state.page == 'home': page_home()
elif st.session_state.page == 'academy': page_academy()
elif st.session_state.page == 'terminal': page_terminal()
