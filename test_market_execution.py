#!/usr/bin/env python3

from decider_agent import is_market_open, update_holdings, get_current_price
from datetime import datetime
import pytz

def test_market_execution():
    """Test that trades execute when market is open"""
    print("=== Testing Market Execution Logic ===")
    
    # Check current market status
    market_open = is_market_open()
    print(f"Market is currently: {'OPEN' if market_open else 'CLOSED'}")
    
    # Test decision execution
    test_decisions = [
        {
            "action": "sell",
            "ticker": "TSLA",
            "amount_usd": 5040.0,
            "reason": "day trading, profit taking (>3% gain), rotate capital to new high-momentum opportunities"
        },
        {
            "action": "buy",
            "ticker": "PLTR",
            "amount_usd": 6000.0,
            "reason": "day trading, strong momentum after earnings beat and guidance raise, high conviction short-term upside"
        },
        {
            "action": "hold",
            "ticker": "QQQ",
            "amount_usd": 0.0,
            "reason": "day trading, modest gain; tech sector remains strong, further upside likely"
        }
    ]
    
    print(f"\nTesting execution of {len(test_decisions)} decisions...")
    
    # Simulate what would happen
    for decision in test_decisions:
        action = decision["action"]
        ticker = decision["ticker"]
        reason = decision["reason"]
        
        print(f"\n--- {action.upper()} {ticker} ---")
        print(f"Reason: {reason}")
        
        if not market_open:
            print(f"❌ Would be SKIPPED: Market is closed")
        else:
            # Check if we can get a price
            price = get_current_price(ticker)
            if price:
                print(f"✅ Would be EXECUTED: Price available (${price:.2f})")
                if action == "sell":
                    print(f"   → Would sell {ticker} at ${price:.2f}")
                elif action == "buy":
                    shares = int(decision["amount_usd"] / price)
                    print(f"   → Would buy {shares} shares of {ticker} at ${price:.2f}")
                elif action == "hold":
                    print(f"   → Would hold {ticker} (no action)")
            else:
                print(f"❌ Would be SKIPPED: No price data available")
    
    print(f"\n=== Summary ===")
    print(f"Market Status: {'OPEN' if market_open else 'CLOSED'}")
    if market_open:
        print("✅ When market is OPEN, trades will be EXECUTED if price data is available")
        print("❌ When market is OPEN but no price data, trades will be SKIPPED")
    else:
        print("❌ When market is CLOSED, all trades will be SKIPPED")
    
    print(f"\n💡 To test actual execution, run when market is open (9:30 AM - 4:00 PM ET)")

if __name__ == "__main__":
    test_market_execution() 