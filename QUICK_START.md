# 🚀 Quick Start Guide

Get your trading bot up and running in 5 minutes!

## Step 1: Install Dependencies

Run the setup script:

```bash
./setup.sh
```

Or manually:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Step 2: Get Telegram Bot Token

1. Open Telegram app
2. Search for [@BotFather](https://t.me/BotFather)
3. Send command: `/newbot`
4. Follow instructions to create your bot
5. Copy the token (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

## Step 3: Configure Bot

Edit `config.env`:

```bash
nano config.env
# or
vim config.env
```

Add your bot token:

```env
TELEGRAM_BOT_TOKEN=your_token_here
```

## Step 4: Run the Bot

```bash
python main.py
```

You should see:
```
============================
TRADING SIGNAL BOT - Starting Application
============================
SYSTEM READY
Initial Balance: $20.00
Max Risk Per Trade: 2.0%
AI Confidence Threshold: 75%
Starting Telegram bot...
```

## Step 5: Test the Bot

1. Open Telegram
2. Find your bot (search for the name you gave it)
3. Send `/start` command
4. Send `/signal` to generate a trading signal
5. Send `/stats` to view statistics
6. Send `/balance` to check balance

## Commands Reference

| Command | What it does |
|---------|-------------|
| `/start` | Welcome message |
| `/signal` | Generate AI trading signal |
| `/stats` | View statistics |
| `/balance` | Check balance |
| `/help` | Show help |

## Troubleshooting

### "No module named 'telegram'"
```bash
source venv/bin/activate
pip install python-telegram-bot
```

### "TELEGRAM_BOT_TOKEN is required"
Check that `config.env` exists and contains your token.

### Bot not responding
1. Check that the bot is running (`python main.py`)
2. Check logs in `trading_bot.log`
3. Verify your bot token is correct

## Next Steps

- Review signals in the database
- Check `trading_bot.log` for detailed logs
- Customize risk parameters in `config.env`
- Study the code to understand how it works

## Understanding the Bot

**System Flow:**
1. You request signal with `/signal`
2. Bot generates random trading opportunity
3. AI analyzes market indicators (simulated)
4. AI confirms or rejects (70%+ confidence)
5. Risk manager calculates position size
6. **NEW**: Calculate stop loss & 3 take profit levels
7. **NEW**: Calculate appropriate leverage
8. Signal saved to database
9. You receive formatted message

**Starting Balance: $20**
- Max risk per trade: ~$0.40 (2%)
- Position size: ~$0.60-1.00
- **No leverage** (1.0x) - maximum safety
- **3 take profit levels** (1.5:1, 3:1, 4.5:1 R/R)
- Very conservative for learning

## Safety Features

✅ AI confirmation required (70%+ confidence)
✅ Position size limits (max 10% of balance)
✅ Conservative starting risk (2%)
✅ Stop loss calculation
✅ Risk scaling as balance grows

Enjoy learning about trading bots! 🚀

