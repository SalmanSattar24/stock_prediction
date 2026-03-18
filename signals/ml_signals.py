"""
ML-Based Trading Signals
Ensemble voting with Random Forest + XGBoost
Walk-forward validation to prevent overfitting
"""

from typing import Dict, List, Tuple
import numpy as np
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')


class MLSignalGenerator:
    """
    ML-based signal generation with ensemble voting
    Combines Random Forest and XGBoost for robust predictions
    """

    def __init__(self, lookback_days: int = 60):
        """
        Initialize ML signal generator
        lookback_days: Period for feature engineering
        """
        self.lookback_days = lookback_days
        self.rf_model = None
        self.xgb_model = None
        self.scaler = None
        self.feature_names = []
        self.is_trained = False

        # Try to import required libraries
        try:
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.preprocessing import StandardScaler
            self.RandomForestClassifier = RandomForestClassifier
            self.StandardScaler = StandardScaler
            self.sklearn_available = True
        except ImportError:
            self.sklearn_available = False
            print("WARNING: scikit-learn not installed. ML signals disabled.")

        try:
            import xgboost as xgb
            self.xgb = xgb
            self.xgboost_available = True
        except ImportError:
            self.xgboost_available = False
            print("WARNING: XGBoost not installed. Using Random Forest only.")

    def engineer_features(self, quote_data: Dict, historical_quotes: List[Dict] = None) -> np.ndarray:
        """
        Engineer features from quote data for ML models
        Features:
        - Gap percentage
        - Intraday range
        - Price position
        - Volume indicators
        - Volatility
        """
        features = []

        try:
            current_price = quote_data.get('c', 0)
            daily_high = quote_data.get('h', 0)
            daily_low = quote_data.get('l', 0)
            prev_close = quote_data.get('pc', 0)
            bid_vol = quote_data.get('bidV', 0)
            ask_vol = quote_data.get('askV', 0)

            if not all([current_price, daily_high, daily_low, prev_close]):
                return None

            # Feature 1: Gap percentage
            gap_pct = ((current_price - prev_close) / prev_close) * 100 if prev_close else 0
            features.append(gap_pct)

            # Feature 2: Intraday range percentage
            intraday_range = ((daily_high - daily_low) / prev_close) * 100 if prev_close else 0
            features.append(intraday_range)

            # Feature 3: Price position in range (0-1)
            position = (current_price - daily_low) / (daily_high - daily_low) if (daily_high - daily_low) != 0 else 0.5
            features.append(position)

            # Feature 4: Bid-Ask imbalance
            if bid_vol and ask_vol and (bid_vol + ask_vol) > 0:
                imbalance = (bid_vol - ask_vol) / (bid_vol + ask_vol)
                features.append(imbalance)
            else:
                features.append(0)

            # Feature 5: Volume ratio
            total_vol = bid_vol + ask_vol if (bid_vol and ask_vol) else 1
            volume_ratio = bid_vol / total_vol if total_vol > 0 else 0.5
            features.append(volume_ratio)

            # Features 6-10: Historical volatility (if available)
            if historical_quotes and len(historical_quotes) >= 5:
                recent_closes = [q.get('c', 0) for q in historical_quotes[-5:] if q.get('c')]
                if len(recent_closes) >= 3:
                    volatility = np.std(recent_closes) / np.mean(recent_closes) if np.mean(recent_closes) > 0 else 0
                    features.append(volatility)

                    # High Close / Low Close ratio
                    highs = [q.get('h', 0) for q in historical_quotes[-5:]]
                    lows = [q.get('l', 0) for q in historical_quotes[-5:]]
                    hl_ratio = np.mean(highs) / np.mean(lows) if np.mean(lows) > 0 else 1
                    features.append(hl_ratio)

                    # Price trend (current vs 5 days ago)
                    if len(recent_closes) >= 5:
                        trend = (recent_closes[-1] - recent_closes[0]) / recent_closes[0] * 100 if recent_closes[0] > 0 else 0
                        features.append(trend)

            # Pad to consistent length
            while len(features) < 10:
                features.append(0)

            self.feature_names = [
                'gap_pct', 'intraday_range', 'price_position', 'bid_ask_imbalance',
                'volume_ratio', 'volatility', 'hl_ratio', 'trend', 'momentum', 'strength'
            ]

            return np.array(features[:10]).reshape(1, -1)

        except Exception as e:
            return None

    def train_ensemble_models(self, X_train: np.ndarray, y_train: np.ndarray) -> Dict:
        """
        Train Random Forest + XGBoost ensemble
        y_train: 1 for bullish signals, 0 for neutral, -1 for bearish
        """
        if not self.sklearn_available:
            return {'status': 'error', 'message': 'scikit-learn not available'}

        training_results = {
            'rf_score': 0,
            'xgb_score': 0,
            'training_samples': len(X_train),
            'feature_counts': X_train.shape[1] if X_train is not None else 0
        }

        try:
            # Initialize scaler
            self.scaler = self.StandardScaler()
            X_scaled = self.scaler.fit_transform(X_train)

            # Train Random Forest
            self.rf_model = self.RandomForestClassifier(
                n_estimators=100,
                max_depth=8,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            )
            self.rf_model.fit(X_scaled, y_train)
            rf_train_score = self.rf_model.score(X_scaled, y_train)
            training_results['rf_score'] = rf_train_score

            # Train XGBoost if available
            if self.xgboost_available:
                self.xgb_model = self.xgb.XGBClassifier(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    random_state=42,
                    verbosity=0,
                    eval_metric='logloss'
                )
                self.xgb_model.fit(X_scaled, y_train)
                xgb_train_score = self.xgb_model.score(X_scaled, y_train)
                training_results['xgb_score'] = xgb_train_score

            self.is_trained = True
            training_results['status'] = 'success'

            return training_results

        except Exception as e:
            training_results['status'] = 'error'
            training_results['error'] = str(e)
            return training_results

    def predict_ensemble(self, X_input: np.ndarray) -> Dict:
        """
        Generate predictions from ensemble (RF + XGBoost)
        Returns consensus probability and direction
        """
        if not self.is_trained or X_input is None:
            return {
                'direction': 'UNKNOWN',
                'confidence': 0,
                'rf_prob': 0,
                'xgb_prob': 0,
                'consensus': 0,
                'signal': 'HOLD'
            }

        try:
            # Scale input
            X_scaled = self.scaler.transform(X_input)

            # Get RF prediction probabilities
            rf_probs = self.rf_model.predict_proba(X_scaled)[0]
            rf_signal = self.rf_model.predict(X_scaled)[0]

            # Get direction from RF (estimate if multiclass)
            # Classes: 0=neutral, 1=bullish, -1=bearish (or 0,1,2 depending on training)
            rf_prob = np.max(rf_probs)  # Confidence of prediction

            result = {
                'rf_prob': rf_prob,
                'rf_signal': rf_signal,
                'xgb_prob': 0,
                'xgb_signal': 0
            }

            # Get XGB prediction if available
            if self.xgboost_available and self.xgb_model is not None:
                xgb_probs = self.xgb_model.predict_proba(X_scaled)[0]
                xgb_signal = self.xgb_model.predict(X_scaled)[0]
                xgb_prob = np.max(xgb_probs)

                result['xgb_prob'] = xgb_prob
                result['xgb_signal'] = xgb_signal

                # Ensemble vote
                consensus_prob = (rf_prob + xgb_prob) / 2
                consensus_signal = (rf_signal + xgb_signal) / 2
            else:
                consensus_prob = rf_prob
                consensus_signal = rf_signal

            # Interpret consensus
            if consensus_signal > 0.5:
                direction = 'BULLISH'
                signal = 'BUY'
            elif consensus_signal < -0.5:
                direction = 'BEARISH'
                signal = 'SELL'
            else:
                direction = 'NEUTRAL'
                signal = 'HOLD'

            result.update({
                'direction': direction,
                'confidence': min(100, consensus_prob * 100),
                'consensus': consensus_signal,
                'signal': signal,
                'timestamp': datetime.now().isoformat()
            })

            return result

        except Exception as e:
            return {
                'direction': 'ERROR',
                'confidence': 0,
                'error': str(e),
                'signal': 'HOLD'
            }

    def model_status(self) -> Dict:
        """Get current model status"""
        return {
            'is_trained': self.is_trained,
            'sklearn_available': self.sklearn_available,
            'xgboost_available': self.xgboost_available,
            'rf_model': self.rf_model is not None,
            'xgb_model': self.xgb_model is not None,
            'scaler': self.scaler is not None,
            'lookback_days': self.lookback_days
        }


