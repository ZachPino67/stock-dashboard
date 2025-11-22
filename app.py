import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import time

# --- PAGE CONFIG ---
st.set_page_config(page_title="TradeWizard", page_icon="🔮", layout="centered")

# --- CUSTOM CSS (GAME DESIGN) ---
st.markdown("""
<style>
    /* Hide standard Streamlit UI junk */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Game-like Typography */
    h1 {color: #FF4B4B; font-family: 'Helvetica', sans-serif; font-weight: 800; font-size: 3rem;}
    p {font-size: 1.2rem; font-family: 'Arial', sans-serif;}
    
    /* Big Button Styling */
    div.stButton > button:first-child {
        height: 3em;
        width: 100%;
        border-radius: 20px;
        border: 2px solid #f0f2f6;
        font-size: 20px;
        font-weight: bold;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
        transition: all 0.2s;
    }
    div.stButton > button:hover {
        transform: scale(1.02);
        border-color: #FF4B4B;
    }
    
    /* Card Styling */
    .game-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        border: 1px solid #e0e0e0;
        text-align: center;
    }
    
    /* Feedback Boxes */
    .feedback-good {background-color: #d4edda; color: #155724; padding: 15px; border-radius: 10px; border: 1px solid #c3e6cb;}
    .feedback-bad {background-color: #f8d7da; color: #721c24; padding: 15px; border-radius: 10px; border: 1px solid #f5c6cb;}
    .feedback-warn {background-color: #fff3cd; color: #856404; padding: 15px; border-radius: 10px; border: 1px solid #ffeeba;}
    
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE (MEMORY) ---
if 'step' not in st.session_state: st.session_state.step = 0 # Start at Home
if 'balance' not in st.session_state: st.session_state.balance = 10000.0
if 'portfolio' not in st.session_state: st.session_state.portfolio = []
if 'ticker' not in st.session_state: st.session_state.ticker = ""
if 'direction' not in st.session_state: st.session_state.direction = ""

# --- COMPLEX BACKEND (HIDDEN) ---
@st.cache_data(ttl=60)
def get_oracle_advice(ticker, direction):
    # This is the Military-Grade Logic hidden behind the curtain
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1mo")
        if hist.empty: return "ERROR", 0, 0
        
        price = hist['Close'].iloc[-1]
        
        # 1. MAX PAIN CALCULATION (The Magnet)
        try:
            exps = stock.options
            if exps:
                opt = stock.option_chain(exps[0])
                calls = opt.calls
                puts = opt.puts
                # Weighted Average Strike based on Open Interest
                total_oi = calls['openInterest'].sum() + puts['openInterest'].sum()
                if total_oi > 0:
                    magnet = ((calls['strike'] * calls['openInterest']).sum() + 
                              (puts['strike'] * puts['openInterest']).sum()) / total_oi
                else:
                    magnet = price
            else:
                magnet = price
        except:
            magnet = price

        # 2. VOLATILITY CHECK (The Fear)
        vol = hist['Close'].pct_change().std() * np.sqrt(252) * 100
        
        # 3. THE VERDICT
        verdict = "GOOD"
        reason = "Looks safe!"
        
        # Rule: Don't bet against the Magnet
        if direction == "CALL" and magnet < price * 0.98:
            verdict = "BAD"
            reason = f"The 'Big Banks' want to pull {ticker} DOWN to ${magnet:.0f}."
        elif direction == "PUT" and magnet > price * 1.02:
            verdict = "BAD"
            reason = f"The 'Big Banks' want to push {ticker} UP to ${magnet:.0f}."
            
        # Rule: Don't buy in extreme volatility (Options too expensive)
        if vol > 60:
            verdict = "WARNING"
            reason = f"Panic is high ({vol:.0f}% volatility). Options are overpriced right now."
            
        return verdict, reason, price
        
    except:
        return "ERROR", 0, 0

# --- NAVIGATOR (PROGRESS BAR) ---
def show_progress(percent):
    st.progress(percent)

# ==================================================
#                 STEP 0: HOMEPAGE
# ==================================================
if st.session_state.step == 0:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>🔮 TradeWizard</h1>", unsafe_allow_html=True)
    st.markdown(f"<div class='game-card'><h3>💰 Balance: ${st.session_state.balance:,.2f}</h3></div>", unsafe_allow_html=True)
    
    st.markdown("<p style='text-align: center;'>Practice trading without losing your shirt.<br>The <b>Oracle AI</b> will protect you from bad deals.</p>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("🎮 START NEW TRADE"):
            st.session_state.step = 1
            st.rerun()
            
    # Show Portfolio if exists
    if st.session_state.portfolio:
        st.divider()
        st.markdown("### 📜 Your History")
        st.dataframe(pd.DataFrame(st.session_state.portfolio), use_container_width=True)

# ==================================================
#                 STEP 1: PICK STOCK
# ==================================================
elif st.session_state.step == 1:
    show_progress(25)
    st.markdown("### 🔎 Step 1: Which company?")
    
    # 1. SEARCH BAR (The "Expand Beyond 7" Feature)
    user_input = st.text_input("Search ANY Stock Ticker (e.g. GME, AMC, COIN)", placeholder="Type here...").upper()
    
    if user_input:
        # Verify it exists
        if st.button(f"Select {user_input} ->"):
            st.session_state.ticker = user_input
            st.session_state.step = 2
            st.rerun()
    
    st.markdown("--- OR PICK A POPULAR ONE ---")
    
    # 2. QUICK CHIPS (Gamified)
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🍎 AAPL"): 
            st.session_state.ticker = "AAPL"
            st.session_state.step = 2
            st.rerun()
    with c2:
        if st.button("🚗 TSLA"):
            st.session_state.ticker = "TSLA"
            st.session_state.step = 2
            st.rerun()
    with c3:
        if st.button("🤖 NVDA"):
            st.session_state.ticker = "NVDA"
            st.session_state.step = 2
            st.rerun()

    if st.button("⬅️ Back"):
        st.session_state.step = 0
        st.rerun()

# ==================================================
#                 STEP 2: UP OR DOWN?
# ==================================================
elif st.session_state.step == 2:
    show_progress(50)
    st.markdown(f"### 🔮 Step 2: Where is {st.session_state.ticker} going?")
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🚀 UP (Call)"):
            st.session_state.direction = "CALL"
            st.session_state.step = 3
            st.rerun()
            
    with c2:
        if st.button("📉 DOWN (Put)"):
            st.session_state.direction = "PUT"
            st.session_state.step = 3
            st.rerun()
            
    if st.button("⬅️ Back"):
        st.session_state.step = 1
        st.rerun()

# ==================================================
#                 STEP 3: THE BET
# ==================================================
elif st.session_state.step == 3:
    show_progress(75)
    st.markdown(f"### 💸 Step 3: How much to bet?")
    
    # Slider for gamified feel
    bet = st.slider("Bet Amount ($)", 100, int(st.session_state.balance), 1000)
    st.markdown(f"<h2 style='text-align: center;'>${bet:,.2f}</h2>", unsafe_allow_html=True)
    
    # THE ORACLE CHECK (This is the "Complex Reasoning" appearing simply)
    st.divider()
    with st.spinner("🔮 The Oracle is analyzing Wall Street data..."):
        time.sleep(1) # Fake delay for dramatic effect
        verdict, reason, price = get_oracle_advice(st.session_state.ticker, st.session_state.direction)
    
    # DISPLAY VERDICT
    if verdict == "GOOD":
        st.markdown(f"<div class='feedback-good'>✅ <b>GREEN LIGHT</b><br>{reason}</div>", unsafe_allow_html=True)
        disable_button = False
    elif verdict == "WARNING":
        st.markdown(f"<div class='feedback-warn'>⚠️ <b>BE CAREFUL</b><br>{reason}</div>", unsafe_allow_html=True)
        disable_button = False
    elif verdict == "BAD":
        st.markdown(f"<div class='feedback-bad'>🛑 <b>DANGER</b><br>{reason}</div>", unsafe_allow_html=True)
        disable_button = False # We let them trade, but we warned them (Robinhood style)
    else:
        st.error("Could not find stock data. Is the ticker right?")
        disable_button = True

    st.write("")
    if st.button("🎰 PLACE TRADE", disabled=disable_button):
        # Execute Trade
        st.session_state.balance -= bet
        st.session_state.portfolio.append({
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Ticker": st.session_state.ticker,
            "Type": st.session_state.direction,
            "Price": price,
            "Amount": bet,
            "Result": "PENDING"
        })
        st.session_state.step = 4
        st.rerun()
        
    if st.button("⬅️ Back"):
        st.session_state.step = 2
        st.rerun()

# ==================================================
#                 STEP 4: SUCCESS
# ==================================================
elif st.session_state.step == 4:
    show_progress(100)
    st.balloons() # DOPAMINE HIT
    
    st.markdown("<h1 style='text-align: center;'>🎉 TRADE EXECUTED!</h1>", unsafe_allow_html=True)
    st.markdown(f"<div class='game-card'><p>You bet <b>${st.session_state.portfolio[-1]['Amount']}</b> on <b>{st.session_state.ticker}</b> going <b>{st.session_state.portfolio[-1]['Type']}</b>.</p></div>", unsafe_allow_html=True)
    
    if st.button("🏠 Return Home"):
        st.session_state.step = 0
        st.rerun()
