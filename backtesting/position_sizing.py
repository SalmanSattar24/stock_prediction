"""
Position Sizing Strategies
Kelly Criterion, ATR-based, Confidence-weighted sizing
"""

from typing import Dict
import numpy as np


class PositionSizer:
    """Calculate optimal position sizes based on multiple strategies"""

    @staticmethod
    def kelly_criterion(win_rate: float, avg_win: float, avg_loss: float) -> float:
        """
        Kelly Criterion position sizing
        f = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
        Returns fraction of capital to risk per trade
        Typically use 25% of Kelly (safer)
        """
        if avg_win <= 0:
            return 0

        if win_rate == 0 or win_rate == 1:
            return 0

        f = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win

        # Cap Kelly (usually 25% of Kelly is used in practice)
        kelly_fraction = max(0, min(f, 0.25))  # Max 25% of full Kelly
        return kelly_fraction

    @staticmethod
    def atr_based_sizing(account_size: float, risk_amount: float,
                        entry_price: float, atr: float, atr_multiple: float = 2.0) -> float:
        """
        ATR-based position sizing
        Adjusts position size by volatility
        Higher volatility = smaller position

        position_size = risk_amount / (entry_price * atr_multiple * atr_pct)
        """
        if entry_price <= 0 or atr <= 0:
            return 0

        atr_pct = (atr / entry_price) * 100
        stop_distance = atr_pct * atr_multiple

        position_size = risk_amount / (entry_price * (stop_distance / 100))
        return max(0, position_size)

    @staticmethod
    def confidence_weighted_sizing(base_position: float, confidence: float) -> float:
        """
        Adjust position size by signal confidence
        Higher confidence = larger position (linear adjustment)
        """
        if confidence < 0 or confidence > 100:
            confidence = 50

        confidence_multiplier = confidence / 100
        return base_position * confidence_multiplier

    @staticmethod
    def volatility_adjusted_sizing(base_position: float, current_vol: float,
                                   average_vol: float, vol_cap: float = 2.0) -> float:
        """
        Adjust position based on current volatility vs average
        High volatility = reduce position
        """
        if average_vol <= 0:
            return base_position

        vol_ratio = current_vol / average_vol
        vol_ratio = min(vol_ratio, vol_cap)  # Cap at maximum

        adjusted = base_position / vol_ratio
        return max(0, adjusted)

    @staticmethod
    def calculate_optimal_position(account_size: float, risk_per_trade: float,
                                  entry_price: float, stop_loss: float,
                                  max_position_pct: float = 0.05,
                                  confidence: float = 100,
                                  volatility_adjustment: float = 1.0) -> Dict:
        """
        Calculate optimal position size using multiple factors

        Returns:
        - position_size: Number of shares
        - position_value: Dollar value
        - risk_amount: Amount risked on trade
        - risk_pct_account: Risk as % of account
        """
        if entry_price <= 0 or stop_loss <= 0:
            return {
                'position_size': 0,
                'position_value': 0,
                'risk_amount': 0,
                'risk_pct_account': 0
            }

        # Calculate base risk amount
        risk_amount = account_size * risk_per_trade

        # Calculate stop loss distance
        stop_distance = entry_price - stop_loss
        if stop_distance <= 0:
            return {
                'position_size': 0,
                'position_value': 0,
                'risk_amount': 0,
                'risk_pct_account': 0
            }

        # Base position from risk calculation
        position_size = risk_amount / stop_distance

        # Apply confidence adjustment
        position_size = PositionSizer.confidence_weighted_sizing(position_size, confidence)

        # Apply volatility adjustment
        position_size = PositionSizer.volatility_adjusted_sizing(
            position_size,
            stop_distance / entry_price,  # Current volatility
            0.02,  # Average volatility (2%)
            vol_cap=2.0
        )

        # Cap at maximum position size
        max_position_value = account_size * max_position_pct
        max_position_size = max_position_value / entry_price
        position_size = min(position_size, max_position_size)

        # Calculate final values
        position_value = position_size * entry_price
        risk_pct = (risk_amount / account_size) * 100

        return {
            'position_size': max(0, position_size),
            'position_value': max(0, position_value),
            'risk_amount': risk_amount,
            'risk_pct_account': risk_pct,
            'stop_loss': stop_loss,
            'stop_distance': stop_distance
        }

    @staticmethod
    def scale_into_position(account_size: float, total_risk: float, num_tranches: int = 3,
                           entry_prices: list = None) -> list:
        """
        Scale into a position with multiple entries
        Useful for reducing adverse execution risk

        Returns list of orders: each with size, price, and cumulative_risk
        """
        if not entry_prices or len(entry_prices) == 0:
            entry_prices = [1.0]  # Default

        if num_tranches > len(entry_prices):
            num_tranches = len(entry_prices)

        if num_tranches <= 0:
            return []

        risk_per_tranche = total_risk / num_tranches
        tranches = []

        for i in range(num_tranches):
            entry_price = entry_prices[i] if i < len(entry_prices) else entry_prices[-1]
            position_size = risk_per_tranche / entry_price if entry_price > 0 else 0

            tranches.append({
                'tranche': i + 1,
                'entry_price': entry_price,
                'position_size': position_size,
                'position_value': position_size * entry_price,
                'cumulative_risk': risk_per_tranche * (i + 1)
            })

        return tranches


if __name__ == "__main__":
    sizer = PositionSizer()

    # Example Kelly Criterion
    kelly_f = sizer.kelly_criterion(win_rate=0.55, avg_win=2.0, avg_loss=1.0)
    print(f"Kelly Fraction: {kelly_f:.4f}")

    # Example optimal position
    pos = sizer.calculate_optimal_position(
        account_size=100000,
        risk_per_trade=0.02,
        entry_price=100,
        stop_loss=92,
        confidence=80
    )
    print(f"Optimal Position:")
    for key, val in pos.items():
        print(f"  {key}: {val}")
