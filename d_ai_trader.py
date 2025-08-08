#!/usr/bin/env python3
"""
D-AI-Trader Unified Automation System

This script orchestrates the entire trading system:
- Summarizer agents run hourly during market hours (8:25am-5:25pm ET) and once daily on weekends (3pm ET)
- Decider agent runs during market hours (9:30am-4pm ET) using all unseen summaries
- Feedback agent runs once daily after the final decider run
"""

import os
import sys
import time
import json
import schedule
import logging
from datetime import datetime, timedelta
import pytz
from sqlalchemy import text
from config import engine, PromptManager, session, openai
from feedback_agent import TradeOutcomeTracker

# Import the existing modules
import main as summarizer_main
import decider_agent as decider
import feedback_agent as feedback_agent_module

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('d-ai-trader.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Timezone configuration
PACIFIC_TIMEZONE = pytz.timezone('US/Pacific')
EASTERN_TIMEZONE = pytz.timezone('US/Eastern')

# Market hours configuration (Eastern Time - market hours are always ET)
MARKET_OPEN_TIME = "09:30"
MARKET_CLOSE_TIME = "16:00"
SUMMARIZER_START_TIME = "08:25"
SUMMARIZER_END_TIME = "17:25"
WEEKEND_SUMMARIZER_TIME = "15:00"  # 3pm ET

class DAITraderOrchestrator:
    def __init__(self):
        self.feedback_tracker = TradeOutcomeTracker()
        self.prompt_manager = PromptManager(client=openai, session=session)
        self.last_processed_summary_id = None
        self.initialize_database()
        
    def initialize_database(self):
        """Initialize database tables for tracking processed summaries"""
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS processed_summaries (
                    id SERIAL PRIMARY KEY,
                    summary_id INTEGER NOT NULL,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_by TEXT NOT NULL,
                    run_id TEXT
                )
            """))
            
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS system_runs (
                    id SERIAL PRIMARY KEY,
                    run_type TEXT NOT NULL,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    status TEXT DEFAULT 'running',
                    details JSONB
                )
            """))
    
    def is_market_open(self):
        """Check if the market is currently open (M-F, 9:30am-4pm ET)"""
        # Get current time in Pacific, convert to Eastern for market hours check
        now_pacific = datetime.now(PACIFIC_TIMEZONE)
        now_eastern = now_pacific.astimezone(EASTERN_TIMEZONE)
        
        # Check if it's a weekday (Monday = 0, Sunday = 6)
        if now_eastern.weekday() >= 5:  # Saturday or Sunday
            return False
            
        # Check if it's within market hours (Eastern Time)
        market_open = now_eastern.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now_eastern.replace(hour=16, minute=0, second=0, microsecond=0)
        
        return market_open <= now_eastern <= market_close
    
    def is_summarizer_time(self):
        """Check if it's time to run summarizers"""
        # Get current time in Pacific, convert to Eastern for time checks
        now_pacific = datetime.now(PACIFIC_TIMEZONE)
        now_eastern = now_pacific.astimezone(EASTERN_TIMEZONE)
        
        # Weekday summarizer hours (8:25am-5:25pm ET)
        if now_eastern.weekday() < 5:  # Monday to Friday
            summarizer_start = now_eastern.replace(hour=8, minute=25, second=0, microsecond=0)
            summarizer_end = now_eastern.replace(hour=17, minute=25, second=0, microsecond=0)
            return summarizer_start <= now_eastern <= summarizer_end
        
        # Weekend summarizer (3pm ET)
        else:
            weekend_time = now_eastern.replace(hour=15, minute=0, second=0, microsecond=0)
            return abs((now_eastern - weekend_time).total_seconds()) < 300  # Within 5 minutes of 3pm
    
    def is_decider_time(self):
        """Check if it's time to run decider (market hours only)"""
        return self.is_market_open()
    
    def is_feedback_time(self):
        """Check if it's time to run feedback (after market close)"""
        # Get current time in Pacific, convert to Eastern for time checks
        now_pacific = datetime.now(PACIFIC_TIMEZONE)
        now_eastern = now_pacific.astimezone(EASTERN_TIMEZONE)
        
        # Only on weekdays
        if now_eastern.weekday() >= 5:
            return False
            
        # After market close (4pm ET)
        market_close = now_eastern.replace(hour=16, minute=0, second=0, microsecond=0)
        feedback_window_end = now_eastern.replace(hour=17, minute=0, second=0, microsecond=0)
        
        return market_close <= now_eastern <= feedback_window_end
    
    def get_unprocessed_summaries(self):
        """Get all summaries that haven't been processed by the decider yet"""
        with engine.connect() as conn:
            # Get all summaries that haven't been processed
            result = conn.execute(text("""
                SELECT s.id, s.agent, s.timestamp, s.run_id, s.data
                FROM summaries s
                LEFT JOIN processed_summaries ps ON s.id = ps.summary_id AND ps.processed_by = 'decider'
                WHERE ps.summary_id IS NULL
                ORDER BY s.timestamp ASC
            """))
            return [row._mapping for row in result]
    
    def mark_summaries_processed(self, summary_ids, processed_by):
        """Mark summaries as processed"""
        with engine.begin() as conn:
            for summary_id in summary_ids:
                conn.execute(text("""
                    INSERT INTO processed_summaries (summary_id, processed_by, run_id)
                    VALUES (:summary_id, :processed_by, :run_id)
                """), {
                    "summary_id": summary_id,
                    "processed_by": processed_by,
                    "run_id": datetime.now().strftime("%Y%m%dT%H%M%S")
                })
    
    def run_summarizer_agents(self):
        """Run the summarizer agents"""
        # Create both the internal run_id and the timestamp for main.py
        internal_run_id = f"summarizer_{datetime.now().strftime('%Y%m%dT%H%M%S')}"
        timestamp = datetime.now().strftime('%Y%m%dT%H%M%S')
        logger.info(f"Starting summarizer agents run: {internal_run_id}")
        
        try:
            # Record run start
            with engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO system_runs (run_type, details)
                    VALUES ('summarizer', :details)
                """), {
                    "details": json.dumps({"run_id": internal_run_id, "timestamp": datetime.now().isoformat()})
                })
            
            # Run the summarizer agents with the correct timestamp format
            summarizer_main.RUN_TIMESTAMP = timestamp
            summarizer_main.RUN_DIR = os.path.join(summarizer_main.SCREENSHOT_DIR, timestamp)
            os.makedirs(summarizer_main.RUN_DIR, exist_ok=True)
            summarizer_main.run_summary_agents()
            
            logger.info(f"Summarizer agents completed successfully: {internal_run_id}")
            
            # Update run status
            with engine.begin() as conn:
                conn.execute(text("""
                    UPDATE system_runs 
                    SET end_time = CURRENT_TIMESTAMP, status = 'completed'
                    WHERE run_type = 'summarizer' AND details->>'run_id' = :run_id
                """), {"run_id": internal_run_id})
                
        except Exception as e:
            logger.error(f"Error running summarizer agents: {e}")
            # Update run status to failed
            with engine.begin() as conn:
                conn.execute(text("""
                    UPDATE system_runs 
                    SET end_time = CURRENT_TIMESTAMP, status = 'failed'
                    WHERE run_type = 'summarizer' AND details->>'run_id' = :run_id
                """), {"run_id": internal_run_id})
    
    def run_decider_agent(self):
        """Run the decider agent with all unprocessed summaries"""
        run_id = f"decider_{datetime.now().strftime('%Y%m%dT%H%M%S')}"
        logger.info(f"Starting decider agent run: {run_id}")
        
        try:
            # Record run start
            with engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO system_runs (run_type, details)
                    VALUES ('decider', :details)
                """), {
                    "details": json.dumps({"run_id": run_id, "timestamp": datetime.now().isoformat()})
                })
            
            # Get unprocessed summaries
            unprocessed_summaries = self.get_unprocessed_summaries()
            
            if not unprocessed_summaries:
                logger.info("No unprocessed summaries found for decider")
                return
            
            logger.info(f"Found {len(unprocessed_summaries)} unprocessed summaries")
            
            # Create a mock run_id for the decider to use
            # We'll use the latest timestamp from the summaries
            latest_timestamp = max(s['timestamp'] for s in unprocessed_summaries)
            mock_run_id = latest_timestamp.strftime("%Y%m%dT%H%M%S")
            
            # Temporarily override the get_latest_run_id function
            original_get_latest_run_id = decider.get_latest_run_id
            
            def mock_get_latest_run_id():
                return mock_run_id
            
            decider.get_latest_run_id = mock_get_latest_run_id
            
            # Update current prices before making decisions
            decider.update_all_current_prices()
            
            # Run the decider agent
            summaries = unprocessed_summaries
            holdings = decider.fetch_holdings()
            decisions = decider.ask_decision_agent(summaries, mock_run_id, holdings)
            decider.store_trade_decisions(decisions, mock_run_id)
            decider.update_holdings(decisions)
            decider.record_portfolio_snapshot()
            
            # Mark summaries as processed
            summary_ids = [s['id'] for s in unprocessed_summaries]
            self.mark_summaries_processed(summary_ids, 'decider')
            
            # Restore original function
            decider.get_latest_run_id = original_get_latest_run_id
            
            logger.info(f"Decider agent completed successfully: {run_id}")
            
            # Update run status
            with engine.begin() as conn:
                conn.execute(text("""
                    UPDATE system_runs 
                    SET end_time = CURRENT_TIMESTAMP, status = 'completed'
                    WHERE run_type = 'decider' AND details->>'run_id' = :run_id
                """), {"run_id": run_id})
                
        except Exception as e:
            logger.error(f"Error running decider agent: {e}")
            # Update run status to failed
            with engine.begin() as conn:
                conn.execute(text("""
                    UPDATE system_runs 
                    SET end_time = CURRENT_TIMESTAMP, status = 'failed'
                    WHERE run_type = 'decider' AND details->>'run_id' = :run_id
                """), {"run_id": run_id})
    
    def run_feedback_agent(self):
        """Run the feedback agent for daily analysis"""
        run_id = f"feedback_{datetime.now().strftime('%Y%m%dT%H%M%S')}"
        logger.info(f"Starting feedback agent run: {run_id}")
        
        try:
            # Record run start
            with engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO system_runs (run_type, details)
                    VALUES ('feedback', :details)
                """), {
                    "details": json.dumps({"run_id": run_id, "timestamp": datetime.now().isoformat()})
                })
            
            # Run the feedback analysis
            feedback_tracker = TradeOutcomeTracker()
            feedback_tracker.analyze_recent_outcomes()
            
            logger.info(f"Feedback agent completed successfully: {run_id}")
            
            # Update run status
            with engine.begin() as conn:
                conn.execute(text("""
                    UPDATE system_runs 
                    SET end_time = CURRENT_TIMESTAMP, status = 'completed'
                    WHERE run_type = 'feedback' AND details->>'run_id' = :run_id
                """), {"run_id": run_id})
                
        except Exception as e:
            logger.error(f"Error running feedback agent: {e}")
            # Update run status to failed
            with engine.begin() as conn:
                conn.execute(text("""
                    UPDATE system_runs 
                    SET end_time = CURRENT_TIMESTAMP, status = 'failed'
                    WHERE run_type = 'feedback' AND details->>'run_id' = :run_id
                """), {"run_id": run_id})
    
    def scheduled_summarizer_job(self):
        """Scheduled job for summarizer agents"""
        if self.is_summarizer_time():
            logger.info("Running scheduled summarizer job")
            self.run_summarizer_agents()
        else:
            logger.info("Skipping summarizer job - outside of scheduled time")
    
    def scheduled_decider_job(self):
        """Scheduled job for decider agent"""
        if self.is_decider_time():
            logger.info("Running scheduled decider job")
            self.run_decider_agent()
        else:
            logger.info("Skipping decider job - market is closed")
    
    def scheduled_feedback_job(self):
        """Scheduled job for feedback agent"""
        if self.is_feedback_time():
            logger.info("Running scheduled feedback job")
            self.run_feedback_agent()
        else:
            logger.info("Skipping feedback job - outside of scheduled time")
    
    def setup_schedule(self):
        """Setup the scheduling for all jobs"""
        # Summarizer agents - every hour during market hours and once daily on weekends
        schedule.every().hour.at(":25").do(self.scheduled_summarizer_job)  # Every hour at :25
        
        # Decider agent - every 30 minutes during market hours
        schedule.every(30).minutes.do(self.scheduled_decider_job)
        
        # Feedback agent - once daily after market close
        schedule.every().day.at("16:30").do(self.scheduled_feedback_job)  # 4:30pm ET
        
        logger.info("Schedule setup completed")
        logger.info("Summarizer agents: Every hour at :25")
        logger.info("Decider agent: Every 30 minutes during market hours")
        logger.info("Feedback agent: Daily at 4:30pm ET")
    
    def run(self):
        """Main run loop"""
        logger.info("Starting D-AI-Trader automation system")
        self.setup_schedule()
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("Shutting down D-AI-Trader automation system")
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
            raise

def main():
    """Main entry point"""
    orchestrator = DAITraderOrchestrator()
    orchestrator.run()

if __name__ == "__main__":
    main() 