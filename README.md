# AI-Powered Trading System with Automated Execution

An intelligent trading system that uses AI agents to analyze financial news from multiple sources, make trading decisions, and track portfolio performance with comprehensive profit/loss monitoring. **Now with full automation and intelligent scheduling!**

## 🚀 Features

### Core Trading System
- **Multi-Source News Analysis**: Scrapes financial news from CNN Money, CNBC, Bloomberg, Fox Business, and Yahoo Finance
- **AI-Powered Decision Making**: Uses OpenAI GPT-4 to analyze news sentiment and generate trading recommendations
- **Automated Trade Execution**: Executes buy/sell decisions based on AI analysis
- **Real-Time Price Updates**: Automatically updates stock prices and portfolio values

### 🤖 **NEW: Automated Execution System**
- **Intelligent Scheduling**: Market-aware automation that respects trading hours and holidays
- **Summarizer Agents**: Run hourly during market hours (8:25 AM - 5:25 PM ET) and once daily on weekends (3:00 PM ET)
- **Decider Agent**: Runs every 30 minutes during market hours (9:30 AM - 4:00 PM ET, M-F)
- **Feedback Agent**: Runs once daily after market close (4:30 PM ET)
- **Enhanced Data Processing**: Processes ALL unseen summaries, not just the latest batch
- **Manual Trigger System**: Dashboard buttons for immediate testing and manual execution

### Advanced Profit Tracking
- **Cumulative Gain/Loss Tracking**: Properly tracks profits/losses across multiple trades of the same stock
- **Portfolio Performance Metrics**: Real-time calculation of total P&L, percentage gains, and portfolio value
- **Historical Performance**: Time-series tracking of portfolio performance over time
- **Visual Analytics**: Interactive charts showing profit/loss trends and portfolio evolution

### Dashboard & Visualization
- **Real-Time Dashboard**: Web interface displaying current holdings, cash balance, and performance metrics
- **Interactive Charts**: Portfolio value and profit/loss visualization over time
- **Trade History**: Complete record of all trading decisions and their outcomes
- **News Summaries**: Display of analyzed financial news that influenced trading decisions
- **Feedback Dashboard**: AI-powered performance analysis and agent improvement insights
- **Manual Trigger Controls**: Buttons to manually run summarizer, decider, and feedback agents for testing
- **🆕 Manual Price Updates**: "Update Stock Prices" button for immediate price refresh and portfolio recalculation

### 🧠 AI Feedback & Learning System
- **Outcome Tracking**: Automatically records and categorizes trade results (significant profit, moderate profit, break-even, moderate loss, significant loss)
- **Performance Analysis**: AI-powered analysis of trading patterns and success factors
- **Agent Improvement**: Dynamic feedback to summarizer and decider agents based on trading performance
- **Continuous Learning**: System improves over time by learning from both successful and unsuccessful trades
- **Pattern Recognition**: Identifies what news patterns and trading strategies work best

### ⚡ **NEW: Aggressive Day Trading Strategy**
- **Short-Term Focus**: 1-3 day holding periods for maximum ROI through frequent trading
- **Quick Profit Taking**: Automatically sells positions with >3% gains to lock in profits
- **Fast Loss Cutting**: Sells positions with >5% losses to minimize downside
- **Capital Rotation**: Evaluates existing positions before making new buys
- **Sequential Trading**: Can sell existing positions and immediately buy new opportunities
- **Cash Management**: Maintains minimum $10 buffer while maximizing capital utilization
- **Momentum Trading**: Buys stocks with positive news/momentum, sells those with negative news
- **Aggressive Positioning**: Considers selling existing positions to fund better opportunities

## 📁 Project Structure

