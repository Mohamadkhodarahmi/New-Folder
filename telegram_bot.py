"""
Telegram bot handler for trading signal notifications.
Provides interactive interface for managing trades and receiving alerts.
"""

import logging
import asyncio
import os
from typing import Optional
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackContext
)

logger = logging.getLogger(__name__)


class TradingBot:
    """
    Telegram bot interface for trading signal system.
    Handles user commands and sends trading signals via Telegram.
    """

    def __init__(self, bot_token: str, signal_generator, db_manager, signal_evaluator, proxy_url: Optional[str] = None):
        """
        Initialize the Telegram bot.
        
        Args:
            bot_token: Telegram bot token from BotFather
            signal_generator: Instance of SignalGenerator
            db_manager: Instance of DatabaseManager
            signal_evaluator: Instance of SignalEvaluator
            proxy_url: Optional proxy URL (e.g., 'socks5://user:pass@host:port' or 'http://host:port')
        """
        self.signal_generator = signal_generator
        self.db_manager = db_manager
        self.signal_evaluator = signal_evaluator
        
        # Build application with optional proxy
        app_builder = Application.builder().token(bot_token)
        
        # Add proxy if provided
        if proxy_url:
            app_builder = app_builder.proxy_url(proxy_url)
            logger.info(f"Using proxy for Telegram: {proxy_url.split('@')[-1] if '@' in proxy_url else proxy_url}")
        
        self.application = app_builder.build()
        
        # Register command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("signal", self.generate_signal_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("balance", self.balance_command))
        self.application.add_handler(CommandHandler("review", self.review_command))
        self.application.add_handler(CommandHandler("accuracy", self.accuracy_command))
        self.application.add_handler(CommandHandler("losers", self.losers_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        
        logger.info("Telegram bot initialized with command handlers")

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command - welcome message and instructions."""
        welcome_message = """
🤖 **Trading Signal Bot**

Welcome to your AI-powered trading assistant!

📊 I generate crypto trading signals with AI confirmation
🤖 Signals are validated by neural network analysis
💰 Dynamic risk management scales with your balance

**Available Commands:**
/start - Show this welcome message
/signal - Generate a new trading signal
/review - Evaluate signal accuracy
/accuracy - Show accuracy statistics
/losers - Review losing signals
/stats - View trading statistics
/balance - Check account balance
/help - Show detailed help

💰 Starting Balance: $20.00
🎯 Conservative risk scaling enabled

Ready to start trading!
"""
        await update.message.reply_text(welcome_message, parse_mode='Markdown')

    async def generate_signal_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /signal command - generate and send a new trading signal."""
        try:
            await update.message.reply_text("🔄 Analyzing market...")
            
            # Generate signal
            signal = self.signal_generator.generate_signal()
            
            if signal:
                # Save to database
                self.db_manager.save_signal(signal)
                
                # Format and send message
                message = self.signal_generator.format_signal_message(signal)
                await update.message.reply_text(message, parse_mode='Markdown')
                
                logger.info(f"Signal sent to user: {signal['symbol']}")
            else:
                await update.message.reply_text(
                    "❌ No valid signals found at the moment. "
                    "Market conditions don't meet our risk criteria."
                )
                
        except Exception as e:
            logger.error(f"Error generating signal: {e}")
            await update.message.reply_text(
                f"❌ Error generating signal: {str(e)}"
            )

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command - show trading statistics."""
        try:
            recent_signals = self.db_manager.get_recent_signals(limit=5)
            
            if not recent_signals:
                await update.message.reply_text(
                    "📊 No signals generated yet. Use /signal to get started!"
                )
                return
            
            # Calculate basic stats
            total_signals = len(recent_signals)
            confirmed_signals = sum(1 for s in recent_signals if s.ai_confirmed)
            
            avg_confidence = sum(s.confidence_score for s in recent_signals) / total_signals
            
            stats_message = f"""
📊 **Trading Statistics**

📈 Total Signals: {total_signals}
✅ AI Confirmed: {confirmed_signals}
📉 Confirmation Rate: {(confirmed_signals/total_signals)*100:.1f}%
🎯 Avg Confidence: {avg_confidence:.1%}

**Recent Signals:**
"""
            for sig in recent_signals[:5]:
                status_emoji = "✅" if sig.ai_confirmed else "❌"
                stats_message += f"{status_emoji} {sig.symbol} {sig.signal_type} "
                stats_message += f"({sig.confidence_score:.1%})\n"
            
            await update.message.reply_text(stats_message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error fetching stats: {e}")
            await update.message.reply_text(f"❌ Error fetching stats: {str(e)}")

    async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /balance command - show account balance and risk parameters."""
        try:
            metrics = self.db_manager.get_performance_metrics()
            
            if not metrics:
                balance = self.signal_generator.risk_manager.current_balance
                await update.message.reply_text(
                    f"💰 **Current Balance:** ${balance:.2f}\n\n"
                    "📊 No performance metrics recorded yet."
                )
                return
            
            balance = metrics.current_balance
            risk_params = self.signal_generator.risk_manager.get_risk_parameters()
            
            balance_message = f"""
💰 **Account Balance:** ${balance:.2f}

⚙️ **Risk Parameters:**
📉 Max Risk per Trade: {risk_params.max_risk_percent:.2f}%
📊 Max Position Size: {risk_params.max_position_size_usd:.2f} USD
🛑 Stop Loss: {risk_params.min_stop_loss_percent:.1f}%

**Performance:**
📈 Total Trades: {metrics.total_trades}
✅ Win Rate: {metrics.win_rate:.1f}%
💵 Total P&L: ${metrics.total_pnl:.2f}
"""
            
            await update.message.reply_text(balance_message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            await update.message.reply_text(f"❌ Error fetching balance: {str(e)}")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command - show detailed help."""
        help_message = """
❓ **Help - Trading Signal Bot**

**Commands:**
• `/signal` - Generate a new AI-validated trading signal
• `/review` - Evaluate accuracy of signals
• `/accuracy` - Show accuracy statistics and performance
• `/losers` - Review losing signals to learn from mistakes
• `/stats` - View trading statistics and signal history
• `/balance` - Check account balance and risk parameters
• `/help` - Show this help message

**Risk Management:**
This bot uses conservative risk management:
• Starts with 2% max risk per trade for small accounts
• Position sizes increase as your balance grows
• AI confirmation required for all signals (min 70% confidence)
• Automatic stop loss calculation

**Starting with $20:**
• Max risk: $0.40 per trade (2%)
• Position size: ~$0.60-1.00 (3-5% of balance)
• Extremely conservative approach

**As you grow:**
• $50+: 2.0% risk per trade
• $100+: 2.5% risk per trade
• $250+: 3.0% risk per trade

⚠️ **Disclaimer:**
Trading cryptocurrencies involves risk. This bot is for educational purposes.
Always trade with money you can afford to lose.
"""
        await update.message.reply_text(help_message, parse_mode='Markdown')

    async def review_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /review command - evaluate all unevaluated signals."""
        try:
            await update.message.reply_text("🔄 Evaluating signals...")
            
            # Evaluate all unevaluated signals
            result = self.signal_evaluator.evaluate_all_unevaluated_signals()
            
            if result['evaluated'] == 0:
                await update.message.reply_text(
                    "✅ No unevaluated signals found."
                )
                return
            
            # Get accuracy stats
            accuracy_stats = self.signal_evaluator.get_accuracy_statistics()
            
            review_message = f"""
📊 **Signal Review Complete**

✅ Evaluated: {result['evaluated']} signals
🎯 Wins: {result['wins']}
❌ Losses: {result['losses']}
📈 Accuracy: {result['accuracy']:.1f}%

**Overall Statistics:**
📊 Total Signals: {accuracy_stats['total']}
✅ Wins: {accuracy_stats['wins']}
❌ Losses: {accuracy_stats['losses']}
🎯 Overall Accuracy: {accuracy_stats['accuracy']:.1f}%

**Target Hits:**
🎯 TP1: {accuracy_stats['tp1_hits']}
🎯 TP2: {accuracy_stats['tp2_hits']}
🎯 TP3: {accuracy_stats['tp3_hits']}
🛑 Stop Loss: {accuracy_stats['sl_hits']}
"""
            
            await update.message.reply_text(review_message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in review: {e}")
            await update.message.reply_text(f"❌ Error reviewing signals: {str(e)}")

    async def accuracy_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /accuracy command - show accuracy statistics."""
        try:
            stats = self.signal_evaluator.get_accuracy_statistics()
            
            if stats['total'] == 0:
                await update.message.reply_text(
                    "📊 No evaluated signals yet. Use /review to evaluate signals."
                )
                return
            
            accuracy_message = f"""
📊 **Accuracy Report**

**Performance:**
📈 Total Signals: {stats['total']}
✅ Wins: {stats['wins']}
❌ Losses: {stats['losses']}
🎯 Win Rate: {stats['accuracy']:.1f}%

**Breakdown:**
🎯 Hit TP1: {stats['tp1_hits']} ({(stats['tp1_hits']/stats['total']*100):.1f}%)
🎯 Hit TP2: {stats['tp2_hits']} ({(stats['tp2_hits']/stats['total']*100):.1f}%)
🎯 Hit TP3: {stats['tp3_hits']} ({(stats['tp3_hits']/stats['total']*100):.1f}%)
🛑 Hit Stop Loss: {stats['sl_hits']} ({(stats['sl_hits']/stats['total']*100):.1f}%)

**Analysis:**
{"🟢 Great performance! Keep it up!" if stats['accuracy'] >= 60 else "🟡 Room for improvement. Review losing signals with /losers" if stats['accuracy'] >= 40 else "🔴 Low accuracy. Consider reviewing signals more carefully."}
"""
            
            await update.message.reply_text(accuracy_message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error fetching accuracy: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def losers_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /losers command - show recent losing signals for review."""
        try:
            losing_signals = self.signal_evaluator.get_losing_signals(limit=5)
            
            if not losing_signals:
                await update.message.reply_text(
                    "✅ No losing signals to review yet!"
                )
                return
            
            losers_message = "📊 **Recent Losing Signals**\n\n"
            
            for i, sig in enumerate(losing_signals[:5], 1):
                tp_status = f"Hit {sig.tp_hit}" if sig.tp_hit != 'NONE' else "No TP hit"
                sl_status = "🛑 Hit SL" if sig.hit_stop_loss else "~ Partial loss"
                
                losers_message += f"""
**Signal {i}:**
💰 {sig.symbol} {sig.signal_type}
💵 Entry: ${sig.entry_price:,.2f} → ${sig.final_price:,.2f}
🤖 Confidence: {sig.confidence_score:.1%}
📊 Outcome: {tp_status if not sig.hit_stop_loss else sl_status}
💰 P&L: ${sig.profit_loss:.2f}
"""
            
            await update.message.reply_text(losers_message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error fetching losers: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")

    def run(self):
        """Start the bot and begin polling for messages."""
        logger.info("Starting Telegram bot...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

