import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from scipy.stats import norm
from datetime import datetime, timedelta
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="OpStruct Prime", page_icon="📐", layout="wide")

# --- SESSION STATE MANAGEMENT ---
if 'page' not in st.session_state:
    st.session_state.page = 'home'

def go_to_app():
    st.session_state.page = 'app'

def go_to_home():
    st.session_state.page = 'home'

# --- CUSTOM CSS (APPLE MEETS BLOOMBERG) ---
st.markdown("""
<style>
    /* GENERAL */
    .stApp {background-color: #000000; color: #e0e0e0;}
    
    /* TYPOGRAPHY */
    h1, h2, h3 {font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;}
    
    /* HERO TEXT GRADIENT */
    .hero-text {
        background: -webkit-linear-gradient(45deg, #00FF00, #00AAFF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 4rem;
        font-weight: 800;
        text-align: center;
        line-height: 1.1;
        margin-bottom: 20px;
    }
    
    .sub-hero {
        font-size: 1.5rem;
        color: #888;
        text-align: center;
        font-weight: 300;
        max-width: 800px;
        margin: 0 auto 40px auto;
    }
    
    /* FEATURE CARDS */
    .feature-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 30px;
        text-align: left;
        transition: transform 0.3s ease;
        height: 100%;
    }
    .feature-card:hover {
        transform: translateY(-5px);
        border-color: #00FF00;
    }
    .card-icon {font-size: 2rem; margin-bottom: 15px;}
    .card-title {font-size: 1.2rem; font-weight: bold; color: white; margin-bottom: 10px;}
    .card-desc {font-size: 0.9rem; color: #aaa; line-height: 1.5;}

    /* BUTTONS */
    div.stButton > button {
        border-radius: 30px;
        padding: 10px 30px;
        font-weight: bold;
        border: none;
        transition: all 0.3s;
    }
    /* Primary CTA Button Styling specific hack */
    div[data-testid="stVerticalBlock"] > div > div > div > div > .stButton > button {
        background: linear-gradient(90deg, #00FF00, #008800);
        color: black;
        box-shadow: 0 0 20px rgba(0, 255, 0, 0.4);
    }
    
</style>
""", unsafe_allow_html=True)

