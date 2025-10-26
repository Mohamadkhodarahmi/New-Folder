# 🤖 Trading Signal Bot with AI Confirmation

A professional Telegram trading bot that generates crypto trading signals with AI-powered confirmation and dynamic risk management.

## 📋 Features

- **🎯 AI Signal Confirmation**: PyTorch neural network validates all trading signals
- **💰 Dynamic Risk Management**: Scales risk from 1.5% (starting) to 3.0% as balance grows
- **📊 Technical Analysis**: AI analyzes market indicators (RSI, MACD, Volume, etc.)
- **⚡ Smart Leverage**: Conservative leverage (1x-10x) based on balance and confidence
- **🛑 Stop Loss & Take Profit**: Automatic SL/TP calculation with 3 profit targets
- **💬 Telegram Interface**: Interactive bot with commands for signals, stats, and balance
- **🗄️ Database Logging**: SQLite database stores all signals and performance metrics
- **🛡️ Conservative Approach**: Built for small accounts ($20 starting balance)

## 🏗️ Architecture

```
main.py                    # Application entry point
├── database.py            # SQLite database operations
├── risk_management.py     # Dynamic risk scaling logic
├── ai_signal_confirmation.py  # PyTorch neural network for signal validation
├── signal_generator.py    # Signal generation engine
└── telegram_bot.py        # Telegram bot interface
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example config file:

```bash
cp config.env.example config.env
```

Edit `config.env` with your Telegram bot token:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
INITIAL_BALANCE=20.0
MAX_RISK_PERCENT=2.0
```

### 3. Get Telegram Bot Token

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` command
3. Follow instructions to create your bot
4. Copy the token to `config.env`

### 4. Run the Bot

```bash
python main.py
```

## 💬 Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Show welcome message |
| `/signal` | Generate a new AI-validated trading signal |
| `/stats` | View trading statistics and history |
| `/balance` | Check account balance and risk parameters |
| `/help` | Show detailed help and documentation |

## ⚡ Leverage System

The bot uses **conservative leverage** that scales with account balance and AI confidence:

| Balance Range | Base Leverage | Max Leverage | Confidence Threshold |
|---------------|---------------|--------------|---------------------|
| < $50 | 1.0x | 1.0x | None (no leverage) |
| $50-100 | 2.0x | 2.0x | 70%+ |
| $100-250 | 3.0x | 5.0x | 80%+ for 5x |
| $250+ | 5.0x | 10.0x | 85%+ for 10x |

**Starting with $20:** No leverage (1.0x) for maximum safety

## 🛑 Stop Loss & Take Profit

Every signal includes:
- **Stop Loss**: Calculated from entry price and risk %
- **3 Take Profit Levels**: Progressive R/R ratios
  - TP1: 1.5:1 Risk/Reward
  - TP2: 3.0:1 Risk/Reward
  - TP3: 4.5:1 Risk/Reward

## 🎯 Risk Management

The bot implements **progressive risk scaling** based on account balance:

| Balance Range | Risk per Trade | Position Size |
|---------------|----------------|---------------|
| $20 - $50 | 1.5% | ~2.25% of balance |
| $50 - $100 | 2.0% | ~4% of balance |
| $100 - $250 | 2.5% | ~6% of balance |
| $250+ | 3.0% | ~8% of balance |

### Starting with $20:

- **Max risk**: $0.40 per trade (2%)
- **Position size**: $0.60-1.00 (3-5% of balance)
- **Stop loss**: 1.0% (tighter for small accounts)
- **AI confidence required**: 70% minimum

## 🧠 AI Signal Confirmation

The bot uses a **PyTorch neural network** to analyze 10 market indicators:

1. RSI (Relative Strength Index)
2. MACD line
3. MACD signal
4. Volume change percentage
5. Price change (short term)
6. Price change (long term)
7. Volatility
8. Support/resistance distance
9. Trend strength
10. Volume profile

**Architecture**:
- Input layer: 10 features
- Hidden layers: 64 → 32 neurons
- Output: Binary classification (CONFIRMED: 1, REJECT: 0)
- Activation: ReLU + Sigmoid
- Initialization: Xavier uniform

## 📊 Example Signal Output

```
📊 TRADING SIGNAL

