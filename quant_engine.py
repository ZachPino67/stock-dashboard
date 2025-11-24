import numpy as np
from scipy.stats import norm
import yfinance as yf
import pandas as pd
from datetime import datetime

class VectorizedQuantEngine:
    def __init__(self):
        # DYNAMIC RISK FREE RATE: Fetch 13-Week Treasury Bill Yield
        try:
            tnx = yf.Ticker("^IRX")
            hist = tnx.history(period="1d")
            if not hist.empty:
                self.r = hist['Close'].iloc[-1] / 100
            else:
                self.r = 0.045 # Fallback
        except:
            self.r = 0.045

    def calculate_greeks_vectorized(self, df, S, T, sigma_col='impliedVolatility', type='call'):
        """
        Vectorized Black-Scholes-Merton.
        Calculates Delta, Theta, Vega, and Theoretical Price instantly for whole chains.
        """
        # Handle missing IVs
        sigma = df[sigma_col].replace(0, np.nan).fillna(0.40) 
        K = df['strike']
        
        # Prevent divide by zero for 0DTE
        T = np.maximum(T, 0.001) 

        d1 = (np.log(S / K) + (self.r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        pdf_d1 = norm.pdf(d1)
        cdf_d1 = norm.cdf(d1)
        cdf_d2 = norm.cdf(d2)
        cdf_neg_d1 = norm.cdf(-d1)
        cdf_neg_d2 = norm.cdf(-d2)

        if type == 'call':
            df['theo_price'] = S * cdf_d1 - K * np.exp(-self.r * T) * cdf_d2
            df['delta'] = cdf_d1
            
            # THETA CALCULATION
            term1 = -(S * sigma * pdf_d1) / (2 * np.sqrt(T))
            term2 = self.r * K * np.exp(-self.r * T) * cdf_d2
            df['theta'] = (term1 - term2) / 365.0
            
        else: # PUT
            df['theo_price'] = K * np.exp(-self.r * T) * cdf_neg_d2 - S * cdf_neg_d1
            df['delta'] = cdf_d1 - 1
            
            # THETA CALCULATION
            term1 = -(S * sigma * pdf_d1) / (2 * np.sqrt(T))
            term2 = self.r * K * np.exp(-self.r * T) * cdf_neg_d2
            df['theta'] = (term1 + term2) / 365.0

        df['vega'] = (S * pdf_d1 * np.sqrt(T)) / 100 
        
        return df

    def find_closest_strike(self, df, target_delta):
        df_clean = df.dropna(subset=['delta'])
        if df_clean.empty: return df.iloc[0]
        idx = (np.abs(df_clean['delta'] - target_delta)).argmin()
        return df_clean.iloc[idx]

    def black_scholes_single(self, S, K, T, sigma, type="call"):
        """ Helper for P&L Simulator Loop """
        T = np.maximum(T, 0.001)
        d1 = (np.log(S / K) + (self.r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        if type == "call": 
            return S * norm.cdf(d1) - K * np.exp(-self.r * T) * norm.cdf(d2)
        else: 
            return K * np.exp(-self.r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
