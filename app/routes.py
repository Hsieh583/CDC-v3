from flask import Blueprint, request, jsonify, send_file
from app.models import db, Case, Document, StatusHistory
from app.sharepoint_service import SharePointService
from app.excel_template import create_procurement_template, create_blank_template
from datetime import datetime
from werkzeug.utils import secure_filename
import os

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Valid status values
VALID_STATUSES = ['Draft', 'Submitted', 'Approved', 'Closed', 'Rejected']


def get_sharepoint_service():
    """Get SharePoint service instance"""
    from flask import current_app
    return SharePointService(current_app.config)


def generate_case_number(prefix='CDC-PR'):
    """
    Generate unique case number
    Format: CDC-PR-YYYY-NNNNN
    """
    year = datetime.now().year
    
    # Get the count of cases created this year
    year_start = datetime(year, 1, 1)
    count = Case.query.filter(Case.created_at >= year_start).count()
    
    # Generate case number
    case_number = f"{prefix}-{year}-{count + 1:05d}"
    
    # Ensure uniqueness
    while Case.query.filter_by(case_number=case_number).first():
        count += 1
        case_number = f"{prefix}-{year}-{count + 1:05d}"
    
    return case_number


@api_bp.route('/cases', methods=['GET'])
def list_cases():
    """
    List all cases with optional filtering
    GET /api/cases?status=Draft&page=1&per_page=20
    """
    try:
        # Get query parameters
        status = request.args.get('status')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '').strip()
        
        # Build query
        query = Case.query
        
        if status:
            query = query.filter_by(current_status=status)
        
        if search:
            query = query.filter(
                db.or_(
                    Case.case_number.like(f'%{search}%'),
                    Case.title.like(f'%{search}%')
                )
            )
        
        # Order by created date descending
        query = query.order_by(Case.created_at.desc())
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'cases': [case.to_dict() for case in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/cases/<int:case_id>', methods=['GET'])
def get_case(case_id):
    """
    Get case details
    GET /api/cases/{id}
    """
    try:
        case = Case.query.get_or_404(case_id)
        
        # Get case details with documents and history
        case_dict = case.to_dict()
        case_dict['documents'] = [doc.to_dict() for doc in case.documents]
        case_dict['status_history'] = [h.to_dict() for h in 
                                       sorted(case.status_history, 
                                              key=lambda x: x.changed_at, 
                                              reverse=True)]
        
        return jsonify({
            'success': True,
            'case': case_dict
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/cases', methods=['POST'])
def create_case():
    """
    Create a new case
    POST /api/cases
    Body: {title: string, notes: string}
    """
    try:
        data = request.get_json()
        title = data.get('title', '').strip()
        notes = data.get('notes', '').strip()
        
        # Generate case number
        case_number = generate_case_number()
        
        # Create SharePoint folder
        sp_service = get_sharepoint_service()
        success, folder_path = sp_service.create_case_folder(case_number)
        
        if not success:
            return jsonify({
                'success': False,
                'error': f'Failed to create folder: {folder_path}'
            }), 500
        
        # Create case in database
        case = Case(
            case_number=case_number,
            title=title,
            current_status='Draft',
            sharepoint_folder_path=folder_path,
            notes=notes
        )
        db.session.add(case)
        
        # Add initial status history
        status_history = StatusHistory(
            case=case,
            old_status=None,
            new_status='Draft',
            notes='Case created'
        )
        db.session.add(status_history)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'case': case.to_dict(),
            'message': f'Case {case_number} created successfully'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/cases/<int:case_id>/documents', methods=['POST'])
def upload_document(case_id):
    """
    Upload document(s) to a case
    POST /api/cases/{id}/documents
    Form data: file (required), doc_type (main/attachment), notes (optional)
    """
    try:
        case = Case.query.get_or_404(case_id)
        
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        doc_type = request.form.get('doc_type', 'attachment')
        notes = request.form.get('notes', '').strip()
        
        # Validate doc_type
        if doc_type not in ['main', 'attachment']:
            return jsonify({
                'success': False,
                'error': 'Invalid doc_type. Must be "main" or "attachment"'
            }), 400
        
        # Check if main document already exists
        if doc_type == 'main':
            existing_main = Document.query.filter_by(
                case_id=case_id, 
                doc_type='main'
            ).first()
            if existing_main:
                return jsonify({
                    'success': False,
                    'error': 'Main document already exists. Please delete it first or upload as attachment.'
                }), 400
        
        # Upload file to SharePoint/local storage
        sp_service = get_sharepoint_service()
        original_filename = file.filename
        safe_filename = secure_filename(original_filename)
        
        success, file_path, error = sp_service.upload_file(
            case.case_number, 
            file, 
            safe_filename
        )
        
        if not success:
            return jsonify({
                'success': False,
                'error': error or 'Failed to upload file'
            }), 500
        
        # Create document record
        document = Document(
            case_id=case_id,
            doc_type=doc_type,
            filename=safe_filename,
            original_filename=original_filename,
            file_size=request.content_length,
            mime_type=file.content_type,
            sharepoint_path=file_path if sp_service.sharepoint_enabled else None,
            local_path=file_path if not sp_service.sharepoint_enabled else None,
            notes=notes
        )
        db.session.add(document)
        
        # Update case timestamp
        case.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'document': document.to_dict(),
            'message': 'Document uploaded successfully'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/cases/<int:case_id>/status', methods=['PUT'])
def update_case_status(case_id):
    """
    Update case status
    PUT /api/cases/{id}/status
    Body: {status: string, notes: string}
    """
    try:
        case = Case.query.get_or_404(case_id)
        data = request.get_json()
        
        new_status = data.get('status', '').strip()
        notes = data.get('notes', '').strip()
        
        if not new_status:
            return jsonify({
                'success': False,
                'error': 'Status is required'
            }), 400
        
        if new_status not in VALID_STATUSES:
            return jsonify({
                'success': False,
                'error': f'Invalid status. Valid statuses: {", ".join(VALID_STATUSES)}'
            }), 400
        
        # Record status change
        old_status = case.current_status
        
        if old_status != new_status:
            status_history = StatusHistory(
                case=case,
                old_status=old_status,
                new_status=new_status,
                notes=notes
            )
            db.session.add(status_history)
            
            case.current_status = new_status
            case.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'case': case.to_dict(),
                'message': f'Status updated from {old_status} to {new_status}'
            })
        else:
            return jsonify({
                'success': True,
                'message': 'Status unchanged'
            })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/cases/<int:case_id>/template', methods=['GET'])
def download_case_template(case_id):
    """
    Download Excel template for a case
    GET /api/cases/{id}/template
    """
    try:
        case = Case.query.get_or_404(case_id)
        
        # Generate Excel template
        template = create_procurement_template(case.case_number, case.title or '')
        
        filename = f"{case.case_number}_procurement_request.xlsx"
        
        return send_file(
            template,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/template/blank', methods=['GET'])
def download_blank_template():
    """
    Download blank Excel template
    GET /api/template/blank
    """
    try:
        template = create_blank_template()
        
        return send_file(
            template,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='procurement_request_template.xlsx'
        )
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/stats', methods=['GET'])
def get_stats():
    """
    Get dashboard statistics
    GET /api/stats
    """
    try:
        total_cases = Case.query.count()
        draft_cases = Case.query.filter_by(current_status='Draft').count()
        submitted_cases = Case.query.filter_by(current_status='Submitted').count()
        approved_cases = Case.query.filter_by(current_status='Approved').count()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_cases': total_cases,
                'draft_cases': draft_cases,
                'submitted_cases': submitted_cases,
                'approved_cases': approved_cases
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
