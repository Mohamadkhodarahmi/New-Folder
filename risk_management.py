"""
Risk management system with dynamic scaling based on account balance.
Implements conservative risk parameters for small accounts with gradual scaling.
"""

import logging
from typing import Dict, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RiskParameters:
    """
    Risk management parameters for each trade.
    
    Attributes:
        max_risk_percent: Maximum percentage of balance to risk per trade
        position_size_percent: Percentage of balance to allocate per position
        max_position_size_usd: Absolute maximum position size in USD
        min_stop_loss_percent: Minimum stop loss percentage
        max_leverage: Maximum leverage allowed
    """
    max_risk_percent: float
    position_size_percent: float
    max_position_size_usd: float
    min_stop_loss_percent: float
    max_leverage: float


class RiskManager:
    """
    Manages position sizing and risk allocation based on account balance.
    Implements dynamic risk scaling: more conservative for small accounts,
    gradually increasing risk as balance grows.
    """

    def __init__(self, initial_balance: float = 20.0, max_risk: float = 2.0):
        """
        Initialize risk manager with initial balance and conservative risk limits.
        
        Args:
            initial_balance: Starting account balance in USD
            max_risk: Maximum percentage of balance to risk per trade (default 2%)
        """
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.max_risk_per_trade = max_risk
        
        # Risk scaling thresholds
        self.balance_tiers = [
            (20, 1.5),   # $20-50: 1.5% risk
            (50, 2.0),   # $50-100: 2.0% risk
            (100, 2.5),  # $100-250: 2.5% risk
            (250, 3.0),  # $250+: 3.0% risk
        ]
        
        # Safety limits
        self.max_position_size_percent = 10  # Never risk more than 10% on single position
        self.max_stop_loss_percent = 5      # Maximum stop loss of 5%
        
        logger.info(f"Risk manager initialized with ${initial_balance:.2f} "
                   f"and {max_risk}% max risk per trade")

    def update_balance(self, new_balance: float):
        """Update current account balance for risk calculations."""
        if new_balance <= 0:
            logger.warning(f"Invalid balance: ${new_balance:.2f}. Keeping previous balance.")
            return
        
        self.current_balance = new_balance
        logger.info(f"Balance updated to ${new_balance:.2f}")

    def get_risk_parameters(self) -> RiskParameters:
        """
        Calculate risk parameters based on current account balance.
        Returns progressively more aggressive parameters as balance grows.
        """
        # Determine risk percentage based on balance tier
        risk_percent = self.max_risk_per_trade
        
        for tier_balance, tier_risk in self.balance_tiers:
            if self.current_balance >= tier_balance:
                risk_percent = tier_risk
        
        # Position size is typically 2-3x the risk amount (for smaller accounts)
        if self.current_balance < 50:
            position_size_multiplier = 1.5
        elif self.current_balance < 100:
            position_size_multiplier = 2.0
        else:
            position_size_multiplier = 2.5
        
        position_size_percent = min(risk_percent * position_size_multiplier, 
                                   self.max_position_size_percent)
        
        # Calculate actual position size in USD
        position_size_usd = (self.current_balance * position_size_percent) / 100
        
        # Stop loss: tighter for small accounts, wider as balance grows
        if self.current_balance < 50:
            stop_loss_percent = 1.0
        elif self.current_balance < 100:
            stop_loss_percent = 1.5
        else:
            stop_loss_percent = 2.0
        
        stop_loss_percent = min(stop_loss_percent, self.max_stop_loss_percent)
        
        # Leverage: conservative, no leverage for accounts under $100
        max_leverage = 1.0 if self.current_balance < 100 else 2.0
        
        return RiskParameters(
            max_risk_percent=risk_percent,
            position_size_percent=position_size_percent,
            max_position_size_usd=position_size_usd,
            min_stop_loss_percent=stop_loss_percent,
            max_leverage=max_leverage
        )

    def calculate_position_size(self, entry_price: float, 
                               confidence_score: float,
                               stop_loss_price: float = None) -> Tuple[float, Dict]:
        """
        Calculate appropriate position size based on risk parameters.
        
        Args:
            entry_price: Entry price for the trade
            confidence_score: AI confidence score (0-1)
            stop_loss_price: Stop loss price (optional, auto-calculated if None)
            
        Returns:
            Tuple of (position_size_usd, risk_details_dict)
        """
        risk_params = self.get_risk_parameters()
        
        # Adjust position size based on confidence score
        confidence_multiplier = max(0.5, min(1.5, confidence_score))
        
        # Calculate base position size
        base_position_size = risk_params.max_position_size_usd * confidence_multiplier
        
        # If stop loss is provided, validate it
        if stop_loss_price:
            stop_loss_percent = abs((stop_loss_price - entry_price) / entry_price) * 100
            
            if stop_loss_percent > risk_params.max_stop_loss_percent:
                logger.warning(f"Stop loss {stop_loss_percent:.2f}% exceeds max "
                             f"{risk_params.max_stop_loss_percent}%")
                # Adjust position size to maintain risk
                adjusted_size = base_position_size * (
                    risk_params.max_stop_loss_percent / stop_loss_percent
                )
                base_position_size = adjusted_size
        
        # Final safety check: never exceed max position size
        final_position_size = min(base_position_size, 
                                 self.current_balance * self.max_position_size_percent / 100)
        
        # Estimate actual risk in USD
        actual_risk = final_position_size * (risk_params.min_stop_loss_percent / 100)
        
        risk_details = {
            'position_size_usd': final_position_size,
            'position_size_percent': (final_position_size / self.current_balance) * 100,
            'risk_amount_usd': actual_risk,
            'risk_percent': (actual_risk / self.current_balance) * 100,
            'confidence_used': confidence_score,
            'stop_loss_percent': risk_params.min_stop_loss_percent
        }
        
        logger.info(f"Calculated position size: ${final_position_size:.2f} "
                   f"({risk_details['position_size_percent']:.2f}% of balance) "
                   f"with ${actual_risk:.2f} at risk ({risk_details['risk_percent']:.2f}%)")
        
        return final_position_size, risk_details

    def validate_signal_risk(self, signal_data: Dict) -> bool:
        """
        Validate that a signal meets risk management criteria.
        
        Args:
            signal_data: Dictionary containing signal information
            
        Returns:
            True if signal passes risk validation, False otherwise
        """
        # Check if position size exceeds limits
        position_size = signal_data.get('position_size', 0)
        
        if position_size > self.current_balance * self.max_position_size_percent / 100:
            logger.warning(f"Position size ${position_size:.2f} exceeds safety limits")
            return False
        
        # Check confidence score
        confidence = signal_data.get('confidence_score', 0)
        if confidence < 0.6:  # Require minimum 60% confidence
            logger.warning(f"Confidence score {confidence:.2%} below minimum threshold")
            return False
        
        # Check balance is positive
        if self.current_balance <= 0:
            logger.error("Account balance is zero or negative")
            return False
        
        return True

