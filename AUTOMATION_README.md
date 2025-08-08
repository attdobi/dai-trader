# D-AI-Trader Automation System

This document describes the unified automation system for the D-AI-Trader project.

## Overview

The `d-ai-trader.py` script orchestrates the entire trading system with intelligent scheduling based on market hours and trading requirements.

## System Components

### 1. Summarizer Agents (`main.py`)
- **Purpose**: Scrape financial news from multiple sources and generate AI summaries
- **Schedule**: 
  - Weekdays: Every hour from 8:25 AM to 5:25 PM ET
  - Weekends: Once daily at 3:00 PM ET
- **Sources**: CNBC, CNN Money, Bloomberg, Fox Business, Yahoo Finance

### 2. Decider Agent (`decider_agent.py`)
- **Purpose**: Analyze summaries and make trading decisions
- **Schedule**: Every 30 minutes during market hours (9:30 AM - 4:00 PM ET, M-F)
- **Key Feature**: Processes ALL unseen summaries, not just the latest batch
- **Output**: Buy/sell decisions with reasoning

### 3. Feedback Agent (`feedback_agent.py`)
- **Purpose**: Analyze trading performance and provide feedback for improvement
- **Schedule**: Once daily at 4:30 PM ET (after market close)
- **Output**: Performance analysis and recommendations for system improvement

## Key Features

### Intelligent Summary Processing
- The decider agent now processes all summaries that haven't been seen before
- This means Monday morning decisions will include Friday evening, weekend, and Monday morning data
- Prevents information loss and ensures comprehensive analysis

### Market Hours Awareness
- System automatically detects market open/close times
- Summarizers run during extended hours (8:25 AM - 5:25 PM ET)
- Decider only runs during actual market hours (9:30 AM - 4:00 PM ET)
- Feedback runs after market close

### Robust Error Handling
- Comprehensive logging to `d-ai-trader.log`
- Database tracking of all system runs
- Automatic retry mechanisms
- Graceful failure handling

### Database Integration
- Tracks processed summaries to avoid duplicates
- Records system run history and status
- Maintains portfolio snapshots
- Stores trading decisions and outcomes

## Installation and Setup

### Prerequisites
- Python 3.9+
- PostgreSQL database
- Chrome browser (for web scraping)
- OpenAI API key

### Quick Start
1. **Clone the repository** (if not already done)
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure database** in `config.py`
4. **Set up environment variables**:
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```
5. **Start the system**:
   ```bash
   ./start_d_ai_trader.sh
   ```

### Manual Start
```bash
# Activate virtual environment
source dai/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the automation system
python3 d-ai-trader.py
```

## Database Schema

### New Tables Added
- `processed_summaries`: Tracks which summaries have been processed by each agent
- `system_runs`: Records all system runs with status and timing information

### Existing Tables Enhanced
- `summaries`: Now linked to processing status
- `holdings`: Enhanced with processing tracking
- `trade_decisions`: Enhanced with run tracking

## Scheduling Details

### Weekday Schedule (Monday - Friday)
- **8:25 AM ET**: First summarizer run
- **9:30 AM ET**: Market opens, decider starts running
- **Every hour at :25**: Summarizer agents run
- **Every 30 minutes**: Decider agent runs (during market hours)
- **4:00 PM ET**: Market closes, decider stops
- **4:30 PM ET**: Feedback agent runs
- **5:25 PM ET**: Last summarizer run

### Weekend Schedule (Saturday - Sunday)
- **3:00 PM ET**: Single summarizer run
- **No decider or feedback runs** (market closed)

## Monitoring and Logging

### Log Files
- `d-ai-trader.log`: Main system log with detailed information
- Console output: Real-time status updates

### Database Monitoring
```sql
-- Check recent system runs
SELECT run_type, start_time, end_time, status 
FROM system_runs 
ORDER BY start_time DESC 
LIMIT 10;

-- Check unprocessed summaries
SELECT COUNT(*) as unprocessed_count 
FROM summaries s
LEFT JOIN processed_summaries ps ON s.id = ps.summary_id AND ps.processed_by = 'decider'
WHERE ps.summary_id IS NULL;
```

### Dashboard
The existing dashboard server (`dashboard_server.py`) continues to work and shows:
- Portfolio performance
- Trading history
- Recent summaries
- System status

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check PostgreSQL is running
   - Verify connection string in `config.py`
   - Ensure database exists

2. **Chrome/Selenium Issues**
   - Update Chrome browser
   - Check ChromeDriver compatibility
   - Verify headless mode settings

3. **API Rate Limits**
   - Check OpenAI API usage
   - Verify API key is valid
   - Monitor rate limit headers

4. **Scheduling Issues**
   - Verify timezone settings
   - Check system clock
   - Review log files for timing errors

### Debug Mode
To run in debug mode with more verbose logging:
```bash
python3 -u d-ai-trader.py 2>&1 | tee debug.log
```

## Configuration

### Timezone Settings
The system uses US Eastern Time (ET) for all scheduling. To change timezone:
1. Modify `ET_TIMEZONE` in `d-ai-trader.py`
2. Update market hours constants
3. Adjust scheduling logic

### Market Hours
Current market hours are hardcoded but can be modified:
- Market Open: 9:30 AM ET
- Market Close: 4:00 PM ET
- Summarizer Start: 8:25 AM ET
- Summarizer End: 5:25 PM ET

### Trading Parameters
Trading limits are configured in `decider_agent.py`:
- `MAX_TRADES`: Maximum trades per decision cycle
- `MAX_FUNDS`: Maximum funds to allocate
- `MIN_BUFFER`: Minimum cash to maintain

## Performance Considerations

### Resource Usage
- **Memory**: ~500MB base, increases with screenshot storage
- **CPU**: Moderate during summarizer runs, low during idle
- **Storage**: Screenshots accumulate over time (consider cleanup)
- **Network**: Regular API calls to OpenAI and financial data sources

### Optimization Tips
1. **Screenshot Cleanup**: Implement periodic cleanup of old screenshots
2. **Database Maintenance**: Regular VACUUM and ANALYZE
3. **Log Rotation**: Implement log rotation for long-running systems
4. **API Caching**: Consider caching frequently accessed data

## Security Considerations

1. **API Keys**: Store securely, never commit to version control
2. **Database**: Use strong passwords and limit access
3. **Network**: Consider VPN for production deployments
4. **Monitoring**: Implement alerts for system failures

## Future Enhancements

1. **Web Interface**: Real-time monitoring dashboard
2. **Alert System**: Email/SMS notifications for important events
3. **Backtesting**: Historical performance analysis
4. **Risk Management**: Enhanced position sizing and stop-loss
5. **Multi-Strategy**: Support for different trading strategies

## Support

For issues or questions:
1. Check the log files first
2. Review this documentation
3. Check the main README.md for general project information
4. Review the FEEDBACK_SYSTEM.md for feedback system details 