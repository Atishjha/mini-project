# backend/app/models/user.py
from .database import db
from datetime import datetime
import hashlib

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(50), default='public')
    department = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        """Hash password (simple - use bcrypt in production)"""
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    def check_password(self, password):
        """Verify password"""
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()

class CallerHistory(db.Model):
    __tablename__ = 'caller_history'
    
    id = db.Column(db.Integer, primary_key=True)
    caller_id = db.Column(db.String(100), nullable=False, index=True)
    caller_type = db.Column(db.String(50))
    total_reports = db.Column(db.Integer, default=0)
    false_reports = db.Column(db.Integer, default=0)
    last_report = db.Column(db.DateTime)
    reputation_score = db.Column(db.Float, default=0.5)
    
    def update_reputation(self):
        """Calculate reputation score"""
        if self.total_reports > 0:
            accuracy = 1.0 - (self.false_reports / self.total_reports)
            self.reputation_score = accuracy
        db.session.commit()