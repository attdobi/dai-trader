#!/usr/bin/env python3
"""
Manual price update script for D-AI-Trader holdings
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import engine
from sqlalchemy import text
from datetime import datetime
import yfinance as yf

def clean_ticker_symbol(ticker):
    """Clean up ticker symbol to extract just the symbol"""
    if not ticker:
        return None
    
    # Remove common prefixes/suffixes and extract just the symbol
    ticker = str(ticker).strip()
    
    # Handle cases like "S&P500 ETF (SPY)" -> "SPY"
    if '(' in ticker and ')' in ticker:
        # Extract text between parentheses
        start = ticker.rfind('(') + 1
        end = ticker.rfind(')')
        if start > 0 and end > start:
            ticker = ticker[start:end]
    
    # Remove common words that might be added by AI
    ticker = ticker.replace('ETF', '').replace('Stock', '').replace('Shares', '').strip()
    
    # Remove any remaining parentheses and clean up
    ticker = ticker.replace('(', '').replace(')', '').strip()
    
    return ticker

def get_current_price_robust(ticker):
    """Get current price with robust error handling"""
    # Clean the ticker symbol first
    clean_ticker = clean_ticker_symbol(ticker)
    if not clean_ticker:
        print(f"Invalid ticker symbol: {ticker}")
        return None
    
    try:
        stock = yf.Ticker(clean_ticker)
        
        # Try multiple approaches to get price data
        # First try: 1 day period
        try:
            hist = stock.history(period="1d")
            if len(hist) > 0:
                return float(hist.iloc[-1].Close)
        except:
            pass
        
        # Second try: 5 day period
        try:
            hist = stock.history(period="5d")
            if len(hist) > 0:
                return float(hist.iloc[-1].Close)
        except:
            pass
        
        # Third try: specific date range (last 7 days)
        try:
            from datetime import datetime, timedelta
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            hist = stock.history(start=start_date, end=end_date)
            if len(hist) > 0:
                return float(hist.iloc[-1].Close)
        except:
            pass
        
        # If all attempts fail, return None
        print(f"No price data available for {clean_ticker} (original: {ticker})")
        return None
        
    except Exception as e:
        print(f"Failed to fetch price for {clean_ticker} (original: {ticker}): {e}")
        return None

def update_all_prices():
    """Update prices for all active holdings"""
    print("=== Updating Current Prices ===")
    
    with engine.begin() as conn:
        # Get all active holdings
        result = conn.execute(text("""
            SELECT ticker, shares, purchase_price, current_price, total_value 
            FROM holdings 
            WHERE is_active = TRUE AND ticker != 'CASH'
        """))
        
        holdings = [dict(row._mapping) for row in result]
        
        if not holdings:
            print("No active holdings found to update.")
            return
        
        print(f"Found {len(holdings)} active holdings to update:")
        
        updated_count = 0
        for holding in holdings:
            ticker = holding['ticker']
            shares = holding['shares']
            old_price = holding['current_price']
            
            print(f"\nUpdating {ticker}...")
            print(f"  Current price: ${old_price:.2f}")
            
            # Get new price
            new_price = get_current_price_robust(ticker)
            
            if new_price is None:
                print(f"  ❌ Could not get price for {ticker}")
                continue
            
            print(f"  New price: ${new_price:.2f}")
            
            # Calculate new values
            new_current_value = shares * new_price
            new_gain_loss = new_current_value - holding['total_value']
            
            # Update the database
            conn.execute(text("""
                UPDATE holdings
                SET current_price = :price,
                    current_value = :current_value,
                    gain_loss = :gain_loss,
                    current_price_timestamp = :timestamp
                WHERE ticker = :ticker
            """), {
                "price": new_price,
                "current_value": new_current_value,
                "gain_loss": new_gain_loss,
                "timestamp": datetime.utcnow(),
                "ticker": ticker
            })
            
            print(f"  ✅ Updated {ticker}: ${old_price:.2f} → ${new_price:.2f}")
            print(f"  Current Value: ${new_current_value:.2f}")
            print(f"  Gain/Loss: ${new_gain_loss:.2f}")
            
            updated_count += 1
        
        print(f"\n=== Summary ===")
        print(f"Successfully updated {updated_count} out of {len(holdings)} holdings")
        
        if updated_count > 0:
            # Record portfolio snapshot after price updates
            try:
                from dashboard_server import record_portfolio_snapshot
                record_portfolio_snapshot()
                print("Portfolio snapshot recorded")
            except Exception as e:
                print(f"Failed to record portfolio snapshot: {e}")

def show_current_holdings():
    """Show current holdings and their prices"""
    print("=== Current Holdings ===")
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT ticker, shares, purchase_price, current_price, 
                   total_value, current_value, gain_loss,
                   current_price_timestamp
            FROM holdings 
            WHERE is_active = TRUE AND ticker != 'CASH'
            ORDER BY current_value DESC
        """))
        
        holdings = [dict(row._mapping) for row in result]
        
        if not holdings:
            print("No active holdings found.")
            return
        
        print(f"{'Ticker':<8} {'Shares':<8} {'Purchase':<10} {'Current':<10} {'Total Val':<10} {'Curr Val':<10} {'Gain/Loss':<10}")
        print("-" * 80)
        
        for holding in holdings:
            ticker = holding['ticker']
            shares = holding['shares']
            purchase_price = holding['purchase_price']
            current_price = holding['current_price']
            total_value = holding['total_value']
            current_value = holding['current_value']
            gain_loss = holding['gain_loss']
            timestamp = holding['current_price_timestamp']
            
            print(f"{ticker:<8} {shares:<8.1f} ${purchase_price:<9.2f} ${current_price:<9.2f} ${total_value:<9.2f} ${current_value:<9.2f} ${gain_loss:<9.2f}")
            
            if timestamp:
                print(f"  Last updated: {timestamp}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Update current prices for D-AI-Trader holdings')
    parser.add_argument('--show', action='store_true', help='Show current holdings without updating')
    parser.add_argument('--update', action='store_true', help='Update all current prices')
    
    args = parser.parse_args()
    
    if args.show:
        show_current_holdings()
    elif args.update:
        update_all_prices()
        print("\n" + "="*50)
        show_current_holdings()
    else:
        # Default: show current holdings
        show_current_holdings()
        print("\nTo update prices, run: python update_prices.py --update") 