```
├── d_ai_trader.py             # 🆕 Main automation orchestrator
├── main.py                    # News scraping and AI analysis
├── decider_agent.py           # Trading decision engine (enhanced)
├── feedback_agent.py          # AI feedback and learning system
├── dashboard_server.py        # Web dashboard and API endpoints (enhanced)
├── config.py                  # Database configuration and AI setup
├── start_d_ai_trader.sh       # 🆕 Easy startup script
├── test_system.py             # 🆕 System validation script
├── requirements.txt           # 🆕 All dependencies
├── run_feedback_analysis.py   # Manual feedback analysis tool
├── test_feedback_system.py    # Feedback system demonstration
├── FEEDBACK_SYSTEM.md         # Comprehensive feedback system documentation
├── AUTOMATION_README.md       # 🆕 Automation system documentation
├── templates/                 # HTML templates for web interface
│   ├── dashboard.html         # Main dashboard with profit tracking (enhanced)
│   ├── feedback_dashboard.html # AI feedback and performance analysis
│   ├── trades.html            # Trading history view
│   ├── summaries.html         # News analysis summaries
│   └── tabs.html              # Base template
└── screenshots/               # Captured screenshots from news sites
```

## 🔧 Installation & Setup

### Prerequisites
- Python 3.8+
- PostgreSQL
- Chrome/Chromium browser (for web scraping)

### Database Setup
```bash
# Install PostgreSQL
sudo apt update && sudo apt install postgresql postgresql-contrib

# Start PostgreSQL service
sudo service postgresql start

# Create database and user
sudo -u postgres createuser -s adobi
sudo -u postgres createdb adobi
```

### Python Dependencies
```bash
# Install all dependencies at once
pip install -r requirements.txt

# Or install individually
pip install sqlalchemy psycopg2-binary flask yfinance pandas python-dotenv openai selenium undetected-chromedriver beautifulsoup4 chromedriver-autoinstaller schedule pytz
```

### Configuration
1. Set your OpenAI API key in `config.py`
2. Ensure database connection string is correct: `postgresql://adobi@localhost/adobi`

## 🎯 Usage

### 🚀 **NEW: Automated Execution (Recommended)**
```bash
# Start the complete automated system
./start_d_ai_trader.sh

# Or run manually
python d_ai_trader.py
```
- **Fully automated**: Runs all components on schedule
- **Market-aware**: Respects trading hours and holidays
- **Intelligent processing**: Handles all unseen summaries
- **Comprehensive logging**: Full system monitoring

### 🧪 **Testing & Manual Execution**
```bash
# Test system components
python test_system.py

# Start dashboard with manual triggers
python dashboard_server.py
```
- **Manual triggers**: Use dashboard buttons for immediate testing
- **End-to-end testing**: Run all agents in sequence
- **Real-time monitoring**: Watch system execution live

### 📊 **Traditional Manual Usage**

#### 1. Collect Financial News
```bash
python main.py
```
- Scrapes financial news from 5 major sources
- Uses AI to analyze sentiment and extract trading insights
- Stores analysis in database for decision making

#### 2. Make Trading Decisions
```bash
python decider_agent.py
```
- **Day Trading Analysis**: Evaluates positions for quick profit-taking (>3% gains) or loss-cutting (>5% losses)
- **Capital Rotation**: Considers selling existing positions to fund better opportunities
- **Sequential Processing**: Sells processed first, then buys using updated cash balance
- **Cash Management**: Maintains minimum $10 buffer while maximizing capital utilization
- **Momentum-Based Decisions**: Buys positive momentum, sells negative news
- Records portfolio snapshots for performance tracking

#### 3. Monitor Performance
```bash
python dashboard_server.py
```
- Starts web dashboard at `http://localhost:8080`
- View real-time portfolio performance
- Monitor profit/loss trends
- Analyze trading history and news impact

#### 4. Analyze Feedback & Performance
```bash
# Run comprehensive feedback analysis
python run_feedback_analysis.py

# Demonstrate feedback system capabilities
python test_feedback_system.py
```
- Analyzes trading outcomes and success patterns
- Generates AI-powered insights for improvement
- Access feedback dashboard at `http://localhost:8080/feedback`
- View performance trends and agent learning progress

