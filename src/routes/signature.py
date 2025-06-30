from flask import Blueprint, request, jsonify
import uuid
import secrets
from datetime import datetime, timedelta
from src.models.signature import Signature
from src.models.document import Document
from src.models.user import Client
from src.extensions import db
from src.utils.auth import token_required, role_required, get_current_user, log_audit_action

signature_bp = Blueprint('signature', __name__)

@signature_bp.route('/signatures/request', methods=['POST'])
@token_required
@role_required(['admin', 'editor', 'sender'])
def request_signature():
    """Request signature for a document"""
    try:
        user = get_current_user()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['document_id', 'signer_email', 'signer_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'message': f'{field} is required'}), 400
        
        # Check if document exists and user has permission
        document = Document.query.get_or_404(data['document_id'])
        if user.role not in ['admin'] and document.created_by != user.id:
            return jsonify({'message': 'Access denied'}), 403
        
        # Generate access token for signature
        access_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=30)  # 30 days to sign
        
        # Create signature request
        signature = Signature(
            document_id=data['document_id'],
            signer_email=data['signer_email'],
            signer_name=data['signer_name'],
            signature_type=data.get('signature_type', 'electronic'),
            status='pending',
            access_token=access_token,
            expires_at=expires_at
        )
        
        db.session.add(signature)
        db.session.commit()
        
        # Log audit action
        log_audit_action('CREATE', 'SIGNATURE_REQUEST', signature.id, {
            'document_id': data['document_id'],
            'signer_email': data['signer_email']
        })
        
        # In a real implementation, you would send an email here
        signature_url = f"/sign/{access_token}"
        
        return jsonify({
            'message': 'Signature request created successfully',
            'signature': signature.to_dict(),
            'signature_url': signature_url
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Signature request failed', 'error': str(e)}), 500

@signature_bp.route('/signatures/sign/<access_token>', methods=['GET'])
def get_signature_details(access_token):
    """Get signature details for signing"""
    try:
        signature = Signature.query.filter_by(access_token=access_token).first_or_404()
        
        # Check if signature is still valid
        if signature.expires_at and signature.expires_at < datetime.utcnow():
            return jsonify({'message': 'Signature link has expired'}), 410
        
        if signature.status != 'pending':
            return jsonify({'message': 'Document already signed or declined'}), 409
        
        # Get document details
        document = Document.query.get(signature.document_id)
        if not document:
            return jsonify({'message': 'Document not found'}), 404
        
        # Return signature details without sensitive information
        return jsonify({
            'signature': {
                'id': signature.id,
                'document_title': document.title,
                'document_description': document.description,
                'signer_name': signature.signer_name,
                'signer_email': signature.signer_email,
                'expires_at': signature.expires_at.isoformat() if signature.expires_at else None,
                'status': signature.status
            },
            'document': {
                'id': document.id,
                'title': document.title,
                'description': document.description,
                'fields': [field.to_dict() for field in document.fields if field.field_type == 'signature']
            }
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to get signature details', 'error': str(e)}), 500

@signature_bp.route('/signatures/sign/<access_token>', methods=['POST'])
def sign_document(access_token):
    """Sign a document"""
    try:
        signature = Signature.query.filter_by(access_token=access_token).first_or_404()
        
        # Check if signature is still valid
        if signature.expires_at and signature.expires_at < datetime.utcnow():
            return jsonify({'message': 'Signature link has expired'}), 410
        
        if signature.status != 'pending':
            return jsonify({'message': 'Document already signed or declined'}), 409
        
        data = request.get_json()
        
        # Validate signature data
        if not data.get('signature_data'):
            return jsonify({'message': 'Signature data is required'}), 400
        
        # Update signature
        signature.signature_data = data['signature_data']
        signature.signed_at = datetime.utcnow()
        signature.status = 'signed'
        signature.ip_address = request.remote_addr
        signature.user_agent = request.headers.get('User-Agent')
        
        # In a real implementation, you would generate a timestamp token here
        signature.timestamp_token = f"timestamp_{uuid.uuid4()}"
        signature.certificate_info = {
            'signed_at': signature.signed_at.isoformat(),
            'ip_address': signature.ip_address,
            'user_agent': signature.user_agent,
            'signature_method': 'electronic'
        }
        
        # Update document status if all signatures are complete
        document = Document.query.get(signature.document_id)
        pending_signatures = Signature.query.filter_by(
            document_id=document.id,
            status='pending'
        ).count()
        
        if pending_signatures == 0:  # No more pending signatures
            document.status = 'completed'
        elif document.status == 'draft':
            document.status = 'sent'
        
        db.session.commit()
        
        # Log audit action
        log_audit_action('SIGN', 'DOCUMENT', document.id, {
            'signature_id': signature.id,
            'signer_email': signature.signer_email
        })
        
        return jsonify({
            'message': 'Document signed successfully',
            'signature': signature.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Signature failed', 'error': str(e)}), 500

@signature_bp.route('/signatures/decline/<access_token>', methods=['POST'])
def decline_signature(access_token):
    """Decline to sign a document"""
    try:
        signature = Signature.query.filter_by(access_token=access_token).first_or_404()
        
        # Check if signature is still valid
        if signature.expires_at and signature.expires_at < datetime.utcnow():
            return jsonify({'message': 'Signature link has expired'}), 410
        
        if signature.status != 'pending':
            return jsonify({'message': 'Document already signed or declined'}), 409
        
        data = request.get_json()
        reason = data.get('reason', 'No reason provided')
        
        # Update signature
        signature.status = 'declined'
        signature.signed_at = datetime.utcnow()
        signature.ip_address = request.remote_addr
        signature.user_agent = request.headers.get('User-Agent')
        signature.certificate_info = {
            'declined_at': signature.signed_at.isoformat(),
            'reason': reason,
            'ip_address': signature.ip_address,
            'user_agent': signature.user_agent
        }
        
        db.session.commit()
        
        # Log audit action
        log_audit_action('DECLINE', 'SIGNATURE', signature.id, {
            'reason': reason,
            'signer_email': signature.signer_email
        })
        
        return jsonify({
            'message': 'Signature declined successfully',
            'signature': signature.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Decline failed', 'error': str(e)}), 500

@signature_bp.route('/signatures', methods=['GET'])
@token_required
def list_signatures():
    """List signatures"""
    try:
        user = get_current_user()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status')
        
        query = Signature.query.join(Document)
        
        # Filter by user role
        if user.role not in ['admin']:
            query = query.filter(Document.created_by == user.id)
        
        # Filter by status if provided
        if status:
            query = query.filter(Signature.status == status)
        
        signatures = query.order_by(Signature.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'signatures': [sig.to_dict() for sig in signatures.items],
            'total': signatures.total,
            'pages': signatures.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch signatures', 'error': str(e)}), 500

@signature_bp.route('/signatures/<signature_id>', methods=['GET'])
@token_required
def get_signature(signature_id):
    """Get signature details"""
    try:
        user = get_current_user()
        signature = Signature.query.get_or_404(signature_id)
        
        # Check permissions
        document = Document.query.get(signature.document_id)
        if user.role not in ['admin'] and document.created_by != user.id:
            return jsonify({'message': 'Access denied'}), 403
        
        return jsonify({'signature': signature.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to fetch signature', 'error': str(e)}), 500

@signature_bp.route('/signatures/<signature_id>/resend', methods=['POST'])
@token_required
@role_required(['admin', 'editor', 'sender'])
def resend_signature(signature_id):
    """Resend signature request"""
    try:
        user = get_current_user()
        signature = Signature.query.get_or_404(signature_id)
        
        # Check permissions
        document = Document.query.get(signature.document_id)
        if user.role not in ['admin'] and document.created_by != user.id:
            return jsonify({'message': 'Access denied'}), 403
        
        if signature.status != 'pending':
            return jsonify({'message': 'Can only resend pending signatures'}), 409
        
        # Generate new access token and extend expiry
        signature.access_token = secrets.token_urlsafe(32)
        signature.expires_at = datetime.utcnow() + timedelta(days=30)
        
        db.session.commit()
        
        # Log audit action
        log_audit_action('RESEND', 'SIGNATURE_REQUEST', signature.id, {
            'signer_email': signature.signer_email
        })
        
        # In a real implementation, you would send an email here
        signature_url = f"/sign/{signature.access_token}"
        
        return jsonify({
            'message': 'Signature request resent successfully',
            'signature_url': signature_url
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Resend failed', 'error': str(e)}), 500

