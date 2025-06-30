from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
from src.models.document import Document, DocumentTemplate, DocumentField
from src.models.user import User
from src.extensions import db
from src.utils.auth import token_required, role_required, get_current_user, log_audit_action

document_bp = Blueprint('document', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@document_bp.route('/documents/templates', methods=['POST'])
@token_required
@role_required(['admin', 'editor'])
def upload_template():
    """Upload a document template"""
    try:
        user = get_current_user()
        
        if 'file' not in request.files:
            return jsonify({'message': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'message': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'message': 'File type not allowed'}), 400
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(os.getcwd(), 'uploads', 'templates')
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)
        
        # Create template record
        template = DocumentTemplate(
            name=request.form.get('name', filename),
            description=request.form.get('description'),
            file_path=file_path,
            file_size=os.path.getsize(file_path),
            mime_type=file.content_type,
            created_by=user.id
        )
        
        db.session.add(template)
        db.session.commit()
        
        # Log audit action
        log_audit_action('CREATE', 'TEMPLATE', template.id, {'name': template.name})
        
        return jsonify({
            'message': 'Template uploaded successfully',
            'template': template.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Template upload failed', 'error': str(e)}), 500

@document_bp.route('/documents/templates', methods=['GET'])
@token_required
def list_templates():
    """List document templates"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        templates = DocumentTemplate.query.filter_by(is_active=True).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'templates': [template.to_dict() for template in templates.items],
            'total': templates.total,
            'pages': templates.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch templates', 'error': str(e)}), 500

@document_bp.route('/documents', methods=['POST'])
@token_required
@role_required(['admin', 'editor', 'sender'])
def create_document():
    """Create a new document"""
    try:
        user = get_current_user()
        data = request.get_json()
        
        # Validate required fields
        if not data.get('title'):
            return jsonify({'message': 'Title is required'}), 400
        
        # Create document
        document = Document(
            template_id=data.get('template_id'),
            title=data['title'],
            description=data.get('description'),
            file_path=data.get('file_path', ''),  # Will be set when file is uploaded
            status='draft',
            created_by=user.id,
            assigned_to=data.get('assigned_to'),
            signature_workflow=data.get('signature_workflow', 'parallel'),
            expires_at=datetime.fromisoformat(data['expires_at']) if data.get('expires_at') else None
        )
        
        db.session.add(document)
        db.session.flush()  # Get the document ID
        
        # Add document fields if provided
        if data.get('fields'):
            for field_data in data['fields']:
                field = DocumentField(
                    document_id=document.id,
                    field_name=field_data['field_name'],
                    field_type=field_data['field_type'],
                    field_value=field_data.get('field_value'),
                    is_required=field_data.get('is_required', False),
                    is_editable=field_data.get('is_editable', True),
                    editable_by_role=field_data.get('editable_by_role'),
                    position_x=field_data.get('position_x'),
                    position_y=field_data.get('position_y'),
                    width=field_data.get('width'),
                    height=field_data.get('height'),
                    page_number=field_data.get('page_number', 1)
                )
                db.session.add(field)
        
        db.session.commit()
        
        # Log audit action
        log_audit_action('CREATE', 'DOCUMENT', document.id, {'title': document.title})
        
        return jsonify({
            'message': 'Document created successfully',
            'document': document.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Document creation failed', 'error': str(e)}), 500

@document_bp.route('/documents', methods=['GET'])
@token_required
def list_documents():
    """List documents"""
    try:
        user = get_current_user()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status')
        
        query = Document.query
        
        # Filter by user role
        if user.role not in ['admin']:
            query = query.filter_by(created_by=user.id)
        
        # Filter by status if provided
        if status:
            query = query.filter_by(status=status)
        
        documents = query.order_by(Document.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'documents': [doc.to_dict() for doc in documents.items],
            'total': documents.total,
            'pages': documents.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch documents', 'error': str(e)}), 500

@document_bp.route('/documents/<document_id>', methods=['GET'])
@token_required
def get_document(document_id):
    """Get document details"""
    try:
        user = get_current_user()
        document = Document.query.get_or_404(document_id)
        
        # Check permissions
        if user.role not in ['admin'] and document.created_by != user.id:
            return jsonify({'message': 'Access denied'}), 403
        
        # Include fields in response
        document_data = document.to_dict()
        document_data['fields'] = [field.to_dict() for field in document.fields]
        
        return jsonify({'document': document_data}), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch document', 'error': str(e)}), 500

@document_bp.route('/documents/<document_id>', methods=['PUT'])
@token_required
@role_required(['admin', 'editor'])
def update_document(document_id):
    """Update document"""
    try:
        user = get_current_user()
        document = Document.query.get_or_404(document_id)
        
        # Check permissions
        if user.role not in ['admin'] and document.created_by != user.id:
            return jsonify({'message': 'Access denied'}), 403
        
        data = request.get_json()
        
        # Update allowed fields
        if 'title' in data:
            document.title = data['title']
        if 'description' in data:
            document.description = data['description']
        if 'status' in data:
            document.status = data['status']
        if 'assigned_to' in data:
            document.assigned_to = data['assigned_to']
        if 'expires_at' in data:
            document.expires_at = datetime.fromisoformat(data['expires_at']) if data['expires_at'] else None
        
        document.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Log audit action
        log_audit_action('UPDATE', 'DOCUMENT', document.id, data)
        
        return jsonify({
            'message': 'Document updated successfully',
            'document': document.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Document update failed', 'error': str(e)}), 500

@document_bp.route('/documents/<document_id>/fields', methods=['POST'])
@token_required
@role_required(['admin', 'editor'])
def add_document_field(document_id):
    """Add field to document"""
    try:
        user = get_current_user()
        document = Document.query.get_or_404(document_id)
        
        # Check permissions
        if user.role not in ['admin'] and document.created_by != user.id:
            return jsonify({'message': 'Access denied'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('field_name') or not data.get('field_type'):
            return jsonify({'message': 'Field name and type are required'}), 400
        
        field = DocumentField(
            document_id=document_id,
            field_name=data['field_name'],
            field_type=data['field_type'],
            field_value=data.get('field_value'),
            is_required=data.get('is_required', False),
            is_editable=data.get('is_editable', True),
            editable_by_role=data.get('editable_by_role'),
            position_x=data.get('position_x'),
            position_y=data.get('position_y'),
            width=data.get('width'),
            height=data.get('height'),
            page_number=data.get('page_number', 1)
        )
        
        db.session.add(field)
        db.session.commit()
        
        # Log audit action
        log_audit_action('CREATE', 'DOCUMENT_FIELD', field.id, {'field_name': field.field_name})
        
        return jsonify({
            'message': 'Field added successfully',
            'field': field.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Field creation failed', 'error': str(e)}), 500

@document_bp.route('/documents/<document_id>/fields/<field_id>', methods=['PUT'])
@token_required
def update_document_field(document_id, field_id):
    """Update document field"""
    try:
        user = get_current_user()
        field = DocumentField.query.filter_by(id=field_id, document_id=document_id).first_or_404()
        document = field.document
        
        # Check permissions
        if not field.is_editable:
            return jsonify({'message': 'Field is not editable'}), 403
        
        if field.editable_by_role and user.role not in [field.editable_by_role, 'admin']:
            return jsonify({'message': 'Insufficient permissions to edit this field'}), 403
        
        data = request.get_json()
        
        # Update field value
        if 'field_value' in data:
            field.field_value = data['field_value']
        
        field.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Log audit action
        log_audit_action('UPDATE', 'DOCUMENT_FIELD', field.id, data)
        
        return jsonify({
            'message': 'Field updated successfully',
            'field': field.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Field update failed', 'error': str(e)}), 500

