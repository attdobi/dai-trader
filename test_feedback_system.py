#!/usr/bin/env python3
"""
Test script for the AI Trading Feedback System

This script demonstrates the key components and functionality
of the feedback system without requiring a full database setup.
"""

import json
from datetime import datetime, timedelta

# Mock data structures to simulate the feedback system
class MockTradeOutcome:
    def __init__(self, ticker, purchase_price, sell_price, hold_days, reason):
        self.ticker = ticker
        self.purchase_price = purchase_price
        self.sell_price = sell_price
        self.gain_loss_percentage = (sell_price - purchase_price) / purchase_price
        self.hold_duration_days = hold_days
        self.original_reason = reason
        self.sell_timestamp = datetime.utcnow() - timedelta(days=hold_days)
        
        # Categorize outcome
        if self.gain_loss_percentage >= 0.05:
            self.outcome_category = 'significant_profit'
        elif self.gain_loss_percentage > 0:
            self.outcome_category = 'moderate_profit'
        elif self.gain_loss_percentage >= -0.02:
            self.outcome_category = 'break_even'
        elif self.gain_loss_percentage >= -0.10:
            self.outcome_category = 'moderate_loss'
        else:
            self.outcome_category = 'significant_loss'

def create_sample_trades():
    """Create sample trading data for demonstration"""
    return [
        MockTradeOutcome('AAPL', 150.00, 165.00, 5, 'Positive earnings report'),
        MockTradeOutcome('GOOGL', 2800.00, 2720.00, 12, 'Market uncertainty'),
        MockTradeOutcome('MSFT', 300.00, 315.00, 8, 'Cloud growth optimism'),
        MockTradeOutcome('TSLA', 250.00, 230.00, 15, 'Production concerns'),
        MockTradeOutcome('NVDA', 450.00, 485.00, 3, 'AI demand surge'),
        MockTradeOutcome('META', 320.00, 298.00, 20, 'Regulatory pressure'),
        MockTradeOutcome('AMZN', 140.00, 152.00, 7, 'E-commerce recovery'),
        MockTradeOutcome('NFLX', 400.00, 420.00, 10, 'Subscriber growth'),
    ]

def analyze_performance(trades):
    """Analyze trading performance and generate insights"""
    total_trades = len(trades)
    profitable_trades = [t for t in trades if t.gain_loss_percentage > 0]
    success_rate = len(profitable_trades) / total_trades if total_trades > 0 else 0
    avg_profit = sum(t.gain_loss_percentage for t in trades) / total_trades
    
    # Group by category
    by_category = {}
    for trade in trades:
        category = trade.outcome_category
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(trade)
    
    # Analyze successful patterns
    successful_reasons = [t.original_reason for t in trades if t.gain_loss_percentage > 0.05]
    unsuccessful_reasons = [t.original_reason for t in trades if t.gain_loss_percentage < -0.05]
    
    return {
        'total_trades': total_trades,
        'success_rate': success_rate,
        'avg_profit': avg_profit,
        'outcome_distribution': {k: len(v) for k, v in by_category.items()},
        'successful_patterns': successful_reasons,
        'unsuccessful_patterns': unsuccessful_reasons,
        'profitable_avg_hold': sum(t.hold_duration_days for t in profitable_trades) / len(profitable_trades) if profitable_trades else 0,
        'unprofitable_trades': [t for t in trades if t.gain_loss_percentage <= 0],
    }

def generate_mock_ai_feedback(analysis):
    """Generate mock AI feedback based on analysis"""
    insights = []
    
    if analysis['success_rate'] > 0.6:
        insights.append("Strong overall performance with good trade selection")
    else:
        insights.append("Performance needs improvement - review trade selection criteria")
    
    if analysis['profitable_avg_hold'] < 10:
        insights.append("Successful trades tend to be short-term - consider quick profit-taking")
    else:
        insights.append("Longer holding periods show better results - patience pays off")
    
    # Analyze successful patterns
    successful_patterns = analysis['successful_patterns']
    if 'earnings' in ' '.join(successful_patterns).lower():
        summarizer_feedback = "Focus more on earnings-related news and reports"
    elif 'growth' in ' '.join(successful_patterns).lower():
        summarizer_feedback = "Prioritize growth and expansion stories"
    else:
        summarizer_feedback = "Diversify news sources and look for sector-specific trends"
    
    # Generate decider feedback
    if analysis['avg_profit'] > 0.02:
        decider_feedback = "Current strategy working well - maintain position sizing"
    else:
        decider_feedback = "Consider reducing position sizes and implementing stricter stop-losses"
    
    return {
        "key_insights": insights,
        "summarizer_feedback": summarizer_feedback,
        "decider_feedback": decider_feedback,
        "successful_patterns": analysis['successful_patterns'][:3],
        "unsuccessful_patterns": analysis['unsuccessful_patterns'][:3],
        "recommendations": [
            "Monitor earnings calendars more closely",
            "Implement dynamic position sizing based on volatility",
            "Consider sector rotation strategies"
        ]
    }