## 📊 Dashboard Features

### Portfolio Overview
- **Total Portfolio Value**: Current market value of all holdings + cash
- **Cash Balance**: Available cash for trading
- **Total Invested**: Cumulative amount invested across all trades
- **Total P&L**: Unrealized gains/losses with percentage change

### Holdings Table
- Individual stock positions with shares, purchase price, current price
- Gain/loss per holding with color-coded indicators
- Reasoning behind each purchase decision

### Interactive Charts
1. **Account Value Over Time**: Portfolio value progression
2. **Profit/Loss Chart**: Dual-axis chart showing:
   - Dollar gains/losses (left axis)
   - Percentage gains (right axis)
   - Color-coded gains (green) and losses (red)

### API Endpoints
- `/api/holdings` - Current portfolio holdings
- `/api/portfolio-history` - Historical portfolio performance
- `/api/profit-loss` - Profit/loss breakdown by holding
- `/api/history` - Account value history
- `/api/feedback` - Feedback analysis and performance metrics
- `/api/trade_outcomes` - Recent trade outcomes and categorization
- `/api/update-prices` - 🆕 Manually update stock prices and portfolio values
- `/api/trigger/summarizer` - 🆕 Manually trigger summarizer agents
- `/api/trigger/decider` - 🆕 Manually trigger decider agent
- `/api/trigger/feedback` - 🆕 Manually trigger feedback agent
- `/api/trigger/all` - 🆕 Manually trigger all agents in sequence

### 🧠 Feedback Dashboard Features
- **Performance Metrics**: Success rate, average profit, trade count across different time periods (7d, 14d, 30d)
- **AI Insights**: Generated recommendations for improving trading strategy and news analysis
- **Trade Outcomes Table**: Color-coded table of recent trades categorized by performance level
- **Agent Feedback**: Specific guidance for summarizer and decider agents based on trading results
- **Trend Analysis**: Interactive charts showing performance trends with success rates and profit margins
- **System Status**: Real-time indicators of feedback system components

## 🧠 AI Analysis Process

### News Analysis
1. **Web Scraping**: Captures screenshots and HTML from financial news sites
2. **AI Processing**: GPT-4 analyzes both visual and text content
3. **Sentiment Extraction**: Identifies market sentiment and actionable insights
4. **Summary Generation**: Creates structured summaries with headlines and insights

### Trading Decisions
1. **Data Aggregation**: Combines all news analysis from current run
2. **Portfolio Context**: Considers current holdings and cash balance
3. **Risk Management**: Enforces position limits and cash reserves
4. **Decision Generation**: AI creates specific buy/sell recommendations with reasoning
5. **🆕 Enhanced Processing**: Processes ALL unseen summaries, not just the latest batch

## 💰 Profit Tracking Implementation

### Cumulative Gain/Loss Logic
The system properly tracks profits/losses across multiple trades:

```python
# For multiple purchases of same stock:
new_shares = existing_shares + additional_shares
new_total_invested = existing_investment + new_purchase_amount
new_avg_price = new_total_invested / new_shares
unrealized_pnl = (new_shares × current_price) - new_total_invested
```

### Portfolio Metrics
- **Total Invested**: Sum of all purchase amounts (cost basis)
- **Current Value**: Market value of all holdings
- **Unrealized P&L**: Difference between current value and total invested
- **Percentage Gain**: (Unrealized P&L / Total Invested) × 100

### Historical Tracking
Portfolio snapshots are automatically recorded:
- After each trading session
- During price updates
- Stored with timestamp for trend analysis

## 🔒 Risk Management

### Trading Limits
- **Maximum Funds**: $10,000 total allocation
- **Cash Reserve**: Always maintain $100 minimum
- **Position Limits**: Maximum 5 active trades
- **Whole Shares**: Only trades whole share quantities

