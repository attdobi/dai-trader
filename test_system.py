#!/usr/bin/env python3
"""
Test script for D-AI-Trader automation system
"""

import sys
import traceback
from datetime import datetime

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    
    try:
        from d_ai_trader import DAITraderOrchestrator
        print("✅ DAITraderOrchestrator imported successfully")
    except Exception as e:
        print(f"❌ Failed to import DAITraderOrchestrator: {e}")
        return False
    
    try:
        import main as summarizer_main
        print("✅ Summarizer main module imported successfully")
    except Exception as e:
        print(f"❌ Failed to import summarizer main: {e}")
        return False
    
    try:
        import decider_agent as decider
        print("✅ Decider agent module imported successfully")
    except Exception as e:
        print(f"❌ Failed to import decider agent: {e}")
        return False
    
    try:
        from feedback_agent import TradeOutcomeTracker
        print("✅ Feedback agent module imported successfully")
    except Exception as e:
        print(f"❌ Failed to import feedback agent: {e}")
        return False
    
    return True

def test_database():
    """Test database connectivity and tables"""
    print("\nTesting database...")
    
    try:
        from config import engine
        from sqlalchemy import text
        
        with engine.connect() as conn:
            # Test basic connection
            conn.execute(text('SELECT 1'))
            print("✅ Database connection successful")
            
            # Test if required tables exist
            tables = ['summaries', 'holdings', 'trade_decisions', 'portfolio_history']
            for table in tables:
                try:
                    conn.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
                    print(f"✅ Table '{table}' exists")
                except Exception as e:
                    print(f"⚠️  Table '{table}' may not exist: {e}")
            
            # Test new tables for automation system
            automation_tables = ['processed_summaries', 'system_runs']
            for table in automation_tables:
                try:
                    conn.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
                    print(f"✅ Automation table '{table}' exists")
                except Exception as e:
                    print(f"⚠️  Automation table '{table}' may not exist: {e}")
                    
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False
    
    return True

def test_orchestrator():
    """Test the orchestrator initialization"""
    print("\nTesting orchestrator...")
    
    try:
        from d_ai_trader import DAITraderOrchestrator
        
        orchestrator = DAITraderOrchestrator()
        print("✅ Orchestrator initialized successfully")
        
        # Test time checking functions
        print(f"Market open: {orchestrator.is_market_open()}")
        print(f"Summarizer time: {orchestrator.is_summarizer_time()}")
        print(f"Decider time: {orchestrator.is_decider_time()}")
        print(f"Feedback time: {orchestrator.is_feedback_time()}")
        
        # Test unprocessed summaries function
        unprocessed = orchestrator.get_unprocessed_summaries()
        print(f"Unprocessed summaries: {len(unprocessed)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Orchestrator test failed: {e}")
        traceback.print_exc()
        return False

def test_scheduling():
    """Test scheduling functionality"""
    print("\nTesting scheduling...")
    
    try:
        import schedule
        
        # Test basic scheduling
        def test_job():
            print("Test job executed")
        
        schedule.every(1).seconds.do(test_job)
        print("✅ Schedule library working")
        
        return True
        
    except Exception as e:
        print(f"❌ Scheduling test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("D-AI-Trader System Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_database,
        test_orchestrator,
        test_scheduling
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready to run.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 