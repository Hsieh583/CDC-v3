from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Case(db.Model):
    """Procurement case model - 請購案件主索引"""
    __tablename__ = 'cases'
    
    id = db.Column(db.Integer, primary_key=True)
    case_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    title = db.Column(db.String(200), nullable=True)
    current_status = db.Column(db.String(20), nullable=False, default='Draft')
    sharepoint_folder_path = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    documents = db.relationship('Document', backref='case', lazy=True, cascade='all, delete-orphan')
    status_history = db.relationship('StatusHistory', backref='case', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert case to dictionary"""
        return {
            'id': self.id,
            'case_number': self.case_number,
            'title': self.title,
            'current_status': self.current_status,
            'sharepoint_folder_path': self.sharepoint_folder_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'notes': self.notes,
            'document_count': len(self.documents),
            'main_document_exists': any(d.doc_type == 'main' for d in self.documents)
        }


class Document(db.Model):
    """Document model - 文件關聯"""
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('cases.id'), nullable=False, index=True)
    doc_type = db.Column(db.String(20), nullable=False)  # 'main' or 'attachment'
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=True)
    mime_type = db.Column(db.String(100), nullable=True)
    sharepoint_path = db.Column(db.String(500), nullable=True)
    local_path = db.Column(db.String(500), nullable=True)
    uploaded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)
    
    def to_dict(self):
        """Convert document to dictionary"""
        return {
            'id': self.id,
            'case_id': self.case_id,
            'doc_type': self.doc_type,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'notes': self.notes
        }


class StatusHistory(db.Model):
    """Status history model - 狀態歷程"""
    __tablename__ = 'status_history'
    
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('cases.id'), nullable=False, index=True)
    old_status = db.Column(db.String(20), nullable=True)
    new_status = db.Column(db.String(20), nullable=False)
    changed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    changed_by = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    def to_dict(self):
        """Convert status history to dictionary"""
        return {
            'id': self.id,
            'case_id': self.case_id,
            'old_status': self.old_status,
            'new_status': self.new_status,
            'changed_at': self.changed_at.isoformat() if self.changed_at else None,
            'changed_by': self.changed_by,
            'notes': self.notes
        }
