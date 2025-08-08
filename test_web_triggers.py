#!/usr/bin/env python3
"""
Test script to verify web app triggers are working correctly
"""

import os
import sys
import time
from datetime import datetime

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_summarizer_trigger():
    """Test the summarizer trigger functionality"""
    print("Testing summarizer trigger...")
    
    try:
        from d_ai_trader import DAITraderOrchestrator
        orchestrator = DAITraderOrchestrator()
        
        # Test the summarizer agents
        print("Running summarizer agents...")
        orchestrator.run_summarizer_agents()
        print("Summarizer agents completed successfully")
        
        return True
    except Exception as e:
        print(f"Error testing summarizer trigger: {e}")
        return False

def test_decider_trigger():
    """Test the decider trigger functionality"""
    print("Testing decider trigger...")
    
    try:
        from d_ai_trader import DAITraderOrchestrator
        orchestrator = DAITraderOrchestrator()
        
        # Test the decider agent
        print("Running decider agent...")
        orchestrator.run_decider_agent()
        print("Decider agent completed successfully")
        
        return True
    except Exception as e:
        print(f"Error testing decider trigger: {e}")
        return False

def test_screenshot_saving():
    """Test that screenshots are being saved correctly"""
    print("Testing screenshot saving...")
    
    try:
        # Check if screenshots directory exists and has recent content
        screenshot_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
        if not os.path.exists(screenshot_dir):
            print(f"Screenshot directory does not exist: {screenshot_dir}")
            return False
        
        # Check for recent screenshot directories
        current_time = datetime.now()
        recent_dirs = []
        
        for item in os.listdir(screenshot_dir):
            item_path = os.path.join(screenshot_dir, item)
            if os.path.isdir(item_path) and item.startswith("2025"):
                try:
                    # Parse timestamp from directory name
                    dir_time = datetime.strptime(item, "%Y%m%dT%H%M%S")
                    if (current_time - dir_time).total_seconds() < 3600:  # Within last hour
                        recent_dirs.append(item)
                except:
                    continue
        
        print(f"Found {len(recent_dirs)} recent screenshot directories: {recent_dirs}")
        
        # Check if any recent directories have PNG files
        png_files_found = False
        for recent_dir in recent_dirs:
            dir_path = os.path.join(screenshot_dir, recent_dir)
            png_files = [f for f in os.listdir(dir_path) if f.endswith('.png')]
            if png_files:
                print(f"Found {len(png_files)} PNG files in {recent_dir}: {png_files}")
                png_files_found = True
        
        if not png_files_found:
            print("No PNG files found in recent screenshot directories")
            return False
        
        return True
    except Exception as e:
        print(f"Error testing screenshot saving: {e}")
        return False

def main():
    """Run all tests"""
    print("Starting web trigger tests...")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Script directory: {os.path.dirname(os.path.abspath(__file__))}")
    
    # Test screenshot saving first
    screenshot_test = test_screenshot_saving()
    print(f"Screenshot saving test: {'PASSED' if screenshot_test else 'FAILED'}")
    
    # Test summarizer trigger
    summarizer_test = test_summarizer_trigger()
    print(f"Summarizer trigger test: {'PASSED' if summarizer_test else 'FAILED'}")
    
    # Test decider trigger
    decider_test = test_decider_trigger()
    print(f"Decider trigger test: {'PASSED' if decider_test else 'FAILED'}")
    
    print("\nTest Summary:")
    print(f"- Screenshot saving: {'✓' if screenshot_test else '✗'}")
    print(f"- Summarizer trigger: {'✓' if summarizer_test else '✗'}")
    print(f"- Decider trigger: {'✓' if decider_test else '✗'}")
    
    if all([screenshot_test, summarizer_test, decider_test]):
        print("\nAll tests PASSED! The web app triggers should work correctly.")
    else:
        print("\nSome tests FAILED. Check the output above for details.")

if __name__ == "__main__":
    main() 