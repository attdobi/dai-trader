import json
from datetime import datetime, timedelta
from sqlalchemy import text
from config import engine, PromptManager, session, openai
import yfinance as yf
import pandas as pd

# Performance thresholds
SIGNIFICANT_PROFIT_THRESHOLD = 0.05  # 5% gain considered significant
SIGNIFICANT_LOSS_THRESHOLD = -0.10   # 10% loss considered significant
FEEDBACK_LOOKBACK_DAYS = 30          # Days to look back for outcome analysis

# PromptManager instance
prompt_manager = PromptManager(client=openai, session=session)

class TradeOutcomeTracker:
    """Tracks outcomes of completed trades and provides feedback"""
    
    def __init__(self):
        self.ensure_outcome_tables_exist()
    
    def ensure_outcome_tables_exist(self):
        """Create tables for tracking trade outcomes and feedback"""
        with engine.begin() as conn:
            # Trade outcomes table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS trade_outcomes (
                    id SERIAL PRIMARY KEY,
                    ticker TEXT NOT NULL,
                    sell_timestamp TIMESTAMP NOT NULL,
                    purchase_price FLOAT NOT NULL,
                    sell_price FLOAT NOT NULL,
                    shares FLOAT NOT NULL,
                    gain_loss_amount FLOAT NOT NULL,
                    gain_loss_percentage FLOAT NOT NULL,
                    hold_duration_days INTEGER NOT NULL,
                    original_reason TEXT,
                    sell_reason TEXT,
                    outcome_category TEXT CHECK (outcome_category IN ('significant_profit', 'moderate_profit', 'break_even', 'moderate_loss', 'significant_loss')),
                    market_context JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Agent feedback table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS agent_feedback (
                    id SERIAL PRIMARY KEY,
                    analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    lookback_period_days INTEGER NOT NULL,
                    total_trades_analyzed INTEGER NOT NULL,
                    success_rate FLOAT NOT NULL,
                    avg_profit_percentage FLOAT NOT NULL,
                    top_performing_patterns JSONB,
                    underperforming_patterns JSONB,
                    recommended_adjustments JSONB,
                    summarizer_feedback TEXT,
                    decider_feedback TEXT
                )
            """))
            
            # Agent instruction updates table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS agent_instruction_updates (
                    id SERIAL PRIMARY KEY,
                    agent_type TEXT NOT NULL CHECK (agent_type IN ('summarizer', 'decider')),
                    update_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    original_instructions TEXT NOT NULL,
                    updated_instructions TEXT NOT NULL,
                    reason_for_update TEXT NOT NULL,
                    performance_trigger JSONB
                )
            """))
            
            # AI Agent Feedback Responses table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS ai_agent_feedback_responses (
                    id SERIAL PRIMARY KEY,
                    agent_type TEXT NOT NULL CHECK (agent_type IN ('summarizer', 'decider', 'feedback_analyzer')),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_prompt TEXT NOT NULL,
                    system_prompt TEXT NOT NULL,
                    ai_response TEXT NOT NULL,
                    context_data JSONB,
                    performance_metrics JSONB,
                    feedback_category TEXT,
                    is_manual_request BOOLEAN DEFAULT FALSE
                )
            """))
            
            # AI Agent Prompts table for version control
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS ai_agent_prompts (
                    id SERIAL PRIMARY KEY,
                    agent_type TEXT NOT NULL CHECK (agent_type IN ('summarizer', 'decider', 'feedback_analyzer')),
                    prompt_version INTEGER NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_prompt TEXT NOT NULL,
                    system_prompt TEXT NOT NULL,
                    description TEXT,
                    is_active BOOLEAN DEFAULT FALSE,
                    created_by TEXT DEFAULT 'system',
                    triggered_by_feedback_id INTEGER REFERENCES ai_agent_feedback_responses(id)
                )
            """))
    
    def record_sell_outcome(self, ticker, sell_price, holding_data, sell_reason="Manual sell"):
        """Record the outcome of a sell transaction"""
        purchase_price = float(holding_data['purchase_price'])
        shares = float(holding_data['shares'])
        purchase_timestamp = holding_data.get('purchase_timestamp')
        
        gain_loss_amount = (sell_price - purchase_price) * shares
        gain_loss_percentage = (sell_price - purchase_price) / purchase_price
        
        # Calculate hold duration
        if purchase_timestamp:
            if isinstance(purchase_timestamp, str):
                purchase_date = datetime.fromisoformat(purchase_timestamp.replace('Z', '+00:00'))
            else:
                purchase_date = purchase_timestamp
            hold_duration = (datetime.utcnow() - purchase_date).days
        else:
            hold_duration = 0
        
        # Categorize outcome
        if gain_loss_percentage >= SIGNIFICANT_PROFIT_THRESHOLD:
            outcome_category = 'significant_profit'
        elif gain_loss_percentage > 0:
            outcome_category = 'moderate_profit'
        elif gain_loss_percentage >= -0.02:  # Within 2% is break even
            outcome_category = 'break_even'
        elif gain_loss_percentage >= SIGNIFICANT_LOSS_THRESHOLD:
            outcome_category = 'moderate_loss'
        else:
            outcome_category = 'significant_loss'
        
        # Get market context (simplified)
        market_context = self._get_market_context(ticker)
        
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO trade_outcomes 
                (ticker, sell_timestamp, purchase_price, sell_price, shares, 
                 gain_loss_amount, gain_loss_percentage, hold_duration_days, 
                 original_reason, sell_reason, outcome_category, market_context)
                VALUES (:ticker, :sell_timestamp, :purchase_price, :sell_price, :shares,
                        :gain_loss_amount, :gain_loss_percentage, :hold_duration_days,
                        :original_reason, :sell_reason, :outcome_category, :market_context)
            """), {
                "ticker": ticker,
                "sell_timestamp": datetime.utcnow(),
                "purchase_price": purchase_price,
                "sell_price": sell_price,
                "shares": shares,
                "gain_loss_amount": gain_loss_amount,
                "gain_loss_percentage": gain_loss_percentage,
                "hold_duration_days": hold_duration,
                "original_reason": holding_data.get('reason', ''),
                "sell_reason": sell_reason,
                "outcome_category": outcome_category,
                "market_context": json.dumps(market_context)
            })
        
        print(f"Recorded {outcome_category} outcome for {ticker}: {gain_loss_percentage:.2%} gain/loss")
        return outcome_category
    
    def _get_market_context(self, ticker):
        """Get basic market context at time of sell"""
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d")
            if len(hist) > 1:
                recent_volatility = hist['Close'].pct_change().std()
                return {
                    "recent_volatility": float(recent_volatility) if not pd.isna(recent_volatility) else 0,
                    "volume_trend": "high" if hist['Volume'].iloc[-1] > hist['Volume'].mean() else "normal"
                }
        except:
            pass
        return {"recent_volatility": 0, "volume_trend": "unknown"}
    
    def analyze_recent_outcomes(self, days_back=FEEDBACK_LOOKBACK_DAYS):
        """Analyze recent trade outcomes and generate feedback"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        with engine.connect() as conn:
            # Get recent outcomes
            result = conn.execute(text("""
                SELECT ticker, gain_loss_percentage, outcome_category, 
                       hold_duration_days, original_reason, sell_reason,
                       market_context
                FROM trade_outcomes 
                WHERE sell_timestamp >= :cutoff_date
                ORDER BY sell_timestamp DESC
            """), {"cutoff_date": cutoff_date})
            
            outcomes = [dict(row._mapping) for row in result]
        
        if not outcomes:
            print("No recent trades to analyze")
            return None
        
        # Calculate metrics
        total_trades = len(outcomes)
        profitable_trades = len([o for o in outcomes if o['gain_loss_percentage'] > 0])
        success_rate = profitable_trades / total_trades if total_trades > 0 else 0
        avg_profit = sum(o['gain_loss_percentage'] for o in outcomes) / total_trades
        
        # Analyze patterns
        analysis = self._analyze_patterns(outcomes)
        
        # Generate AI feedback
        feedback = self._generate_ai_feedback(outcomes, success_rate, avg_profit, analysis)
        
        # Store feedback
        feedback_id = self._store_feedback(days_back, total_trades, success_rate, 
                                         avg_profit, analysis, feedback)
        
        return {
            "feedback_id": feedback_id,
            "success_rate": success_rate,
            "avg_profit": avg_profit,
            "total_trades": total_trades,
            "feedback": feedback
        }
    
    def _analyze_patterns(self, outcomes):
        """Analyze patterns in trading outcomes"""
        # Group by outcome category
        by_category = {}
        for outcome in outcomes:
            category = outcome['outcome_category']
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(outcome)
        
        # Analyze reasons for good vs bad outcomes
        good_outcomes = [o for o in outcomes if o['gain_loss_percentage'] > SIGNIFICANT_PROFIT_THRESHOLD]
        bad_outcomes = [o for o in outcomes if o['gain_loss_percentage'] < SIGNIFICANT_LOSS_THRESHOLD]
        
        good_reasons = [o['original_reason'] for o in good_outcomes if o['original_reason']]
        bad_reasons = [o['original_reason'] for o in bad_outcomes if o['original_reason']]
        
        return {
            "outcome_distribution": {k: len(v) for k, v in by_category.items()},
            "successful_reasons": good_reasons,
            "unsuccessful_reasons": bad_reasons,
            "avg_hold_duration_profitable": sum(o['hold_duration_days'] for o in good_outcomes) / len(good_outcomes) if good_outcomes else 0,
            "avg_hold_duration_unprofitable": sum(o['hold_duration_days'] for o in bad_outcomes) / len(bad_outcomes) if bad_outcomes else 0
        }
    
    def _generate_ai_feedback(self, outcomes, success_rate, avg_profit, analysis):
        """Use AI to generate feedback for improving agent performance"""
        outcomes_summary = json.dumps({
            "total_trades": len(outcomes),
            "success_rate": success_rate,
            "avg_profit_percentage": avg_profit,
            "outcome_distribution": analysis["outcome_distribution"],
            "successful_patterns": analysis["successful_reasons"][:5],  # Top 5
            "unsuccessful_patterns": analysis["unsuccessful_reasons"][:5],
            "timing_insights": {
                "profitable_avg_hold_days": analysis["avg_hold_duration_profitable"],
                "unprofitable_avg_hold_days": analysis["avg_hold_duration_unprofitable"]
            }
        }, indent=2)
        
        prompt = f"""
Analyze the following trading performance data and provide specific feedback to improve the performance of our AI trading agents.

Performance Data:
{outcomes_summary}

Please provide:
1. Key insights about what's working well and what isn't
2. Specific recommendations for the SUMMARIZER agents (how they should adjust their news analysis focus)
3. Specific recommendations for the DECIDER agent (how it should adjust its trading strategy)
4. Patterns in successful vs unsuccessful trades
5. Timing and market context insights

Focus on actionable improvements that can be incorporated into agent prompts and decision-making logic.
"""

        system_prompt = """You are a trading performance analyst providing feedback to improve AI trading agents. 
Your analysis should be data-driven, specific, and actionable. Focus on patterns that can help agents make better decisions.

Please provide your response in the following JSON format:
{
    "summarizer_feedback": "Specific recommendations for the summarizer agent",
    "decider_feedback": "Specific recommendations for the decider agent", 
    "key_insights": ["insight 1", "insight 2", "insight 3"]
}"""
        
        try:
            # Get the AI response using the same method as the new feedback system
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]

            response = prompt_manager.client.chat.completions.create(
                model="gpt-4.1",
                messages=messages,
                max_tokens=2000,
                temperature=0.3,
            )
            ai_response = response.choices[0].message.content.strip()
            
            # Parse the response to extract summarizer and decider feedback
            # The AI should provide structured feedback, but we'll handle it gracefully
            try:
                # Try to parse as JSON first
                feedback_data = json.loads(ai_response)
                return feedback_data
            except json.JSONDecodeError:
                # If not JSON, create a structured response from the text
                return {
                    "summarizer_feedback": ai_response,
                    "decider_feedback": ai_response,
                    "key_insights": [ai_response],
                    "raw_response": ai_response
                }
                
        except Exception as e:
            print(f"Failed to generate AI feedback: {e}")
            return {
                "summarizer_feedback": "Unable to generate AI feedback",
                "decider_feedback": "Unable to generate AI feedback",
                "key_insights": []
            }
    
    def _store_feedback(self, lookback_days, total_trades, success_rate, avg_profit, analysis, feedback):
        """Store the generated feedback in the database"""
        with engine.begin() as conn:
            result = conn.execute(text("""
                INSERT INTO agent_feedback 
                (lookback_period_days, total_trades_analyzed, success_rate, avg_profit_percentage,
                 top_performing_patterns, underperforming_patterns, recommended_adjustments,
                 summarizer_feedback, decider_feedback)
                VALUES (:lookback_days, :total_trades, :success_rate, :avg_profit,
                        :top_patterns, :under_patterns, :adjustments, :summarizer_fb, :decider_fb)
                RETURNING id
            """), {
                "lookback_days": lookback_days,
                "total_trades": total_trades,
                "success_rate": success_rate,
                "avg_profit": avg_profit,
                "top_patterns": json.dumps(analysis["successful_reasons"]),
                "under_patterns": json.dumps(analysis["unsuccessful_reasons"]),
                "adjustments": json.dumps(feedback),
                "summarizer_fb": json.dumps(feedback.get("summarizer_feedback", "")),
                "decider_fb": json.dumps(feedback.get("decider_feedback", ""))
            })
            return result.fetchone()[0]
    
    def get_latest_feedback(self):
        """Get the most recent feedback for agent improvement"""
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT summarizer_feedback, decider_feedback, recommended_adjustments,
                       success_rate, avg_profit_percentage, total_trades_analyzed
                FROM agent_feedback 
                ORDER BY analysis_timestamp DESC 
                LIMIT 1
            """))
            row = result.fetchone()
            if row:
                return dict(row._mapping)
            return None
    
    def update_agent_instructions(self, agent_type, new_instructions, reason):
        """Record updates to agent instructions based on feedback"""
        # Get current instructions (this would need to be implemented based on how instructions are stored)
        current_instructions = self._get_current_instructions(agent_type)
        
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO agent_instruction_updates 
                (agent_type, original_instructions, updated_instructions, reason_for_update)
                VALUES (:agent_type, :original, :updated, :reason)
            """), {
                "agent_type": agent_type,
                "original": current_instructions,
                "updated": new_instructions,
                "reason": reason
            })
        
        print(f"Updated {agent_type} instructions based on feedback")
    
    def _get_current_instructions(self, agent_type):
        """Get current instructions for an agent type"""
        # This would need to be implemented based on where instructions are stored
        # For now, return a placeholder
        return f"Current {agent_type} instructions"
    
    def generate_ai_feedback_response(self, agent_type, context_data=None, performance_metrics=None, is_manual_request=False):
        """Generate AI feedback response for a specific agent and store it"""
        
        # Try to get active prompt from database first
        active_prompt = self.get_active_prompt(agent_type)
        
        if active_prompt:
            # Use stored prompts
            user_prompt_template = active_prompt["user_prompt"]
            system_prompt = active_prompt["system_prompt"]
            
            # Format the user prompt with context data
            user_prompt = user_prompt_template.format(
                context_data=json.dumps(context_data, indent=2) if context_data else "No specific context provided",
                performance_metrics=json.dumps(performance_metrics, indent=2) if performance_metrics else "No performance data available"
            )
        else:
            # Fallback to hardcoded prompts (for backward compatibility)
            if agent_type == "summarizer":
                user_prompt_template = """
You are a financial summary agent helping a trading system. Analyze the current market conditions and provide feedback on how to improve news analysis and summarization.

Context Data: {context_data}
Performance Metrics: {performance_metrics}

Please provide:
1. Analysis of current summarization effectiveness
2. Specific recommendations for improving news analysis focus
3. Suggestions for better pattern recognition in financial news
4. Areas where the summarizer should pay more or less attention
5. Tips for identifying market manipulation vs genuine news

Focus on actionable improvements that can be incorporated into the summarizer's analysis approach.
"""
                system_prompt = """You are an expert financial analyst providing feedback to improve AI news summarization for trading decisions. 
Your analysis should be data-driven, specific, and actionable. Focus on patterns that can help the summarizer agent make better decisions."""
                
            elif agent_type == "decider":
                user_prompt_template = """
You are a trading decision-making AI. Analyze the current trading performance and provide feedback on how to improve trading strategy and decision-making.

Context Data: {context_data}
Performance Metrics: {performance_metrics}

Please provide:
1. Analysis of current trading strategy effectiveness
2. Specific recommendations for improving buy/sell decision timing
3. Suggestions for better risk management and position sizing
4. Areas where the decider should be more or less aggressive
5. Tips for identifying optimal entry and exit points

Focus on actionable improvements that can be incorporated into the decider's trading logic.
"""
                system_prompt = """You are an expert trading strategist providing feedback to improve AI trading decisions. 
Your analysis should be data-driven, specific, and actionable. Focus on patterns that can help the decider agent make better decisions."""
                
            elif agent_type == "feedback_analyzer":
                user_prompt_template = """
You are a trading performance analyst. Review the current trading system performance and provide comprehensive feedback for system improvement.

Context Data: {context_data}
Performance Metrics: {performance_metrics}

Please provide:
1. Overall system performance analysis
2. Key strengths and weaknesses identified
3. Specific recommendations for both summarizer and decider agents
4. Market condition analysis and adaptation strategies
5. Long-term improvement suggestions

Focus on comprehensive insights that can guide the entire trading system's evolution.
"""
                system_prompt = """You are a senior trading system analyst providing comprehensive feedback for AI trading system improvement. 
Your analysis should be thorough, data-driven, and provide actionable insights for all system components."""
            
            else:
                raise ValueError(f"Unknown agent type: {agent_type}")
            
            # Format the user prompt
            user_prompt = user_prompt_template.format(
                context_data=json.dumps(context_data, indent=2) if context_data else "No specific context provided",
                performance_metrics=json.dumps(performance_metrics, indent=2) if performance_metrics else "No performance data available"
            )
        
        try:
            # Get the AI response using the same method as summarizer/decider
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            response = prompt_manager.client.chat.completions.create(
                model="gpt-4.1",
                messages=messages,
                max_tokens=2000,
                temperature=0.3,
            )
            ai_response = response.choices[0].message.content.strip()
            
            # Store the response in the database
            feedback_id = self._store_ai_feedback_response(
                agent_type=agent_type,
                user_prompt=user_prompt,
                system_prompt=system_prompt,
                ai_response=ai_response,
                context_data=context_data,
                performance_metrics=performance_metrics,
                is_manual_request=is_manual_request
            )
            
            return {
                "feedback_id": feedback_id,
                "response": ai_response,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Failed to generate AI feedback for {agent_type}: {e}")
            return {
                "error": str(e),
                "response": f"Unable to generate AI feedback for {agent_type}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _store_ai_feedback_response(self, agent_type, user_prompt, system_prompt, ai_response, context_data=None, performance_metrics=None, is_manual_request=False):
        """Store AI feedback response in the database"""
        with engine.begin() as conn:
            result = conn.execute(text("""
                INSERT INTO ai_agent_feedback_responses 
                (agent_type, user_prompt, system_prompt, ai_response, context_data, performance_metrics, is_manual_request)
                VALUES (:agent_type, :user_prompt, :system_prompt, :ai_response, :context_data, :performance_metrics, :is_manual_request)
                RETURNING id
            """), {
                "agent_type": agent_type,
                "user_prompt": user_prompt,
                "system_prompt": system_prompt,
                "ai_response": ai_response,
                "context_data": json.dumps(context_data) if context_data else None,
                "performance_metrics": json.dumps(performance_metrics) if performance_metrics else None,
                "is_manual_request": is_manual_request
            })
            return result.fetchone()[0]
    
    def get_recent_ai_feedback_responses(self, limit=50):
        """Get recent AI feedback responses"""
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, agent_type, timestamp, user_prompt, system_prompt, ai_response, 
                       context_data, performance_metrics, is_manual_request
                FROM ai_agent_feedback_responses 
                ORDER BY timestamp DESC 
                LIMIT :limit
            """), {"limit": limit})
            
            responses = []
            for row in result:
                # Handle context_data - it might be a dict or JSON string
                context_data = None
                if row.context_data:
                    if isinstance(row.context_data, dict):
                        context_data = row.context_data
                    else:
                        try:
                            context_data = json.loads(row.context_data)
                        except (json.JSONDecodeError, TypeError):
                            context_data = str(row.context_data)
                
                # Handle performance_metrics - it might be a dict or JSON string
                performance_metrics = None
                if row.performance_metrics:
                    if isinstance(row.performance_metrics, dict):
                        performance_metrics = row.performance_metrics
                    else:
                        try:
                            performance_metrics = json.loads(row.performance_metrics)
                        except (json.JSONDecodeError, TypeError):
                            performance_metrics = str(row.performance_metrics)
                
                responses.append({
                    "id": row.id,
                    "agent_type": row.agent_type,
                    "timestamp": row.timestamp.isoformat() if row.timestamp else None,
                    "user_prompt": row.user_prompt,
                    "system_prompt": row.system_prompt,
                    "ai_response": row.ai_response,
                    "context_data": context_data,
                    "performance_metrics": performance_metrics,
                    "is_manual_request": row.is_manual_request
                })
            
            return responses
    
    def get_active_prompt(self, agent_type):
        """Get the currently active prompt for an agent type"""
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT user_prompt, system_prompt, prompt_version, description
                FROM ai_agent_prompts 
                WHERE agent_type = :agent_type AND is_active = TRUE
                ORDER BY prompt_version DESC
                LIMIT 1
            """), {"agent_type": agent_type})
            
            row = result.fetchone()
            if row:
                return {
                    "user_prompt": row.user_prompt,
                    "system_prompt": row.system_prompt,
                    "prompt_version": row.prompt_version,
                    "description": row.description
                }
            return None
    
    def save_prompt_version(self, agent_type, user_prompt, system_prompt, description="", created_by="system", triggered_by_feedback_id=None):
        """Save a new version of prompts for an agent type"""
        with engine.begin() as conn:
            # Get the next version number
            result = conn.execute(text("""
                SELECT COALESCE(MAX(prompt_version), 0) + 1 as next_version
                FROM ai_agent_prompts 
                WHERE agent_type = :agent_type
            """), {"agent_type": agent_type})
            
            next_version = result.fetchone().next_version
            
            # Deactivate all existing prompts for this agent
            conn.execute(text("""
                UPDATE ai_agent_prompts 
                SET is_active = FALSE 
                WHERE agent_type = :agent_type
            """), {"agent_type": agent_type})
            
            # Insert new prompt version
            conn.execute(text("""
                INSERT INTO ai_agent_prompts 
                (agent_type, prompt_version, user_prompt, system_prompt, description, is_active, created_by, triggered_by_feedback_id)
                VALUES (:agent_type, :prompt_version, :user_prompt, :system_prompt, :description, TRUE, :created_by, :triggered_by_feedback_id)
            """), {
                "agent_type": agent_type,
                "prompt_version": next_version,
                "user_prompt": user_prompt,
                "system_prompt": system_prompt,
                "description": description,
                "created_by": created_by,
                "triggered_by_feedback_id": triggered_by_feedback_id
            })
            
            return next_version
    
    def get_prompt_history(self, agent_type, limit=10):
        """Get prompt history for an agent type"""
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT p.id, p.prompt_version, p.timestamp, p.user_prompt, p.system_prompt, 
                       p.description, p.is_active, p.created_by, p.triggered_by_feedback_id,
                       f.ai_response as feedback_response
                FROM ai_agent_prompts p
                LEFT JOIN ai_agent_feedback_responses f ON p.triggered_by_feedback_id = f.id
                WHERE p.agent_type = :agent_type
                ORDER BY p.prompt_version DESC 
                LIMIT :limit
            """), {"agent_type": agent_type, "limit": limit})
            
            prompts = []
            for row in result:
                prompts.append({
                    "id": row.id,
                    "prompt_version": row.prompt_version,
                    "timestamp": row.timestamp.isoformat() if row.timestamp else None,
                    "user_prompt": row.user_prompt,
                    "system_prompt": row.system_prompt,
                    "description": row.description,
                    "is_active": row.is_active,
                    "created_by": row.created_by,
                    "triggered_by_feedback_id": row.triggered_by_feedback_id,
                    "feedback_response": row.feedback_response
                })
            
            return prompts

def main():
    """Run feedback analysis on recent trades"""
    tracker = TradeOutcomeTracker()
    
    # Analyze recent outcomes
    feedback_result = tracker.analyze_recent_outcomes()
    
    if feedback_result:
        print(f"\n=== FEEDBACK ANALYSIS ===")
        print(f"Analyzed {feedback_result['total_trades']} recent trades")
        print(f"Success Rate: {feedback_result['success_rate']:.1%}")
        print(f"Average Profit: {feedback_result['avg_profit']:.2%}")
        print(f"\nFeedback stored with ID: {feedback_result['feedback_id']}")
        
        # Print key insights
        feedback = feedback_result['feedback']
        if isinstance(feedback, dict):
            if 'key_insights' in feedback:
                print(f"\nKey Insights: {feedback['key_insights']}")
            if 'summarizer_feedback' in feedback:
                print(f"\nSummarizer Feedback: {feedback['summarizer_feedback']}")
            if 'decider_feedback' in feedback:
                print(f"\nDecider Feedback: {feedback['decider_feedback']}")
    else:
        print("No recent trades found for analysis")

if __name__ == "__main__":
    main()