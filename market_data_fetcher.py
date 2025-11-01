"""
Market data fetching system using CCXT.
Fetches real-time OHLCV data and calculates technical indicators.
"""

import logging
import ccxt
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class MarketDataFetcher:
    """
    Fetches real market data from exchanges using CCXT.
    Calculates technical indicators for signal generation.
    """

    def __init__(self, exchange_name: str = 'binance', sandbox: bool = False):
        """
        Initialize market data fetcher.
        
        Args:
            exchange_name: Exchange name (binance, bybit, etc.)
            sandbox: Use sandbox/testnet if True
        """
        self.exchange_name = exchange_name
        exchange_class = getattr(ccxt, exchange_name)
        
        self.exchange = exchange_class({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot'  # Use spot trading
            }
        })
        
        if sandbox:
            self.exchange.set_sandbox_mode(True)
            logger.info(f"Using {exchange_name} sandbox mode")
        
        # Test connection
        try:
            self.exchange.load_markets()
            logger.info(f"Connected to {exchange_name}. Markets loaded: {len(self.exchange.markets)}")
        except Exception as e:
            logger.error(f"Failed to connect to {exchange_name}: {e}")
            raise
    
    def fetch_ohlcv(
        self, 
        symbol: str, 
        timeframe: str = '1h', 
        limit: int = 200
    ) -> pd.DataFrame:
        """
        Fetch OHLCV (candlestick) data for a symbol.
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Candle timeframe ('1m', '5m', '15m', '1h', '4h', '1d')
            limit: Number of candles to fetch
            
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        try:
            # Normalize symbol format
            symbol = self._normalize_symbol(symbol)
            
            # Fetch OHLCV data
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            # Convert to DataFrame
            df = pd.DataFrame(
                ohlcv, 
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('datetime', inplace=True)
            
            logger.debug(f"Fetched {len(df)} candles for {symbol} ({timeframe})")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching OHLCV for {symbol}: {e}")
            raise
    
    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol format for exchange."""
        # Ensure format matches exchange expectations
        if '/' not in symbol:
            # Assume USDT pair if no quote currency specified
            return f"{symbol}/USDT"
        return symbol
    
    def fetch_current_price(self, symbol: str) -> float:
        """
        Fetch current market price for a symbol.
        
        Args:
            symbol: Trading pair
            
        Returns:
            Current price as float
        """
        try:
            symbol = self._normalize_symbol(symbol)
            ticker = self.exchange.fetch_ticker(symbol)
            return float(ticker['last'])
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            raise
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> Dict:
        """
        Calculate comprehensive technical indicators from OHLCV data.
        
        Indicators:
        - RSI (Relative Strength Index)
        - MACD (Moving Average Convergence Divergence)
        - EMA (Exponential Moving Averages)
        - Bollinger Bands
        - Volume indicators
        - Price momentum
        - Volatility (ATR)
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Dictionary with calculated indicators
        """
        if len(df) < 50:
            logger.warning(f"Insufficient data: {len(df)} candles. Need at least 50.")
            return self._default_indicators()
        
        try:
            close = df['close'].values
            high = df['high'].values
            low = df['low'].values
            volume = df['volume'].values
            
            # RSI (14 period)
            rsi = self._calculate_rsi(close, period=14)
            
            # MACD (12, 26, 9)
            macd_line, macd_signal, macd_hist = self._calculate_macd(close)
            
            # EMAs
            ema_20 = self._calculate_ema(close, period=20)
            ema_50 = self._calculate_ema(close, period=50)
            ema_200 = self._calculate_ema(close, period=200)
            
            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(close, period=20, std=2)
            
            # ATR (Average True Range) for volatility
            atr = self._calculate_atr(high, low, close, period=14)
            
            # Volume indicators
            volume_ma = np.mean(volume[-20:])
            volume_change = ((volume[-1] - volume_ma) / volume_ma) * 100 if volume_ma > 0 else 0
            
            # Price changes
            price_change_short = ((close[-1] - close[-5]) / close[-5]) * 100 if len(close) >= 5 else 0
            price_change_long = ((close[-1] - close[-20]) / close[-20]) * 100 if len(close) >= 20 else 0
            
            # Support/Resistance levels (simplified: recent lows/highs)
            recent_high = np.max(high[-20:])
            recent_low = np.min(low[-20:])
            support_distance = ((close[-1] - recent_low) / recent_low) * 100
            resistance_distance = ((recent_high - close[-1]) / close[-1]) * 100
            
            # Trend strength (using EMA alignment and slope)
            trend_strength = self._calculate_trend_strength(ema_20, ema_50, ema_200, close)
            
            # Volume profile (current volume vs average)
            volume_profile = volume[-1] / volume_ma if volume_ma > 0 else 1.0
            
            # Volatility (normalized ATR as percentage of price)
            volatility = (atr[-1] / close[-1]) * 100 if close[-1] > 0 else 0
            
            indicators = {
                'rsi': float(rsi[-1]),
                'macd': float(macd_line[-1]),
                'macd_signal': float(macd_signal[-1]),
                'macd_histogram': float(macd_hist[-1]),
                'ema_20': float(ema_20[-1]),
                'ema_50': float(ema_50[-1]),
                'ema_200': float(ema_200[-1]),
                'bb_upper': float(bb_upper[-1]),
                'bb_middle': float(bb_middle[-1]),
                'bb_lower': float(bb_lower[-1]),
                'atr': float(atr[-1]),
                'volume_change': float(volume_change),
                'price_change_short': float(price_change_short),
                'price_change_long': float(price_change_long),
                'support_distance': float(support_distance),
                'resistance_distance': float(resistance_distance),
                'trend_strength': float(trend_strength),
                'volume_profile': float(volume_profile),
                'volatility': float(volatility),
                'current_price': float(close[-1]),
                'recent_high': float(recent_high),
                'recent_low': float(recent_low)
            }
            
            logger.debug(f"Calculated indicators: RSI={indicators['rsi']:.2f}, "
                        f"MACD={indicators['macd']:.4f}, Trend={indicators['trend_strength']:.2f}")
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return self._default_indicators()
    
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> np.ndarray:
        """Calculate Relative Strength Index."""
        delta = np.diff(prices)
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        
        avg_gain = np.zeros_like(prices)
        avg_loss = np.zeros_like(prices)
        
        # Initial average
        avg_gain[period] = np.mean(gain[:period])
        avg_loss[period] = np.mean(loss[:period])
        
        # Smoothing
        for i in range(period + 1, len(prices)):
            avg_gain[i] = (avg_gain[i-1] * (period - 1) + gain[i-1]) / period
            avg_loss[i] = (avg_loss[i-1] * (period - 1) + loss[i-1]) / period
        
        rs = np.where(avg_loss != 0, avg_gain / avg_loss, 0)
        rsi = 100 - (100 / (1 + rs))
        rsi[:period] = 50  # Fill initial values
        
        return rsi
    
    def _calculate_macd(
        self, 
        prices: np.ndarray, 
        fast: int = 12, 
        slow: int = 26, 
        signal: int = 9
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Calculate MACD line, signal line, and histogram."""
        ema_fast = self._calculate_ema(prices, period=fast)
        ema_slow = self._calculate_ema(prices, period=slow)
        
        macd_line = ema_fast - ema_slow
        
        # Signal line is EMA of MACD line
        macd_signal = self._calculate_ema(macd_line, period=signal)
        
        # Histogram
        macd_hist = macd_line - macd_signal
        
        return macd_line, macd_signal, macd_hist
    
    def _calculate_ema(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate Exponential Moving Average."""
        ema = np.zeros_like(prices)
        multiplier = 2 / (period + 1)
        
        # Initialize with SMA
        ema[period - 1] = np.mean(prices[:period])
        
        # Calculate EMA
        for i in range(period, len(prices)):
            ema[i] = (prices[i] * multiplier) + (ema[i-1] * (1 - multiplier))
        
        return ema
    
    def _calculate_bollinger_bands(
        self, 
        prices: np.ndarray, 
        period: int = 20, 
        std: int = 2
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Calculate Bollinger Bands."""
        sma = np.zeros_like(prices)
        
        # Calculate SMA
        for i in range(period - 1, len(prices)):
            sma[i] = np.mean(prices[i - period + 1:i + 1])
        
        # Calculate standard deviation
        std_dev = np.zeros_like(prices)
        for i in range(period - 1, len(prices)):
            std_dev[i] = np.std(prices[i - period + 1:i + 1])
        
        upper = sma + (std_dev * std)
        lower = sma - (std_dev * std)
        
        return upper, sma, lower
    
    def _calculate_atr(
        self, 
        high: np.ndarray, 
        low: np.ndarray, 
        close: np.ndarray, 
        period: int = 14
    ) -> np.ndarray:
        """Calculate Average True Range."""
        tr = np.zeros_like(high)
        
        for i in range(1, len(high)):
            tr1 = high[i] - low[i]
            tr2 = abs(high[i] - close[i-1])
            tr3 = abs(low[i] - close[i-1])
            tr[i] = max(tr1, tr2, tr3)
        
        # Calculate ATR as EMA of TR
        atr = self._calculate_ema(tr, period=period)
        atr[:period] = np.mean(tr[:period])  # Fill initial values
        
        return atr
    
    def _calculate_trend_strength(
        self, 
        ema_20: np.ndarray, 
        ema_50: np.ndarray, 
        ema_200: np.ndarray, 
        close: np.ndarray
    ) -> float:
        """
        Calculate trend strength (0-100).
        
        Strong uptrend: EMA20 > EMA50 > EMA200, price above EMAs
        Strong downtrend: EMA20 < EMA50 < EMA200, price below EMAs
        Range/weak trend: Mixed alignment
        """
        current_close = close[-1]
        ema20_curr = ema_20[-1]
        ema50_curr = ema_50[-1]
        ema200_curr = ema_200[-1]
        
        # Check EMA alignment
        bullish_alignment = ema20_curr > ema50_curr > ema200_curr
        bearish_alignment = ema20_curr < ema50_curr < ema200_curr
        
        if bullish_alignment and current_close > ema20_curr:
            # Strong uptrend: calculate strength based on distance from EMAs
            strength = min(100, 50 + ((current_close - ema20_curr) / ema20_curr) * 1000)
        elif bearish_alignment and current_close < ema20_curr:
            # Strong downtrend
            strength = min(100, 50 + ((ema20_curr - current_close) / ema20_curr) * 1000)
        else:
            # Weak trend or range
            strength = 30  # Low trend strength
        
        return max(0, min(100, strength))
    
    def _default_indicators(self) -> Dict:
        """Return default indicators when calculation fails."""
        return {
            'rsi': 50.0,
            'macd': 0.0,
            'macd_signal': 0.0,
            'macd_histogram': 0.0,
            'ema_20': 0.0,
            'ema_50': 0.0,
            'ema_200': 0.0,
            'bb_upper': 0.0,
            'bb_middle': 0.0,
            'bb_lower': 0.0,
            'atr': 0.0,
            'volume_change': 0.0,
            'price_change_short': 0.0,
            'price_change_long': 0.0,
            'support_distance': 0.0,
            'resistance_distance': 0.0,
            'trend_strength': 0.0,
            'volume_profile': 1.0,
            'volatility': 0.0,
            'current_price': 0.0,
            'recent_high': 0.0,
            'recent_low': 0.0
        }
    
    def get_market_data_for_signal(self, symbol: str) -> Dict:
        """
        Get complete market data dictionary for signal generation.
        This formats indicators to match expected format in ai_signal_confirmation.py
        
        Args:
            symbol: Trading pair
            
        Returns:
            Dictionary with market indicators in expected format
        """
        # Fetch OHLCV data
        df = self.fetch_ohlcv(symbol, timeframe='1h', limit=200)
        
        # Calculate indicators
        indicators = self.calculate_technical_indicators(df)
        
        # Format for AI confirmation system
        market_data = {
            'rsi': indicators['rsi'],
            'macd': indicators['macd'],
            'macd_signal': indicators['macd_signal'],
            'volume_change': indicators['volume_change'],
            'price_change_short': indicators['price_change_short'],
            'price_change_long': indicators['price_change_long'],
            'volatility': indicators['volatility'],
            'support_resistance': indicators['support_distance'],  # Distance to support
            'trend_strength': indicators['trend_strength'],
            'volume_profile': indicators['volume_profile'],
            # Additional data for range detection and entry finding
            'full_indicators': indicators,
            'ohlcv_df': df,
            'current_price': indicators['current_price']
        }
        
        return market_data

