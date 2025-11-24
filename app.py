import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from scipy.stats import norm
from datetime import datetime, timedelta
import plotly.graph_objects as go
import requests

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
    
    /* ACADEMY LEVEL SELECTOR */
    div.row-widget.stRadio > div {flex-direction: row;}
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE NAVIGATION ---
if 'page' not in st.session_state: st.session_state.page = 'home'

def set_page(page_name):
    st.session_state.page = page_name

# --- CONTENT DATABASE (THE CURRICULUM) ---
ACADEMY_CONTENT = {
    "101": {
        "title": "101: The Contract",
        "levels": {
            "Rookie": {
                "Call": "**The Coupon.** Imagine a coupon that lets you buy a TV for $500. If the TV price goes to $700, that coupon is worth $200. If the price drops to $400, the coupon is worthless, but you don't *have* to use it.",
                "Put": "**Car Insurance.** You pay a premium to protect your car. If you crash (stock crashes), the insurance pays out. If you don't crash, the insurance company keeps your premium.",
                "Key": "Options are rights, not obligations."
            },
            "Trader": {
                "Call": "**Leveraged Bullish Bet.** A standard contract controlling 100 shares. Buying a Call gives you positive Delta. You need the stock to move UP fast enough to beat Theta (time decay).",
                "Put": "**Leveraged Bearish Bet.** Controls 100 shares short. Buying a Put gives you negative Delta. Used for speculation (betting on a crash) or hedging (protecting a portfolio).",
                "Key": "1 Option Contract = 100 Shares. Use this leverage carefully."
            },
            "Quant": {
                "Call": "A derivative instrument offering convex exposure. The payoff function is `max(S - K, 0)`. As spot price `S` increases, Delta approaches 1.0.",
                "Put": "A hedge against tail risk. The payoff function is `max(K - S, 0)`. Puts typically trade at a higher implied volatility than Calls due to 'Skew' (fear is stronger than greed).",
                "Key": "Payoff structures are non-linear."
            }
        }
    },
    "201": {
        "title": "201: The Casino Rule",
        "levels": {
            "Rookie": {
                "Buy": "**Buying Lottery Tickets.** Low chance of winning, but if you win, you win big. Most tickets end up in the trash.",
                "Sell": "**Being the Casino.** You sell the tickets. You win small amounts very often (keeping the ticket price), but occasionally you have to pay out a jackpot.",
                "Key": "Casinos make more money than gamblers."
            },
            "Trader": {
                "Buy": "**Long Volatility.** Defined Risk / Unlimited Reward. Low Probability of Profit (POP). You need a big move to profit.",
                "Sell": "**Short Volatility.** Unlimited Risk / Defined Reward. High Probability of Profit (POP). You profit if the stock stays flat, goes your way, or moves slightly against you.",
                "Key": "Professional traders often SELL options to harvest premium."
            },
            "Quant": {
                "Buy": "Purchasing Gamma. You are betting that realized volatility will exceed implied volatility. You suffer from negative Theta (time decay).",
                "Sell": "Selling Variance Risk Premium (VRP). Historically, Implied Volatility is overstated compared to Realized Volatility. Selling captures this spread.",
                "Key": "VRP is a structural edge in the market."
            }
        }
    },
    "301": {
        "title": "301: The Greeks",
        "levels": {
            "Rookie": {
                "Delta": "**Speed.** How much your option price changes for every $1 the stock moves.",
                "Theta": "**Time Tax.** How much value your option loses every single day just by existing (ice cube melting).",
                "Vega": "**Panic.** How much the price rises when people get scared (volatility goes up).",
                "Key": "Greeks tell you 'Why' you made or lost money."
            },
            "Trader": {
                "Delta": "**Directional Exposure.** Also serves as a rough proxy for Probability ITM (e.g., 30 Delta = ~30% chance of expiring ITM).",
                "Theta": "**Daily Bill.** If you are Long Options, you pay Theta. If you are Short Options, you collect Theta.",
                "Vega": "**Volatility Exposure.** In high IV rank, options are expensive (Short Vega strategies preferred). In low IV rank, options are cheap (Long Vega strategies preferred).",
                "Key": "Manage your Greeks to manage your risk."
            },
            "Quant": {
                "Delta": "First derivative of Price w.r.t Underlying ($dS$). $\\frac{\\partial V}{\\partial S}$",
                "Theta": "First derivative of Price w.r.t Time ($dt$). $\\frac{\\partial V}{\\partial t}$",
                "Vega": "First derivative of Price w.r.t Volatility ($d\\sigma$). $\\frac{\\partial V}{\\partial \\sigma}$",
                "Key": "Sensitivity analysis using partial derivatives of the Black-Scholes equation."
            }
        }
    },
    "401": {
        "title": "401: Spreads",
        "levels": {
            "Rookie": {
                "Concept": "**The Combo Meal.** Instead of just buying a burger (Call), you buy a burger and sell a drink. It lowers the cost, but caps how much food you get.",
                "Benefit": "It stops you from losing your shirt. You know exactly how much you can make or lose before you start.",
                "Key": "Spreads make trading safer and cheaper."
            },
            "Trader": {
                "Concept": "**Vertical Spreads.** Buying one strike and selling another in the same expiration. Reduces cost basis and neutralizes volatility risk.",
                "Benefit": "Defined Risk. A 'Debit Spread' is a cheaper directional bet. A 'Credit Spread' allows you to be the casino with a safety net.",
                "Key": "Most sustainable retail strategies rely on spreads, not naked calls/puts."
            },
            "Quant": {
                "Concept": "**Isolating Factors.** Spreads allow you to isolate specific Greeks. A 'Calendar Spread' isolates Theta/Vega while neutralizing Delta. A 'Vertical' isolates Delta while neutralizing Vega.",
                "Benefit": "Capital Efficiency. Spreads drastically reduce margin requirements compared to naked positions.",
                "Key": "Structuring allows for precision engineering of the P&L curve."
            }
        }
    }
}

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
            <div style="margin-top: 10px; color: #aaa;">
                From "Zero" to "Hedge Fund" in 4 modules.<br>
                Choose your difficulty: Rookie, Trader, or Quant.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Enter University ->", key="home_academy"): set_page('academy')
        
    with c2:
        st.markdown("""
        <div class="concept-card">
            <div class="concept-emoji">📐</div>
            <div class="concept-title">The Terminal</div>
            <div style="margin-top: 10px; color: #aaa;">
                Institutional-grade structuring engine.<br>
                Visualize Greeks, Time Decay, and P&L.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Launch Terminal ->", key="home_terminal"): set_page('terminal')

# ==================================================
#                 PAGE 2: THE ACADEMY
# ==================================================
def page_academy():
    st.title("🎓 OpStruct University")
    
    # LEVEL SELECTOR
    st.markdown("### 🎚️ Select Your Clearance Level")
    level = st.radio("Difficulty:", ["Rookie", "Trader", "Quant"], horizontal=True, label_visibility="collapsed")
    
    # DYNAMIC HEADER BASED ON LEVEL
    if level == "Rookie":
        st.caption("🟢 **Mode: Rookie.** Explaining concepts using analogies (Insurance, Coupons, Casinos).")
    elif level == "Trader":
        st.caption("🟡 **Mode: Trader.** Focusing on mechanics, risk management, and market terminology.")
    else:
        st.caption("🔴 **Mode: Quant.** Focusing on math, derivatives, and structural edges.")
    
    st.divider()

    # TABS FOR MODULES
    t1, t2, t3, t4 = st.tabs(["101: The Contract", "201: Casino Rule", "301: The Greeks", "401: Spreads"])
    
    # --- TAB 1: CONTRACTS ---
    with t1:
        content = ACADEMY_CONTENT["101"]["levels"][level]
        st.header(ACADEMY_CONTENT["101"]["title"])
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.info(f"📞 **CALL**\n\n{content['Call']}")
        with col_b:
            st.warning(f"📉 **PUT**\n\n{content['Put']}")
        
        st.success(f"💡 **Takeaway:** {content['Key']}")

    # --- TAB 2: BUY VS SELL ---
    with t2:
        content = ACADEMY_CONTENT["201"]["levels"][level]
        st.header(ACADEMY_CONTENT["201"]["title"])
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.error(f"💸 **Buying Options (Debit)**\n\n{content['Buy']}")
        with col_b:
            st.success(f"🏦 **Selling Options (Credit)**\n\n{content['Sell']}")
            
        st.info(f"💡 **Takeaway:** {content['Key']}")

    # --- TAB 3: GREEKS ---
    with t3:
        content = ACADEMY_CONTENT["301"]["levels"][level]
        st.header(ACADEMY_CONTENT["301"]["title"])
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Δ Delta", "Direction", help=content['Delta'])
        c1.markdown(f"<small>{content['Delta']}</small>", unsafe_allow_html=True)
        
        c2.metric("Θ Theta", "Time", help=content['Theta'])
        c2.markdown(f"<small>{content['Theta']}</small>", unsafe_allow_html=True)
        
        c3.metric("ν Vega", "Volatility", help=content['Vega'])
        c3.markdown(f"<small>{content['Vega']}</small>", unsafe_allow_html=True)
        
        st.divider()
        st.success(f"💡 **Takeaway:** {content['Key']}")

    # --- TAB 4: SPREADS ---
    with t4:
        content = ACADEMY_CONTENT["401"]["levels"][level]
        st.header(ACADEMY_CONTENT["401"]["title"])
        
        st.markdown(f"### {content['Concept']}")
        st.write(content['Benefit'])
        st.success(f"💡 **Takeaway:** {content['Key']}")

# ==================================================
#                 PAGE 3: THE TERMINAL (PRO)
# ==================================================
def page_terminal():
    class QuantEngine:
        def __init__(self, risk_free_rate=0.045):
            self.r = risk_free_rate
        def black_scholes_call(self, S, K, T, sigma):
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

    def get_iv_rank(stock_obj):
        try:
            hist = stock_obj.history(period="1y")
            hist['Log_Ret'] = np.log(hist['Close'] / hist['Close'].shift(1))
            hist['Volatility'] = hist['Log_Ret'].rolling(window=30).std() * np.sqrt(252) * 100
            vol_data = hist['Volatility'].dropna()
            current_vol = vol_data.iloc[-1]
            return current_vol, (current_vol - vol_data.min()) / (vol_data.max() - vol_data.min()) * 100
        except: return 0, 0

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
    
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d")
        if hist.empty: return
        exps = stock.options
        if not exps: return

        with c2: expiry = st.selectbox("Expiration", exps[:12])
        with c3: view = st.selectbox("Strategy", ["Bullish (Call Spread)", "Bearish (Put Spread)", "Neutral (Income Strangle)"])

        with st.spinner(f"Running Analysis for {ticker}..."):
            current_price = hist['Close'].iloc[-1]
            curr_vol, iv_rank = get_iv_rank(stock)
            
            # DASHBOARD METRICS
            st.markdown("### 📊 Volatility Regime")
            m1, m2, m3 = st.columns(3)
            m1.metric("Spot Price", f"${current_price:.2f}")
            m2.metric("IV Rank", f"{iv_rank:.0f}%")
            
            regime_msg = "Neutral"
            if iv_rank > 50: regime_msg = "HIGH (Expensive Options)"
            elif iv_rank < 20: regime_msg = "LOW (Cheap Options)"
            m3.metric("Regime", regime_msg)
            
            st.divider()

            # GREEKS
            _, calls, puts = get_chain(ticker, expiry)
            calls = calculate_greeks(calls, current_price, expiry, "call")
            puts = calculate_greeks(puts, current_price, expiry, "put")
            dte = (datetime.strptime(expiry, '%Y-%m-%d') - datetime.now()).days

            # STRATEGY LOGIC
            trade = {}
            if "Bullish" in view:
                buy_leg = quant.find_closest_strike(calls, 0.50)
                sell_leg = quant.find_closest_strike(calls, 0.30)
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
            
            # RENDERER
            if trade:
                st.subheader(f"🤖 Generated: {trade['Type']}")
                total_price = 0
                legs_html = ""
                
                for leg in trade['Legs']:
                    price = leg['lastPrice']
                    side = leg['side']
                    if side == "BUY": total_price += price
                    else: total_price -= price
                    color = "🟢" if side == "BUY" else "🔴"
                    legs_html += f"<p>{color} <b>{side}</b> ${leg['strike']} (Delta: {leg['calc_delta']:.2f}) - ${price:.2f}</p>"

                cost_label = f"Est. Debit: ${total_price*100:.2f}" if total_price > 0 else f"Est. Credit: ${abs(total_price)*100:.2f}"

                st.markdown(f"""
                <div style="background: #111; padding: 20px; border-left: 5px solid #00FF00; border-radius: 10px;">
                    {legs_html}
                    <hr style="border-color: #444;">
                    <h3>{cost_label}</h3>
                </div>
                """, unsafe_allow_html=True)
                
                # --- SIMULATION & CHART ---
                st.divider()
                st.subheader("🧪 Probability Lab")
                
                sim_col1, sim_col2 = st.columns(2)
                with sim_col1: 
                    slider_max = dte if dte > 0 else 1
                    days_forward = st.slider("⏳ Time Travel (Days Passed)", 0, slider_max, 0)
                with sim_col2: 
                    vol_adjust = st.slider("⚡ Volatility Adjustment (%)", -80, 300, 0)

                spot_range = np.linspace(current_price * 0.7, current_price * 1.3, 200)
                
                # Expiration P&L
                pnl_expiration = np.zeros_like(spot_range) - (total_price * 100)
                for leg in trade['Legs']:
                    payoff = np.maximum(0, spot_range - leg['strike']) if leg['type'] == "call" else np.maximum(0, leg['strike'] - spot_range)
                    pnl_expiration += (payoff * 100) if leg['side'] == "BUY" else -(payoff * 100)

                # Simulated P&L
                pnl_simulated = np.zeros_like(spot_range) - (total_price * 100)
                sim_T = max(0.001, (dte - days_forward) / 365.0)
                for leg in trade['Legs']:
                    sim_sigma = max(0.01, leg['impliedVolatility'] * (1 + vol_adjust/100))
                    new_price = quant.black_scholes_call(spot_range, leg['strike'], sim_T, sim_sigma) if leg['type'] == "call" else quant.black_scholes_put(spot_range, leg['strike'], sim_T, sim_sigma)
                    pnl_simulated += (new_price * 100) if leg['side'] == "BUY" else -(new_price * 100)

                fig = go.Figure()
                fig.add_trace(go.Scatter(x=spot_range, y=pnl_expiration, mode='lines', name='At Expiration (Hard Truth)', line=dict(color='white', dash='dot')))
                fig.add_trace(go.Scatter(x=spot_range, y=pnl_simulated, mode='lines', name=f'Simulated (T+{days_forward})', fill='tozeroy', line=dict(color='#00FF00' if pnl_simulated.max() > 0 else '#FF4B4B')))
                fig.add_hline(y=0, line_color="gray", line_width=1)
                fig.add_vline(x=current_price, line_color="yellow", annotation_text="Spot")
                fig.update_layout(template="plotly_dark", height=500, title="Projected Outcome", yaxis_title="P/L ($)")
                st.plotly_chart(fig, use_container_width=True)
                
                with st.expander("🔍 How to read this chart (The 'Aha!' Moment)"):
                    st.markdown("""
                    This chart shows you the **Future**:
                    
                    1.  **The X-Axis (Bottom):** The price of the stock in the future.
                    2.  **The Y-Axis (Left):** How much money you make (Green) or lose (Red).
                    3.  **The Two Lines:**
                        * ⚪ **White Dotted Line (Expiration):** This is the "Hard Truth." This is exactly what you get paid on the final day. No math, just logic.
                        * 🌈 **Solid Colored Line (Today/Simulated):** This is the value of your trade **right now**.
                    
                    **Try this:**
                    * Slide **Time Travel** forward. Watch the *Colored Line* melt into the *White Line*. That is **Theta Decay** happening before your eyes.
                    * Slide **Volatility** up. Watch the *Colored Line* float higher. That is **Vega** (Panic) inflating the prices.
                    """)

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
