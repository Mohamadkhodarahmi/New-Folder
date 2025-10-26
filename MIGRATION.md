# 🔄 Database Migration Guide

## New Features Added

The signal system now includes:
- **Leverage**: Calculated based on balance and confidence
- **Stop Loss Price**: Calculated from entry price and risk %
- **Take Profit Levels**: 3 TP levels with progressive R/R ratios (1.5:1, 3:1, 4.5:1)

## Migration Steps

### Option 1: Delete Old Database (Recommended for Development)

If you're still in development/testing phase:

```bash
# Delete the old database
rm trading_bot.db

# Run the bot - it will create a new database with updated schema
python main.py
```

### Option 2: Manual Migration (For Production)

If you have important data to preserve:

1. **Backup your database first:**
```bash
cp trading_bot.db trading_bot_backup.db
```

2. **Run the bot** - SQLAlchemy will add new columns automatically for nullable fields

3. **Verify the migration:**
```bash
sqlite3 trading_bot.db
.schema trade_signals
.quit
```

The new schema should include:
- `stop_loss_price`
- `take_profit_1`, `take_profit_2`, `take_profit_3`
- `leverage`

## New Signal Format

Signals now include additional fields:

```python
signal = {
    'symbol': 'BTC/USDT',
    'signal_type': 'BUY',
    'entry_price': 42350.00,
    'stop_loss_price': 41700.00,
    'take_profit_1': 43000.00,  # 1.5:1 R/R
    'take_profit_2': 44000.00,  # 3:1 R/R
    'take_profit_3': 45000.00,  # 4.5:1 R/R
    'leverage': 1.0,
    # ... other fields
}
```

## Leverage Logic

The leverage system is conservative and scales with account balance:

| Balance | Max Leverage | Conditions |
|---------|-------------|------------|
| < $50 | 1.0x (none) | Always |
| $50-100 | 2.0x | Requires 70%+ confidence |
| $100-250 | 3.0x (default), 5.0x (high confidence) | Requires 80%+ for 5x |
| $250+ | 5.0x (default), 10.0x (very high confidence) | Requires 85%+ for 10x |

## Stop Loss & Take Profit Calculation

**For BUY signals:**
- Stop Loss: `entry * (1 - sl_percent/100)` - Below entry
- TP1: `entry * (1 + sl_percent * 1.5/100)` - 1.5:1 R/R
- TP2: `entry * (1 + sl_percent * 3.0/100)` - 3:1 R/R
- TP3: `entry * (1 + sl_percent * 4.5/100)` - 4.5:1 R/R

**For SELL signals:**
- Stop Loss: `entry * (1 + sl_percent/100)` - Above entry
- TP1: `entry * (1 - sl_percent * 1.5/100)` - 1.5:1 R/R
- TP2: `entry * (1 - sl_percent * 3.0/100)` - 3:1 R/R
- TP3: `entry * (1 - sl_percent * 4.5/100)` - 4.5:1 R/R

## Example Signal Output

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

## Notes

- Old signals in the database will have `NULL` values for new fields
- New signals will always include complete stop loss, TP, and leverage data
- Leverage is conservative for your $20 starting balance (no leverage initially)
- Risk/Reward ratios are automatically calculated and displayed
