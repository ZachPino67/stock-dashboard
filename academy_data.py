# --- CSS STYLING ---
APP_STYLE = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=JetBrains+Mono:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0B0E11; color: #E0E0E0; }
    h1, h2, h3 { font-weight: 600; letter-spacing: -0.5px; }

    /* CUSTOM CLASSES */
    .hero-title {
        font-size: 4.5rem;
        background: -webkit-linear-gradient(45deg, #00FF88, #00A3FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
        line-height: 1.1;
    }
    .mono { font-family: 'JetBrains Mono', monospace; }
    .concept-card {
        background: rgba(30, 35, 45, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 24px;
        border-radius: 12px;
        margin-bottom: 20px;
        transition: transform 0.2s ease;
    }
    .concept-card:hover {
        transform: translateY(-2px);
        border-color: rgba(0, 255, 136, 0.3);
    }
    .concept-title { color: #00FF88; font-weight: 700; font-size: 1.3rem; margin-bottom: 8px; }

    /* TICKET STYLES */
    .trade-ticket {
        background: #151920; border: 1px solid #333; border-radius: 12px; 
        padding: 24px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    .ticket-header {
        font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px;
        color: #888; border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 15px;
    }
    .leg-row {
        display: flex; justify-content: space-between; padding: 12px 0; 
        border-bottom: 1px solid #2a2e35; font-family: 'JetBrains Mono', monospace; font-size: 0.95rem;
    }
    .leg-buy { color: #00FF88; background: rgba(0, 255, 136, 0.1); padding: 2px 6px; border-radius: 4px; }
    .leg-sell { color: #FF4B4B; background: rgba(255, 75, 75, 0.1); padding: 2px 6px; border-radius: 4px; }
    .cost-val { font-size: 1.8rem; font-weight: 700; color: #fff; }
    
    div[data-testid="stMetric"] { background-color: #161B22; border: 1px solid #30363D; border-radius: 8px; }
    section[data-testid="stSidebar"] button { width: 100%; text-align: left; border: none; background: transparent; color: #ccc; }
    section[data-testid="stSidebar"] button:hover { color: #fff; background: #1F2530; }

    @media only screen and (max-width: 600px) {
        .hero-title { font-size: 2.8rem !important; }
        .concept-card, .trade-ticket { padding: 16px !important; }
        div.block-container { padding-top: 2rem !important; }
    }
</style>
"""

# --- EDUCATIONAL CONTENT ---
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
