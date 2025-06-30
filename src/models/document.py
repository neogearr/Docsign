import uuid
from datetime import datetime
from src.extensions import db

class DocumentTemplate(db.Model):
    __tablename__ = 'document_templates'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.BigInteger)
    mime_type = db.Column(db.String(100))
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', backref='document_templates')
    documents = db.relationship('Document', backref='template', lazy=True)
    
    def __repr__(self):
        return f'<DocumentTemplate {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'created_by': self.created_by,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    template_id = db.Column(db.String(36), db.ForeignKey('document_templates.id'))
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.BigInteger)
    mime_type = db.Column(db.String(100))
    status = db.Column(db.String(50), default='draft')
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'))
    assigned_to = db.Column(db.String(36), db.ForeignKey('clients.id'))
    signature_workflow = db.Column(db.String(20), default='parallel')
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', backref='documents')
    assignee = db.relationship('Client', backref='assigned_documents')
    fields = db.relationship('DocumentField', backref='document', lazy=True, cascade='all, delete-orphan')
    signatures = db.relationship('Signature', backref='document', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Document {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'template_id': self.template_id,
            'title': self.title,
            'description': self.description,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'status': self.status,
            'created_by': self.created_by,
            'assigned_to': self.assigned_to,
            'signature_workflow': self.signature_workflow,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class DocumentField(db.Model):
    __tablename__ = 'document_fields'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = db.Column(db.String(36), db.ForeignKey('documents.id'), nullable=False)
    field_name = db.Column(db.String(255), nullable=False)
    field_type = db.Column(db.String(50), nullable=False)
    field_value = db.Column(db.Text)
    is_required = db.Column(db.Boolean, default=False)
    is_editable = db.Column(db.Boolean, default=True)
    editable_by_role = db.Column(db.String(50))
    position_x = db.Column(db.Float)
    position_y = db.Column(db.Float)
    width = db.Column(db.Float)
    height = db.Column(db.Float)
    page_number = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<DocumentField {self.field_name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'document_id': self.document_id,
            'field_name': self.field_name,
            'field_type': self.field_type,
            'field_value': self.field_value,
            'is_required': self.is_required,
            'is_editable': self.is_editable,
            'editable_by_role': self.editable_by_role,
            'position_x': self.position_x,
            'position_y': self.position_y,
            'width': self.width,
            'height': self.height,
            'page_number': self.page_number,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

