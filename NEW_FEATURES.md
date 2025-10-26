# 🆕 New Features - Leverage, Stop Loss & Take Profit

## Overview

Your trading signal bot now includes three powerful additions:
1. **⚡ Smart Leverage System** - Conservative leverage based on balance and AI confidence
2. **🛑 Stop Loss Calculation** - Automatic SL based on entry price and risk %
3. **🎯 Take Profit Levels** - Three TP levels with progressive risk/reward ratios

---

## ⚡ Smart Leverage System

### How It Works

The leverage system is **extremely conservative** for small accounts, scaling up only as your balance grows:

| Your Balance | Base Leverage | Maximum Leverage | Confidence Required |
|--------------|---------------|------------------|---------------------|
| **$20-$50** | **1.0x** | **1.0x** (no leverage) | N/A |
| $50-$100 | 2.0x | 2.0x | 70%+ |
| $100-$250 | 3.0x | 5.0x | 80%+ for 5x |
| $250+ | 5.0x | 10.0x | 85%+ for 10x |

### What This Means for You

**Starting with $20:** You'll have **NO leverage** (1.0x). This means:
- Maximum safety
- No amplified risk
- Perfect for learning
- Real position sizes only

**As Your Balance Grows:**
- $50+: Can use 2x leverage (borrow 1x your capital)
- $100+: Can use 3x-5x (only with high confidence signals)
- $250+: Can use up to 10x (only with very high confidence 85%+)

### Example Calculations

**With $20 balance:**
- Position: $0.80
- Leverage: 1.0x (no borrowing)
- Total exposure: $0.80

**With $100 balance and 2x leverage:**
- Position: $3.00
- Leverage: 2.0x
- Total exposure: $6.00 (using borrowed funds)

---

## 🛑 Stop Loss Calculation

### How Stop Loss is Calculated

Stop loss is calculated from your entry price and the risk percentage:

**For BUY signals:**
```
Stop Loss = Entry Price × (1 - Stop Loss % / 100)
```

**For SELL signals:**
```
Stop Loss = Entry Price × (1 + Stop Loss % / 100)
```

### Example

**Entry:** $42,350  
**Stop Loss %:** 1.24%  
**Signal Type:** BUY

```
Stop Loss = $42,350 × (1 - 1.24 / 100)
Stop Loss = $42,350 × 0.9876
Stop Loss = $41,826
```

If price drops to $41,826, you exit with your pre-defined loss ($0.19 in this case).

---

## 🎯 Take Profit Levels

### Three Profit Targets

Every signal includes **3 take profit levels** with progressive risk/reward ratios:

| Level | Risk/Reward | Description |
|-------|-------------|-------------|
| **TP1** | 1.5:1 | Quick profit, take 1/3 of position |
| **TP2** | 3.0:1 | Medium profit, take 1/3 of position |
| **TP3** | 4.5:1 | Maximum profit, take 1/3 of position |

### Example Calculation

**Entry:** $42,350  
**Stop Loss:** $41,826 (1.24% away)  
**TP1:** $42,968 (1.5 × 1.24% = 1.86% away)  
**TP2:** $43,922 (3.0 × 1.24% = 3.72% away)  
**TP3:** $44,876 (4.5 × 1.24% = 5.58% away)

### Risk/Reward Explained

**Risk/Reward ratio** tells you how much you could gain vs. how much you might lose:

- **1.5:1 R/R**: If you risk $1, you aim to gain $1.50
- **3.0:1 R/R**: If you risk $1, you aim to gain $3.00
- **4.5:1 R/R**: If you risk $1, you aim to gain $4.50

The higher the R/R ratio, the larger potential profit relative to risk.

---

## 📊 Complete Signal Example

Here's what a signal looks like with all new features:

```
📊 TRADING SIGNAL

💰 Symbol: BTC/USDT
🎯 Signal: BUY
⚡ Leverage: 1.0x                   ← NEW: Leverage recommendation
🤖 AI Confidence: 82.5%

💵 Entry Price: $42,350.00
🛑 Stop Loss: $41,826.00 (1.24%)   ← NEW: Calculated SL
🎯 TP1: $42,968.00 (R/R: 1.50:1)   ← NEW: First profit target
🎯 TP2: $43,922.00                  ← NEW: Second profit target
🎯 TP3: $44,876.00                  ← NEW: Third profit target

📈 Position Size: $0.95
⚠️ Risk Amount: $0.19 (0.95%)
⏰ Time: 2024-01-15T10:30:00

✅ AI CONFIRMED
```

---

## 🎓 How to Use the New Features

### For Your $20 Starting Balance

1. **Leverage**: 1.0x (no borrowing) - safest option
2. **Stop Loss**: Automatically set based on your risk tolerance
3. **Take Profits**: Use TP1 for quick gains, let TP2/TP3 run for larger profits

### Recommended Strategy with $20

**Conservative Approach:**
- Exit at TP1: Guarantees 1.5:1 profit
- Risk: $0.19, Profit: $0.29

**Balanced Approach:**
- Take profits at TP1, TP2, TP3 (1/3 each)
- Average profit: ~3:1 overall

**Aggressive Approach (Not Recommended):**
- Let position run to TP3
- Maximum profit: 4.5:1

---

## 🔒 Safety Notes

### Important Warnings

1. **Leverage amplifies both profits and losses**
   - With $20, leverage stays at 1.0x (safe)
   - Only increases as balance grows

2. **Always respect stop loss**
   - If price hits SL, exit immediately
   - Don't widen your SL to avoid losses

3. **Take profit in stages**
   - Use TP1, TP2, TP3 to lock in profits
   - Don't let winning trades turn into losses

4. **Start conservatively**
   - With $20, focus on learning
   - As balance grows, you can increase risk gradually

---

## 📈 Database Updates

The database now stores:
- `stop_loss_price`: Calculated stop loss price
- `take_profit_1`: First profit target
- `take_profit_2`: Second profit target  
- `take_profit_3`: Third profit target
- `leverage`: Recommended leverage amount

---

## 🚀 Getting Started

1. **Run the bot** as usual with `python main.py`
2. **Generate a signal** with `/signal`
3. **Review the signal** - new fields are automatically included
4. **Check balance** with `/balance` to see current leverage settings
5. **Monitor signals** with `/stats`

All new features are automatic - no configuration needed!

---

## 💡 Pro Tips

1. **Track your signals**: Check which TP levels you hit most often
2. **Review leverage**: As balance grows, leverage increases automatically
3. **Risk management**: Stop loss is always calculated for your protection
4. **Profit taking**: Use multiple TPs to lock in profits at various stages

Enjoy the enhanced signal system! 🎉

