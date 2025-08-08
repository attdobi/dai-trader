#!/usr/bin/env python3
"""
Feedback Analysis Runner

This script demonstrates the feedback system for the AI trading platform.
It analyzes recent trading outcomes and provides insights to improve agent performance.
"""

import sys
import json
from datetime import datetime, timedelta
from feedback_agent import TradeOutcomeTracker, SIGNIFICANT_PROFIT_THRESHOLD, SIGNIFICANT_LOSS_THRESHOLD

def main():
    """Main function to run feedback analysis"""
    print("=== AI Trading Feedback Analysis System ===")
    print(f"Significant profit threshold: {SIGNIFICANT_PROFIT_THRESHOLD:.1%}")
    print(f"Significant loss threshold: {SIGNIFICANT_LOSS_THRESHOLD:.1%}")
    print()
    
    try:
        # Initialize the tracker
        tracker = TradeOutcomeTracker()
        print("✓ Feedback tracker initialized")
        print("✓ Database tables created/verified")
        
        # Run comprehensive analysis
        print("\n=== Running Analysis ===")
        
        # Analyze different time periods
        time_periods = [7, 14, 30]
        
        for days in time_periods:
            print(f"\n--- Analysis for last {days} days ---")
            result = tracker.analyze_recent_outcomes(days_back=days)
            
            if result:
                print(f"Trades analyzed: {result['total_trades']}")
                print(f"Success rate: {result['success_rate']:.1%}")
                print(f"Average profit: {result['avg_profit']:.2%}")
                print(f"Feedback ID: {result['feedback_id']}")
                
                # Display feedback insights
                feedback = result['feedback']
                if isinstance(feedback, dict):
                    print("\n📊 Key Insights:")
                    for key, value in feedback.items():
                        if key not in ['summarizer_feedback', 'decider_feedback']:
                            print(f"  {key}: {value}")
                    
                    if 'summarizer_feedback' in feedback:
                        print(f"\n📈 Summarizer Guidance:")
                        print(f"  {feedback['summarizer_feedback']}")
                    
                    if 'decider_feedback' in feedback:
                        print(f"\n🎯 Decider Guidance:")
                        print(f"  {feedback['decider_feedback']}")
                else:
                    print(f"Raw feedback: {feedback}")
            else:
                print("No trades found for this period")
        
        # Show latest feedback that agents would use
        print("\n=== Latest Agent Feedback ===")
        latest = tracker.get_latest_feedback()
        if latest:
            print(f"Based on {latest['total_trades_analyzed']} trades")
            print(f"Success rate: {latest['success_rate']:.1%}")
            print(f"Average profit: {latest['avg_profit_percentage']:.2%}")
            print("\nThis feedback is automatically incorporated into agent decisions.")
        else:
            print("No feedback available yet - system needs trading history to generate insights.")
        
        print("\n=== System Status ===")
        print("✓ Outcome tracking: Active")
        print("✓ Performance analysis: Active") 
        print("✓ Agent feedback: Active")
        print("✓ Instruction updates: Ready")
        
        print("\n=== Next Steps ===")
        print("1. Run trading decisions (decider_agent.py) - will now use feedback")
        print("2. Execute trades - outcomes will be automatically tracked")
        print("3. Feedback analysis runs periodically to improve performance")
        print("4. Check dashboard for performance visualization")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

def demonstrate_outcome_recording():
    """Demonstrate how trade outcomes are recorded"""
    print("\n=== Demonstrating Outcome Recording ===")
    
    tracker = TradeOutcomeTracker()
    
    # Example of how a sell outcome would be recorded
    example_holding = {
        'purchase_price': 150.00,
        'shares': 10,
        'purchase_timestamp': datetime.utcnow() - timedelta(days=5),
        'reason': 'Positive earnings report'
    }
    
    # Simulate different outcomes
    outcomes = [
        ('AAPL', 165.00, 'significant_profit'),  # 10% gain
        ('GOOGL', 145.00, 'moderate_loss'),      # 3.3% loss  
        ('MSFT', 152.00, 'moderate_profit'),     # 1.3% gain
    ]
    
    print("Simulating trade outcomes:")
    for ticker, sell_price, expected_category in outcomes:
        try:
            category = tracker.record_sell_outcome(
                ticker, sell_price, example_holding, f"Demo sell of {ticker}"
            )
            print(f"  {ticker}: ${sell_price:.2f} -> {category} (expected: {expected_category})")
        except Exception as e:
            print(f"  {ticker}: Error - {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demonstrate_outcome_recording()
    
    exit_code = main()
    sys.exit(exit_code)