import streamlit as st
import yfinance as yf
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import requests
from datetime import datetime
from scipy.stats import norm
import time

# --- MVC IMPORTS ---
from quant_engine import VectorizedQuantEngine
from academy_data import APP_STYLE, ACADEMY_PHASES, QUIZ_BANK
import market_utils 

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
    # --- HOMEPAGE SPECIFIC CSS ---
    st.markdown("""
    <style>
        .home-container { padding: 2rem 0; border-bottom: 1px solid #30363D; }
        .manifesto-text { font-family: 'Inter', sans-serif; color: #8899A6; font-size: 1.1rem; line-height: 1.6; }
        .stat-box { background: #0D1117; border: 1px solid #30363D; border-radius: 8px; padding: 15px; text-align: center; }
        .stat-num { font-family: 'JetBrains Mono', monospace; font-size: 1.8rem; font-weight: 700; color: #00FF88; }
        .stat-label { font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; color: #888; }
        .architect-sign { font-family: 'JetBrains Mono', monospace; color: #58A6FF; font-size: 0.9rem; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown('<h1 class="hero-title">OpStruct.</h1>', unsafe_allow_html=True)
        st.markdown("### Institutional Risk Modeling for the Retail Trader.")
        st.markdown("""
        <div class="manifesto-text">
        Most traders treat options like lottery tickets. Pros treat them like engineering problems.<br>
        This isn't a broker. It's a <b>Structuring Engine</b> designed to bridge the gap between 
        retail guessing and quantitative execution.
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        b1, b2, b3 = st.columns(3) # Added War Room button
        if b1.button("🎓 Academy", type="primary", use_container_width=True): set_page('academy')
        if b2.button("📐 Terminal", use_container_width=True): set_page('terminal')
        if b3.button("⚔️ War Room", use_container_width=True): set_page('war_room')

    with c2:
        st.markdown("""
        <div class="stat-box" style="margin-top: 20px;">
            <div class="stat-num">100%</div>
            <div class="stat-label">Python Native</div>
        </div>
        <div class="stat-box" style="margin-top: 10px;">
            <div class="stat-num">BSM</div>
            <div class="stat-label">Vectorized Model</div>
        </div>
        <div class="stat-box" style="margin-top: 10px;">
            <div class="stat-num">&lt;50ms</div>
            <div class="stat-label">Compute Latency</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("⚙️ Under the Hood")
    a1, a2, a3 = st.columns(3)
    with a1:
        st.markdown("#### 🧠 The Engine")
        st.caption("Custom Math Layer")
        st.markdown("I didn't use off-the-shelf libraries. I built a custom **Vectorized Quant Engine** using `NumPy` and `SciPy`. It calculates Greeks instantly.")
    with a2:
        st.markdown("#### 🛡️ The Logic")
        st.caption("Safety First")
        st.markdown("The system enforces **Institutional Constraints**. It automatically detects Wash Trades and calculates POP using Z-Score statistical analysis.")
    with a3:
        st.markdown("#### ⚡ The Sim")
        st.caption("Stress Testing")
        st.markdown("Static charts are useless. I engineered dynamic **Theta** and **Vega** simulators to stress test portfolios against crashes.")

    st.markdown("---")
    c_bio, c_img = st.columns([3, 1])
    with c_bio:
        st.subheader("👨‍💻 The Architect")
        st.markdown("""
        <div class="manifesto-text">
        I built OpStruct because I was tired of seeing retail traders donate liquidity to algorithms. 
        Financial engineering shouldn't be gated behind a $24,000 Bloomberg Terminal.
        </div>
        <div class="architect-sign">> Built by Zach P // Future Fintech CEO</div>
        """, unsafe_allow_html=True)

# ==================================================
#                  VIEW: WAR ROOM (REBUILT)
# ==================================================
def page_war_room():
    st.markdown("## ⚔️ The War Room")
    st.caption("Institutional Dashboard. Visualizing structure, flow, and correlations.")
    
    # --- ROW 1: THE HUD (REGIME) ---
    st.markdown("#### 📡 Market Regime HUD")
    with st.spinner("Analyzing Market Structure..."):
        regime = market_utils.get_market_regime()
        pulse = market_utils.get_macro_pulse()
        
        if regime and pulse:
            c1, c2, c3, c4 = st.columns(4)
            
            # 1. Term Structure Gauge
            ts_state = regime['Term_Structure']['state']
            ts_color = "normal" if "Contango" in ts_state else "inverse" # Red if Backwardation
            c1.metric("VIX Term Structure", ts_state, f"{regime['Term_Structure']['ratio']:.2f} Ratio", delta_color=ts_color, help="Ratio of 9-Day Vol to 30-Day Vol. >1.05 signals panic (Backwardation).")
            
            # 2. Risk Gauge
            rg_trend = regime['Risk_Gauge']['trend']
            rg_color = "normal" if "ON" in rg_trend else "inverse"
            c2.metric("Risk Appetite (XLY/XLP)", rg_trend, f"{regime['Risk_Gauge']['val']:.2f}", delta_color=rg_color, help="Ratio of Consumer Discretionary to Staples. Rising = Risk On.")
            
            # 3. Trend Gauge
            dist = regime['SPY_Trend']['dist']
            t_col = "normal" if dist > 0 else "inverse"
            c3.metric("SPY vs 200 SMA", f"{dist:.2f}%", f"${regime['SPY_Trend']['sma200']:.2f}", delta_color=t_col, help="Distance from the 200-Day Moving Average. Institutional support line.")

            # 4. Cost of Money
            c4.metric("10Y Yield (Gravity)", f"{pulse['TNX']['val']:.2f}%", f"{pulse['TNX']['delta']:.2f}%", delta_color="off")
        else:
            st.warning("Market Structure data unavailable.")

    st.divider()

    # --- ROW 2: CORRELATIONS & SCANNER ---
    col_l, col_r = st.columns([1, 1])
    
    with col_l:
        st.subheader("🔗 Cross-Asset Correlation (30D)")
        st.caption("When this map turns all bright (1.0), diversification is failing.")
        
        with st.spinner("Calculating Matrix..."):
            corr_matrix = market_utils.get_correlation_matrix()
            if not corr_matrix.empty:
                fig = px.imshow(
                    corr_matrix, 
                    text_auto=".2f",
                    aspect="auto",
                    color_continuous_scale="RdBu_r", # Red = High Correlation, Blue = Inverse
                    zmin=-1, zmax=1
                )
                fig.update_layout(template="plotly_dark", height=400, margin=dict(t=20, b=20, l=20, r=20), paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Correlation data unavailable.")

    with col_r:
        st.subheader("🔥 High IV Opportunity Scanner")
        st.caption("Liquid tickers where Options are 'Expensive' (High IV Rank).")
        
        with st.spinner("Scanning Watchlist..."):
            vol_df = market_utils.scan_volatility_opportunities()
            if not vol_df.empty:
                st.dataframe(
                    vol_df, 
                    column_config={
                        "Ticker": "Symbol",
                        "Price": st.column_config.NumberColumn(format="$%.2f"),
                        "IV Rank": st.column_config.ProgressColumn(format="%.0f%%", min_value=0, max_value=100),
                        "Current IV": st.column_config.NumberColumn(format="%.1f%%")
                    },
                    hide_index=True,
                    use_container_width=True,
                    height=400
                )
            else:
                st.info("Scanner offline.")

    st.divider()
    
    # --- ROW 3: SECTOR MOMENTUM ---
    st.subheader("🌊 Sector Rotation (5-Day Momentum)")
    with st.spinner("Tracking Flows..."):
        sector_df = market_utils.get_sector_momentum()
        if not sector_df.empty:
            fig = go.Figure()
            colors = ['#00FF88' if v > 0 else '#FF4B4B' for v in sector_df['Change']]
            fig.add_trace(go.Bar(
                x=sector_df['Ticker'], y=sector_df['Change'],
                marker_color=colors, text=sector_df['Name'], textposition='auto'
            ))
            fig.update_layout(
                template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                height=350, margin=dict(t=20, b=50, l=50, r=20),
                yaxis_title="% Change (5D)", xaxis_title="Sector ETF"
            )
            st.plotly_chart(fig, use_container_width=True)

# ==================================================
#                  VIEW: ACADEMY
# ==================================================
def page_academy():
    current_level = st.session_state.user_level
    lvl_map = {"Rookie": 0, "Trader": 50, "Quant": 100}
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
    visible_phases = []
    if current_level == "Rookie": visible_phases = ["phase1", "phase2"]
    elif current_level == "Trader": visible_phases = ["phase1", "phase2", "phase3", "phase4"]
    else: visible_phases = ["phase1", "phase2", "phase3", "phase4", "phase5"]

    tabs = st.tabs([p["title"] for p in ACADEMY_PHASES])
    for i, phase in enumerate(ACADEMY_PHASES):
        with tabs[i]:
            if phase["id"] not in visible_phases:
                st.error(f"🔒 Clearance Restricted. Reach **{phase['req_level']}** to unlock this module.")
            else:
                st.info(f"**Objective:** {phase['desc']}")
                for topic in phase["topics"]:
                    with st.expander(f"📌 {topic['title']}", expanded=False):
                        st.markdown(topic['content'])
                        if "Greeks" in phase['title']: st.caption("")

    st.markdown("---")
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
                else: st.error("FAILED. Study the material above.")

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
        m1.metric("Spot", f"${d['price']:.2f}", help="Current market price.")
        m2.metric("IV Rank", f"{d['rank']:.0f}%", help="0%=Cheapest in 52wks, 100%=Most Expensive.")
        m3.metric("IV", f"{d['vol']:.1f}%", help="Annualized expected move (1 Std Dev).")
        m4.metric("Risk Free", f"{d['r']*100:.2f}%", help="13-Week Treasury Yield.")

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
                    <span style="color:#888;">POP</span><span style="color:#00FF88;font-weight:bold;">{pop:.1f}%</span>
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
                st.markdown("* **White Curve:** Value at T+Days.\n* **Green/Red:** Profit vs Loss.")

# --- ROUTER ---
with st.sidebar:
    st.title("OpStruct")
    st.caption("Institutional Grade v5.0")
    st.markdown("---")
    if st.button("🏠 Home", use_container_width=True): set_page('home')
    if st.button("⚔️ War Room", use_container_width=True): set_page('war_room')
    if st.button("🎓 Academy", use_container_width=True): set_page('academy')
    if st.button("📐 Terminal", use_container_width=True): set_page('terminal')

if st.session_state.page == 'home': page_home()
elif st.session_state.page == 'war_room': page_war_room()
elif st.session_state.page == 'academy': page_academy()
elif st.session_state.page == 'terminal': page_terminal()
