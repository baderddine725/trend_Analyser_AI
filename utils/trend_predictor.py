import logging
from datetime import datetime, timedelta
from statistics import mean, stdev
import math

logger = logging.getLogger(__name__)

class TrendPredictor:
    def __init__(self):
        self.sequence_length = 7  # Number of days to look back

    def prepare_data(self, trends_data):
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

    def predict_next_trends(self, current_trends, days_ahead=7):
        """Predict trend metrics for the next n days using simple moving average"""
        try:
            dates, values = self.prepare_data(current_trends)
            if not dates or len(values) < 2:
                return []

            predictions = []

            # Calculate trend using simple moving average and standard deviation
            recent_values = values[-self.sequence_length:] if len(values) > self.sequence_length else values
            avg_change = mean([values[i] - values[i-1] for i in range(1, len(recent_values))])
            baseline = recent_values[-1]

            # Calculate volatility for confidence scoring
            try:
                volatility = stdev(recent_values) / mean(recent_values) if len(recent_values) > 1 else 0.5
            except (ZeroDivisionError, ValueError):
                volatility = 0.5

            for i in range(days_ahead):
                # Predict next value using baseline + trend
                predicted_value = max(0, baseline + (avg_change * (i + 1)))

                # Calculate prediction date
                pred_date = (dates[-1] if dates else datetime.utcnow()) + timedelta(days=i+1)

                # Calculate confidence score based on prediction distance and volatility
                confidence = 100 * (1 - min(1, (i/days_ahead + volatility)))

                predictions.append({
                    'date': pred_date.strftime('%Y-%m-%d'),
                    'predicted_views': int(predicted_value),
                    'confidence': round(max(0, min(100, confidence)), 2)
                })

            return predictions
        except Exception as e:
            logger.error(f"Error making predictions: {str(e)}")
            return []

    def get_trending_topics_forecast(self, historical_trends):
        """Analyze and forecast trending topics"""
        try:
            # Group trends by topic
            topic_trends = {}
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