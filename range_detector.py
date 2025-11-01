"""
Range detection system to identify sideways/consolidation markets.
Helps avoid trading in choppy, range-bound conditions.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class MarketCondition(Enum):
    """Market condition classification."""
    STRONG_UPTREND = "strong_uptrend"
    WEAK_UPTREND = "weak_uptrend"
    STRONG_DOWNTREND = "strong_downtrend"
    WEAK_DOWNTREND = "weak_downtrend"
    RANGE_BOUND = "range_bound"
    VOLATILE_RANGE = "volatile_range"


class RangeDetector:
    """
    Detects range-bound markets and filters out trading opportunities
    when markets are in consolidation phases.
    """
    
    def __init__(
        self,
        adx_threshold: float = 25.0,
        range_threshold: float = 0.02,
        lookback_periods: int = 50
    ):
        """
        Initialize range detector.
        
        Args:
            adx_threshold: ADX threshold below which market is considered ranging (default: 25)
            range_threshold: Price range percentage threshold (2% = range bound)
            lookback_periods: Number of periods to analyze for range detection
        """
        self.adx_threshold = adx_threshold
        self.range_threshold = range_threshold
        self.lookback_periods = lookback_periods
        
        logger.info(f"Range detector initialized (ADX threshold: {adx_threshold}, "
                   f"Range threshold: {range_threshold*100:.1f}%)")
    
    def detect_market_condition(
        self, 
        indicators: Dict, 
        ohlcv_df: pd.DataFrame
    ) -> Tuple[MarketCondition, Dict]:
        """
        Detect current market condition (trending vs range-bound).
        
        Args:
            indicators: Dictionary with technical indicators
            ohlcv_df: DataFrame with OHLCV data
            
        Returns:
            Tuple of (MarketCondition, details_dict)
        """
        try:
            if len(ohlcv_df) < self.lookback_periods:
                logger.warning(f"Insufficient data for range detection: {len(ohlcv_df)} candles")
                return MarketCondition.RANGE_BOUND, {'reason': 'insufficient_data'}
            
            # Calculate ADX (Average Directional Index)
            adx_value = self._calculate_adx(ohlcv_df, period=14)
            
            # Analyze price range
            range_analysis = self._analyze_price_range(ohlcv_df)
            
            # Check EMA alignment
            ema_alignment = self._analyze_ema_alignment(indicators)
            
            # Analyze volatility
            volatility_analysis = self._analyze_volatility(ohlcv_df, indicators)
            
            # Determine market condition
            condition, details = self._classify_market_condition(
                adx_value=adx_value,
                range_analysis=range_analysis,
                ema_alignment=ema_alignment,
                volatility_analysis=volatility_analysis,
                indicators=indicators
            )
            
            logger.info(f"Market condition: {condition.value} (ADX: {adx_value:.2f}, "
                       f"Range: {range_analysis['range_percent']:.2f}%)")
            
            return condition, details
            
        except Exception as e:
            logger.error(f"Error detecting market condition: {e}")
            return MarketCondition.RANGE_BOUND, {'reason': 'error', 'error': str(e)}
    
    def is_tradeable(self, condition: MarketCondition) -> bool:
        """
        Determine if market condition is suitable for trading.
        
        Args:
            condition: MarketCondition enum value
            
        Returns:
            True if market is tradeable (trending), False if range-bound
        """
        tradeable_conditions = [
            MarketCondition.STRONG_UPTREND,
            MarketCondition.WEAK_UPTREND,
            MarketCondition.STRONG_DOWNTREND,
            MarketCondition.WEAK_DOWNTREND
        ]
        
        return condition in tradeable_conditions
    
    def _calculate_adx(
        self, 
        df: pd.DataFrame, 
        period: int = 14
    ) -> float:
        """
        Calculate Average Directional Index (ADX).
        
        ADX measures trend strength:
        - ADX > 25: Strong trend
        - ADX 20-25: Moderate trend
        - ADX < 20: Weak trend or range-bound
        
        Args:
            df: DataFrame with OHLCV data
            period: ADX calculation period
            
        Returns:
            ADX value (0-100)
        """
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        
        # Calculate +DM and -DM
        plus_dm = np.zeros(len(high))
        minus_dm = np.zeros(len(high))
        
        for i in range(1, len(high)):
            up_move = high[i] - high[i-1]
            down_move = low[i-1] - low[i]
            
            if up_move > down_move and up_move > 0:
                plus_dm[i] = up_move
            else:
                plus_dm[i] = 0
            
            if down_move > up_move and down_move > 0:
                minus_dm[i] = down_move
            else:
                minus_dm[i] = 0
        
        # Calculate True Range
        tr = np.zeros(len(high))
        for i in range(1, len(high)):
            tr1 = high[i] - low[i]
            tr2 = abs(high[i] - close[i-1])
            tr3 = abs(low[i] - close[i-1])
            tr[i] = max(tr1, tr2, tr3)
        
        # Smooth TR, +DM, -DM using Wilder's smoothing
        atr = self._wilders_smoothing(tr, period)
        plus_di_smooth = self._wilders_smoothing(plus_dm, period)
        minus_di_smooth = self._wilders_smoothing(minus_dm, period)
        
        # Calculate +DI and -DI
        plus_di = np.zeros(len(atr))
        minus_di = np.zeros(len(atr))
        
        for i in range(period, len(atr)):
            if atr[i] > 0:
                plus_di[i] = (plus_di_smooth[i] / atr[i]) * 100
                minus_di[i] = (minus_di_smooth[i] / atr[i]) * 100
        
        # Calculate DX (Directional Index)
        dx = np.zeros(len(plus_di))
        for i in range(period, len(plus_di)):
            di_diff = abs(plus_di[i] - minus_di[i])
            di_sum = plus_di[i] + minus_di[i]
            if di_sum > 0:
                dx[i] = (di_diff / di_sum) * 100
        
        # ADX is smoothed DX
        adx = self._wilders_smoothing(dx, period)
        
        return float(adx[-1]) if len(adx) > 0 else 0.0
    
    def _wilders_smoothing(self, data: np.ndarray, period: int) -> np.ndarray:
        """Apply Wilder's smoothing (EMA-like with different alpha)."""
        smoothed = np.zeros_like(data)
        
        # Initialize with SMA
        smoothed[period - 1] = np.mean(data[:period])
        
        # Wilder's smoothing: (previous * (n-1) + current) / n
        alpha = 1.0 / period
        for i in range(period, len(data)):
            smoothed[i] = smoothed[i-1] * (1 - alpha) + data[i] * alpha
        
        return smoothed
    
    def _analyze_price_range(self, df: pd.DataFrame) -> Dict:
        """
        Analyze price range over lookback period.
        
        Returns:
            Dictionary with range analysis metrics
        """
        lookback_df = df.tail(self.lookback_periods)
        
        high_max = lookback_df['high'].max()
        low_min = lookback_df['low'].min()
        current_price = df['close'].iloc[-1]
        
        # Calculate range as percentage of price
        price_range = high_max - low_min
        range_percent = (price_range / current_price) * 100 if current_price > 0 else 0
        
        # Calculate how much price has moved within the range
        range_position = ((current_price - low_min) / price_range) * 100 if price_range > 0 else 50
        
        return {
            'range_percent': range_percent,
            'range_position': range_position,
            'range_high': high_max,
            'range_low': low_min,
            'is_range_bound': range_percent < (self.range_threshold * 100)
        }
    
    def _analyze_ema_alignment(self, indicators: Dict) -> Dict:
        """
        Analyze EMA alignment to determine trend direction.
        
        Returns:
            Dictionary with EMA alignment analysis
        """
        ema_20 = indicators.get('ema_20', 0)
        ema_50 = indicators.get('ema_50', 0)
        ema_200 = indicators.get('ema_200', 0)
        current_price = indicators.get('current_price', 0)
        
        # Check alignment
        bullish = ema_20 > ema_50 > ema_200
        bearish = ema_20 < ema_50 < ema_200
        aligned = bullish or bearish
        
        # Check price relative to EMAs
        price_above_ema20 = current_price > ema_20 if ema_20 > 0 else False
        price_below_ema20 = current_price < ema_20 if ema_20 > 0 else False
        
        return {
            'bullish_alignment': bullish,
            'bearish_alignment': bearish,
            'is_aligned': aligned,
            'price_above_ema20': price_above_ema20,
            'price_below_ema20': price_below_ema20,
            'alignment_strength': abs(ema_20 - ema_50) / ema_50 * 100 if ema_50 > 0 else 0
        }
    
    def _analyze_volatility(
        self, 
        df: pd.DataFrame, 
        indicators: Dict
    ) -> Dict:
        """
        Analyze market volatility to identify choppy conditions.
        
        Returns:
            Dictionary with volatility analysis
        """
        lookback_df = df.tail(20)
        
        # Calculate price swings
        price_changes = lookback_df['close'].pct_change().dropna()
        volatility = price_changes.std() * 100
        
        # Count direction changes (chop)
        direction_changes = 0
        for i in range(1, len(lookback_df)):
            if i > 0:
                prev_change = lookback_df['close'].iloc[i] - lookback_df['close'].iloc[i-1]
                curr_change = lookback_df['close'].iloc[i-1] - lookback_df['close'].iloc[i-2] if i > 1 else 0
                if (prev_change > 0 and curr_change < 0) or (prev_change < 0 and curr_change > 0):
                    direction_changes += 1
        
        chop_ratio = direction_changes / len(lookback_df) if len(lookback_df) > 0 else 0
        
        atr_value = indicators.get('atr', 0)
        current_price = indicators.get('current_price', 1)
        atr_percent = (atr_value / current_price) * 100 if current_price > 0 else 0
        
        return {
            'volatility': volatility,
            'chop_ratio': chop_ratio,
            'atr_percent': atr_percent,
            'is_choppy': chop_ratio > 0.4  # More than 40% direction changes
        }
    
    def _classify_market_condition(
        self,
        adx_value: float,
        range_analysis: Dict,
        ema_alignment: Dict,
        volatility_analysis: Dict,
        indicators: Dict
    ) -> Tuple[MarketCondition, Dict]:
        """
        Classify market condition based on all analysis.
        
        Returns:
            Tuple of (MarketCondition, details_dict)
        """
        trend_strength = indicators.get('trend_strength', 0)
        
        # Primary check: ADX and range
        is_range_bound = (
            adx_value < self.adx_threshold or 
            range_analysis['is_range_bound'] or
            volatility_analysis['is_choppy']
        )
        
        if is_range_bound:
            if volatility_analysis['volatility'] > 3.0:
                return MarketCondition.VOLATILE_RANGE, {
                    'adx': adx_value,
                    'range_percent': range_analysis['range_percent'],
                    'volatility': volatility_analysis['volatility'],
                    'reason': 'high_volatility_range'
                }
            else:
                return MarketCondition.RANGE_BOUND, {
                    'adx': adx_value,
                    'range_percent': range_analysis['range_percent'],
                    'reason': 'low_adx_or_narrow_range'
                }
        
        # Trending market - determine direction
        if ema_alignment['bullish_alignment']:
            if adx_value > 30 and trend_strength > 70:
                return MarketCondition.STRONG_UPTREND, {
                    'adx': adx_value,
                    'trend_strength': trend_strength,
                    'reason': 'strong_bullish_trend'
                }
            else:
                return MarketCondition.WEAK_UPTREND, {
                    'adx': adx_value,
                    'trend_strength': trend_strength,
                    'reason': 'weak_bullish_trend'
                }
        
        elif ema_alignment['bearish_alignment']:
            if adx_value > 30 and trend_strength > 70:
                return MarketCondition.STRONG_DOWNTREND, {
                    'adx': adx_value,
                    'trend_strength': trend_strength,
                    'reason': 'strong_bearish_trend'
                }
            else:
                return MarketCondition.WEAK_DOWNTREND, {
                    'adx': adx_value,
                    'trend_strength': trend_strength,
                    'reason': 'weak_bearish_trend'
                }
        
        # Default: range-bound
        return MarketCondition.RANGE_BOUND, {
            'adx': adx_value,
            'reason': 'mixed_signals'
        }

