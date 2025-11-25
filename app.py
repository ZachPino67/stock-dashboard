import streamlit as st
import yfinance as yf
import numpy as np
import plotly.graph_objects as go
import requests
from datetime import datetime
from scipy.stats import norm
import time

# --- MVC IMPORTS ---
from quant_engine import VectorizedQuantEngine
from academy_data import APP_STYLE, ACADEMY_PHASES, QUIZ_BANK

# --- CONFIGURATION ---
st.set_page_config(
    page_title="OpStruct Pro",
    page_icon="♟️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# INJECT GLOBAL CSS
st.markdown(APP_STYLE, unsafe_allow_html=True)

# --- SESSION STATE ---
if 'page' not in st.session_state: st.session_state.page = 'home'
if 'user_level' not in st.session_state: st.session_state.user_level = 'Rookie'

def set_page(page_name):
    st.session_state.page = page_name

# --- CACHED UTILITIES ---
@st.cache_data(ttl=86400, show_spinner=False)
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

@st.cache_data(ttl=300, show_spinner=False)
def fetch_market_data(ticker, expiry, current_price):
    engine = VectorizedQuantEngine()
    stock = yf.Ticker(ticker)
    try:
        opt = stock.option_chain(expiry)
        calls, puts = opt.calls, opt.puts
    except: return None, None, None
    T = (datetime.strptime(expiry, "%Y-%m-%d") - datetime.now()).days / 365.0
    calls = engine.calculate_greeks_vectorized(calls, current_price, T, type='call')
    puts = engine.calculate_greeks_vectorized(puts, current_price, T, type='put')
    return calls, puts, engine.r

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
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown("""
        <div class="concept-card">
            <div class="concept-emoji">🎓</div>
            <div class="concept-title">The University</div>
            <p class="card-text">Institutional Curriculum. From <b>Account Killers</b> to <b>Dark Pools</b>.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Enter University →", use_container_width=True): set_page('academy')
    with c2:
        st.markdown("""
        <div class="concept-card">
            <div class="concept-emoji">📐</div>
            <div class="concept-title">The Terminal</div>
            <p class="card-text">Structuring engine with <b>Theta & Vega Simulators</b>.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Launch Terminal →", use_container_width=True): set_page('terminal')

# ==================================================
#                  VIEW: ACADEMY (UPDATED)
# ==================================================
def page_academy():
    current_level = st.session_state.user_level
    lvl_map = {"Rookie": 0, "Trader": 50, "Quant": 100}
    
    # LEVEL HEADER & OVERRIDE
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown(f"## 🎓 Clearance: <span style='color:#00FF88'>{current_level.upper()}</span>", unsafe_allow_html=True)
        st.progress(lvl_map.get(current_level, 0))
    with c2:
        st.caption("Override Clearance")
        levels = ["Rookie", "Trader", "Quant"]
        sel = st.selectbox("Lvl", levels, index=levels.index(current_level), label_visibility="collapsed")
        if sel != current_level:
            st.session_state.user_level = sel
            st.rerun()

    st.markdown("---")
    
    # PERMISSION LOGIC
    # Rookie sees Phase 1-2. Trader sees 1-4. Quant sees 1-5.
    visible_phases = []
    if current_level == "Rookie": visible_phases = ["phase1", "phase2"]
    elif current_level == "Trader": visible_phases = ["phase1", "phase2", "phase3", "phase4"]
    else: visible_phases = ["phase1", "phase2", "phase3", "phase4", "phase5"]

    # RENDER PHASES
    tabs = st.tabs([p["title"] for p in ACADEMY_PHASES])
    
    for i, phase in enumerate(ACADEMY_PHASES):
        with tabs[i]:
            # LOCK LOGIC
            if phase["id"] not in visible_phases:
                st.error(f"🔒 Clearance Restricted. Reach **{phase['req_level']}** to unlock this module.")
                st.markdown(f"*{phase['desc']}*")
            else:
                st.info(f"**Objective:** {phase['desc']}")
                
                # Render Topics
                for topic in phase["topics"]:
                    with st.expander(f"📌 {topic['title']}", expanded=False):
                        st.markdown(topic['content'])
                        # Inject Diagram Tags for AI context (Instructions)
                        if "Greeks" in phase['title']: st.caption("")
                        if "Structure" in phase['title']: st.caption("")
                        if "Edge" in phase['title']: st.caption("")

    st.markdown("---")
    
    # EXAM SECTION
    if current_level == "Quant":
        st.balloons()
        st.success("🎉 Curriculum Complete.")
        if st.button("Reset"): 
            st.session_state.user_level = 'Rookie'
            st.rerun()
    else:
        st.subheader(f"🚀 Promotion Exam: {current_level} to Next Level")
        with st.form(key=f"quiz_{current_level}"):
            score = 0
            qs = QUIZ_BANK.get(current_level, [])
            for idx, q in enumerate(qs):
                st.markdown(f"**Q{idx+1}: {q['q']}**")
                ans = st.radio(f"A{idx}", q['options'], key=f"q_{current_level}_{idx}", label_visibility="collapsed")
                if ans == q['a']: score += 1
                st.divider()
            
            if st.form_submit_button("Submit Exam"):
                if score == len(qs):
                    st.success("PASSED!")
                    st.session_state.user_level = "Trader" if current_level == "Rookie" else "Quant"
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("FAILED. Study the material above.")

# ==================================================
#                  VIEW: TERMINAL
# ==================================================
def page_terminal():
    st.markdown("## 📐 OpStruct Pro Terminal")
    
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        raw = st.text_input("Ticker", "SPY").strip()
        ticker = lookup_ticker(raw)
    
    stock = yf.Ticker(ticker)
    try: 
        exps = stock.options
        if not exps: raise ValueError
    except: 
        st.warning("No options found."); return

    with c2: expiry = st.selectbox("Expiry", exps[:12])
    with c3: view = st.selectbox("Strategy", ["Bullish (Call Debit)", "Bearish (Put Debit)", "Neutral (Strangle)"])

    if st.button("Initialize Analysis", type="primary", use_container_width=True):
        with st.spinner("Crunching..."):
            hist = stock.history(period="5d")
            if hist.empty: return
            curr_price = hist['Close'].iloc[-1]
            try:
                h = stock.history(period="1y")
                vol = np.log(h['Close']/h['Close'].shift(1)).rolling(30).std()*np.sqrt(252)*100
                curr_vol, iv_rank = vol.iloc[-1], (vol.iloc[-1]-vol.min())/(vol.max()-vol.min())*100
            except: curr_vol, iv_rank = 0, 0

            calls, puts, r = fetch_market_data(ticker, expiry, curr_price)
            if calls is None: st.error("Math Error"); return

            eng = VectorizedQuantEngine()
            trade = {}
            if "Bullish" in view:
                b = eng.find_closest_strike(calls, 0.50)
                valid = calls[calls['strike'] > b['strike']]
                s = eng.find_closest_strike(valid, 0.30) if not valid.empty else b
                b['side'], s['side'], b['type'], s['type'] = "BUY", "SELL", "call", "call"
                trade = {"Legs": [b, s], "Type": "Call Debit Spread"}
            elif "Bearish" in view:
                b = eng.find_closest_strike(puts, -0.50)
                valid = puts[puts['strike'] < b['strike']]
                s = eng.find_closest_strike(valid, -0.30) if not valid.empty else b
                b['side'], s['side'], b['type'], s['type'] = "BUY", "SELL", "put", "put"
                trade = {"Legs": [b, s], "Type": "Put Debit Spread"}
            elif "Neutral" in view:
                c = eng.find_closest_strike(calls, 0.20)
                p = eng.find_closest_strike(puts, -0.20)
                c['side'], p['side'], c['type'], p['type'] = "SELL", "SELL", "call", "put"
                trade = {"Legs": [c, p], "Type": "Short Strangle"}

            st.session_state['data'] = {
                "ticker": ticker, "price": curr_price, "rank": iv_rank, "vol": curr_vol, "r": r,
                "calls": calls, "puts": puts, "trade": trade, "dte": (datetime.strptime(expiry, '%Y-%m-%d')-datetime.now()).days
            }

    if 'data' in st.session_state:
        d = st.session_state['data']
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Spot", f"${d['price']:.2f}", help="Current market price of the underlying asset.")
        m2.metric(
            "IV Rank", f"{d['rank']:.0f}%", 
            help="Relative valuation. 0% = Cheapest in 52wks, 100% = Most Expensive. >50% suggests Selling Premium."
        )
        m3.metric(
            "IV", f"{d['vol']:.1f}%", 
            help="Implied Volatility. Annualized expected move (1 Std Dev). 20% IV = Market expects +/- 20% move over 1yr."
        )
        m4.metric(
            "Risk Free", f"{d['r']*100:.2f}%", 
            help="13-Week Treasury Yield. The 'Hurdle Rate'. Higher rates make Calls expensive and Puts cheap (Rho)."
        )

        st.divider()
        c_l, c_r = st.columns([1, 2])
        
        with c_l:
            t = d['trade']
            cost = 0
            rows = ""
            for l in t['Legs']:
                p = l.get('lastPrice', l.get('theo_price', 0))
                cost += p if l['side']=="BUY" else -p
                css = "leg-buy" if l['side']=="BUY" else "leg-sell"
                rows += f'<div class="leg-row"><span class="mono"><b class="{css}">{l["side"]}</b> {l["strike"]} {l["type"].upper()}</span><span class="mono" style="color:#888;">Δ {l["delta"]:.2f} | ${p:.2f}</span></div>'
            
            pop = 50.0
            if "Debit" in t['Type']:
                l1 = t['Legs'][0]
                move = d['price'] * (d['vol']/100) * np.sqrt(d['dte']/365.0)
                if move > 0:
                    be = l1['strike'] + cost if "Call" in t['Type'] else l1['strike'] - cost
                    z = abs(d['price'] - be) / move
                    pop = norm.sf(z) * 100

            st.markdown(f"""
            <div class="trade-ticket">
                <div class="ticket-header"><span>{t['Type']}</span></div>{rows}
                <div class="ticket-footer"><div class="cost-display"><div class="cost-val">{'Debit' if cost>0 else 'Credit'}: ${abs(cost)*100:.0f}</div></div></div>
                <div style="margin-top:15px;padding:8px;background:rgba(255,255,255,0.05);border-radius:4px;display:flex;justify-content:space-between;">
                    <span style="color:#888;">Probability of Profit (PoP)</span><span style="color:#00FF88;font-weight:bold;">{pop:.1f}%</span>
                </div>
            </div>""", unsafe_allow_html=True)

        with c_r:
            l1, l2 = st.columns(2)
            day = l1.slider("Days Fwd", 0, max(1, d['dte']), 0)
            shock = l2.slider("Vol Shock", -50, 50, 0)
            
            eng = VectorizedQuantEngine()
            eng.r = d['r']
            x = np.linspace(d['price']*0.8, d['price']*1.2, 100)
            y = np.zeros_like(x) - (cost*100)
            T_sim = max(0.001, (d['dte']-day)/365.0)
            
            for l in t['Legs']:
                sig = max(0.01, l['impliedVolatility']*(1+shock/100))
                lp = eng.black_scholes_single(x, l['strike'], T_sim, sig, l['type'])
                y += (lp*100) if l['side']=="BUY" else -(lp*100)
                
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=x[y>=0], y=y[y>=0], fill='tozeroy', fillcolor='rgba(0,255,136,0.2)', line=dict(color='#00FF88', width=0)))
            fig.add_trace(go.Scatter(x=x[y<0], y=y[y<0], fill='tozeroy', fillcolor='rgba(255,75,75,0.2)', line=dict(color='#FF4B4B', width=0)))
            fig.add_trace(go.Scatter(x=x, y=y, line=dict(color='white', width=2)))
            fig.add_vline(x=d['price'], line_dash="dash", line_color="#F4D03F")
            fig.update_layout(template="plotly_dark", height=350, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("📊 Chart Guide", expanded=False):
                st.markdown("""
                * **White Curve:** Value at selected date (Gamma).
                * **Green/Red:** Profit vs Loss zones.
                * **Simulators:** Use sliders to test Time Decay (Theta) and Panic (Vega).
                """)

# --- ROUTER ---
with st.sidebar:
    st.title("OpStruct")
    if st.button("🏠 Home"): set_page('home')
    if st.button("🎓 Academy"): set_page('academy')
    if st.button("📐 Terminal"): set_page('terminal')

if st.session_state.page == 'home': page_home()
elif st.session_state.page == 'academy': page_academy()
elif st.session_state.page == 'terminal': page_terminal()
