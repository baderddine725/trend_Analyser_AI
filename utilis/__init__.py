import logging
from datetime import datetime, timedelta
from statistics import mean, stdev
import numpy as np
from typing import List, Dict, Optional, Union, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class TrendData:
    timestamp: str
    view_count: int

@dataclass
class PredictionResult:
    date: str
    predicted_views: int
    confidence: float
    upper_bound: int
    lower_bound: int

class TrendPredictor:
    def __init__(self):
        self.sequence_length = 7  # Number of days to look back
        self.alpha = 0.3  # Smoothing factor for exponential smoothing

    def prepare_data(self, trends_data: List[Dict[str, Any]]) -> tuple[Optional[List[datetime]], Optional[List[int]]]:
        """Prepare time series data for prediction"""
        try:
            if not trends_data or len(trends_data) < 2:
                logger.warning("Insufficient data for prediction")
                return None, None

            # Convert trends data to list
            dates = [datetime.strptime(t['timestamp'], '%Y-%m-%d %H:%M:%S') for t in trends_data]
            values = [t['view_count'] for t in trends_data]

            return dates, values
        except Exception as e:
            logger.error(f"Error preparing data: {str(e)}")
            return None, None

    def exponential_smoothing(self, values: List[int]) -> List[int]:
        """Apply exponential smoothing to the time series"""
        result: List[int] = [values[0]]  # Initialize with first value
        for n in range(1, len(values)):
            # Convert float result to int
            smoothed_value = int(self.alpha * values[n] + (1 - self.alpha) * result[n-1])
            result.append(smoothed_value)
        return result

    def calculate_confidence_intervals(self, values: List[int], smoothed_values: List[int]) -> tuple[List[int], List[int]]:
        """Calculate upper and lower confidence bounds"""
        residuals = [v - s for v, s in zip(values, smoothed_values)]
        std_dev = int(stdev(residuals)) if len(residuals) > 1 else abs(mean(residuals)) if residuals else 0

        upper_bounds = [int(s + 2 * std_dev) for s in smoothed_values]
        lower_bounds = [max(0, int(s - 2 * std_dev)) for s in smoothed_values]

        return upper_bounds, lower_bounds

    def detect_seasonality(self, values: List[int]) -> Optional[int]:
        """Detect seasonal patterns in the data"""
        if len(values) < 14:  # Need at least 2 weeks of data
            return None

        # Simple autocorrelation for weekly patterns
        weekly_correlation = float(np.corrcoef(values[7:], values[:-7])[0,1])
        return 7 if abs(weekly_correlation) > 0.7 else None

    def predict_next_trends(self, current_trends: List[Dict[str, Any]], days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Predict trend metrics for the next n days using exponential smoothing"""
        try:
            dates, values = self.prepare_data(current_trends)
            if not dates or not values or len(values) < 2:
                return []

            # Apply exponential smoothing
            smoothed_values = self.exponential_smoothing(values)

            # Detect seasonality
            seasonal_period = self.detect_seasonality(values)

            # Calculate recent trend
            recent_changes = [smoothed_values[i] - smoothed_values[i-1] 
                            for i in range(max(1, len(smoothed_values)-self.sequence_length), len(smoothed_values))]
            recent_change = int(mean(recent_changes))

            predictions = []
            last_value = smoothed_values[-1]
            upper_bounds, lower_bounds = self.calculate_confidence_intervals(values, smoothed_values)

            for i in range(days_ahead):
                # Predict next value considering seasonality if detected
                if seasonal_period and len(values) >= seasonal_period:
                    seasonal_factor = values[-seasonal_period + (i % seasonal_period)] / max(1, values[-seasonal_period])
                    predicted_value = max(0, int((last_value + recent_change * (i + 1)) * seasonal_factor))
                else:
                    predicted_value = max(0, int(last_value + recent_change * (i + 1)))

                # Calculate prediction interval
                std_range = upper_bounds[-1] - lower_bounds[-1]
                confidence = 100 * (1 - min(1, (i/days_ahead + std_range/max(1, predicted_value)/4)))

                pred_date = dates[-1] + timedelta(days=i+1)

                predictions.append({
                    'date': pred_date.strftime('%Y-%m-%d'),
                    'predicted_views': predicted_value,
                    'confidence': round(max(0, min(100, confidence)), 2),
                    'upper_bound': int(predicted_value + std_range/2),
                    'lower_bound': max(0, int(predicted_value - std_range/2))
                })

            return predictions
        except Exception as e:
            logger.error(f"Error making predictions: {str(e)}")
            return []

    def get_trending_topics_forecast(self, historical_trends: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Analyze and forecast trending topics"""
        try:
            # Group trends by topic
            topic_trends: Dict[str, List[Dict[str, Any]]] = {}
            for trend in historical_trends:
                topic = trend['text'].lower()
                if topic not in topic_trends:
                    topic_trends[topic] = []
                topic_trends[topic].append({
                    'timestamp': trend['timestamp'],
                    'view_count': trend['view_count']
                })

            forecasts = {}
            for topic, trends in topic_trends.items():
                if len(trends) >= 2:  # Need at least 2 points for prediction
                    predictions = self.predict_next_trends(trends)
                    if predictions:
                        forecasts[topic] = predictions

            return forecasts
        except Exception as e:
            logger.error(f"Error generating topic forecast: {str(e)}")
            return {}
