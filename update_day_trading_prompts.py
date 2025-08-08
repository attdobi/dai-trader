#!/usr/bin/env python3
"""
Update prompts with latest day trading improvements
"""

from feedback_agent import TradeOutcomeTracker
from config import PromptManager, session, openai

def update_decider_prompt():
    """Update the decider agent prompt with latest day trading improvements"""
    
    tracker = TradeOutcomeTracker()
    prompt_manager = PromptManager(client=openai, session=session)
    
    # New day trading focused prompt
    new_user_prompt = """
You are an AGGRESSIVE DAY TRADING AI. Make buy/sell recommendations for short-term trading based on the summaries and current portfolio.
Focus on 1-3 day holding periods, maximize ROI through frequent trading. Do not exceed {MAX_TRADES} total trades, never allocate more than ${MAX_FUNDS - MIN_BUFFER} total.
Retain at least ${MIN_BUFFER} in funds.

DAY TRADING STRATEGY:
- Take profits quickly: Sell positions with >3% gains
- Cut losses fast: Sell positions with >5% losses  
- Be aggressive: If you have conviction for a new buy, consider selling existing positions to fund it
- Rotate capital: Don't hold positions too long, look for better opportunities
- Use momentum: Buy stocks with positive news/momentum, sell those with negative news

IMPORTANT: Before making buy decisions, evaluate if you should sell existing positions to free up cash. Consider:
1. Which current positions have gains that can be locked in?
2. Which positions are underperforming and should be cut?
3. Is the new opportunity better than holding current positions?

Performance Context: {feedback_context}

Summaries:
{summarized_text}

Current Holdings (with current prices and gains/losses):
{holdings_text}

Return a JSON list of trade decisions. Each decision should include:
- action ("buy" or "sell")
- ticker
- amount_usd (funds to allocate or recover)
- reason (day trading, profit taking, loss cutting, funding new position, etc)
Respond strictly in valid JSON format with keys.
"""

    new_system_prompt = "You are an aggressive day trading AI focused on short-term gains and capital rotation. Learn from past performance feedback to improve decisions."

    # Save the new prompt version
    version = tracker.save_prompt_version(
        agent_type="decider",
        user_prompt=new_user_prompt,
        system_prompt=new_system_prompt,
        description="Updated with aggressive day trading strategy - profit taking at 3% gains, loss cutting at 5% losses, capital rotation logic",
        created_by="system",
        triggered_by_feedback_id=None
    )
    
    print(f"✅ Updated DeciderAgent prompt to version {version}")
    print("📝 New features:")
    print("   - Aggressive day trading strategy (1-3 day holds)")
    print("   - Quick profit taking (>3% gains)")
    print("   - Fast loss cutting (>5% losses)")
    print("   - Capital rotation logic")
    print("   - Sequential sell-then-buy capability")

def update_summarizer_prompt():
    """Update the summarizer agent prompt to focus on day trading relevant news"""
    
    tracker = TradeOutcomeTracker()
    
    new_user_prompt = """
Analyze the provided financial news content and extract trading-relevant information for day trading decisions.

Focus on:
1. **Immediate Impact News**: Events that could affect stock prices within 1-3 days
2. **Momentum Indicators**: Positive/negative sentiment that could drive short-term price movement
3. **Volume/Volatility Triggers**: News that could increase trading volume or volatility
4. **Sector Rotation**: News affecting entire sectors or market segments
5. **Earnings/Events**: Upcoming catalysts that could move prices quickly

For each piece of news, identify:
- **Ticker symbols** mentioned
- **Short-term impact** (positive/negative/neutral)
- **Time sensitivity** (immediate/1-3 days/week)
- **Confidence level** in the analysis
- **Potential price movement** magnitude

Return a structured analysis with:
- **Headlines**: Key news items with ticker symbols
- **Insights**: Trading implications for day trading strategy
- **Risk factors**: Potential downside or uncertainty
- **Opportunity rating**: 1-10 scale for day trading potential

Focus on actionable insights for aggressive day trading with 1-3 day holding periods.
"""

    new_system_prompt = "You are a financial news analyst specializing in day trading opportunities. Extract actionable insights for short-term trading decisions."

    # Save the new prompt version
    version = tracker.save_prompt_version(
        agent_type="summarizer",
        user_prompt=new_user_prompt,
        system_prompt=new_system_prompt,
        description="Updated for day trading focus - immediate impact news, momentum indicators, short-term catalysts",
        created_by="system",
        triggered_by_feedback_id=None
    )
    
    print(f"✅ Updated SummarizerAgent prompt to version {version}")
    print("📝 New features:")
    print("   - Day trading focused news analysis")
    print("   - Immediate impact assessment")
    print("   - Momentum and volatility indicators")
    print("   - Short-term catalyst identification")

if __name__ == "__main__":
    print("🔄 Updating prompts with latest day trading improvements...")
    
    update_decider_prompt()
    print()
    update_summarizer_prompt()
    
    print("\n🎯 All prompts updated successfully!")
    print("The feedback system will now use the latest day trading strategies.") 