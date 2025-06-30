import uuid
from datetime import datetime
from src.extensions import db

class Tenant(db.Model):
    __tablename__ = 'tenants'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)
    subdomain = db.Column(db.String(100), unique=True, nullable=False)
    plan_type = db.Column(db.String(50), nullable=False, default='basic')
    max_users = db.Column(db.Integer, default=10)
    max_documents = db.Column(db.Integer, default=100)
    max_signatures = db.Column(db.Integer, default=500)
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', backref='tenant', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'subdomain': self.subdomain,
            'plan_type': self.plan_type,
            'max_users': self.max_users,
            'max_documents': self.max_documents,
            'max_signatures': self.max_signatures,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Tenant {self.name}>'

