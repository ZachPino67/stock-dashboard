import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from scipy.stats import norm
from datetime import datetime, timedelta
import plotly.graph_objects as go
import requests

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="OpStruct Academy",
    page_icon="♟️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ADVANCED CSS STYLING ---
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
    
    /* TERMINAL FONT FOR NUMBERS */
    .mono {
        font-family: 'JetBrains Mono', monospace;
    }
    
    /* CUSTOM CARDS (Glassmorphism) */
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
        color: #00FF88; /* Cyber Green */
        font-weight: 700;
        font-size: 1.3rem;
        margin-bottom: 8px;
    }
    
    /* TRADE TICKET STYLES */
    .trade-ticket {
        background: #111; 
        border: 1px solid #333; 
        border-radius: 8px; 
        padding: 20px;
        font-family: 'JetBrains Mono', monospace;
    }
    .leg-row {
        display: flex; 
        justify-content: space-between; 
        padding: 8px 0; 
        border-bottom: 1px solid #222;
    }
    .leg-buy { color: #00FF88; }
    .leg-sell { color: #FF4B4B; }
    
    /* RADIO BUTTON AS TOGGLES */
    div[role="radiogroup"] {
        background-color: #161B22;
        padding: 4px;
        border-radius: 8px;
        display: inline-flex;
    }
    
    div[role="radiogroup"] label {
        border-radius: 6px;
        padding: 0px 16px;
        margin-right: 0px !important;
        border: 1px solid transparent;
        transition: all 0.3s;
    }

    div[role="radiogroup"] label[data-baseweb="radio"] > div:first-child {
        display: none; /* Hide default radio circle */
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
    
    /* DIVIDERS */
    hr {
        border-color: #30363D;
    }
</style>
""", unsafe_allow_html=True)

# --- NAVIGATION STATE ---
if 'page' not in st.session_state: st.session_state.page = 'home'

def set_page(page_name):
    st.session_state.page = page_name

# --- EDUCATIONAL CONTENT REPOSITORY ---
ACADEMY_CONTENT = {
    "101": {
        "title": "Module 101: The Option Contract",
        "levels": {
            "Rookie": {
                "Call": "**The Discount Coupon.** Imagine a coupon that guarantees you can buy a TV for $500. If the store price rises to $700, your coupon is instantly worth $200. If the price drops to $400, the coupon is worthless, but you have no obligation to use it.",
                "Put": "**Car Insurance.** You pay a premium to insure your car. If you crash (the stock drops), the insurance company pays you the difference. If you don't crash, you simply lose the small premium you paid.",
                "Key": "Options give you rights without obligations."
            },
            "Trader": {
                "Call": "**Bullish Leverage.** A contract giving you the right to buy 100 shares at a specific strike price. It offers uncapped upside with capped downside (cost of the premium). You need price velocity (Delta) to overcome time decay (Theta).",
                "Put": "**Bearish Protection.** A contract giving you the right to sell 100 shares. Traders use Puts to speculate on downside moves or to hedge existing stock portfolios (reducing portfolio Beta).",
                "Key": "One contract controls 100 shares. Leverage cuts both ways."
            },
            "Quant": {
                "Call": "An asymmetric payoff instrument with positive convexity. The value is derived from `max(S - K, 0)`. As spot price `S` increases relative to strike `K`, the option's Delta approaches 1.0, mimicking the underlying asset.",
                "Put": "A hedging instrument with a payoff of `max(K - S, 0)`. In equity markets, Puts generally trade at a higher Implied Volatility (IV) than Calls due to 'Volatility Skew'—market participants price downside fear more aggressively than upside greed.",
                "Key": "Payoff functions are non-linear; Greeks measure the rate of change."
            }
        }
    },
    "201": {
        "title": "Module 201: The Casino Rule (Buying vs. Selling)",
        "levels": {
            "Rookie": {
                "Buy": "**Buying Lottery Tickets.** You pay a small amount for a chance to win big. Most tickets expire worthless. This is a low-probability, high-reward strategy.",
                "Sell": "**Owning the Casino.** You sell the tickets to others. You collect small payments frequently. Occasionally, someone hits a jackpot and you must pay them, but mathematically, the house always wins in the long run.",
                "Key": "Casinos (Sellers) generally make more consistent money than Gamblers (Buyers)."
            },
            "Trader": {
                "Buy": "**Long Volatility (Debit).** Defined Risk / Unlimited Reward. However, you face a low Probability of Profit (POP). You need the stock to move significantly to overcome the premium paid.",
                "Sell": "**Short Volatility (Credit).** Unlimited Risk / Defined Reward. High Probability of Profit (POP). You profit if the stock goes your way, stays flat, or even moves slightly against you.",
                "Key": "Professional income strategies often involve selling premium (Theta Decay)."
            },
            "Quant": {
                "Buy": "Purchasing Gamma. You are betting that Realized Volatility (RV) will exceed Implied Volatility (IV). You suffer from negative Theta, meaning time works against you.",
                "Sell": "Harvesting the Variance Risk Premium (VRP). Historically, Implied Volatility tends to overstate actual moves. Selling options captures this spread. You are short Gamma but long Theta.",
                "Key": "VRP is a structural edge in financial markets."
            }
        }
    },
    "301": {
        "title": "Module 301: The Greeks (Risk Metrics)",
        "levels": {
            "Rookie": {
                "Delta": "**Speed.** How much your option's price changes for every $1 the stock moves. (e.g., Delta 0.50 means you make 50 cents if the stock goes up $1).",
                "Theta": "**Time Decay.** The daily fee you pay for holding the option. Like an ice cube melting, your option loses value every day it doesn't move.",
                "Vega": "**Panic Meter.** How much the option price inflates when the market gets scared. When news hits, prices go up even if the stock doesn't move.",
                "Key": "The Greeks explain *why* you are making or losing money."
            },
            "Trader": {
                "Delta": "**Directional Exposure & Probability.** Delta creates your directional bias. It also serves as a proxy for the probability of expiring In-The-Money (ITM). A 30 Delta option has roughly a 30% chance of expiring ITM.",
                "Theta": "**Daily Carry.** If you are Long Options, Theta is your enemy (bleeding value). If you are Short Options, Theta is your income (collecting rent).",
                "Vega": "**Volatility Sensitivity.** In high IV environments, options are expensive—prefer selling Vega. In low IV environments, options are cheap—prefer buying Vega.",
                "Key": "Risk management is simply Greek management."
            },
            "Quant": {
                "Delta": "First partial derivative with respect to Underlying Price: $\\frac{\\partial V}{\\partial S}$. Represents the hedge ratio.",
                "Theta": "First partial derivative with respect to Time: $\\frac{\\partial V}{\\partial t}$. Represents the non-linear decay of extrinsic value.",
                "Vega": "First partial derivative with respect to Volatility: $\\frac{\\partial V}{\\partial \\sigma}$. Measures sensitivity to changes in the market's implied standard deviation.",
                "Key": "These are sensitivity coefficients derived from the Black-Scholes-Merton differential equation."
            }
        }
    },
    "401": {
        "title": "Module 401: Structuring Spreads",
        "levels": {
            "Rookie": {
                "Concept": "**The Combo Meal.** Instead of just buying a burger (Call), you buy a burger and sell a drink to offset the cost. It limits how much food you get, but it's much cheaper.",
                "Benefit": "It prevents catastrophic loss. You define exactly how much you can lose before you enter the trade, so you can sleep at night.",
                "Key": "Spreads make trading safer, cheaper, and more predictable."
            },
            "Trader": {
                "Concept": "**Vertical Spreads.** Simultaneously buying and selling options in the same expiration cycle. This reduces your cost basis (Debit Spreads) or generates income (Credit Spreads) while capping your maximum risk.",
                "Benefit": "Defined Risk & Probability Enhancement. A spread lowers the break-even point of a trade, increasing your statistical probability of success compared to a naked option.",
                "Key": "Most sustainable retail strategies utilize spreads to neutralize volatility risk."
            },
            "Quant": {
                "Concept": "**Factor Isolation.** Spreads allow a structurer to isolate specific Greeks. A 'Vertical Spread' isolates Delta while neutralizing Vega. A 'Calendar Spread' isolates Theta and Vega while neutralizing Delta.",
                "Benefit": "Capital Efficiency & Margin Relief. Spreads drastically reduce margin requirements (Buying Power Reduction) compared to naked positions, improving Return on Capital (ROC).",
                "Key": "Structuring allows for the precision engineering of the P&L curve topology."
            }
        }
    }
}

# --- HELPER: SMART TICKER SEARCH ---
@st.cache_data(ttl=86400)
def lookup_ticker(query):
    query = query.strip().upper()
    # 1. Direct Try
    try:
        t = yf.Ticker(query)
        if not t.history(period="1d").empty: return query
    except: pass
    # 2. Search API
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
    st.markdown(
        """
        <div style="text-align: center;">
            <h1 style="font-size: 4.5rem; background: -webkit-linear-gradient(45deg, #00FF88, #00A3FF); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0;">OpStruct.</h1>
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
            <p class="card-text">
                From "Zero" to "Hedge Fund" in 4 structured modules.
                Choose your difficulty level: <b>Rookie, Trader, or Quant.</b>
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Enter University →", key="btn_academy", use_container_width=True):
            set_page('academy')
        
    with col2:
        st.markdown("""
        <div class="concept-card">
            <div class="concept-emoji">📐</div>
            <div class="concept-title">The Terminal</div>
            <p class="card-text">
                Institutional-grade structuring engine powered by Black-Scholes.
                <b>Visualize P&L, Time Decay, and Greeks</b> in real-time.
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Launch Terminal →", key="btn_terminal", use_container_width=True):
            set_page('terminal')

# ==================================================
#                 PAGE 2: THE ACADEMY
# ==================================================
def page_academy():
    st.markdown("## 🎓 OpStruct University")
    
    # CONTROL BAR
    with st.container():
        c1, c2 = st.columns([1, 3])
        with c1:
            st.markdown("#### Select Clearance Level")
        with c2:
            level = st.radio(
                "Difficulty:", 
                ["Rookie", "Trader", "Quant"], 
                horizontal=True, 
                label_visibility="collapsed"
            )
    
    # CONTEXT ALERT
    if level == "Rookie":
        st.info("🟢 **Mode: Rookie.** Explaining concepts using simple analogies (Insurance, Coupons, Casinos).")
    elif level == "Trader":
        st.warning("🟡 **Mode: Trader.** Focusing on trade mechanics, risk management, and market terminology.")
    else:
        st.error("🔴 **Mode: Quant.** Focusing on mathematical derivatives, pricing models, and structural edges.")
    
    st.markdown("<br>", unsafe_allow_html=True)

    # CURRICULUM TABS
    tabs = st.tabs(["101: Contracts", "201: The Casino Rule", "301: The Greeks", "401: Spreads"])
    
    # --- MODULE 101 ---
    with tabs[0]:
        content = ACADEMY_CONTENT["101"]["levels"][level]
        st.subheader(ACADEMY_CONTENT["101"]["title"])
        
        c_left, c_right = st.columns(2, gap="medium")
        with c_left:
            st.markdown(f"""
            <div class="concept-card" style="border-left: 4px solid #00FF88;">
                <div class="concept-title">📞 CALL</div>
                <div class="card-text">{content['Call']}</div>
            </div>
            """, unsafe_allow_html=True)
        with c_right:
            st.markdown(f"""
            <div class="concept-card" style="border-left: 4px solid #FF4B4B;">
                <div class="concept-title">📉 PUT</div>
                <div class="card-text">{content['Put']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.success(f"💡 **Key Takeaway:** {content['Key']}")

    # --- MODULE 201 ---
    with tabs[1]:
        content = ACADEMY_CONTENT["201"]["levels"][level]
        st.subheader(ACADEMY_CONTENT["201"]["title"])
        
        c_left, c_right = st.columns(2, gap="medium")
        with c_left:
            st.markdown(f"""
            <div class="concept-card" style="border-left: 4px solid #FF4B4B;">
                <div class="concept-title">💸 Buying (Debit)</div>
                <div class="card-text">{content['Buy']}</div>
            </div>
            """, unsafe_allow_html=True)
        with c_right:
            st.markdown(f"""
            <div class="concept-card" style="border-left: 4px solid #00FF88;">
                <div class="concept-title">🏦 Selling (Credit)</div>
                <div class="card-text">{content['Sell']}</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.info(f"💡 **Key Takeaway:** {content['Key']}")

    # --- MODULE 301 ---
    with tabs[2]:
        content = ACADEMY_CONTENT["301"]["levels"][level]
        st.subheader(ACADEMY_CONTENT["301"]["title"])
        
        g1, g2, g3 = st.columns(3, gap="medium")
        with g1:
            st.metric("Δ Delta", "Direction")
            st.markdown(f"<div class='card-text' style='font-size:0.9rem; margin-top:10px;'>{content['Delta']}</div>", unsafe_allow_html=True)
        with g2:
            st.metric("Θ Theta", "Time Decay")
            st.markdown(f"<div class='card-text' style='font-size:0.9rem; margin-top:10px;'>{content['Theta']}</div>", unsafe_allow_html=True)
        with g3:
            st.metric("ν Vega", "Volatility")
            st.markdown(f"<div class='card-text' style='font-size:0.9rem; margin-top:10px;'>{content['Vega']}</div>", unsafe_allow_html=True)
        
        st.divider()
        st.success(f"💡 **Key Takeaway:** {content['Key']}")

    # --- MODULE 401 ---
    with tabs[3]:
        content = ACADEMY_CONTENT["401"]["levels"][level]
        st.subheader(ACADEMY_CONTENT["401"]["title"])
        
        st.markdown(f"""
        <div class="concept-card">
            <h3 style="color: #00A3FF; margin-bottom: 10px;">{content['Concept']}</h3>
            <p class="card-text">{content['Benefit']}</p>
        </div>
        """, unsafe_allow_html=True)
        st.success(f"💡 **Key Takeaway:** {content['Key']}")

# ==================================================
#                 PAGE 3: THE TERMINAL (PRO)
# ==================================================
def page_terminal():
    # --- QUANT ENGINE (BLACK-SCHOLES) ---
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

    # --- DATA UTILITIES ---
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

    def calculate_greeks(df, spot, expiry_date, backup_vol, type="call"):
        T = (datetime.strptime(expiry_date, "%Y-%m-%d") - datetime.now()).days / 365.0
        if T < 0.001: T = 0.001
        deltas = []
        for index, row in df.iterrows():
            # If IV is missing from data (common in yfinance), use historical vol as backup
            iv = row['impliedVolatility']
            if iv < 0.01 or pd.isna(iv): 
                iv = backup_vol / 100.0
                
            if type == "call": d = quant.get_delta(spot, row['strike'], T, iv, "call")
            else: d = quant.get_delta(spot, row['strike'], T, iv, "put")
            deltas.append(d)
        df['calc_delta'] = deltas
        # Fallback for empty IV in dataframe
        df['impliedVolatility'] = df['impliedVolatility'].replace(0, backup_vol/100.0)
        return df

    # --- TERMINAL UI ---
    st.markdown("## 📐 OpStruct Pro Terminal")
    st.markdown("Automated structuring based on Delta-Neutral or Directional Logic.")
    st.markdown("---")
    
    # INPUT SECTION
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        raw_input = st.text_input("Ticker Symbol", "SPY").strip()
        ticker = lookup_ticker(raw_input)
        if ticker != raw_input.upper(): st.caption(f"✅ Resolved: **{ticker}**")
    
    # FETCH DATA
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d")
        if hist.empty: 
            st.error("Ticker not found or data unavailable.")
            return
        
        exps = stock.options
        if not exps: 
            st.warning("No options chain found for this asset.")
            return

        with c2: expiry = st.selectbox("Expiration Date", exps[:12])
        with c3: view = st.selectbox("Market View / Strategy", ["Bullish (Call Debit Spread)", "Bearish (Put Debit Spread)", "Neutral (Income Strangle)"])

        # EXECUTION
        if st.button("Run Quant Analysis", type="primary", use_container_width=True):
            with st.spinner(f"Pulling Option Chain & Calculating Greeks for {ticker}..."):
                current_price = hist['Close'].iloc[-1]
                curr_vol, iv_rank = get_iv_rank(stock)
                
                # --- MARKET DASHBOARD ---
                st.markdown(f"#### 📊 {ticker} Market Data")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Spot Price", f"${current_price:.2f}")
                m2.metric("IV Rank (1Y)", f"{iv_rank:.0f}%")
                m3.metric("Implied Vol", f"{curr_vol:.1f}%")
                
                regime_msg = "Neutral"
                regime_color = "off"
                if iv_rank > 50: 
                    regime_msg = "HIGH IV"
                    regime_color = "normal" 
                elif iv_rank < 20: 
                    regime_msg = "LOW IV"
                    regime_color = "inverse"
                m4.metric("Vol Regime", regime_msg, delta_color=regime_color)
                
                st.divider()

                # --- GREEK CALCULATION ---
                _, calls, puts = get_chain(ticker, expiry)
                
                # Use Historical Vol as backup if Implied Vol is 0 (Fixes 0 Delta Bug)
                calls = calculate_greeks(calls, current_price, expiry, curr_vol, "call")
                puts = calculate_greeks(puts, current_price, expiry, curr_vol, "put")
                dte = (datetime.strptime(expiry, '%Y-%m-%d') - datetime.now()).days

                # --- ALGORITHMIC STRUCTURING ---
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
                
                # --- TRADE VISUALIZER ---
                if trade:
                    st.subheader(f"🤖 Algo Recommendation: {trade['Type']}")
                    total_price = 0
                    
                    # Construct Visual Card using safe HTML construction
                    rows = ""
                    for leg in trade['Legs']:
                        price = leg['lastPrice']
                        side = leg['side']
                        if side == "BUY": total_price += price
                        else: total_price -= price
                        
                        css_class = "leg-buy" if side == "BUY" else "leg-sell"
                        
                        # We build rows here
                        rows += f"""
                        <div class="leg-row">
                            <span class="mono"><b class="{css_class}">{side}</b> {leg['strike']} {leg['type'].upper()}</span>
                            <span class="mono" style="color: #888;">Δ {leg['calc_delta']:.2f} | ${price:.2f}</span>
                        </div>
                        """

                    net_cost = total_price * 100
                    cost_label = f"Net Debit: ${net_cost:.2f}" if total_price > 0 else f"Net Credit: ${abs(net_cost):.2f}"
                    
                    # Calculate Breakevens (Rough estimate)
                    be_html = ""
                    if trade['Type'] == "Call Debit Spread":
                        be = trade['Legs'][0]['strike'] + total_price
                        be_html = f"<div class='mono' style='margin-top:8px; color:#aaa;'>Breakeven: ${be:.2f}</div>"
                    elif trade['Type'] == "Put Debit Spread":
                        be = trade['Legs'][0]['strike'] - total_price
                        be_html = f"<div class='mono' style='margin-top:8px; color:#aaa;'>Breakeven: ${be:.2f}</div>"
                    
                    final_html = f"""
                    <div class="trade-ticket">
                        <div style="margin-bottom: 10px; color: #fff; font-weight: bold; border-bottom: 1px solid #333; padding-bottom: 5px;">
                            STRATEGY TICKET
                        </div>
                        {rows}
                        <div style="text-align: right; margin-top: 15px; border-top: 1px solid #333; padding-top: 10px;">
                            <h2 style="margin:0; color: #fff;">{cost_label}</h2>
                            {be_html}
                            <small style="color: #666;">*Excluding commissions</small>
                        </div>
                    </div>
                    """
                    
                    # RENDER HTML SAFELY
                    st.markdown(final_html, unsafe_allow_html=True)
                    
                    # --- PROBABILITY LAB ---
                    st.markdown("### 🧪 Probability Lab")
                    st.markdown("Simulate how **Time** and **Volatility** affect your P&L curve.")
                    
                    l1, l2 = st.columns(2)
                    with l1: 
                        slider_max = dte if dte > 0 else 1
                        days_forward = st.slider("⏳ Time Travel (Days into Future)", 0, slider_max, 0)
                    with l2: 
                        vol_adjust = st.slider("⚡ Volatility Shock (%)", -50, 100, 0)

                    # P&L CALCULATION ENGINE
                    spot_range = np.linspace(current_price * 0.7, current_price * 1.3, 200)
                    
                    # 1. Expiration Line (White Dotted)
                    pnl_expiration = np.zeros_like(spot_range) - (total_price * 100)
                    for leg in trade['Legs']:
                        payoff = np.maximum(0, spot_range - leg['strike']) if leg['type'] == "call" else np.maximum(0, leg['strike'] - spot_range)
                        pnl_expiration += (payoff * 100) if leg['side'] == "BUY" else -(payoff * 100)

                    # 2. Simulated Line (Colored)
                    pnl_simulated = np.zeros_like(spot_range) - (total_price * 100)
                    sim_T = max(0.001, (dte - days_forward) / 365.0)
                    for leg in trade['Legs']:
                        # Shock the IV
                        sim_sigma = max(0.01, leg['impliedVolatility'] * (1 + vol_adjust/100))
                        
                        # Re-price option using Black-Scholes
                        if leg['type'] == "call":
                            new_price = quant.black_scholes_call(spot_range, leg['strike'], sim_T, sim_sigma)
                        else:
                            new_price = quant.black_scholes_put(spot_range, leg['strike'], sim_T, sim_sigma)
                            
                        pnl_simulated += (new_price * 100) if leg['side'] == "BUY" else -(new_price * 100)

                    # PLOTLY CHART
                    fig = go.Figure()
                    
                    # Expiration Trace
                    fig.add_trace(go.Scatter(
                        x=spot_range, y=pnl_expiration, 
                        mode='lines', 
                        name='At Expiration', 
                        line=dict(color='white', dash='dot', width=1)
                    ))
                    
                    # Current/Simulated Trace
                    line_color = '#00FF88' if pnl_simulated.max() > 0 else '#FF4B4B'
                    fig.add_trace(go.Scatter(
                        x=spot_range, y=pnl_simulated, 
                        mode='lines', 
                        name=f'Simulated (T+{days_forward})', 
                        fill='tozeroy', 
                        line=dict(color=line_color, width=3)
                    ))
                    
                    fig.add_hline(y=0, line_color="#555", line_width=1)
                    fig.add_vline(x=current_price, line_color="#F4D03F", line_dash="dash", annotation_text="Spot Price")
                    
                    fig.update_layout(
                        template="plotly_dark", 
                        height=500, 
                        title="P&L Simulation", 
                        yaxis_title="Profit / Loss ($)",
                        xaxis_title="Underlying Price",
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        hovermode="x unified"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    with st.expander("🔍 Decoder: How to read this chart"):
                        st.markdown("""
                        **The Visual Intuition:**
                        
                        1.  **Dotted White Line:** This is the *Hard Truth*. It is your P&L on the day of expiration. You cannot escape this math.
                        2.  **Solid Colored Line:** This is your P&L *Right Now*. It is curvy because of **Time Value** and **Implied Volatility**.
                        
                        **Why do they look different?**
                        * **Theta (Time):** As time passes (slide the Time Travel bar), the colored line will slowly collapse onto the white line.
                        * **Vega (Volatility):** If volatility spikes (slide the Volatility Shock bar), the colored line will inflate like a balloon, expanding away from the white line.
                        """)

    except Exception as e:
        st.error(f"Analysis Error: {str(e)}")
        st.caption("Common issues: Invalid ticker symbol, lack of options data for this expiry, or API timeout.")

# ==================================================
#                 MAIN CONTROLLER
# ==================================================
with st.sidebar:
    st.title("OpStruct")
    st.markdown("<small>v2.2.0 // Educational Build</small>", unsafe_allow_html=True)
    st.markdown("---")
    
    if st.button("🏠 Home", use_container_width=True): set_page('home')
    if st.button("🎓 Academy", use_container_width=True): set_page('academy')
    if st.button("📐 Terminal", use_container_width=True): set_page('terminal')
    
    st.markdown("---")
    st.markdown("""
    <div style="font-size: 0.8rem; color: #666;">
    <b>Disclaimer:</b><br>
    This tool is for educational purposes only. 
    It relies on delayed data and theoretical models (Black-Scholes) which may not reflect real-world execution prices.
    </div>
    """, unsafe_allow_html=True)

# PAGE ROUTING
if st.session_state.page == 'home': page_home()
elif st.session_state.page == 'academy': page_academy()
elif st.session_state.page == 'terminal': page_terminal()
