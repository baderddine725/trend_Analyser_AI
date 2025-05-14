from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Float
from sqlalchemy.orm import relationship
from database import Base

class Platform(Base):
    __tablename__ = "platform"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    trends = relationship('Trend', back_populates='platform')

class Trend(Base):
    __tablename__ = "trend"

    id = Column(Integer, primary_key=True)
    text = Column(String(200), nullable=False)
    hashtags = Column(JSON)
    view_count = Column(Integer)
    platform_id = Column(Integer, ForeignKey('platform.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    platform = relationship('Platform', back_populates='trends')
    content_suggestions = relationship('Content', back_populates='trend')
    prediction_data = relationship('TrendPrediction', back_populates='trend')
    engagement_history = relationship('TrendEngagement', back_populates='trend')

class Content(Base):
    __tablename__ = "content"

    id = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False)
    suggestion = Column(String)
    format = Column(String(50))
    estimated_engagement = Column(String(20))
    trend_id = Column(Integer, ForeignKey('trend.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    trend = relationship('Trend', back_populates='content_suggestions')

class TrendPrediction(Base):
    __tablename__ = "trend_prediction"

    id = Column(Integer, primary_key=True)
    trend_id = Column(Integer, ForeignKey('trend.id'), nullable=False)
    predicted_views = Column(Integer)
    confidence_score = Column(Float)
    prediction_date = Column(DateTime)
    target_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    trend = relationship('Trend', back_populates='prediction_data')

class TrendEngagement(Base):
    __tablename__ = "trend_engagement"

    id = Column(Integer, primary_key=True)
    trend_id = Column(Integer, ForeignKey('trend.id'), nullable=False)
    view_count = Column(Integer)
    engagement_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    trend = relationship('Trend', back_populates='engagement_history')
