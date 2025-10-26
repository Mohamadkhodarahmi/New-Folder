"""
Signal evaluation and accuracy tracking system.
Evaluates signal outcomes by checking if price hit TP levels or stop loss.
"""

import logging
import random
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SignalEvaluator:
    """
    Evaluates trading signals to determine accuracy and outcomes.
    Simulates price movements to determine if TPs or SL were hit.
    """

    def __init__(self, db_manager):
        """
        Initialize signal evaluator.
        
        Args:
            db_manager: Instance of DatabaseManager for data operations
        """
        self.db_manager = db_manager
        
        # Outcome probabilities (for simulation)
        # In production, this would use real market data
        self.tp1_probability = 0.40  # 40% chance to hit TP1
        self.tp2_probability = 0.25  # 25% chance to hit TP2
        self.tp3_probability = 0.15  # 15% chance to hit TP3
        self.sl_probability = 0.20  # 20% chance to hit SL
        
        logger.info("Signal evaluator initialized")

    def evaluate_signal(self, signal) -> Optional[Dict]:
        """
        Evaluate a single signal's outcome.
        
        Args:
            signal: TradeSignal object from database
            
        Returns:
            Dictionary with evaluation results
        """
        try:
            # Determine outcome based on probabilities
            # In production, this would check actual price movements
            outcome = self._simulate_outcome(signal)
            
            logger.info(f"Evaluating signal {signal.id}: {signal.symbol} {signal.signal_type} "
                       f"→ {outcome['outcome']} ({outcome['tp_hit']})")
            
            return outcome
            
        except Exception as e:
            logger.error(f"Error evaluating signal: {e}")
            return None

    def _simulate_outcome(self, signal) -> Dict:
        """
        Simulate signal outcome based on probabilities.
        In production, this would check actual price movements from exchange API.
        
        Args:
            signal: TradeSignal object
            
        Returns:
            Dictionary with outcome details
        """
        # Generate random number to determine outcome
        rand = random.random()
        
        # Simulate which level was hit based on probabilities
        if rand < self.sl_probability:
            # Hit stop loss - LOSS
            return self._create_loss_outcome(signal)
        elif rand < (self.sl_probability + self.tp1_probability):
            # Hit TP1 - WIN
            return self._create_win_outcome(signal, tp_level='TP1')
        elif rand < (self.sl_probability + self.tp1_probability + self.tp2_probability):
            # Hit TP2 - WIN
            return self._create_win_outcome(signal, tp_level='TP2')
        elif rand < (self.sl_probability + self.tp1_probability + self.tp2_probability + self.tp3_probability):
            # Hit TP3 - WIN
            return self._create_win_outcome(signal, tp_level='TP3')
        else:
            # No clear outcome (price moved but didn't hit TP or SL)
            # Treat as LOSS (didn't reach profit target)
            return self._create_loss_outcome(signal, hit_sl=False)

    def _create_win_outcome(self, signal, tp_level: str) -> Dict:
        """
        Create a winning outcome dictionary.
        
        Args:
            signal: TradeSignal object
            tp_level: Which TP was hit (TP1, TP2, TP3)
            
        Returns:
            Dictionary with win outcome
        """
        # Determine which TP level and calculate profit
        if tp_level == 'TP1':
            final_price = signal.take_profit_1
            tp_hit = 'TP1'
        elif tp_level == 'TP2':
            final_price = signal.take_profit_2
            tp_hit = 'TP2'
        else:
            final_price = signal.take_profit_3
            tp_hit = 'TP3'
        
        # Calculate profit based on TP level
        # For simplicity, use 1.5:1, 3:1, 4.5:1 R/R ratios
        rr_ratios = {'TP1': 1.5, 'TP2': 3.0, 'TP3': 4.5}
        profit_multiplier = rr_ratios.get(tp_hit, 1.5)
        
        # Profit = risk * profit_multiplier
        # Use estimated risk amount: 2% of position size for small accounts
        estimated_risk = signal.position_size * 0.02
        profit = estimated_risk * profit_multiplier
        
        return {
            'outcome': 'WIN',
            'tp_hit': tp_hit,
            'hit_stop_loss': False,
            'final_price': final_price,
            'profit_loss': profit
        }

    def _create_loss_outcome(self, signal, hit_sl: bool = True) -> Dict:
        """
        Create a losing outcome dictionary.
        
        Args:
            signal: TradeSignal object
            hit_sl: Whether stop loss was hit
            
        Returns:
            Dictionary with loss outcome
        """
        estimated_risk = signal.position_size * 0.02
        
        if hit_sl:
            final_price = signal.stop_loss_price
            profit = -estimated_risk
        else:
            # Price moved but didn't hit TP (partial loss)
            final_price = signal.entry_price * 0.995  # Small move against position
            profit = -estimated_risk * 0.5
        
        return {
            'outcome': 'LOSS',
            'tp_hit': 'NONE',
            'hit_stop_loss': hit_sl,
            'final_price': final_price,
            'profit_loss': profit
        }

    def evaluate_all_unevaluated_signals(self) -> Dict:
        """
        Evaluate all signals that haven't been evaluated yet.
        
        Returns:
            Dictionary with evaluation summary
        """
        unevaluated_signals = self.db_manager.get_unevaluated_signals()
        
        if not unevaluated_signals:
            logger.info("No unevaluated signals found")
            return {'evaluated': 0, 'wins': 0, 'losses': 0}
        
        wins = 0
        losses = 0
        
        for signal in unevaluated_signals:
            outcome_data = self.evaluate_signal(signal)
            
            if outcome_data:
                # Update signal in database
                self.db_manager.update_signal_outcome(signal.id, outcome_data)
                
                # Count outcomes
                if outcome_data['outcome'] == 'WIN':
                    wins += 1
                else:
                    losses += 1
        
        total = wins + losses
        accuracy = (wins / total * 100) if total > 0 else 0
        
        logger.info(f"Evaluated {total} signals: {wins} wins, {losses} losses ({accuracy:.1f}% accuracy)")
        
        return {
            'evaluated': total,
            'wins': wins,
            'losses': losses,
            'accuracy': accuracy
        }

    def get_accuracy_statistics(self) -> Dict:
        """
        Calculate overall accuracy statistics.
        
        Returns:
            Dictionary with accuracy stats
        """
        all_signals = self.db_manager.get_recent_signals(limit=100)
        
        total = len(all_signals)
        wins = sum(1 for s in all_signals if s.outcome == 'WIN')
        losses = sum(1 for s in all_signals if s.outcome == 'LOSS')
        
        if total == 0:
            return {
                'total': 0,
                'wins': 0,
                'losses': 0,
                'accuracy': 0.0,
                'tp1_hits': 0,
                'tp2_hits': 0,
                'tp3_hits': 0,
                'sl_hits': 0
            }
        
        tp1_hits = sum(1 for s in all_signals if s.tp_hit == 'TP1')
        tp2_hits = sum(1 for s in all_signals if s.tp_hit == 'TP2')
        tp3_hits = sum(1 for s in all_signals if s.tp_hit == 'TP3')
        sl_hits = sum(1 for s in all_signals if s.hit_stop_loss)
        
        return {
            'total': total,
            'wins': wins,
            'losses': losses,
            'accuracy': (wins / total * 100) if total > 0 else 0,
            'tp1_hits': tp1_hits,
            'tp2_hits': tp2_hits,
            'tp3_hits': tp3_hits,
            'sl_hits': sl_hits
        }

    def get_losing_signals(self, limit: int = 10) -> List:
        """Get recent losing signals for review."""
        return self.db_manager.get_signals_by_outcome('LOSS')[:limit]

    def get_winning_signals(self, limit: int = 10) -> List:
        """Get recent winning signals for analysis."""
        return self.db_manager.get_signals_by_outcome('WIN')[:limit]

