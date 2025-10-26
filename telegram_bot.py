"""
Telegram bot handler for trading signal notifications.
Provides interactive interface for managing trades and receiving alerts.
"""

import logging
import asyncio
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

    def __init__(self, bot_token: str, signal_generator, db_manager):
        """
        Initialize the Telegram bot.
        
        Args:
            bot_token: Telegram bot token from BotFather
            signal_generator: Instance of SignalGenerator
            db_manager: Instance of DatabaseManager
        """
        self.signal_generator = signal_generator
        self.db_manager = db_manager
        self.application = Application.builder().token(bot_token).build()
        
        # Register command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("signal", self.generate_signal_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("balance", self.balance_command))
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

    def run(self):
        """Start the bot and begin polling for messages."""
        logger.info("Starting Telegram bot...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