class WalkForwardValidator:
    """
    Walk-forward validation for ML models
    Train on rolling window, test on forward period
    Prevents overfitting by validating on unseen data
    """

    def __init__(self, train_period_days: int = 252, test_period_days: int = 28):
        """
        train_period_days: Period to train model (typically 1 year)
        test_period_days: Period to test model (typically 1 month)
        """
        self.train_period = train_period_days
        self.test_period = test_period_days
        self.validation_results = []

    def run_walk_forward(self, data: List[Dict], signal_gen: MLSignalGenerator) -> List[Dict]:
        """
        Run walk-forward validation on dataset
        data: List of daily records with date, features, returns
        Returns: List of validation results
        """
        if not data or len(data) < (self.train_period + self.test_period):
            return []

        results = []
        total_days = len(data)
        current_idx = 0

        while current_idx + self.train_period + self.test_period <= total_days:
            # Split into train and test
            train_data = data[current_idx:current_idx + self.train_period]
            test_data = data[current_idx + self.train_period:current_idx + self.train_period + self.test_period]

            # Extract features and labels for training
            X_train = np.array([r.get('features', []) for r in train_data])
            y_train = np.array([r.get('label', 0) for r in train_data])

            # Train model
            train_result = signal_gen.train_ensemble_models(X_train, y_train)

            # Test on forward period
            test_predictions = []
            for test_record in test_data:
                X_test = np.array(test_record.get('features', [])).reshape(1, -1)
                pred = signal_gen.predict_ensemble(X_test)
                actual_label = test_record.get('label', 0)

                test_predictions.append({
                    'predicted': pred.get('direction', 'UNKNOWN'),
                    'actual': actual_label,
                    'confidence': pred.get('confidence', 0)
                })

            # Calculate metrics
            correct = sum(1 for p in test_predictions if (p['predicted'] == 'BULLISH' and p['actual'] > 0) or
                                                         (p['predicted'] == 'BEARISH' and p['actual'] < 0) or
                                                         (p['predicted'] == 'NEUTRAL' and p['actual'] == 0))
            accuracy = correct / len(test_predictions) if test_predictions else 0

            results.append({
                'period': f"{current_idx}-{current_idx + self.train_period + self.test_period}",
                'train_score': train_result.get('rf_score', 0),
                'test_accuracy': accuracy,
                'predictions_count': len(test_predictions),
                'train_result': train_result
            })

            # Roll forward
            current_idx += self.test_period

        self.validation_results = results
        return results

    def get_validation_summary(self) -> Dict:
        """Summary of walk-forward validation results"""
        if not self.validation_results:
            return {}

        avg_accuracy = np.mean([r['test_accuracy'] for r in self.validation_results])
        avg_train_score = np.mean([r['train_score'] for r in self.validation_results])

        return {
            'validation_periods': len(self.validation_results),
            'avg_test_accuracy': avg_accuracy,
            'avg_train_score': avg_train_score,
            'results': self.validation_results
        }


if __name__ == "__main__":
    gen = MLSignalGenerator(lookback_days=60)
    print("ML Signal Generator Status:")
    print(gen.model_status())

    # Example: Generate features and predict
    sample_quote = {
        'c': 100.0,
        'h': 102.0,
        'l': 98.0,
        'pc': 99.0,
        'bidV': 1000,
        'askV': 800
    }

    features = gen.engineer_features(sample_quote)
    if features is not None:
        print(f"\nEngineered features shape: {features.shape}")
        print(f"Features: {features}")
