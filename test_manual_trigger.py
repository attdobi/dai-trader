#!/usr/bin/env python3
"""
Test script for manual trigger functionality
"""

import sys
import traceback
from datetime import datetime

def test_manual_summarizer():
    """Test manual summarizer trigger"""
    print("Testing manual summarizer trigger...")
    
    try:
        from d_ai_trader import DAITraderOrchestrator
        
        orchestrator = DAITraderOrchestrator()
        
        # Test the summarizer function
        print("Running summarizer agents...")
        orchestrator.run_summarizer_agents()
        
        print("✅ Manual summarizer trigger test completed")
        return True
        
    except Exception as e:
        print(f"❌ Manual summarizer trigger test failed: {e}")
        traceback.print_exc()
        return False

def test_manual_decider():
    """Test manual decider trigger"""
    print("\nTesting manual decider trigger...")
    
    try:
        from d_ai_trader import DAITraderOrchestrator
        
        orchestrator = DAITraderOrchestrator()
        
        # Test the decider function
        print("Running decider agent...")
        orchestrator.run_decider_agent()
        
        print("✅ Manual decider trigger test completed")
        return True
        
    except Exception as e:
        print(f"❌ Manual decider trigger test failed: {e}")
        traceback.print_exc()
        return False

def test_manual_feedback():
    """Test manual feedback trigger"""
    print("\nTesting manual feedback trigger...")
    
    try:
        from d_ai_trader import DAITraderOrchestrator
        
        orchestrator = DAITraderOrchestrator()
        
        # Test the feedback function
        print("Running feedback agent...")
        orchestrator.run_feedback_agent()
        
        print("✅ Manual feedback trigger test completed")
        return True
        
    except Exception as e:
        print(f"❌ Manual feedback trigger test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run manual trigger tests"""
    print("Manual Trigger Test")
    print("=" * 50)
    
    tests = [
        test_manual_summarizer,
        test_manual_decider,
        test_manual_feedback
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
    print(f"Manual Trigger Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All manual trigger tests passed! Dashboard buttons should work.")
        return True
    else:
        print("⚠️  Some manual trigger tests failed. Check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 