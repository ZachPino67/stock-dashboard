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
    
    /* ACADEMY SPECIFIC */
    .topic-header {
        color: #fff;
        font-weight: 600;
        font-size: 1.1rem;
        border-left: 3px solid #00FF88;
        padding-left: 10px;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    .alpha-alert {
        background: rgba(255, 75, 75, 0.1);
        border: 1px solid #FF4B4B;
        padding: 10px;
        border-radius: 6px;
        font-size: 0.9rem;
        margin-top: 10px;
    }

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

# --- NEW CURRICULUM STRUCTURE ---
ACADEMY_PHASES = [
    {
        "id": "phase1",
        "title": "Phase 1: Account Killers",
        "req_level": "Rookie",
        "desc": "Mechanics & Risk. If you ignore these, you will blow up. Period.",
        "topics": [
            {"title": "Liquidity & Slippage", "content": "The Bid-Ask spread is the 'vig'. In illiquid options, a wide spread (e.g., $2.00 bid / $2.50 ask) guarantees a loss. **Rule:** Only trade SPY, QQQ, AAPL, or high-volume tickers."},
            {"title": "Assignment Risk (Pin Risk)", "content": "If short an ATM option at expiration, you face Pin Risk. You may be assigned stock over the weekend, exposing you to massive gap risk Monday morning."},
            {"title": "Dividend Risk", "content": "Short Calls near ex-dividend date are dangerous. If the dividend > remaining Put value, you WILL be assigned early and owe the cash."},
            {"title": "Gamma Risk (The Widow Maker)", "content": "Gamma measures Delta acceleration. Short-dated options (0DTE) have explosive Gamma. Small moves against you become catastrophic losses in minutes."},
            {"title": "IV Crush", "content": "Buying before earnings is a novice mistake. IV inflates price; after news, IV collapses. You can get the direction right and still lose money."},
            {"title": "Theta Decay", "content": "Options are wasting assets. Decay is non-linear and accelerates in the last 30 days. Being long without a catalyst is bleeding chips."},
            {"title": "Order Types", "content": "Never use Market Orders. Algos will fill you at the worst price. Always use Limit Orders."},
            {"title": "Margin Requirements", "content": "Know Reg T vs. Portfolio Margin. Volatility spikes expand margin requirements, forcing liquidation at the bottom."}
        ]
    },
    {
        "id": "phase2",
        "title": "Phase 2: The Engine (Greeks)",
        "req_level": "Rookie",
        "desc": "Options are priced on variables. You trade the Greeks, not the stock.",
        "topics": [
            {"title": "Delta", "content": "Price sensitivity. Mastery: Treat Delta as probability. 0.30 Delta = ~30% chance expiring ITM."},
            {"title": "Vega", "content": "Sensitivity to Volatility. Long options need rising Vega. Short options need crushing Vega."},
            {"title": "Rho", "content": "Interest Rate sensitivity. In high-rate environments, Rho impacts LEAPS and long-dated pricing significantly."},
            {"title": "Vanna (2nd Order)", "content": "**Alpha:** How Delta changes as Vol changes. Market Makers hedge these flows."},
            {"title": "Charm (2nd Order)", "content": "**Alpha:** How Delta changes as Time passes. Helps predict end-of-day flows in SPX."}
        ]
    },
    {
        "id": "phase3",
        "title": "Phase 3: The Environment",
        "req_level": "Trader",
        "desc": "Assessing the terrain (Volatility & Structure) before choosing a vehicle.",
        "topics": [
            {"title": "IV vs Historical Vol (HV)", "content": "IV is market price; HV is actual movement. **Edge:** Sell when IV > HV (overpriced), Buy when IV < HV."},
            {"title": "Volatility Skew (The Smirk)", "content": "Puts are usually more expensive than Calls (Downside Skew) because markets crash faster than they rally."},
            {"title": "Term Structure", "content": "Contango (Normal) vs Backwardation (Panic). If near-term IV > long-term IV, the market is in fear mode."},
            {"title": "Put-Call Parity", "content": "The math link between Calls, Puts, and Stock. Defines why Synthetic positions work."},
            {"title": "Expected Move", "content": "Market pricing of movement. Calc: ~85% of the value of the ATM Straddle."}
        ]
    },
    {
        "id": "phase4",
        "title": "Phase 4: Strategy",
        "req_level": "Trader",
        "desc": "How to express a view without dying.",
        "topics": [
            {"title": "Defined vs Undefined Risk", "content": "Naked Puts = Unlimited Risk. Put Spreads = Defined Risk. Stick to defined risk to avoid ruin."},
            {"title": "Probability of Profit (POP)", "content": "High POP (Selling OTM) = Bad Risk/Reward. Low POP (Buying OTM) = Lottery Tickets. Find the balance."},
            {"title": "Rolling", "content": "Defensive mechanic. Closing a loser to open a new one later. **Warning:** Often just extends the pain."},
            {"title": "Legging In/Out", "content": "Entering spreads one leg at a time. **Roast:** Creates accidental directional risk. Execute as one complex order."},
            {"title": "Kelly Criterion (Sizing)", "content": "Never risk >2% of capital. Leverage is massive; small sizing prevents ruin."}
        ]
    },
    {
        "id": "phase5",
        "title": "Phase 5: The Edge",
        "req_level": "Quant",
        "desc": "Market Structure & Dark Pools. Where the pros eat.",
        "topics": [
            {"title": "Dealer Gamma (GEX)", "content": "If Dealers are Short Gamma, they sell drops (accelerate crashes). If Long Gamma, they suppress vol. Knowing the flip point is massive Alpha."},
            {"title": "Dark Pools", "content": "Institutional block flows. Can signal insider sentiment, but might just be hedging. Context is key."},
            {"title": "Correlation Breakdown", "content": "In a crash, correlation goes to 1. Diversification fails. All stocks dump together."}
        ]
    }
]

# --- UPDATED QUIZ BANK ---
QUIZ_BANK = {
    "Rookie": [
        {"q": "What happens to Implied Volatility (IV) after an earnings event?", "options": ["It Spikes", "It Crushes (Collapses)", "Stays the same"], "a": "It Crushes (Collapses)"},
        {"q": "Which Greek measures 'Time Decay'?", "options": ["Delta", "Vega", "Theta"], "a": "Theta"},
        {"q": "What is the safest order type for options?", "options": ["Market Order", "Limit Order", "Stop Loss"], "a": "Limit Order"}
    ],
    "Trader": [
        {"q": "If Near-Term IV is higher than Long-Term IV, the market is in...?", "options": ["Contango", "Backwardation", "Equilibrium"], "a": "Backwardation"},
        {"q": "You are 'Short Gamma'. If the market drops, Dealers will likely...?", "options": ["Buy the dip", "Sell (Accelerate the drop)", "Do nothing"], "a": "Sell (Accelerate the drop)"},
        {"q": "What defines 'Expected Move'?", "options": ["Value of ATM Call", "Value of ATM Put", "85% of ATM Straddle"], "a": "85% of ATM Straddle"}
    ],
    "Quant": [
         {"q": "Vanna measures the sensitivity of Delta to changes in...?", "options": ["Time", "Volatility", "Interest Rates"], "a": "Volatility"},
         {"q": "In a true market crash, correlation between S&P 500 stocks tends to...?", "options": ["Go to 0", "Go to 1 (Converge)", "Stay random"], "a": "Go to 1 (Converge)"}
    ]
}
