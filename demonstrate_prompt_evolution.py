#!/usr/bin/env python3
"""
Demonstration script showing prompt evolution with feedback linking
"""

from feedback_agent import TradeOutcomeTracker

def demonstrate_prompt_evolution():
    """Demonstrate the complete prompt evolution workflow"""
    tracker = TradeOutcomeTracker()
    
    print("🔄 Demonstrating Prompt Evolution with Feedback Linking")
    print("=" * 60)
    
    # Step 1: Generate feedback
    print("\n1️⃣ Generating AI feedback for summarizer...")
    feedback_result = tracker.generate_ai_feedback_response(
        'summarizer', 
        {'context': 'demonstration'}, 
        {'performance': 0.6}, 
        True
    )
    
    if feedback_result.get('feedback_id'):
        feedback_id = feedback_result['feedback_id']
        print(f"✅ Generated feedback (ID: {feedback_id})")
        
        # Step 2: Create new prompt based on feedback
        print("\n2️⃣ Creating new prompt based on feedback...")
        
        new_user_prompt = """You are a financial summary agent helping a trading system. Analyze the current market conditions and provide feedback on how to improve news analysis and summarization.

Context Data: {context_data}
Performance Metrics: {performance_metrics}

Please provide:
1. Analysis of current summarization effectiveness
2. Specific recommendations for improving news analysis focus
3. Suggestions for better pattern recognition in financial news
4. Areas where the summarizer should pay more or less attention
5. Tips for identifying market manipulation vs genuine news
6. Concrete examples of successful vs unsuccessful news analysis patterns
7. Specific language patterns and keywords to focus on

Focus on actionable improvements that can be incorporated into the summarizer's analysis approach.
Provide concrete examples and specific language patterns to look for.
Include quantitative metrics when possible."""

        new_system_prompt = """You are an expert financial analyst providing feedback to improve AI news summarization for trading decisions. 
Your analysis should be data-driven, specific, and actionable. Focus on patterns that can help the summarizer agent make better decisions.
Always provide concrete examples and specific recommendations rather than general advice.
Include specific language patterns, keywords, and quantitative metrics when possible."""

        # Save new prompt version linked to the feedback
        version = tracker.save_prompt_version(
            agent_type="summarizer",
            user_prompt=new_user_prompt,
            system_prompt=new_system_prompt,
            description="Enhanced prompt based on AI feedback - includes concrete examples and metrics",
            created_by="demonstration_script",
            triggered_by_feedback_id=feedback_id
        )
        
        print(f"✅ Created prompt version {version} linked to feedback {feedback_id}")
        
        # Step 3: Show the evolution
        print("\n3️⃣ Displaying prompt evolution...")
        prompts = tracker.get_prompt_history('summarizer')
        
        for i, prompt in enumerate(prompts):
            print(f"\n📝 Version {prompt['prompt_version']} ({prompt['timestamp']})")
            print(f"   Status: {'🟢 Active' if prompt['is_active'] else '⚪ Inactive'}")
            print(f"   Description: {prompt['description']}")
            if prompt['triggered_by_feedback_id']:
                print(f"   Triggered by feedback: {prompt['triggered_by_feedback_id']}")
                print(f"   Feedback preview: {prompt['feedback_response'][:100]}...")
            else:
                print("   Triggered by: Initial setup")
            print("-" * 40)
        
        print("\n🎉 Prompt evolution demonstration complete!")
        print("📊 You can now view this in the dashboard under '🔄 Prompt Evolution'")
        
    else:
        print("❌ Failed to generate feedback")

if __name__ == "__main__":
    demonstrate_prompt_evolution() 