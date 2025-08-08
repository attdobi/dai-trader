# AI Trading Feedback System

## Overview

The feedback system has been added to track trading outcomes and provide intelligent feedback to improve the performance of the AI trading agents. This system creates a continuous learning loop where the agents get better over time based on real trading results.

## Components

### 1. Trade Outcome Tracker (`feedback_agent.py`)

**Purpose**: Automatically tracks the results of sell decisions and categorizes outcomes.

**Key Features**:
- Records purchase price, sell price, gain/loss percentage, and hold duration
- Categorizes outcomes: `significant_profit`, `moderate_profit`, `break_even`, `moderate_loss`, `significant_loss`
- Stores market context at the time of sale
- Configurable profit/loss thresholds (default: 5% profit, 10% loss)

**Database Tables**:
- `trade_outcomes`: Stores individual trade results
- `agent_feedback`: Stores AI-generated performance analysis
- `agent_instruction_updates`: Tracks changes to agent instructions

### 2. Performance Analysis

**AI-Powered Feedback**: Uses OpenAI to analyze patterns in trading outcomes and generate specific recommendations for:
- **Summarizer Agents**: How to improve news analysis and focus
- **Decider Agent**: How to adjust trading strategy and timing

**Metrics Tracked**:
- Success rate (percentage of profitable trades)
- Average profit/loss percentage
- Hold duration analysis
- Pattern recognition in successful vs unsuccessful trades

### 3. Agent Integration

**Automatic Feedback Integration**:
- Summarizer agents receive guidance on what types of news to focus on
- Decider agent gets strategic recommendations based on past performance
- Feedback is automatically incorporated into agent prompts

**Dynamic Learning**:
- System runs feedback analysis periodically (30% chance on each trading cycle)
- Agents automatically improve their decision-making based on historical performance

## Usage

### Manual Feedback Analysis

```bash
# Run comprehensive feedback analysis
python run_feedback_analysis.py

# Demonstrate outcome recording with sample data
python run_feedback_analysis.py --demo
```

### Automatic Integration

The feedback system is automatically integrated into the existing trading workflow:

1. **During Trading**: `decider_agent.py` automatically records sell outcomes
2. **Decision Making**: Both summarizer and decider agents use latest feedback
3. **Periodic Analysis**: System automatically generates new insights

### Dashboard Visualization

Access the feedback dashboard at: `http://localhost:8080/feedback`

**Features**:
- Real-time performance metrics
- Performance trend charts
- AI-generated feedback insights
- Recent trade outcomes table
- System status indicators

## Configuration

### Performance Thresholds

```python
# In feedback_agent.py
SIGNIFICANT_PROFIT_THRESHOLD = 0.05  # 5% gain
SIGNIFICANT_LOSS_THRESHOLD = -0.10   # 10% loss
FEEDBACK_LOOKBACK_DAYS = 30          # Analysis period
```

### Trading Configuration

```python
# In decider_agent.py
MAX_TRADES = 5
MAX_FUNDS = 10000
MIN_BUFFER = 100
```

## Key Features

### 1. Outcome Classification

Trades are automatically classified into categories:

- **Significant Profit** (≥5%): High-performing trades to learn from
- **Moderate Profit** (0-5%): Successful but modest gains
- **Break Even** (-2% to 2%): Neutral outcomes
- **Moderate Loss** (-10% to -2%): Minor losses to analyze
- **Significant Loss** (≤-10%): Major losses requiring attention

### 2. AI-Powered Insights

The system uses OpenAI to analyze patterns and generate actionable feedback:

```python
# Example feedback structure
{
    "key_insights": ["Pattern analysis", "Timing insights", "Market context"],
    "summarizer_feedback": "Focus on earnings reports and sector rotations",
    "decider_feedback": "Reduce position sizes in volatile markets",
    "successful_patterns": ["Positive earnings", "Tech sector momentum"],
    "unsuccessful_patterns": ["Pre-earnings volatility", "Macro uncertainty"]
}
```

### 3. Continuous Learning

- **Self-Improving**: Agents automatically incorporate feedback
- **Data-Driven**: Decisions based on actual trading performance
- **Adaptive**: System learns from both successes and failures

## API Endpoints

### Feedback Data
```
GET /api/feedback
```
Returns performance analysis and latest feedback.

### Trade Outcomes
```
GET /api/trade_outcomes
```
Returns recent trade outcomes with details.

### Dashboard
```
GET /feedback
```
Displays the feedback analysis dashboard.

## Database Schema

### trade_outcomes
```sql
CREATE TABLE trade_outcomes (
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
    outcome_category TEXT,
    market_context JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### agent_feedback
```sql
CREATE TABLE agent_feedback (
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
);
```

## Benefits

1. **Improved Performance**: Agents learn from past mistakes and successes
2. **Data-Driven Decisions**: Strategy adjustments based on actual results
3. **Automated Learning**: No manual intervention required
4. **Transparent Analysis**: Clear insights into what's working and what isn't
5. **Continuous Improvement**: System gets better over time

## Example Workflow

1. **Trade Execution**: Agent decides to sell AAPL at $165 (bought at $150)
2. **Outcome Recording**: System records 10% profit as "significant_profit"
3. **Pattern Analysis**: AI identifies that "positive earnings" led to good outcomes
4. **Feedback Generation**: Recommends focusing more on earnings-related news
5. **Agent Update**: Summarizer agent adjusts to prioritize earnings information
6. **Improved Decisions**: Future trades benefit from this learning

## Monitoring

The system provides multiple ways to monitor performance:

- **Dashboard**: Real-time visualization at `/feedback`
- **Logs**: Detailed logging of all feedback operations
- **Database**: Direct query access to all historical data
- **API**: Programmatic access to performance metrics

This feedback system transforms the AI trading platform from a static system into a continuously learning and improving intelligent trading assistant.