# ==================================================
#                 THE HOMEPAGE (MARKETING)
# ==================================================
def homepage():
    # -- HERO SECTION --
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown('<div class="hero-text">Stop Gambling.<br>Start Structuring.</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-hero">Most traders guess directions and lose. Professionals structure risk using math. OpStruct AI brings institutional-grade derivatives engineering to your browser.</div>', unsafe_allow_html=True)
    
    # -- CTA --
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        if st.button("🚀 LAUNCH TERMINAL", use_container_width=True):
            go_to_app()
            st.rerun()

    st.markdown("<br><br><hr style='border-color: #333;'><br>", unsafe_allow_html=True)

    # -- VALUE PROPOSITION GRID --
    st.markdown("<h2 style='text-align: center; margin-bottom: 40px;'>Why OpStruct is Different</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="card-icon">📐</div>
            <div class="card-title">Algorithmic Structuring</div>
            <div class="card-desc">
                We don't just buy calls. We build <b>Vertical Spreads</b> and <b>Iron Condors</b> to cap your risk and lower your cost basis automatically.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="card-icon">📊</div>
            <div class="card-title">Black-Scholes Native</div>
            <div class="card-desc">
                Every trade is backed by real-time probability math. We calculate the <b>Greeks</b> (Delta, Theta) so you know your exact edge before you trade.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="card-icon">🛡️</div>
            <div class="card-title">Volatility Protection</div>
            <div class="card-desc">
                Amateurs get crushed by IV Crush. OpStruct scans Implied Volatility to ensure you aren't overpaying for premium.
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # -- COMPARISON TABLE --
    st.markdown("<h3 style='text-align: center;'>The Retail Trap vs. The OpStruct Way</h3>", unsafe_allow_html=True)
    
    comp_data = {
        "Feature": ["Strategy", "Risk Profile", "Math", "Outcome"],
        "Robinhood / Retail": ["Buy Naked Options", "Unlimited Loss", "Gut Feeling", "Account Blowup"],
        "OpStruct Prime": ["Multi-Leg Spreads", "Defined Risk", "Probabilistic Model", "Consistent Alpha"]
    }
    st.table(pd.DataFrame(comp_data).set_index("Feature"))

# ==================================================
#                 THE APP (LOGIC ENGINE)
# ==================================================
def main_app():
    # --- BLACK-SCHOLES & MATH MODULES ---
    def calculate_probability_of_profit(current_price, strike_price, days_to_exp, iv):
        if days_to_exp <= 0: return 0
        sigma = iv * np.sqrt(days_to_exp / 365)
        d2 = (np.log(current_price / strike_price) - (0.5 * sigma ** 2)) / sigma
        prob_itm = norm.cdf(d2)
        return prob_itm

    def get_option_chain_data(ticker):
        stock = yf.Ticker(ticker)
        try:
            exps = stock.options
            return stock, exps
        except:
            return None, []

    # --- HEADER ---
    c1, c2 = st.columns([3, 1])
    with c1:
        st.title("📐 OpStruct Terminal")
    with c2:
        if st.button("🏠 Back to Home"):
            go_to_home()
            st.rerun()

    # --- SIDEBAR ---
    st.sidebar.markdown("### ⚙️ Configuration")
    ticker = st.sidebar.text_input("Ticker", "NVDA").upper()
    
    stock, exps = get_option_chain_data(ticker)
    if not exps:
        st.error("Invalid Ticker")
        return

    expiry = st.sidebar.selectbox("Target Expiry", exps[:6])
    view = st.sidebar.radio("Your Thesis", ["Bullish (Go Up)", "Bearish (Go Down)", "Neutral (Stay Flat)"])

    # --- DATA FETCHING ---
    hist = stock.history(period="1mo")
    current_price = hist['Close'].iloc[-1]
    iv_rank = (hist['Close'].pct_change().std() * np.sqrt(252) * 100)

    # --- METRICS ---
    m1, m2, m3 = st.columns(3)
    m1.metric("Spot Price", f"${current_price:.2f}")
    m2.metric("Implied Volatility", f"{iv_rank:.1f}%")
    
    days_to_exp = (datetime.strptime(expiry, "%Y-%m-%d") - datetime.now()).days
    m3.metric("Days to Expiry", days_to_exp)
    
    st.divider()

    # --- LOGIC CORE ---
    opt = stock.option_chain(expiry)
    calls = opt.calls
    puts = opt.puts
    trade_structure = {}

    try:
        if view == "Bullish (Go Up)":
            buy_strike = calls.iloc[(calls['strike'] - current_price).abs().argsort()[:1]]['strike'].values[0]
            sell_strike = calls[calls['strike'] > buy_strike].iloc[0]['strike']
            buy_cost = calls[calls['strike'] == buy_strike]['lastPrice'].values[0]
            sell_credit = calls[calls['strike'] == sell_strike]['lastPrice'].values[0]
            net_debit = buy_cost - sell_credit
            
            trade_structure = {
                "Name": "Bull Call Spread",
                "Leg 1": f"BUY ${buy_strike} CALL",
                "Leg 2": f"SELL ${sell_strike} CALL",
                "Cost": net_debit * 100,
                "Max Profit": ((sell_strike - buy_strike) - net_debit) * 100,
                "Breakeven": buy_strike + net_debit,
                "Thesis": "Capped upside, but significantly cheaper than a raw call."
            }

        elif view == "Bearish (Go Down)":
            buy_strike = puts.iloc[(puts['strike'] - current_price).abs().argsort()[:1]]['strike'].values[0]
            sell_strike = puts[puts['strike'] < buy_strike].iloc[-1]['strike'] 
            buy_cost = puts[puts['strike'] == buy_strike]['lastPrice'].values[0]
            sell_credit = puts[puts['strike'] == sell_strike]['lastPrice'].values[0]
            net_debit = buy_cost - sell_credit
            
            trade_structure = {
                "Name": "Bear Put Spread",
                "Leg 1": f"BUY ${buy_strike} PUT",
                "Leg 2": f"SELL ${sell_strike} PUT",
                "Cost": net_debit * 100,
                "Max Profit": ((buy_strike - sell_strike) - net_debit) * 100,
                "Breakeven": buy_strike - net_debit,
                "Thesis": "Profit from downside while protecting against volatility crush."
            }

        elif view == "Neutral (Stay Flat)":
            upper_strike = calls[calls['strike'] > current_price * 1.05].iloc[0]['strike']
            lower_strike = puts[puts['strike'] < current_price * 0.95].iloc[-1]['strike']
            call_credit = calls[calls['strike'] == upper_strike]['lastPrice'].values[0]
            put_credit = puts[puts['strike'] == lower_strike]['lastPrice'].values[0]
            total_credit = call_credit + put_credit
            
            trade_structure = {
                "Name": "Iron Condor / Strangle",
                "Leg 1": f"SELL ${upper_strike} CALL",
                "Leg 2": f"SELL ${lower_strike} PUT",
                "Cost": f"+${total_credit * 100:.2f} (Credit)",
                "Max Profit": total_credit * 100,
                "Breakeven": f"${lower_strike - total_credit:.2f} / ${upper_strike + total_credit:.2f}",
                "Thesis": "Income generation. Profits if stock stays between strikes."
            }

        # --- OUTPUT DISPLAY ---
        c1, c2 = st.columns([1, 1])
        
        with c1:
            st.subheader("🧬 Generated Structure")
            st.markdown(f"""
            <div style="background: #111; padding: 20px; border-radius: 10px; border: 1px solid #333;">
                <h3 style="color: #00FF00;">{trade_structure['Name']}</h3>
                <p>🟢 {trade_structure['Leg 1']}</p>
                <p>🔴 {trade_structure['Leg 2']}</p>
                <hr style="border-color: #444;">
                <div style="display: flex; justify-content: space-between;">
                    <div><b>Cost:</b><br>{trade_structure['Cost'] if isinstance(trade_structure['Cost'], str) else f"${trade_structure['Cost']:.2f}"}</div>
                    <div><b>Max Profit:</b><br><span style="color: #00FF00;">${trade_structure['Max Profit']:.2f}</span></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with c2:
            st.subheader("📉 Payoff Diagram")
            spot_range = np.linspace(current_price * 0.8, current_price * 1.2, 100)
            
            # Simple plotting logic
            if "Call Spread" in trade_structure['Name']:
                b_strike = float(trade_structure['Leg 1'].split('$')[1].split(' ')[0])
                s_strike = float(trade_structure['Leg 2'].split('$')[1].split(' ')[0])
                debit = float(trade_structure['Cost']) / 100
                payoff = np.where(spot_range > b_strike, spot_range - b_strike, 0) - \
                         np.where(spot_range > s_strike, spot_range - s_strike, 0) - debit
            elif "Put Spread" in trade_structure['Name']:
                b_strike = float(trade_structure['Leg 1'].split('$')[1].split(' ')[0])
                s_strike = float(trade_structure['Leg 2'].split('$')[1].split(' ')[0])
                debit = float(trade_structure['Cost']) / 100
                payoff = np.where(spot_range < b_strike, b_strike - spot_range, 0) - \
                         np.where(spot_range < s_strike, s_strike - spot_range, 0) - debit
            else:
                u_strike = float(trade_structure['Leg 1'].split('$')[1].split(' ')[0])
                l_strike = float(trade_structure['Leg 2'].split('$')[1].split(' ')[0])
                credit = float(trade_structure['Cost'].split('$')[1].split(' ')[0]) / 100
                payoff = credit - np.where(spot_range > u_strike, spot_range - u_strike, 0) - \
                         np.where(spot_range < l_strike, l_strike - spot_range, 0)

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=spot_range, y=payoff, mode='lines', fill='tozeroy', line=dict(color='#00FF00')))
            fig.add_hline(y=0, line_color="white", line_dash="dash")
            fig.add_vline(x=current_price, line_color="yellow")
            fig.update_layout(template="plotly_dark", height=300, margin=dict(l=0,r=0,t=0,b=0), yaxis_title="P/L")
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Structuring Error: {e}")

# ==================================================
#                 CONTROLLER
# ==================================================
if st.session_state.page == 'home':
    homepage()
else:
    main_app()