💰 Symbol: BTC/USDT
🎯 Signal: BUY
⚡ Leverage: 1.0x
🤖 AI Confidence: 82.5%

💵 Entry Price: $42,350.00
🛑 Stop Loss: $41,826.00 (1.24%)
🎯 TP1: $42,968.00 (R/R: 1.50:1)
🎯 TP2: $43,922.00
🎯 TP3: $44,876.00

📈 Position Size: $0.95
⚠️ Risk Amount: $0.19 (0.95%)
⏰ Time: 2024-01-15T10:30:00

✅ AI CONFIRMED
```

## ⚙️ Configuration

Edit `config.env` to customize:

```env
# Trading Configuration
INITIAL_BALANCE=20.0
MAX_RISK_PERCENT=2.0
BASE_CURRENCY=USDT

# AI Model Configuration
MODEL_CONFIDENCE_THRESHOLD=0.75
SIGNAL_COOLDOWN_MINUTES=15

# Safety Settings
MAX_POSITION_SIZE_PERCENT=10
MIN_BALANCE_FOR_SCALING=50
```

## 🗂️ Database Schema

**trade_signals** table:
- `id`: Auto-incrementing ID
- `timestamp`: Signal generation time
- `symbol`: Trading pair (e.g., BTC/USDT)
- `signal_type`: BUY or SELL
- `entry_price`: Entry price
- `stop_loss_price`: Stop loss price (calculated)
- `take_profit_1/2/3`: Three take profit levels
- `leverage`: Recommended leverage (1.0x to 10.0x)
- `confidence_score`: AI confidence (0-1)
- `ai_confirmed`: Boolean flag
- `risk_percent`: Risk percentage
- `position_size`: Position size in USD
- `status`: PENDING, EXECUTED, or REJECTED

**performance_metrics** table:
- `id`: Auto-incrementing ID
- `timestamp`: Metric capture time
- `current_balance`: Account balance
- `total_trades`: Total trades executed
- `winning_trades`: Winning trades count
- `losing_trades`: Losing trades count
- `win_rate`: Win percentage
- `total_pnl`: Profit and loss

## 🔧 Development

### Project Structure

```
.
├── main.py                      # Entry point
├── database.py                  # Database layer
├── risk_management.py          # Risk calculations
├── ai_signal_confirmation.py    # PyTorch AI model
├── signal_generator.py          # Signal generation
├── telegram_bot.py             # Bot interface
├── requirements.txt             # Dependencies
├── config.env.example          # Config template
└── README.md                   # Documentation
```

### Adding Real Exchange Integration

To add real market data, modify `signal_generator.py`:

```python
import ccxt

def fetch_market_data(self, symbol):
    exchange = ccxt.binance()
    ticker = exchange.fetch_ticker(symbol)
    ohlcv = exchange.fetch_ohlcv(symbol, '1h', limit=100)
    # Calculate indicators and return market_data dict
```

### Training Custom AI Model

The bot includes an untrained model by default. To train:

1. Collect historical signal data
2. Label confirmed signals (target: 1, rejected: 0)
3. Train using PyTorch optimization
4. Save model weights
5. Load in `AISignalConfirmer`

## ⚠️ Disclaimer

This bot is for **educational purposes** only. Cryptocurrency trading involves substantial risk. Never trade with money you cannot afford to lose. Past performance does not guarantee future results.

## 📝 License

This project is provided as-is for educational purposes.

## 🆘 Support

For issues or questions:
1. Check the logs in `trading_bot.log`
2. Review configuration in `config.env`
3. Test with `/signal` command in Telegram

