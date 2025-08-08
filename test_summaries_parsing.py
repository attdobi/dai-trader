#!/usr/bin/env python3
"""
Test script to verify summaries parsing logic
"""

import json
from config import engine
from sqlalchemy import text

def test_summaries_parsing():
    """Test the summaries parsing logic"""
    print("Testing summaries parsing...")
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT * FROM summaries 
            WHERE data::text NOT LIKE '%%API error, no response%%'
            ORDER BY id DESC LIMIT 5
        """)).fetchall()

        summaries = []
        for row in result:
            try:
                # Parse the outer JSON structure
                outer = json.loads(row.data)
                summary_data = outer.get("summary", {})
                
                # Handle case where summary_data might be a string or dict
                if isinstance(summary_data, str):
                    try:
                        summary_data = json.loads(summary_data)
                    except json.JSONDecodeError:
                        # If it's not JSON, treat it as plain text
                        summary_data = {"headlines": [], "insights": summary_data}
                elif not isinstance(summary_data, dict):
                    summary_data = {"headlines": [], "insights": str(summary_data)}

                summary = {
                    "agent": row.agent,
                    "timestamp": row.timestamp,
                    "headlines": summary_data.get("headlines", []),
                    "insights": summary_data.get("insights", "")
                }
                
                summaries.append(summary)
                print(f"✓ Successfully parsed {row.agent}")
                print(f"  Headlines: {len(summary['headlines'])} items")
                print(f"  Insights length: {len(summary['insights'])} chars")
                print(f"  First headline: {summary['headlines'][0] if summary['headlines'] else 'None'}")
                print()
                
            except Exception as e:
                print(f"✗ Failed to parse summary row {row.id}: {e}")
                print(f"Raw data: {row.data[:200]}...")
                print()
                continue

        print(f"Successfully parsed {len(summaries)} out of {len(result)} summaries")
        return len(summaries) > 0

if __name__ == "__main__":
    success = test_summaries_parsing()
    if success:
        print("✓ Summaries parsing test PASSED!")
    else:
        print("✗ Summaries parsing test FAILED!") 