from datetime import datetime
from app import db

class HistoricalMetrics(db.Model):
    """Stores aggregated historical metrics in PostgreSQL."""
    __tablename__ = 'historical_metrics'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    metric_type = db.Column(db.String(50), nullable=False)  # e.g., 'daily_steps', 'weekly_activity'
    value = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes for efficient querying
    __table_args__ = (
        db.Index('idx_metrics_user_date_type', 'user_id', 'date', 'metric_type'),
    )

    def __repr__(self):
        return f'<HistoricalMetrics {self.metric_type} for user {self.user_id} on {self.date}>'

    @classmethod
    def get_user_metrics(cls, user_id, start_date, end_date, metric_type=None):
        """Get historical metrics for a user within a date range."""
        query = cls.query.filter(
            cls.user_id == user_id,
            cls.date.between(start_date, end_date)
        )
        if metric_type:
            query = query.filter(cls.metric_type == metric_type)
        return query.order_by(cls.date).all()

    @classmethod
    def get_latest_metric(cls, user_id, metric_type):
        """Get the latest metric value for a user."""
        return cls.query.filter(
            cls.user_id == user_id,
            cls.metric_type == metric_type
        ).order_by(cls.date.desc()).first() 