#!/usr/bin/env python3
"""
Script to initialize default prompts in the database
"""

from feedback_agent import TradeOutcomeTracker

def initialize_default_prompts():
    """Initialize default prompts for all agent types"""
    tracker = TradeOutcomeTracker()
    
    # Default prompts for each agent type
    default_prompts = {
        "summarizer": {
            "user_prompt": """You are a financial summary agent helping a trading system. Analyze the current market conditions and provide feedback on how to improve news analysis and summarization.

Context Data: {context_data}
Performance Metrics: {performance_metrics}

Please provide:
1. Analysis of current summarization effectiveness
2. Specific recommendations for improving news analysis focus
3. Suggestions for better pattern recognition in financial news
4. Areas where the summarizer should pay more or less attention
5. Tips for identifying market manipulation vs genuine news

Focus on actionable improvements that can be incorporated into the summarizer's analysis approach.""",
            "system_prompt": """You are an expert financial analyst providing feedback to improve AI news summarization for trading decisions. 
Your analysis should be data-driven, specific, and actionable. Focus on patterns that can help the summarizer agent make better decisions.""",
            "description": "Default summarizer feedback prompt - focuses on news analysis improvements"
        },
        "decider": {
            "user_prompt": """You are a trading decision-making AI. Analyze the current trading performance and provide feedback on how to improve trading strategy and decision-making.

Context Data: {context_data}
Performance Metrics: {performance_metrics}

Please provide:
1. Analysis of current trading strategy effectiveness
2. Specific recommendations for improving buy/sell decision timing
3. Suggestions for better risk management and position sizing
4. Areas where the decider should be more or less aggressive
5. Tips for identifying optimal entry and exit points

Focus on actionable improvements that can be incorporated into the decider's trading logic.""",
            "system_prompt": """You are an expert trading strategist providing feedback to improve AI trading decisions. 
Your analysis should be data-driven, specific, and actionable. Focus on patterns that can help the decider agent make better decisions.""",
            "description": "Default decider feedback prompt - focuses on trading strategy improvements"
        },
        "feedback_analyzer": {
            "user_prompt": """You are a trading performance analyst. Review the current trading system performance and provide comprehensive feedback for system improvement.

Context Data: {context_data}
Performance Metrics: {performance_metrics}

Please provide:
1. Overall system performance analysis
2. Key strengths and weaknesses identified
3. Specific recommendations for both summarizer and decider agents
4. Market condition analysis and adaptation strategies
5. Long-term improvement suggestions

Focus on comprehensive insights that can guide the entire trading system's evolution.""",
            "system_prompt": """You are a senior trading system analyst providing comprehensive feedback for AI trading system improvement. 
Your analysis should be thorough, data-driven, and provide actionable insights for all system components.""",
            "description": "Default system analysis prompt - comprehensive system-wide feedback"
        }
    }
    
    # Save default prompts for each agent type
    for agent_type, prompt_data in default_prompts.items():
        try:
            version = tracker.save_prompt_version(
                agent_type=agent_type,
                user_prompt=prompt_data["user_prompt"],
                system_prompt=prompt_data["system_prompt"],
                description=prompt_data["description"],
                created_by="system"
            )
            print(f"✅ Initialized {agent_type} prompt (version {version})")
        except Exception as e:
            print(f"❌ Failed to initialize {agent_type} prompt: {e}")
    
    print("\n🎉 Default prompts initialized successfully!")
    print("You can now view and edit prompts through the dashboard.")

if __name__ == "__main__":
    initialize_default_prompts() 