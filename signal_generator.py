"""
Trading signal generation engine.
Generates BUY/SELL signals based on technical analysis and market conditions.
Now includes real market data fetching, range detection, and optimal entry finding.
"""

import logging
import random
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from market_data_fetcher import MarketDataFetcher
from range_detector import RangeDetector, MarketCondition
from optimal_entry_finder import OptimalEntryFinder, EntryType

logger = logging.getLogger(__name__)


class SignalGenerator:
    """
    Generates trading signals based on technical indicators.
    Integrates with AI confirmation system for validation.
    Uses real market data, range detection, and optimal entry finding.
    """

    def __init__(
        self, 
        ai_confirmer, 
        risk_manager,
        exchange_name: str = 'binance',
        use_real_data: bool = True
    ):
        """
        Initialize signal generator with AI confirmer and risk manager.
        
        Args:
            ai_confirmer: Instance of AISignalConfirmer for signal validation
            risk_manager: Instance of RiskManager for position sizing
            exchange_name: Exchange name for data fetching (default: 'binance')
            use_real_data: Use real market data if True, mock data if False
        """
        self.ai_confirmer = ai_confirmer
        self.risk_manager = risk_manager
        self.supported_symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT']
        self.use_real_data = use_real_data
        
        # Initialize market data components
        if use_real_data:
            try:
                self.data_fetcher = MarketDataFetcher(exchange_name=exchange_name, sandbox=False)
                logger.info("Real market data fetcher initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize real data fetcher: {e}. Falling back to mock data.")
                self.use_real_data = False
                self.data_fetcher = None
        else:
            self.data_fetcher = None
        
        # Initialize range detector and entry finder
        self.range_detector = RangeDetector(
            adx_threshold=25.0,
            range_threshold=0.02,
            lookback_periods=50
        )
        self.entry_finder = OptimalEntryFinder(
            pullback_percent=0.01,
            breakout_confirmation=2,
            support_resistance_tolerance=0.005
        )
        
        # Signal quality parameters
        self.min_confidence = 0.70
        self.min_signal_strength = 0.5
        
        logger.info(f"Signal generator initialized (real_data={self.use_real_data})")

    def generate_signal(self, symbol: Optional[str] = None) -> Optional[Dict]:
        """
        Generate a trading signal for a given symbol.
        Now includes range detection and optimal entry finding.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
                   If None, randomly selects from supported symbols
                   
        Returns:
            Dictionary containing signal details or None if no valid signal
        """
        # Select symbol if not provided
        if symbol is None:
            symbol = random.choice(self.supported_symbols)
        
        logger.info(f"Analyzing {symbol} for trading opportunities...")
        
        # Initialize default values
        entry_type = EntryType.NO_ENTRY
        entry_details = {'entry_reason': 'No analysis performed'}
        market_condition = MarketCondition.RANGE_BOUND
        condition_details = {}
        signal_type = None
        entry_price = 0
        formatted_market_data = {}
        
        # Fetch real market data or use mock
        if self.use_real_data and self.data_fetcher:
            try:
                market_data = self.data_fetcher.get_market_data_for_signal(symbol)
                ohlcv_df = market_data.get('ohlcv_df')
                indicators = market_data.get('full_indicators', {})
                
                # Detect market condition (range vs trending)
                market_condition, condition_details = self.range_detector.detect_market_condition(
                    indicators=indicators,
                    ohlcv_df=ohlcv_df
                )
                
                # Check if market is tradeable (avoid range-bound markets)
                if not self.range_detector.is_tradeable(market_condition):
                    logger.info(f"Signal rejected for {symbol}: Market is {market_condition.value} "
                               f"(ADX: {condition_details.get('adx', 0):.2f}). Avoiding range-bound markets.")
                    return None
                
                # Find optimal entry point
                entry_type, entry_details, suggested_signal = self.entry_finder.find_optimal_entry(
                    market_condition=market_condition.value,
                    indicators=indicators,
                    ohlcv_df=ohlcv_df
                )
                
                # Check if optimal entry was found
                if entry_type == EntryType.NO_ENTRY:
                    logger.info(f"Signal rejected for {symbol}: {entry_details.get('message', 'No optimal entry found')}")
                    return None
                
                # Use suggested signal type from entry finder
                signal_type = suggested_signal
                entry_price = indicators.get('current_price', 0)
                
                # Format market data for AI confirmation
                formatted_market_data = {
                    'rsi': indicators.get('rsi', 50.0),
                    'macd': indicators.get('macd', 0.0),
                    'macd_signal': indicators.get('macd_signal', 0.0),
                    'volume_change': indicators.get('volume_change', 0.0),
                    'price_change_short': indicators.get('price_change_short', 0.0),
                    'price_change_long': indicators.get('price_change_long', 0.0),
                    'volatility': indicators.get('volatility', 0.0),
                    'support_resistance': indicators.get('support_distance', 0.0),
                    'trend_strength': indicators.get('trend_strength', 0.0),
                    'volume_profile': indicators.get('volume_profile', 1.0)
                }
                
                logger.info(f"Market condition: {market_condition.value}, Entry type: {entry_type.value}")
                
            except Exception as e:
                logger.error(f"Error fetching real data for {symbol}: {e}. Falling back to mock data.")
                # Fallback to mock data
                signal_type = random.choice(['BUY', 'SELL'])
                market_data = self.ai_confirmer.generate_mock_market_data(signal_type)
                formatted_market_data = market_data
                entry_price = self._simulate_entry_price(symbol)
                entry_type = EntryType.TREND_FOLLOW
                entry_details = {'entry_reason': 'Mock data fallback'}
                market_condition = MarketCondition.WEAK_UPTREND
                condition_details = {}
        else:
            # Use mock data (fallback)
            signal_type = random.choice(['BUY', 'SELL'])
            market_data = self.ai_confirmer.generate_mock_market_data(signal_type)
            formatted_market_data = market_data
            entry_price = self._simulate_entry_price(symbol)
            entry_type = EntryType.TREND_FOLLOW
            entry_details = {'entry_reason': 'Mock data'}
            market_condition = MarketCondition.WEAK_UPTREND
            condition_details = {}
        
        # Validate we have signal type and entry price
        if not signal_type or entry_price <= 0:
            logger.warning(f"Invalid signal data for {symbol}")
            return None
        
        # Get AI confirmation
        is_confirmed, confidence = self.ai_confirmer.confirm_signal(
            signal_type, formatted_market_data
        )
        
        # Only proceed if AI confirms the signal
        if not is_confirmed or confidence < self.min_confidence:
            logger.info(f"Signal rejected for {symbol}: "
                       f"AI confidence {confidence:.2%} below threshold")
            return None
        
        # Calculate position size using risk manager
        position_size, risk_details = self.risk_manager.calculate_position_size(
            entry_price=entry_price,
            confidence_score=confidence
        )
        
        # Calculate stop loss and take profit levels
        sl_tp_data = self._calculate_sl_tp_levels(
            entry_price=entry_price,
            signal_type=signal_type,
            stop_loss_percent=risk_details['stop_loss_percent']
        )
        
        # Calculate leverage based on balance and confidence
        leverage = self._calculate_leverage(
            position_size=position_size,
            balance=self.risk_manager.current_balance,
            confidence=confidence
        )
        
        # Construct signal dictionary
        signal = {
            'symbol': symbol,
            'signal_type': signal_type,
            'entry_price': entry_price,
            'stop_loss_price': sl_tp_data['stop_loss'],
            'take_profit_1': sl_tp_data['take_profit_1'],
            'take_profit_2': sl_tp_data['take_profit_2'],
            'take_profit_3': sl_tp_data['take_profit_3'],
            'leverage': leverage,
            'confidence_score': confidence,
            'ai_confirmed': is_confirmed,
            'risk_percent': risk_details['risk_percent'],
            'position_size': position_size,
            'risk_amount_usd': risk_details['risk_amount_usd'],
            'stop_loss_percent': risk_details['stop_loss_percent'],
            'market_data': formatted_market_data,
            'timestamp': datetime.utcnow().isoformat(),
            # Additional metadata from new systems
            'market_condition': market_condition.value,
            'entry_type': entry_type.value,
            'entry_details': entry_details,
            'condition_details': condition_details
        }
        
        # Validate signal risk
        if not self.risk_manager.validate_signal_risk(signal):
            logger.warning(f"Signal failed risk validation for {symbol}")
            return None
        
        logger.info(f"Signal generated: {symbol} {signal_type} @ ${entry_price:.2f} "
                   f"(confidence: {confidence:.2%}, size: ${position_size:.2f})")
        
        return signal

    def _simulate_entry_price(self, symbol: str) -> float:
        """
        Simulate entry price for a symbol.
        In production, this would fetch real-time price from exchange API.
        """
        # Simulate realistic prices for different symbols
        base_prices = {
            'BTC/USDT': (30000, 50000),
            'ETH/USDT': (2000, 3500),
            'BNB/USDT': (200, 400),
            'ADA/USDT': (0.4, 0.8)
        }
        
        base_min, base_max = base_prices.get(symbol, (1, 10))
        return round(random.uniform(base_min, base_max), 2)
    
    def _calculate_sl_tp_levels(self, entry_price: float, signal_type: str, 
                                  stop_loss_percent: float) -> Dict:
        """
        Calculate stop loss and take profit levels based on entry price and risk.
        
        Args:
            entry_price: Entry price for the trade
            signal_type: 'BUY' or 'SELL'
            stop_loss_percent: Stop loss percentage
            
        Returns:
            Dictionary with stop loss and take profit prices
        """
        if signal_type == 'BUY':
            # For long positions: SL below entry, TP above entry
            stop_loss = entry_price * (1 - stop_loss_percent / 100)
            take_profit_1 = entry_price * (1 + (stop_loss_percent * 1.5) / 100)  # 1.5:1 R/R
            take_profit_2 = entry_price * (1 + (stop_loss_percent * 3.0) / 100)  # 3:1 R/R
            take_profit_3 = entry_price * (1 + (stop_loss_percent * 4.5) / 100)  # 4.5:1 R/R
        else:  # SELL
            # For short positions: SL above entry, TP below entry
            stop_loss = entry_price * (1 + stop_loss_percent / 100)
            take_profit_1 = entry_price * (1 - (stop_loss_percent * 1.5) / 100)
            take_profit_2 = entry_price * (1 - (stop_loss_percent * 3.0) / 100)
            take_profit_3 = entry_price * (1 - (stop_loss_percent * 4.5) / 100)
        
        return {
            'stop_loss': round(stop_loss, 2),
            'take_profit_1': round(take_profit_1, 2),
            'take_profit_2': round(take_profit_2, 2),
            'take_profit_3': round(take_profit_3, 2)
        }
    
    def _calculate_leverage(self, position_size: float, balance: float, 
                           confidence: float) -> float:
        """
        Calculate appropriate leverage based on position size, balance, and confidence.
        
        Conservative approach:
        - No leverage for accounts under $50
        - Low leverage (2x) for $50-100
        - Moderate leverage (5x) for $100-250, only if confidence is high
        - Higher leverage (10x) for accounts over $250, if confidence is very high
        
        Args:
            position_size: Size of position in USD
            balance: Current account balance
            confidence: AI confidence score (0-1)
            
        Returns:
            Recommended leverage (1.0 to 10.0)
        """
        # Base leverage based on balance
        if balance < 50:
            base_leverage = 1.0
        elif balance < 100:
            base_leverage = 2.0
        elif balance < 250:
            # Only use 5x leverage if confidence is 80%+
            base_leverage = 5.0 if confidence >= 0.80 else 3.0
        else:
            # For larger accounts, can use up to 10x with high confidence
            base_leverage = 10.0 if confidence >= 0.85 else 5.0
        
        # Adjust leverage based on confidence
        if confidence < 0.75:
            leverage_multiplier = 0.8
        elif confidence < 0.85:
            leverage_multiplier = 1.0
        else:
            leverage_multiplier = 1.1
        
        calculated_leverage = min(base_leverage * leverage_multiplier, 10.0)
        
        logger.info(f"Calculated leverage: {calculated_leverage:.1f}x "
                   f"(balance: ${balance:.2f}, confidence: {confidence:.2%})")
        
        return round(calculated_leverage, 1)

    def generate_signal_batch(self, count: int = 5) -> List[Dict]:
        """
        Generate multiple signals to analyze market opportunities.
        
        Args:
            count: Number of signals to generate
            
        Returns:
            List of validated signal dictionaries
        """
        signals = []
        
        for i in range(count):
            try:
                signal = self.generate_signal()
                if signal:
                    signals.append(signal)
            except Exception as e:
                logger.error(f"Error generating signal {i+1}: {e}")
        
        logger.info(f"Generated {len(signals)} valid signals out of {count} attempts")
        return signals

    def format_signal_message(self, signal: Dict) -> str:
        """
        Format signal data into readable Telegram message.
        
        Args:
            signal: Signal dictionary from generate_signal()
            
        Returns:
            Formatted string message
        """
        symbol = signal['symbol']
        sig_type = signal['signal_type']
        entry = signal['entry_price']
        stop_loss = signal['stop_loss_price']
        tp1 = signal['take_profit_1']
        tp2 = signal['take_profit_2']
        tp3 = signal['take_profit_3']
        leverage = signal['leverage']
        confidence = signal['confidence_score']
        size = signal['position_size']
        risk = signal['risk_amount_usd']
        risk_pct = signal['risk_percent']
        
        # Calculate risk/reward ratios
        sl_distance = abs(entry - stop_loss) / entry * 100
        tp1_distance = abs(tp1 - entry) / entry * 100
        rr_ratio = tp1_distance / sl_distance if sl_distance > 0 else 0
        
        # Get additional info if available
        market_condition = signal.get('market_condition', 'unknown')
        entry_type = signal.get('entry_type', 'unknown')
        entry_reason = signal.get('entry_details', {}).get('entry_reason', 'Technical analysis')
        risk_reward = signal.get('entry_details', {}).get('risk_reward', 'moderate')
        
        message = f"""
📊 TRADING SIGNAL

💰 Symbol: {symbol}
🎯 Signal: {sig_type}
⚡ Leverage: {leverage:.1f}x
🤖 AI Confidence: {confidence:.1%}

📈 Market Condition: {market_condition.replace('_', ' ').title()}
🎯 Entry Strategy: {entry_type.replace('_', ' ').title()}
💡 Entry Reason: {entry_reason}
📊 Risk/Reward: {risk_reward.title()}

💵 Entry Price: ${entry:,.2f}
🛑 Stop Loss: ${stop_loss:,.2f} ({sl_distance:.2f}%)
🎯 TP1: ${tp1:,.2f} (R/R: {rr_ratio:.2f}:1)
🎯 TP2: ${tp2:,.2f}
🎯 TP3: ${tp3:,.2f}

📈 Position Size: ${size:.2f}
⚠️ Risk Amount: ${risk:.2f} ({risk_pct:.2f}%)
⏰ Time: {signal['timestamp']}

{'✅ AI CONFIRMED' if signal['ai_confirmed'] else '❌ AI REJECTED'}
{'✅ TRENDING MARKET - NOT RANGE-BOUND' if market_condition != 'range_bound' else ''}
"""
        
        return message.strip()

