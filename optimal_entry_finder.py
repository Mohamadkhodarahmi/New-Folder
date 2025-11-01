"""
Optimal entry point identification system.
Finds best entry points during trends: breakouts, pullbacks, support/resistance levels.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class EntryType(Enum):
    """Entry signal types."""
    BREAKOUT = "breakout"
    PULLBACK = "pullback"
    SUPPORT_BOUNCE = "support_bounce"
    RESISTANCE_REJECTION = "resistance_rejection"
    TREND_FOLLOW = "trend_follow"
    NO_ENTRY = "no_entry"


class OptimalEntryFinder:
    """
    Identifies optimal entry points during trending markets.
    Avoids entries in range-bound conditions and finds best risk/reward setups.
    """
    
    def __init__(
        self,
        pullback_percent: float = 0.01,
        breakout_confirmation: int = 2,
        support_resistance_tolerance: float = 0.005
    ):
        """
        Initialize optimal entry finder.
        
        Args:
            pullback_percent: Minimum pullback percentage to consider (default: 1%)
            breakout_confirmation: Number of candles to confirm breakout
            support_resistance_tolerance: Tolerance for S/R levels (0.5%)
        """
        self.pullback_percent = pullback_percent
        self.breakout_confirmation = breakout_confirmation
        self.support_resistance_tolerance = support_resistance_tolerance
        
        logger.info("Optimal entry finder initialized")
    
    def find_optimal_entry(
        self,
        market_condition: str,
        indicators: Dict,
        ohlcv_df: pd.DataFrame
    ) -> Tuple[EntryType, Dict, Optional[str]]:
        """
        Find optimal entry point based on market condition and price action.
        
        Args:
            market_condition: MarketCondition enum value (from RangeDetector)
            indicators: Dictionary with technical indicators
            ohlcv_df: DataFrame with OHLCV data
            
        Returns:
            Tuple of (EntryType, entry_details_dict, suggested_signal_type)
            suggested_signal_type: 'BUY', 'SELL', or None
        """
        try:
            if len(ohlcv_df) < 50:
                return EntryType.NO_ENTRY, {'reason': 'insufficient_data'}, None
            
            current_price = indicators['current_price']
            
            # Find support and resistance levels
            support_levels, resistance_levels = self._find_support_resistance(
                ohlcv_df, 
                lookback=50
            )
            
            # Analyze entry opportunities based on market condition
            if 'uptrend' in market_condition.lower():
                entry_type, details, signal = self._find_uptrend_entry(
                    ohlcv_df,
                    indicators,
                    support_levels,
                    resistance_levels,
                    current_price
                )
            
            elif 'downtrend' in market_condition.lower():
                entry_type, details, signal = self._find_downtrend_entry(
                    ohlcv_df,
                    indicators,
                    support_levels,
                    resistance_levels,
                    current_price
                )
            
            else:
                # Range-bound or unclear - no entry
                return EntryType.NO_ENTRY, {
                    'reason': 'range_bound_market',
                    'message': 'Market is range-bound. Waiting for trend to develop.'
                }, None
            
            logger.info(f"Optimal entry found: {entry_type.value} for {signal}")
            return entry_type, details, signal
            
        except Exception as e:
            logger.error(f"Error finding optimal entry: {e}")
            return EntryType.NO_ENTRY, {'reason': 'error', 'error': str(e)}, None
    
    def _find_uptrend_entry(
        self,
        df: pd.DataFrame,
        indicators: Dict,
        support_levels: List[float],
        resistance_levels: List[float],
        current_price: float
    ) -> Tuple[EntryType, Dict, str]:
        """
        Find optimal entry point in uptrend.
        
        Entry strategies:
        1. Pullback to support (best R/R)
        2. Breakout above resistance
        3. Bounce off EMA support
        4. Trend continuation after minor pullback
        """
        ema_20 = indicators.get('ema_20', current_price)
        ema_50 = indicators.get('ema_50', current_price)
        rsi = indicators.get('rsi', 50)
        macd_hist = indicators.get('macd_histogram', 0)
        
        # Get recent price action
        recent_candles = df.tail(10)
        
        # Strategy 1: Pullback to support (best entry)
        nearest_support = self._find_nearest_level(current_price, support_levels, 'below')
        if nearest_support and self._is_near_level(current_price, nearest_support):
            pullback_distance = ((current_price - nearest_support) / nearest_support) * 100
            
            if pullback_distance < 2.0 and rsi < 60:  # Near support, not overbought
                return EntryType.SUPPORT_BOUNCE, {
                    'entry_price': current_price,
                    'support_level': nearest_support,
                    'distance_to_support': pullback_distance,
                    'entry_reason': 'Bouncing off support in uptrend',
                    'risk_reward': 'excellent'
                }, 'BUY'
        
        # Strategy 2: Pullback to EMA (good entry)
        if current_price > ema_20 > ema_50:
            distance_to_ema20 = ((current_price - ema_20) / ema_20) * 100
            
            # Pullback to EMA20 (1-3% above)
            if 0.5 < distance_to_ema20 < 3.0 and rsi < 65:
                return EntryType.PULLBACK, {
                    'entry_price': current_price,
                    'ema_level': ema_20,
                    'distance_to_ema': distance_to_ema20,
                    'entry_reason': 'Pullback to EMA20 in uptrend',
                    'risk_reward': 'good'
                }, 'BUY'
        
        # Strategy 3: Breakout above resistance
        nearest_resistance = self._find_nearest_level(current_price, resistance_levels, 'above')
        if nearest_resistance:
            distance_to_resistance = ((nearest_resistance - current_price) / current_price) * 100
            
            # Near resistance - wait for breakout
            if distance_to_resistance < 1.0:
                # Check for breakout confirmation
                breakout_confirmed = self._check_breakout(
                    recent_candles,
                    nearest_resistance,
                    direction='up'
                )
                
                if breakout_confirmed:
                    return EntryType.BREAKOUT, {
                        'entry_price': current_price,
                        'resistance_level': nearest_resistance,
                        'distance_to_resistance': distance_to_resistance,
                        'entry_reason': 'Breakout above resistance in uptrend',
                        'risk_reward': 'moderate'
                    }, 'BUY'
        
        # Strategy 4: Trend continuation (momentum entry)
        if (rsi > 55 and rsi < 70 and  # Healthy momentum, not overbought
            macd_hist > 0 and  # Positive momentum
            current_price > ema_20):  # Above short-term trend
            
            return EntryType.TREND_FOLLOW, {
                'entry_price': current_price,
                'rsi': rsi,
                'entry_reason': 'Trend continuation with momentum',
                'risk_reward': 'moderate'
            }, 'BUY'
        
        # No optimal entry found
        return EntryType.NO_ENTRY, {
            'reason': 'waiting_for_better_setup',
            'message': 'Uptrend detected but waiting for pullback or breakout confirmation'
        }, None
    
    def _find_downtrend_entry(
        self,
        df: pd.DataFrame,
        indicators: Dict,
        support_levels: List[float],
        resistance_levels: List[float],
        current_price: float
    ) -> Tuple[EntryType, Dict, str]:
        """
        Find optimal entry point in downtrend (SHORT entries).
        """
        ema_20 = indicators.get('ema_20', current_price)
        ema_50 = indicators.get('ema_50', current_price)
        rsi = indicators.get('rsi', 50)
        macd_hist = indicators.get('macd_histogram', 0)
        
        recent_candles = df.tail(10)
        
        # Strategy 1: Rejection at resistance
        nearest_resistance = self._find_nearest_level(current_price, resistance_levels, 'above')
        if nearest_resistance and self._is_near_level(current_price, nearest_resistance):
            rejection_distance = ((nearest_resistance - current_price) / nearest_resistance) * 100
            
            if rejection_distance < 2.0 and rsi > 40:  # Near resistance, not oversold
                return EntryType.RESISTANCE_REJECTION, {
                    'entry_price': current_price,
                    'resistance_level': nearest_resistance,
                    'distance_to_resistance': rejection_distance,
                    'entry_reason': 'Rejection at resistance in downtrend',
                    'risk_reward': 'excellent'
                }, 'SELL'
        
        # Strategy 2: Pullback to EMA in downtrend
        if current_price < ema_20 < ema_50:
            distance_to_ema20 = ((ema_20 - current_price) / current_price) * 100
            
            if 0.5 < distance_to_ema20 < 3.0 and rsi > 35:
                return EntryType.PULLBACK, {
                    'entry_price': current_price,
                    'ema_level': ema_20,
                    'distance_to_ema': distance_to_ema20,
                    'entry_reason': 'Pullback to EMA20 in downtrend',
                    'risk_reward': 'good'
                }, 'SELL'
        
        # Strategy 3: Breakdown below support
        nearest_support = self._find_nearest_level(current_price, support_levels, 'below')
        if nearest_support:
            distance_to_support = ((current_price - nearest_support) / current_price) * 100
            
            if distance_to_support < 1.0:
                breakdown_confirmed = self._check_breakout(
                    recent_candles,
                    nearest_support,
                    direction='down'
                )
                
                if breakdown_confirmed:
                    return EntryType.BREAKOUT, {
                        'entry_price': current_price,
                        'support_level': nearest_support,
                        'distance_to_support': distance_to_support,
                        'entry_reason': 'Breakdown below support in downtrend',
                        'risk_reward': 'moderate'
                    }, 'SELL'
        
        # Strategy 4: Trend continuation (short momentum)
        if (rsi < 45 and rsi > 30 and  # Healthy downward momentum
            macd_hist < 0 and  # Negative momentum
            current_price < ema_20):  # Below short-term trend
            
            return EntryType.TREND_FOLLOW, {
                'entry_price': current_price,
                'rsi': rsi,
                'entry_reason': 'Downtrend continuation with momentum',
                'risk_reward': 'moderate'
            }, 'SELL'
        
        # No optimal entry found
        return EntryType.NO_ENTRY, {
            'reason': 'waiting_for_better_setup',
            'message': 'Downtrend detected but waiting for pullback or breakdown confirmation'
        }, None
    
    def _find_support_resistance(
        self,
        df: pd.DataFrame,
        lookback: int = 50
    ) -> Tuple[List[float], List[float]]:
        """
        Identify support and resistance levels using pivot points.
        
        Returns:
            Tuple of (support_levels, resistance_levels)
        """
        lookback_df = df.tail(lookback)
        highs = lookback_df['high'].values
        lows = lookback_df['low'].values
        closes = lookback_df['close'].values
        
        # Find local peaks (resistance) and troughs (support)
        support_levels = []
        resistance_levels = []
        
        window = 5  # Look for peaks/troughs in 5-candle windows
        
        for i in range(window, len(highs) - window):
            # Check for resistance (local high)
            is_peak = True
            for j in range(i - window, i + window + 1):
                if j != i and highs[j] >= highs[i]:
                    is_peak = False
                    break
            
            if is_peak:
                resistance_levels.append(highs[i])
            
            # Check for support (local low)
            is_trough = True
            for j in range(i - window, i + window + 1):
                if j != i and lows[j] <= lows[i]:
                    is_trough = False
                    break
            
            if is_trough:
                support_levels.append(lows[i])
        
        # Filter and cluster nearby levels
        resistance_levels = self._cluster_levels(resistance_levels)
        support_levels = self._cluster_levels(support_levels)
        
        # Sort: resistance descending, support ascending
        resistance_levels.sort(reverse=True)
        support_levels.sort()
        
        return support_levels[:5], resistance_levels[:5]  # Return top 5 levels
    
    def _cluster_levels(self, levels: List[float], tolerance_percent: float = 1.0) -> List[float]:
        """Cluster nearby levels together."""
        if not levels:
            return []
        
        levels = sorted(levels)
        clustered = []
        
        current_cluster = [levels[0]]
        
        for level in levels[1:]:
            # Check if level is within tolerance of current cluster
            avg_cluster = np.mean(current_cluster)
            tolerance = avg_cluster * (tolerance_percent / 100)
            
            if abs(level - avg_cluster) <= tolerance:
                current_cluster.append(level)
            else:
                # Save cluster average and start new cluster
                clustered.append(np.mean(current_cluster))
                current_cluster = [level]
        
        # Add last cluster
        if current_cluster:
            clustered.append(np.mean(current_cluster))
        
        return clustered
    
    def _find_nearest_level(
        self,
        price: float,
        levels: List[float],
        direction: str = 'below'
    ) -> Optional[float]:
        """Find nearest support/resistance level."""
        if not levels:
            return None
        
        if direction == 'below':
            # Find nearest level below price
            below_levels = [l for l in levels if l < price]
            return max(below_levels) if below_levels else None
        else:
            # Find nearest level above price
            above_levels = [l for l in levels if l > price]
            return min(above_levels) if above_levels else None
    
    def _is_near_level(self, price: float, level: float, tolerance_percent: float = 1.0) -> bool:
        """Check if price is near a support/resistance level."""
        tolerance = level * (tolerance_percent / 100)
        return abs(price - level) <= tolerance
    
    def _check_breakout(
        self,
        recent_candles: pd.DataFrame,
        level: float,
        direction: str = 'up'
    ) -> bool:
        """
        Check if breakout is confirmed.
        
        Args:
            recent_candles: Recent price candles
            level: Support/resistance level
            direction: 'up' or 'down'
            
        Returns:
            True if breakout is confirmed
        """
        confirmation_count = 0
        
        for i in range(len(recent_candles) - self.breakout_confirmation, len(recent_candles)):
            candle = recent_candles.iloc[i]
            
            if direction == 'up':
                # Breakout above: close must be above level
                if candle['close'] > level:
                    confirmation_count += 1
            else:
                # Breakdown below: close must be below level
                if candle['close'] < level:
                    confirmation_count += 1
        
        return confirmation_count >= self.breakout_confirmation

