#!/usr/bin/env python3
"""
Manual price update script for when yfinance API is down
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import engine
from sqlalchemy import text
from datetime import datetime

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
        
        return holdings

def update_price_manually(ticker, new_price):
    """Manually update price for a specific ticker"""
    try:
        new_price = float(new_price)
    except ValueError:
        print(f"Invalid price: {new_price}")
        return False
    
    with engine.begin() as conn:
        # Get current holding
        result = conn.execute(text("""
            SELECT shares, total_value, current_price
            FROM holdings 
            WHERE ticker = :ticker AND is_active = TRUE
        """), {"ticker": ticker})
        
        holding = result.fetchone()
        if not holding:
            print(f"Holding not found for {ticker}")
            return False
        
        shares = holding.shares
        total_value = holding.total_value
        old_price = holding.current_price
        
        # Calculate new values
        new_current_value = shares * new_price
        new_gain_loss = new_current_value - total_value
        
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
        
        print(f"✅ Updated {ticker}: ${old_price:.2f} → ${new_price:.2f}")
        print(f"   Current Value: ${new_current_value:.2f}")
        print(f"   Gain/Loss: ${new_gain_loss:.2f}")
        
        return True

def record_portfolio_snapshot():
    """Record current portfolio state"""
    with engine.begin() as conn:
        # Ensure portfolio_history table exists
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS portfolio_history (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_portfolio_value FLOAT,
                cash_balance FLOAT,
                total_invested FLOAT,
                total_profit_loss FLOAT,
                percentage_gain FLOAT,
                holdings_snapshot JSONB
            )
        """))
        
        # Get current holdings
        result = conn.execute(text("""
            SELECT ticker, shares, purchase_price, current_price, 
                   total_value, current_value, gain_loss
            FROM holdings
            WHERE is_active = TRUE
        """)).fetchall()
        
        holdings = [dict(row._mapping) for row in result]
        
        # Calculate portfolio metrics
        cash_balance = next((h["current_value"] for h in holdings if h["ticker"] == "CASH"), 0)
        stock_holdings = [h for h in holdings if h["ticker"] != "CASH"]
        
        total_current_value = sum(h["current_value"] for h in stock_holdings)
        total_invested = sum(h["total_value"] for h in stock_holdings)
        total_profit_loss = sum(h["gain_loss"] for h in stock_holdings)
        
        total_portfolio_value = cash_balance + total_current_value
        percentage_gain = (total_profit_loss / total_invested * 100) if total_invested > 0 else 0
        
        # Record snapshot
        import json
        conn.execute(text("""
            INSERT INTO portfolio_history (
                total_portfolio_value, cash_balance, total_invested, 
                total_profit_loss, percentage_gain, holdings_snapshot
            ) VALUES (:total_portfolio_value, :cash_balance, :total_invested, 
                     :total_profit_loss, :percentage_gain, :holdings_snapshot)
        """), {
            "total_portfolio_value": total_portfolio_value,
            "cash_balance": cash_balance,
            "total_invested": total_invested,
            "total_profit_loss": total_profit_loss,
            "percentage_gain": percentage_gain,
            "holdings_snapshot": json.dumps(holdings)
        })
        
        print("Portfolio snapshot recorded")

def interactive_update():
    """Interactive price update"""
    holdings = show_current_holdings()
    
    if not holdings:
        return
    
    print("\n=== Manual Price Update ===")
    print("Enter ticker and new price (e.g., 'TSLA 310.50') or 'done' to finish")
    print("Enter 'snapshot' to record portfolio snapshot")
    
    while True:
        try:
            user_input = input("\nEnter ticker and price: ").strip()
            
            if user_input.lower() == 'done':
                break
            elif user_input.lower() == 'snapshot':
                record_portfolio_snapshot()
                continue
            elif user_input.lower() == 'show':
                show_current_holdings()
                continue
            
            parts = user_input.split()
            if len(parts) != 2:
                print("Format: TICKER PRICE (e.g., TSLA 310.50)")
                continue
            
            ticker = parts[0].upper()
            price = parts[1]
            
            if update_price_manually(ticker, price):
                # Record snapshot after each update
                record_portfolio_snapshot()
        
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Manual price update for D-AI-Trader holdings')
    parser.add_argument('--show', action='store_true', help='Show current holdings')
    parser.add_argument('--update', nargs=2, metavar=('TICKER', 'PRICE'), help='Update price for specific ticker')
    parser.add_argument('--interactive', action='store_true', help='Interactive price update mode')
    parser.add_argument('--snapshot', action='store_true', help='Record portfolio snapshot')
    
    args = parser.parse_args()
    
    if args.show:
        show_current_holdings()
    elif args.update:
        ticker, price = args.update
        if update_price_manually(ticker.upper(), price):
            record_portfolio_snapshot()
    elif args.snapshot:
        record_portfolio_snapshot()
    elif args.interactive:
        interactive_update()
    else:
        # Default: show current holdings
        show_current_holdings()
        print("\nUsage examples:")
        print("  python manual_price_update.py --update TSLA 310.50")
        print("  python manual_price_update.py --interactive")
        print("  python manual_price_update.py --snapshot") 