def print_performance_summary(analysis, feedback):
    """Print a comprehensive performance summary"""
    print("=" * 60)
    print("🤖 AI TRADING FEEDBACK SYSTEM - DEMONSTRATION")
    print("=" * 60)
    
    print(f"\n📊 PERFORMANCE METRICS")
    print(f"Total Trades: {analysis['total_trades']}")
    print(f"Success Rate: {analysis['success_rate']:.1%}")
    print(f"Average Profit: {analysis['avg_profit']:.2%}")
    print(f"Avg Hold Time (Profitable): {analysis['profitable_avg_hold']:.1f} days")
    
    print(f"\n📈 OUTCOME DISTRIBUTION")
    for category, count in analysis['outcome_distribution'].items():
        percentage = (count / analysis['total_trades']) * 100
        print(f"  {category.replace('_', ' ').title()}: {count} trades ({percentage:.1f}%)")
    
    print(f"\n🎯 AI-GENERATED INSIGHTS")
    for i, insight in enumerate(feedback['key_insights'], 1):
        print(f"  {i}. {insight}")
    
    print(f"\n📝 AGENT FEEDBACK")
    print(f"Summarizer: {feedback['summarizer_feedback']}")
    print(f"Decider: {feedback['decider_feedback']}")
    
    print(f"\n✅ SUCCESSFUL PATTERNS")
    for pattern in feedback['successful_patterns']:
        print(f"  • {pattern}")
    
    print(f"\n❌ PATTERNS TO AVOID")
    for pattern in feedback['unsuccessful_patterns']:
        print(f"  • {pattern}")
    
    print(f"\n💡 RECOMMENDATIONS")
    for rec in feedback['recommendations']:
        print(f"  • {rec}")

def demonstrate_outcome_recording():
    """Demonstrate how trade outcomes are recorded and categorized"""
    print("\n" + "=" * 60)
    print("🔍 TRADE OUTCOME RECORDING DEMONSTRATION")
    print("=" * 60)
    
    sample_trades = create_sample_trades()
    
    print(f"\nRecorded {len(sample_trades)} sample trades:")
    print(f"{'Ticker':<8} {'Purchase':<10} {'Sell':<10} {'Gain/Loss':<12} {'Category':<18} {'Reason'}")
    print("-" * 80)
    
    for trade in sample_trades:
        gain_loss_pct = f"{trade.gain_loss_percentage:.2%}"
        category = trade.outcome_category.replace('_', ' ').title()
        reason = trade.original_reason[:25] + "..." if len(trade.original_reason) > 25 else trade.original_reason
        
        print(f"{trade.ticker:<8} ${trade.purchase_price:<9.2f} ${trade.sell_price:<9.2f} {gain_loss_pct:<12} {category:<18} {reason}")
    
    return sample_trades

def demonstrate_feedback_loop():
    """Demonstrate the complete feedback loop"""
    print("\n" + "=" * 60)
    print("🔄 FEEDBACK LOOP DEMONSTRATION")
    print("=" * 60)
    
    print("\n1. 📈 Collecting trade outcomes...")
    trades = demonstrate_outcome_recording()
    
    print("\n2. 🧮 Analyzing performance patterns...")
    analysis = analyze_performance(trades)
    
    print("\n3. 🤖 Generating AI feedback...")
    feedback = generate_mock_ai_feedback(analysis)
    
    print("\n4. 📋 Performance summary:")
    print_performance_summary(analysis, feedback)
    
    print("\n5. 🔄 How this improves future decisions:")
    print("   • Summarizer agents will focus on earnings-related news")
    print("   • Decider agent will adjust position sizing strategy")
    print("   • Both agents learn from successful/unsuccessful patterns")
    print("   • System continuously improves with each trading cycle")

def main():
    """Main demonstration function"""
    print("🚀 Starting AI Trading Feedback System Demonstration...")
    
    try:
        demonstrate_feedback_loop()
        
        print("\n" + "=" * 60)
        print("✅ SYSTEM STATUS")
        print("=" * 60)
        print("• Outcome tracking: ✓ Active")
        print("• Performance analysis: ✓ Active")
        print("• AI feedback generation: ✓ Active")
        print("• Agent instruction updates: ✓ Ready")
        print("• Dashboard visualization: ✓ Available")
        
        print("\n🎯 NEXT STEPS:")
        print("1. Run actual trading system to generate real data")
        print("2. Monitor performance at http://localhost:8080/feedback")
        print("3. Watch agents improve over time")
        print("4. Analyze trends and patterns in the dashboard")
        
        print(f"\n📚 For more details, see: FEEDBACK_SYSTEM.md")
        
    except Exception as e:
        print(f"❌ Error during demonstration: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())