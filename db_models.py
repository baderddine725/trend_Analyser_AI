from datetime import datetime
from db import db

class Platform(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    trends = db.relationship('Trend', backref='platform', lazy=True)

class Trend(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200), nullable=False)
    hashtags = db.Column(db.JSON)
    view_count = db.Column(db.Integer)
    platform_id = db.Column(db.Integer, db.ForeignKey('platform.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    content_suggestions = db.relationship('Content', backref='trend', lazy=True)

class Content(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)  # video, image, etc.
    suggestion = db.Column(db.Text, nullable=False)
    format = db.Column(db.String(50))
    estimated_engagement = db.Column(db.String(20))
    trend_id = db.Column(db.Integer, db.ForeignKey('trend.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
