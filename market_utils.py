import yfinance as yf
import pandas as pd
import numpy as np

# --- CONFIGURATION ---
SECTOR_MAP = {
    'XLK': 'Tech', 'XLF': 'Financials', 'XLV': 'Health',
    'XLE': 'Energy', 'XLY': 'Discretionary', 'XLP': 'Staples',
    'XLI': 'Industrial', 'XLB': 'Materials', 'XLC': 'Comms',
    'XLU': 'Utilities', 'IYR': 'Real Estate'
}

LIQUID_WATCHLIST = [
    'SPY', 'QQQ', 'IWM', 'NVDA', 'TSLA', 'AMD', 
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 
    'NFLX', 'COIN', 'MSTR', 'PLTR'
]

def get_macro_pulse():
    """Fetches key macro indicators: VIX, 10Y Yield, Dollar."""
    tickers = ['^VIX', '^TNX', 'DX-Y.NYB']
    try:
        data = yf.download(tickers, period="5d", progress=False)['Close']
        # Handle Multi-index column issue in new yfinance versions
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
            
        pulse = {}
        # VIX
        if '^VIX' in data:
            vix = data['^VIX'].iloc[-1]
            vix_prev = data['^VIX'].iloc[-2]
            pulse['VIX'] = {"val": vix, "delta": vix - vix_prev}
        
        # 10Y Yield (^TNX is usually index points, e.g., 42.50 = 4.25%)
        if '^TNX' in data:
            tnx = data['^TNX'].iloc[-1]
            tnx_prev = data['^TNX'].iloc[-2]
            pulse['TNX'] = {"val": tnx/10, "delta": (tnx - tnx_prev)/10} # Convert to %
            
        # DXY
        if 'DX-Y.NYB' in data:
            dxy = data['DX-Y.NYB'].iloc[-1]
            dxy_prev = data['DX-Y.NYB'].iloc[-2]
            pulse['DXY'] = {"val": dxy, "delta": dxy - dxy_prev}
            
        return pulse
    except Exception as e:
        return None

def get_sector_momentum():
    """Calculates 5-day Relative Strength of Sectors."""
    try:
        data = yf.download(list(SECTOR_MAP.keys()), period="5d", progress=False)['Close']
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
            
        momentum = []
        for ticker, name in SECTOR_MAP.items():
            if ticker in data:
                start = data[ticker].iloc[0]
                end = data[ticker].iloc[-1]
                pct_change = ((end - start) / start) * 100
                momentum.append({"Ticker": ticker, "Name": name, "Change": pct_change})
        
        return pd.DataFrame(momentum).sort_values("Change", ascending=False)
    except:
        return pd.DataFrame()

def scan_volatility_opportunities():
    """
    Scans the Liquid Watchlist for High IV Rank.
    Note: Calculating IV Rank requires 1 year of history, so this is heavy.
    """
    results = []
    
    # Batch download to save time
    try:
        data = yf.download(LIQUID_WATCHLIST, period="1y", group_by='ticker', progress=False)
        
        for ticker in LIQUID_WATCHLIST:
            try:
                # Extract single ticker dataframe
                df = data[ticker]
                if df.empty: continue
                
                # Calculate Volatility (30-day rolling std dev of log returns)
                df['Log_Ret'] = np.log(df['Close'] / df['Close'].shift(1))
                df['Vol'] = df['Log_Ret'].rolling(window=30).std() * np.sqrt(252) * 100
                
                # Drop NaNs
                vol_clean = df['Vol'].dropna()
                if vol_clean.empty: continue
                
                current_vol = vol_clean.iloc[-1]
                min_vol = vol_clean.min()
                max_vol = vol_clean.max()
                
                # IV Rank Calculation
                iv_rank = 0
                if max_vol != min_vol:
                    iv_rank = (current_vol - min_vol) / (max_vol - min_vol) * 100
                
                results.append({
                    "Ticker": ticker,
                    "Price": df['Close'].iloc[-1],
                    "IV Rank": iv_rank,
                    "Current IV": current_vol
                })
            except:
                continue
                
        return pd.DataFrame(results).sort_values("IV Rank", ascending=False)
    except:
        return pd.DataFrame()
