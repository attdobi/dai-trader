#!/usr/bin/env python3
"""
Example script showing how to update prompts
"""

from feedback_agent import TradeOutcomeTracker

def update_summarizer_prompt():
    """Example of updating the summarizer prompt"""
    tracker = TradeOutcomeTracker()
    
    # New improved prompt
    new_user_prompt = """You are a financial summary agent helping a trading system. Analyze the current market conditions and provide feedback on how to improve news analysis and summarization.

Context Data: {context_data}
Performance Metrics: {performance_metrics}

Please provide:
1. Analysis of current summarization effectiveness
2. Specific recommendations for improving news analysis focus
3. Suggestions for better pattern recognition in financial news
4. Areas where the summarizer should pay more or less attention
5. Tips for identifying market manipulation vs genuine news
6. Specific examples of successful vs unsuccessful news analysis patterns

Focus on actionable improvements that can be incorporated into the summarizer's analysis approach.
Provide concrete examples and specific language patterns to look for."""

    new_system_prompt = """You are an expert financial analyst providing feedback to improve AI news summarization for trading decisions. 
Your analysis should be data-driven, specific, and actionable. Focus on patterns that can help the summarizer agent make better decisions.
Always provide concrete examples and specific recommendations rather than general advice."""

    try:
        version = tracker.save_prompt_version(
            agent_type="summarizer",
            user_prompt=new_user_prompt,
            system_prompt=new_system_prompt,
            description="Enhanced summarizer prompt with more specific guidance and examples",
            created_by="example_script"
        )
        print(f"✅ Updated summarizer prompt to version {version}")
        
        # Test the new prompt
        result = tracker.generate_ai_feedback_response('summarizer', {'test': 'enhanced'}, {'test_metric': 0.7}, True)
        print(f"✅ Generated feedback with new prompt (ID: {result.get('feedback_id')})")
        
    except Exception as e:
        print(f"❌ Failed to update prompt: {e}")

if __name__ == "__main__":
    print("🔄 Updating summarizer prompt...")
    update_summarizer_prompt()
    print("\n📝 You can now view the updated prompts in the dashboard!") 