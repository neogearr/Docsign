import uuid
from datetime import datetime
from src.extensions import db

class Signature(db.Model):
    __tablename__ = 'signatures'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = db.Column(db.String(36), db.ForeignKey('documents.id'), nullable=False)
    signer_email = db.Column(db.String(255), nullable=False)
    signer_name = db.Column(db.String(255), nullable=False)
    signature_type = db.Column(db.String(50), default='electronic')
    signature_data = db.Column(db.Text)
    ip_address = db.Column(db.String(45))  # IPv6 compatible
    user_agent = db.Column(db.Text)
    signed_at = db.Column(db.DateTime)
    certificate_info = db.Column(db.JSON)
    timestamp_token = db.Column(db.Text)
    status = db.Column(db.String(50), default='pending')
    access_token = db.Column(db.String(255), unique=True)
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Signature {self.signer_email} - {self.status}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'document_id': self.document_id,
            'signer_email': self.signer_email,
            'signer_name': self.signer_name,
            'signature_type': self.signature_type,
            'signature_data': self.signature_data,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'signed_at': self.signed_at.isoformat() if self.signed_at else None,
            'certificate_info': self.certificate_info,
            'timestamp_token': self.timestamp_token,
            'status': self.status,
            'access_token': self.access_token,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False)
    resource_id = db.Column(db.String(36))
    details = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='audit_logs')
    
    def __repr__(self):
        return f'<AuditLog {self.action} - {self.resource_type}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'details': self.details,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    related_document_id = db.Column(db.String(36), db.ForeignKey('documents.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='notifications')
    related_document = db.relationship('Document', backref='notifications')
    
    def __repr__(self):
        return f'<Notification {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'is_read': self.is_read,
            'related_document_id': self.related_document_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

