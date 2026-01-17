"""
Database models for the deduplicator application.
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import os

Base = declarative_base()


class ScanSession(Base):
    """Represents a scan session (can be paused/resumed)"""
    __tablename__ = 'scan_sessions'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    created_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(50), default='pending')  # pending, running, paused, completed
    file_types = Column(Text)  # JSON string of selected file types
    similarity_threshold = Column(Float, default=0.95)
    
    scanned_paths = relationship('ScannedPath', back_populates='session', cascade='all, delete-orphan')
    duplicate_groups = relationship('DuplicateGroup', back_populates='session', cascade='all, delete-orphan')


class ScannedPath(Base):
    """Paths that were scanned in a session"""
    __tablename__ = 'scanned_paths'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('scan_sessions.id'))
    path = Column(Text)
    include_subdirs = Column(Boolean, default=True)
    processed = Column(Boolean, default=False)
    
    session = relationship('ScanSession', back_populates='scanned_paths')


class DuplicateGroup(Base):
    """A group of duplicate files"""
    __tablename__ = 'duplicate_groups'
    __table_args__ = (
        Index('idx_duplicate_groups_session_id', 'session_id'),
    )

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('scan_sessions.id'))
    file_type = Column(String(50))  # image, document, video, archive, code
    similarity_score = Column(Float)
    hash_value = Column(String(255), nullable=True)  # For exact duplicates

    session = relationship('ScanSession', back_populates='duplicate_groups')
    files = relationship('FileEntry', back_populates='group', cascade='all, delete-orphan')


class FileEntry(Base):
    """Individual file in a duplicate group"""
    __tablename__ = 'file_entries'
    __table_args__ = (
        Index('idx_file_entries_group_id', 'group_id'),
    )

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('duplicate_groups.id'))
    file_path = Column(Text)
    file_size = Column(Integer)
    modified_time = Column(DateTime)
    thumbnail_path = Column(Text, nullable=True)  # For images/videos
    file_metadata = Column(Text, nullable=True)  # JSON string for additional info
    marked_for_deletion = Column(Boolean, default=False)

    group = relationship('DuplicateGroup', back_populates='files')


class SortingSession(Base):
    """Represents an auto-sorting operation"""
    __tablename__ = 'sorting_sessions'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    created_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime, nullable=True)
    source_paths = Column(Text)  # JSON list of source paths
    destination_path = Column(Text)
    use_ml_categorization = Column(Boolean, default=False)
    status = Column(String(50), default='pending')


class Database:
    """Database handler"""
    
    def __init__(self, db_path='~/.local/share/deduplicator/deduplicator.db'):
        db_path = os.path.expanduser(db_path)
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def get_session(self):
        """Get a new database session"""
        return self.Session()
    
    def create_scan_session(self, name, file_types, similarity_threshold=0.95):
        """Create a new scan session"""
        session = self.get_session()
        scan_session = ScanSession(
            name=name,
            file_types=file_types,
            similarity_threshold=similarity_threshold
        )
        session.add(scan_session)
        session.commit()
        session_id = scan_session.id
        session.close()
        return session_id
    
    def get_scan_session(self, session_id):
        """Get a scan session by ID"""
        session = self.get_session()
        scan_session = session.query(ScanSession).filter_by(id=session_id).first()
        session.close()
        return scan_session
    
    def update_session_status(self, session_id, status):
        """Update session status"""
        session = self.get_session()
        scan_session = session.query(ScanSession).filter_by(id=session_id).first()
        if scan_session:
            scan_session.status = status
            if status == 'completed':
                scan_session.completed_at = datetime.now()
            session.commit()
        session.close()
