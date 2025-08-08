#!/usr/bin/env python3

from decider_agent import engine, get_unprocessed_summaries, update_all_current_prices, fetch_holdings, ask_decision_agent, store_trade_decisions, update_holdings, mark_summaries_processed
from sqlalchemy import text
from datetime import datetime
import json

def create_test_summary():
    """Create a test unprocessed summary"""
    with engine.begin() as conn:
        # Create a test summary
        test_summary = {
            "agent": "Agent_Test",
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "headlines": ["Test headline 1", "Test headline 2"],
                "insights": "This is a test summary for testing the decider agent."
            },
            "screenshot_paths": [],
            "run_id": "test_run"
        }
        
        conn.execute(text("""
            INSERT INTO summaries (agent, timestamp, run_id, data)
            VALUES (:agent, :timestamp, :run_id, :data)
        """), {
            "agent": test_summary["agent"],
            "timestamp": datetime.utcnow(),
            "run_id": test_summary["run_id"],
            "data": json.dumps(test_summary)
        })
        
        print("✅ Created test unprocessed summary")

def test_decider_with_current_prices():
    """Test the decider agent with current prices"""
    print("=== Testing Decider Agent with Current Prices ===")
    
    # Get unprocessed summaries
    unprocessed_summaries = get_unprocessed_summaries()
    print(f"Found {len(unprocessed_summaries)} unprocessed summaries")
    
    if not unprocessed_summaries:
        print("No unprocessed summaries found.")
        return
    
    # Create a run_id
    latest_timestamp = max(s['timestamp'] for s in unprocessed_summaries)
    run_id = latest_timestamp.strftime("%Y%m%dT%H%M%S")
    
    # Update current prices before making decisions
    update_all_current_prices()
    
    # Fetch holdings
    holdings = fetch_holdings()
    
    # Check if we have current prices for decision making
    holdings_without_prices = [h for h in holdings if h['ticker'] != 'CASH' and h['current_price'] == h['purchase_price']]
    if holdings_without_prices:
        tickers_without_prices = [h['ticker'] for h in holdings_without_prices]
        print(f"\n⚠️  WARNING: Using purchase prices for decision making on: {', '.join(tickers_without_prices)}")
        print("💡 Consider manually updating prices for accurate decision making")
    
    # Make decisions
    decisions = ask_decision_agent(unprocessed_summaries, run_id, holdings)
    
    # Store decisions
    store_trade_decisions(decisions, run_id)
    
    # Update holdings
    update_holdings(decisions)
    
    # Mark summaries as processed
    summary_ids = [s['id'] for s in unprocessed_summaries]
    mark_summaries_processed(summary_ids)
    
    print(f"✅ Decider agent test completed for run {run_id}")

if __name__ == "__main__":
    # Create a test summary
    create_test_summary()
    
    # Test the decider
    test_decider_with_current_prices() 