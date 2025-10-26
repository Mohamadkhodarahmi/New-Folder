"""
Main entry point for the Trading Signal Bot.
Initializes all components and starts the Telegram bot interface.
"""

import logging
import os
from dotenv import load_dotenv
from database import DatabaseManager
from risk_management import RiskManager
from ai_signal_confirmation import AISignalConfirmer
from signal_generator import SignalGenerator
from telegram_bot import TradingBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def load_configuration():
    """Load configuration from environment variables."""
    load_dotenv('config.env')
    
    config = {
        'telegram_bot_token': os.getenv('TELEGRAM_BOT_TOKEN'),
        'initial_balance': float(os.getenv('INITIAL_BALANCE', '20.0')),
        'max_risk_percent': float(os.getenv('MAX_RISK_PERCENT', '2.0')),
        'model_confidence_threshold': float(os.getenv('MODEL_CONFIDENCE_THRESHOLD', '0.75'))
    }
    
    # Validate required configuration
    if not config['telegram_bot_token']:
        raise ValueError("TELEGRAM_BOT_TOKEN is required in config.env")
    
    logger.info("Configuration loaded successfully")
    return config


def initialize_system(config):
    """
    Initialize all system components.
    
    Components:
    1. Database manager for signal storage
    2. Risk manager for position sizing
    3. AI confirmer for signal validation
    4. Signal generator for trading signals
    5. Telegram bot for user interface
    """
    logger.info("Initializing trading signal system components...")
    
    # Initialize database
    db_manager = DatabaseManager()
    logger.info("✓ Database manager initialized")
    
    # Initialize risk management
    risk_manager = RiskManager(
        initial_balance=config['initial_balance'],
        max_risk=config['max_risk_percent']
    )
    logger.info("✓ Risk manager initialized")
    
    # Initialize AI signal confirmation
    ai_confirmer = AISignalConfirmer()
    logger.info("✓ AI signal confirmer initialized")
    
    # Initialize signal generator
    signal_generator = SignalGenerator(
        ai_confirmer=ai_confirmer,
        risk_manager=risk_manager
    )
    logger.info("✓ Signal generator initialized")
    
    # Initialize Telegram bot
    telegram_bot = TradingBot(
        bot_token=config['telegram_bot_token'],
        signal_generator=signal_generator,
        db_manager=db_manager
    )
    logger.info("✓ Telegram bot initialized")
    
    return telegram_bot


def main():
    """Main application entry point."""
    try:
        logger.info("=" * 60)
        logger.info("TRADING SIGNAL BOT - Starting Application")
        logger.info("=" * 60)
        
        # Load configuration
        config = load_configuration()
        
        # Initialize system
        bot = initialize_system(config)
        
        # Display system information
        logger.info("\n" + "=" * 60)
        logger.info("SYSTEM READY")
        logger.info("=" * 60)
        logger.info(f"Initial Balance: ${config['initial_balance']:.2f}")
        logger.info(f"Max Risk Per Trade: {config['max_risk_percent']}%")
        logger.info(f"AI Confidence Threshold: {config['model_confidence_threshold']:.0%}")
        logger.info("=" * 60 + "\n")
        
        # Start the bot
        logger.info("Starting Telegram bot...")
        bot.run()
        
    except KeyboardInterrupt:
        logger.info("\nShutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()