### Error Handling
- Graceful handling of API failures
- Retry logic for network issues
- Fallback mechanisms for price data
- Comprehensive logging for debugging

## 📈 Performance Analytics

### Real-Time Metrics
- Live portfolio valuation
- Instant profit/loss calculations
- Performance percentage tracking
- Individual holding analytics

### Historical Analysis
- Time-series portfolio performance
- Trade decision outcomes
- News impact correlation
- Trend identification

## 🛠️ Technical Architecture

### Database Schema
- **holdings**: Current portfolio positions with cumulative tracking
- **portfolio_history**: Time-series portfolio snapshots
- **trade_decisions**: AI trading recommendations and outcomes
- **summaries**: Financial news analysis and insights
- **🆕 processed_summaries**: Tracks which summaries have been processed by each agent
- **🆕 system_runs**: Records all system runs with status and timing information

### Technology Stack
- **Backend**: Python, SQLAlchemy, PostgreSQL
- **Frontend**: Flask, Chart.js, HTML/CSS/JavaScript
- **AI**: OpenAI GPT-4 for analysis and decision making
- **Data**: yfinance for market data, Selenium for web scraping
- **🆕 Automation**: schedule, pytz for intelligent scheduling and timezone handling

### Security & Authentication
- PostgreSQL peer authentication
- Secure API key management
- Input validation and SQL injection prevention

## 📝 Configuration Options

### Trading Parameters
```python
MAX_TRADES = 5          # Maximum concurrent positions
MAX_FUNDS = 10000       # Total available capital
MIN_BUFFER = 100        # Minimum cash reserve
```

### Update Intervals
```python
REFRESH_INTERVAL_MINUTES = 10  # Price update frequency
```

### 🆕 **Automation Schedule**
```python
# Summarizer Agents
WEEKDAY_SUMMARIZER_HOURS = "8:25-17:25"  # Every hour at :25
WEEKEND_SUMMARIZER_TIME = "15:00"        # Once daily at 3pm ET

# Decider Agent  
MARKET_HOURS = "9:30-16:00"              # Every 30 minutes during market hours
WEEKDAYS_ONLY = "Monday-Friday"

# Feedback Agent
FEEDBACK_TIME = "16:30"                  # Once daily after market close
```

## 🚨 Important Notes

1. **Educational Purpose**: This system is for educational and research purposes
2. **Risk Warning**: Trading involves financial risk - use with caution
3. **API Costs**: Monitor OpenAI API usage to control costs
4. **Market Hours**: System automatically respects market hours and holidays
5. **Demo Mode**: Test with small amounts before full deployment
6. **🆕 Automation**: System runs continuously - monitor logs and performance
7. **🆕 Testing**: Use manual triggers for immediate testing without waiting for scheduled runs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is for educational purposes. Please ensure compliance with relevant financial regulations and API terms of service.

## 🔗 Dependencies

- **SQLAlchemy**: Database ORM
- **Flask**: Web framework
- **yfinance**: Stock market data
- **OpenAI**: AI analysis
- **Selenium**: Web scraping
- **Chart.js**: Data visualization
- **PostgreSQL**: Database storage
- **🆕 schedule**: Python job scheduling
- **🆕 pytz**: Timezone handling
- **🆕 undetected-chromedriver**: Enhanced web scraping
- **🆕 chromedriver-autoinstaller**: Automatic Chrome driver management

---

**⚠️ Disclaimer**: This software is for educational purposes only. Trading involves significant financial risk. Always do your own research and consider consulting with financial professionals before making investment decisions.

---

## 📚 **Additional Documentation**

- **[AUTOMATION_README.md](AUTOMATION_README.md)**: Comprehensive guide to the automation system
- **[FEEDBACK_SYSTEM.md](FEEDBACK_SYSTEM.md)**: Detailed feedback system documentation