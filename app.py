import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from scipy.stats import norm
from datetime import datetime, timedelta
import plotly.graph_objects as go
import requests
import textwrap

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
    }
    .leg-buy { color: #00FF88; background: rgba(0, 255, 136, 0.1); padding: 2px 6px; border-radius: 4px; }
    .leg-sell { color: #FF4B4B; background: rgba(255, 75, 75, 0.1); padding: 2px 6px; border-radius: 4px; }
    
    .ticket-footer {
        margin-top: 20px;
        padding-top: 15px;
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
    }
    .cost-display {
        text-align: right;
    }
    .cost-val {
        font-size: 1.8rem;
        font-weight: 700;
        color: #fff;
    }
    
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
                "Call": "The Discount Coupon. Imagine a coupon that guarantees you can buy a TV for $500. If the store price rises to $700, your coupon is instantly worth $200. If the price drops to $400, the coupon is worthless, but you have no obligation to use it.",
                "Put": "Car Insurance. You pay a premium to insure your car. If you crash (the stock drops), the insurance company pays you the difference. If you don't crash, you simply lose the small premium you paid.",
                "Key": "Options give you rights without obligations."
            },
            "Trader": {
                "Call": "Bullish Leverage. A contract giving you the right to buy 100 shares at a specific strike price. It offers uncapped upside with capped downside (cost of the premium). You need price velocity (Delta) to overcome time decay (Theta).",
                "Put": "Bearish Protection. A contract giving you the right to sell 100 shares. Traders use Puts to speculate on downside moves or to hedge existing stock portfolios (reducing portfolio Beta).",
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
                "Buy": "Buying Lottery Tickets. You pay a small amount for a chance to win big. Most tickets expire worthless. This is a low-probability, high-reward strategy.",
                "Sell": "Owning the Casino. You sell the tickets to others. You collect small payments frequently. Occasionally, someone hits a jackpot and you must pay them, but mathematically, the house always wins in the long run.",
                "Key": "Casinos (Sellers) generally make more consistent money than Gamblers (Buyers)."
            },
            "Trader": {
                "Buy": "Long Volatility (Debit). Defined Risk / Unlimited Reward. However, you face a low Probability of Profit (POP). You need the stock to move significantly to overcome the premium paid.",
                "Sell": "Short Volatility (Credit). Unlimited Risk / Defined Reward. High Probability of Profit (POP). You profit if the stock goes your way, stays flat, or even moves slightly against you.",
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
                "Delta": "Speed. How much your option's price changes for every $1 the stock moves. (e.g., Delta 0.50 means you make 50 cents if the stock goes up $1).",
                "Theta": "Time Decay. The daily fee you pay for holding the option. Like an ice cube melting, your option loses value every day it doesn't move.",
                "Vega": "Panic Meter. How much the option price inflates when the market gets scared. When news hits, prices go up even if the stock doesn't move.",
                "Key": "The Greeks explain why you are making or losing money."
            },
            "Trader": {
                "Delta": "Directional Exposure & Probability.** Delta creates your directional bias. It also serves as a proxy for the probability of expiring In-The-Money (ITM). A 30 Delta option has roughly a 30% chance of expiring ITM.",
                "Theta": "Daily Carry. If you are Long Options, Theta is your enemy (bleeding value). If you are Short Options, Theta is your income (collecting rent).",
                "Vega": "*Volatility Sensitivity. In high IV environments, options are expensive—prefer selling Vega. In low IV environments, options are cheap—prefer buying Vega.",
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
                "Concept": "The Combo Meal. Instead of just buying a burger (Call), you buy a burger and sell a drink to offset the cost. It limits how much food you get, but it's much cheaper.",
                "Benefit": "It prevents catastrophic loss. You define exactly how much you can lose before you enter the trade, so you can sleep at night.",
                "Key": "Spreads make trading safer, cheaper, and more predictable."
            },
            "Trader": {
                "Concept": "Vertical Spreads. Simultaneously buying and selling options in the same expiration cycle. This reduces your cost basis (Debit Spreads) or generates income (Credit Spreads) while capping your maximum risk.",
                "Benefit": "Defined Risk & Probability Enhancement. A spread lowers the break-even point of a trade, increasing your statistical probability of success compared to a naked option.",
                "Key": "Most sustainable retail strategies utilize spreads to neutralize volatility risk."
            },
            "Quant": {
                "Concept": "Factor Isolation. Spreads allow a structurer to isolate specific Greeks. A 'Vertical Spread' isolates Delta while neutralizing Vega. A 'Calendar Spread' isolates Theta and Vega while neutralizing Delta.",
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

# # [KEEP YOUR EXISTING IMPORTS, CSS, AND ACADEMY CODE UP TOP]
# REPLACE THE QuantEngine AND page_terminal FUNCTIONS WITH THIS:

# --- OPTIMIZED QUANT ENGINE (VECTORIZED) ---
class VectorizedQuantEngine:
    def __init__(self, risk_free_rate=0.045):
        self.r = risk_free_rate

    def calculate_greeks_vectorized(self, df, S, T, sigma_col='impliedVolatility', type='call'):
        """
        Performs Black-Scholes calc on the ENTIRE dataframe column at once.
        0 loops. 100x faster.
        """
        # Data cleaning: Ensure Sigma and T are safe
        sigma = df[sigma_col].replace(0, np.nan).fillna(0.20) # Handle 0 IV
        K = df['strike']
        
        # d1 and d2 Calculation
        d1 = (np.log(S / K) + (self.r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        if type == 'call':
            # Price
            df['theo_price'] = S * norm.cdf(d1) - K * np.exp(-self.r * T) * norm.cdf(d2)
            # Greeks
            df['delta'] = norm.cdf(d1)
            df['theta'] = (- (S * sigma * norm.pdf(d1)) / (2 * np.sqrt(T)) - self.r * K * np.exp(-self.r * T) * norm.cdf(d2)) / 365.0
        else:
            # Price
            df['theo_price'] = K * np.exp(-self.r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
            # Greeks
            df['delta'] = norm.cdf(d1) - 1
            df['theta'] = (- (S * sigma * norm.pdf(d1)) / (2 * np.sqrt(T)) + self.r * K * np.exp(-self.r * T) * norm.cdf(-d2)) / 365.0

        # Gamma and Vega are the same for Calls and Puts
        df['gamma'] = norm.pdf(d1) / (S * sigma * np.sqrt(T))
        df['vega'] = S * norm.pdf(d1) * np.sqrt(T) / 100.0
        
        return df

    def find_closest_strike(self, df, target_delta):
        # Vectorized lookup
        idx = (np.abs(df['delta'] - target_delta)).argmin()
        return df.iloc[idx]

    def black_scholes_single(self, S, K, T, sigma, type="call"):
        # For the simulation slider (single value calc)
        d1 = (np.log(S / K) + (self.r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        if type == "call":
            return S * norm.cdf(d1) - K * np.exp(-self.r * T) * norm.cdf(d2)
        else:
            return K * np.exp(-self.r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

# ==================================================
#                  PAGE 3: THE TERMINAL (PRO)
# ==================================================
def page_terminal():
    quant = VectorizedQuantEngine()

    # --- DATA UTILITIES ---
    def get_iv_rank(stock_obj):
        try:
            hist = stock_obj.history(period="1y")
            if hist.empty: return 0, 0
            hist['Log_Ret'] = np.log(hist['Close'] / hist['Close'].shift(1))
            # Annualized Volatility
            hist['Volatility'] = hist['Log_Ret'].rolling(window=30).std() * np.sqrt(252) * 100
            vol_data = hist['Volatility'].dropna()
            current_vol = vol_data.iloc[-1]
            # IV Rank Calculation
            mn, mx = vol_data.min(), vol_data.max()
            if mx == mn: return current_vol, 0
            iv_rank = (current_vol - mn) / (mx - mn) * 100
            return current_vol, iv_rank
        except: return 0, 0

    @st.cache_data(ttl=300) # Cache this for 5 mins so sliders don't re-fetch API
    def get_chain_and_greeks(ticker, expiry, current_price):
        stock = yf.Ticker(ticker)
        try:
            opt = stock.option_chain(expiry)
            calls = opt.calls
            puts = opt.puts
        except Exception:
            return None, None
            
        # Calculate Time to Expiry once
        T = (datetime.strptime(expiry, "%Y-%m-%d") - datetime.now()).days / 365.0
        if T < 0.001: T = 0.001

        # VECTORIZED CALCULATION (Instant)
        calls = quant.calculate_greeks_vectorized(calls, current_price, T, type='call')
        puts = quant.calculate_greeks_vectorized(puts, current_price, T, type='put')
        
        return calls, puts

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
    stock = yf.Ticker(ticker)
    try:
        exps = stock.options
    except:
        exps = []

    if not exps: 
        st.warning("No options chain found. Market may be closed or ticker invalid.")
        return

    with c2: expiry = st.selectbox("Expiration Date", exps[:12])
    with c3: view = st.selectbox("Market View", ["Bullish (Call Debit Spread)", "Bearish (Put Debit Spread)", "Neutral (Iron Condor / Strangle)"])

    # INITIALIZATION BUTTON
    if st.button("Initialize Terminal", type="primary", use_container_width=True):
        with st.spinner(f"Analyzing Volatility Surface for {ticker}..."):
            hist = stock.history(period="5d")
            if hist.empty:
                st.error("Data fetch failed.")
                return
            
            current_price = hist['Close'].iloc[-1]
            curr_vol, iv_rank = get_iv_rank(stock)
            
            # --- GREEK CALCULATION (Now Vectorized) ---
            calls, puts = get_chain_and_greeks(ticker, expiry, current_price)
            
            if calls is None:
                st.error("Failed to retrieve option chain.")
                return

            dte = (datetime.strptime(expiry, '%Y-%m-%d') - datetime.now()).days

            # --- ALGORITHMIC STRUCTURING ---
            trade = {}
            if "Bullish" in view:
                buy_leg = quant.find_closest_strike(calls, 0.50)
                sell_leg = quant.find_closest_strike(calls, 0.30)
                # Ensure rational strikes (Buy Low Strike, Sell High Strike for Call Debit)
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
                # Strangle: Sell OTM Put and Sell OTM Call
                call_leg = quant.find_closest_strike(calls, 0.20)
                put_leg = quant.find_closest_strike(puts, -0.20)
                call_leg['side'] = "SELL"; put_leg['side'] = "SELL"
                call_leg['type'] = "call"; put_leg['type'] = "put"
                trade = {"Legs": [call_leg, put_leg], "Type": "Short Strangle"}

            # --- STORE IN SESSION STATE ---
            st.session_state['terminal_data'] = {
                "ticker": ticker,
                "current_price": current_price,
                "iv_rank": iv_rank,
                "curr_vol": curr_vol,
                "calls": calls, # Store DF for plotting
                "puts": puts,   # Store DF for plotting
                "trade": trade,
                "dte": dte
            }

    # --- RENDERING (FROM SESSION STATE) ---
    if 'terminal_data' in st.session_state:
        data = st.session_state['terminal_data']
        
        # 1. MARKET DATA
        regime_msg = "Normal"
        regime_color = "off"
        if data['iv_rank'] > 50: 
            regime_msg = "High Vol (Sell Premium)"
            regime_color = "normal" 
        elif data['iv_rank'] < 20: 
            regime_msg = "Low Vol (Buy Premium)"
            regime_color = "inverse"

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Spot Price", f"${data['current_price']:.2f}")
        m2.metric("IV Rank (1Y)", f"{data['iv_rank']:.0f}%")
        m3.metric("Implied Vol", f"{data['curr_vol']:.1f}%")
        m4.metric("Regime", regime_msg, delta_color=regime_color)
        
        # 2. VOLATILITY SKEW CHART (New Feature)
        st.markdown("##### 🎢 Volatility Skew (The 'Smile')")
        with st.expander("Show Volatility Surface Analysis", expanded=True):
            skew_fig = go.Figure()
            # Filter for relevant strikes (Spot +/- 20%) to hide noise
            calls_view = data['calls'][ (data['calls']['strike'] > data['current_price']*0.8) & (data['calls']['strike'] < data['current_price']*1.2) ]
            puts_view = data['puts'][ (data['puts']['strike'] > data['current_price']*0.8) & (data['puts']['strike'] < data['current_price']*1.2) ]
            
            skew_fig.add_trace(go.Scatter(x=calls_view['strike'], y=calls_view['impliedVolatility']*100, mode='lines', name='Call IV', line=dict(color='#00FF88')))
            skew_fig.add_trace(go.Scatter(x=puts_view['strike'], y=puts_view['impliedVolatility']*100, mode='lines', name='Put IV', line=dict(color='#FF4B4B')))
            skew_fig.add_vline(x=data['current_price'], line_dash="dash", line_color="white", annotation_text="Spot")
            
            skew_fig.update_layout(
                template="plotly_dark", height=300, 
                title="IV Skew (Puts vs Calls)",
                yaxis_title="Implied Volatility %", xaxis_title="Strike Price",
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(skew_fig, use_container_width=True)

        st.divider()

        # 3. TRADE TICKET
        trade = data['trade']
        if trade:
            c_left, c_right = st.columns([1, 2])
            
            with c_left:
                st.subheader("Ticket")
                total_price = 0
                rows = ""
                for leg in trade['Legs']:
                    # Use lastPrice if available, else theoretical price
                    price = leg.get('lastPrice', leg.get('theo_price', 0))
                    
                    side = leg['side']
                    if side == "BUY": total_price += price
                    else: total_price -= price
                    
                    css_class = "leg-buy" if side == "BUY" else "leg-sell"
                    rows += f"""<div class="leg-row"><span class="mono"><b class="{css_class}">{side}</b> {leg['strike']} {leg['type'].upper()}</span><span class="mono" style="color: #888;">Δ {leg['delta']:.2f} | ${price:.2f}</span></div>"""

                net_cost = total_price * 100
                cost_label = f"Debit: ${net_cost:.2f}" if total_price > 0 else f"Credit: ${abs(net_cost):.2f}"
                
                final_html = f"""
                <div class="trade-ticket">
                    <div class="ticket-header">
                        <span>{trade['Type'].upper()}</span>
                    </div>
                    {rows}
                    <div class="ticket-footer">
                        <div class="cost-display">
                            <div class="cost-val">{cost_label}</div>
                        </div>
                    </div>
                </div>
                """
                st.markdown(textwrap.dedent(final_html), unsafe_allow_html=True)

            with c_right:
                # 4. PROBABILITY LAB
                st.subheader("Probability Lab")
                l1, l2 = st.columns(2)
                with l1: 
                    slider_max = data['dte'] if data['dte'] > 0 else 1
                    days_forward = st.slider("⏳ Time (Days)", 0, slider_max, 0)
                with l2: 
                    vol_adjust = st.slider("⚡ Vol Adjust (%)", -50, 100, 0)

                # Simulation Logic
                spot_range = np.linspace(data['current_price'] * 0.7, data['current_price'] * 1.3, 100)
                sim_T = max(0.001, (data['dte'] - days_forward) / 365.0)
                
                pnl_simulated = np.zeros_like(spot_range) - (total_price * 100)
                
                for leg in trade['Legs']:
                    sim_sigma = max(0.01, leg['impliedVolatility'] * (1 + vol_adjust/100))
                    
                    # We use the single calculator here for the loop over ranges
                    # But we could vectorize this too if we wanted extreme speed
                    leg_prices = quant.black_scholes_single(spot_range, leg['strike'], sim_T, sim_sigma, leg['type'])
                    
                    if leg['side'] == "BUY": pnl_simulated += (leg_prices * 100)
                    else: pnl_simulated -= (leg_prices * 100)

                # Chart
                fig = go.Figure()
                line_color = '#00FF88' if pnl_simulated[int(len(pnl_simulated)/2)] > 0 else '#FF4B4B'
                
                fig.add_trace(go.Scatter(
                    x=spot_range, y=pnl_simulated, 
                    mode='lines', name=f'T+{days_forward}', 
                    fill='tozeroy', line=dict(color=line_color, width=2)
                ))
                fig.add_vline(x=data['current_price'], line_color="#F4D03F", line_dash="dash")
                fig.add_hline(y=0, line_color="#555")
                
                fig.update_layout(
                    template="plotly_dark", height=350,
                    margin=dict(l=20, r=20, t=30, b=20),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig, use_container_width=True)

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
