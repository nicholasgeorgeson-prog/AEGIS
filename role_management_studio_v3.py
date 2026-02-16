"""
Role Management Studio v3.0
Enterprise Role Extraction, Document Registry, and Responsibility Aggregation

KEY FEATURES:
- Document Registry: Track all source documents with status (active/retired/modified)
- Role-Document Mapping: Know exactly which documents mention each role
- Responsibility Aggregation: Consolidate all responsibilities per role across documents
- Export API: Structured data for external tools

Author: Nick / SAIC Systems Engineering
For: Technical Review Tool Integration
"""

import os
import sys
import json
import hashlib
import shutil
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from contextlib import contextmanager
import re
import csv

# Structured logging support
try:
    from config_logging import get_logger
    _logger = get_logger('role_studio')
except ImportError:
    _logger = None

def _log(message: str, level: str = 'info', **kwargs):
    """Internal logging helper with fallback."""
    if _logger:
        getattr(_logger, level)(message, **kwargs)
    elif level in ('warning', 'error', 'critical'):
        print(f"[RoleStudio] {level.upper()}: {message}")

# Ensure core extractor is available
try:
    from role_extractor_v3 import RoleExtractor, ExtractedRole, RoleOccurrence
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from role_extractor_v3 import RoleExtractor, ExtractedRole, RoleOccurrence


# =============================================================================
# CONFIGURATION / SETTINGS
# =============================================================================

@dataclass
class StudioSettings:
    """User-configurable settings."""
    
    database_path: str = "role_database.json"
    use_shared_drive: bool = False
    shared_drive_path: str = ""
    
    user_name: str = ""
    user_email: str = ""
    organization: str = ""
    
    auto_save: bool = True
    lock_timeout: int = 60
    backup_on_save: bool = True
    max_backups: int = 10
    
    default_category: str = "Other"
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'StudioSettings':
        defaults = cls()
        for key, value in data.items():
            if hasattr(defaults, key):
                setattr(defaults, key, value)
        return defaults
    
    def get_effective_db_path(self) -> str:
        if self.use_shared_drive and self.shared_drive_path:
            return os.path.join(self.shared_drive_path, "role_database.json")
        return self.database_path
    
    def get_lock_file_path(self) -> str:
        return self.get_effective_db_path() + ".lock"
    
    def get_settings_path(self) -> str:
        return os.path.join(os.path.expanduser("~"), ".role_studio_settings.json")
    
    def save(self):
        with open(self.get_settings_path(), 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls) -> 'StudioSettings':
        settings = cls()
        settings_path = settings.get_settings_path()
        if os.path.exists(settings_path):
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    return cls.from_dict(json.load(f))
            except Exception:  # Intentionally ignored
                pass
        return settings


# =============================================================================
# FILE LOCKING
# =============================================================================

class FileLock:
    """File-based locking for concurrent access."""
    
    def __init__(self, lock_path: str, timeout: int = 60, user_id: str = None):
        self.lock_path = lock_path
        self.timeout = timeout
        self.user_id = user_id or f"{os.environ.get('USER', 'user')}@{uuid.uuid4().hex[:8]}"
        self._lock_acquired = False
    
    def acquire(self) -> bool:
        start_time = time.time()
        while time.time() - start_time < self.timeout:
            try:
                if os.path.exists(self.lock_path):
                    lock_age = time.time() - os.path.getmtime(self.lock_path)
                    if lock_age > 300:
                        try:
                            os.remove(self.lock_path)
                        except Exception:  # Intentionally ignored
                            pass
                    else:
                        try:
                            with open(self.lock_path, 'r', encoding='utf-8') as f:
                                lock_info = json.load(f)
                            if lock_info.get('user_id') == self.user_id:
                                self._lock_acquired = True
                                return True
                            time.sleep(1)
                            continue
                        except Exception:  # Caught and handled
                            try:
                                os.remove(self.lock_path)
                            except Exception:  # Intentionally ignored
                                pass
                
                lock_info = {
                    'user_id': self.user_id,
                    'timestamp': datetime.now().isoformat(),
                    'hostname': os.environ.get('COMPUTERNAME', os.environ.get('HOSTNAME', 'unknown')),
                    'pid': os.getpid()
                }
                
                fd = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    json.dump(lock_info, f)
                
                self._lock_acquired = True
                return True
                
            except FileExistsError:
                time.sleep(0.5)
            except OSError:
                time.sleep(1)
        
        return False
    
    def release(self):
        if self._lock_acquired:
            try:
                if os.path.exists(self.lock_path):
                    with open(self.lock_path, 'r', encoding='utf-8') as f:
                        lock_info = json.load(f)
                    if lock_info.get('user_id') == self.user_id:
                        os.remove(self.lock_path)
            except Exception:  # Intentionally ignored
                pass
            finally:
                self._lock_acquired = False
    
    def __enter__(self):
        if not self.acquire():
            raise TimeoutError(f"Could not acquire lock on {self.lock_path}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return False


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class SourceDocument:
    """
    A source document in the registry.
    Tracks document metadata and status.
    """
    id: str
    filename: str
    filepath: str
    document_type: str  # e.g., "Standard", "Specification", "Contract", "Process", "Manual"
    title: str
    version: str
    revision: str
    status: str  # "active", "retired", "superseded", "draft"
    
    # Dates
    date_added: str
    date_modified: str
    effective_date: str
    retirement_date: str
    
    # Metadata
    added_by: str
    modified_by: str
    description: str
    notes: str
    tags: List[str]
    
    # Processing info
    last_processed: str
    roles_found: int
    processing_notes: str
    
    # Relationships
    supersedes: List[str]  # Document IDs this supersedes
    superseded_by: str  # Document ID that supersedes this
    related_documents: List[str]
    
    custom_fields: Dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SourceDocument':
        defaults = {
            'id': '', 'filename': '', 'filepath': '', 'document_type': 'Other',
            'title': '', 'version': '', 'revision': '', 'status': 'active',
            'date_added': datetime.now().isoformat(),
            'date_modified': datetime.now().isoformat(),
            'effective_date': '', 'retirement_date': '',
            'added_by': '', 'modified_by': '', 'description': '', 'notes': '',
            'tags': [], 'last_processed': '', 'roles_found': 0, 'processing_notes': '',
            'supersedes': [], 'superseded_by': '', 'related_documents': [],
            'custom_fields': {}
        }
        defaults.update(data)
        return cls(**{k: v for k, v in defaults.items() if k in cls.__dataclass_fields__})
    
    @classmethod
    def create_new(cls, filepath: str, doc_type: str = "Other", 
                   user_name: str = "") -> 'SourceDocument':
        """Create a new document entry from a file path."""
        filename = os.path.basename(filepath)
        now = datetime.now().isoformat()
        
        # Try to extract version/revision from filename
        version = ""
        revision = ""
        
        # Common patterns: "Doc_v1.2.docx", "Doc_Rev_A.pdf", "Doc_1.0.docx"
        version_match = re.search(r'[_\s]v?(\d+\.?\d*)', filename, re.IGNORECASE)
        if version_match:
            version = version_match.group(1)
        
        rev_match = re.search(r'[_\s]rev[_\s]?([a-z0-9]+)', filename, re.IGNORECASE)
        if rev_match:
            revision = rev_match.group(1).upper()
        
        return cls(
            id=hashlib.md5(f"{filepath}{now}".encode()).hexdigest()[:12],
            filename=filename,
            filepath=filepath,
            document_type=doc_type,
            title=os.path.splitext(filename)[0],
            version=version,
            revision=revision,
            status='active',
            date_added=now,
            date_modified=now,
            effective_date="",
            retirement_date="",
            added_by=user_name,
            modified_by=user_name,
            description="",
            notes="",
            tags=[],
            last_processed="",
            roles_found=0,
            processing_notes="",
            supersedes=[],
            superseded_by="",
            related_documents=[],
            custom_fields={}
        )


@dataclass
class RoleResponsibility:
    """
    A single responsibility statement for a role.
    Tracks the source document and context.
    """
    id: str
    role_id: str
    responsibility_text: str
    action_verb: str  # e.g., "shall", "reviews", "approves"
    
    # Source tracking
    source_document_id: str
    source_document_name: str
    source_location: str  # Section, paragraph, etc.
    source_context: str  # Surrounding text for context
    
    # Metadata
    date_added: str
    added_by: str
    is_active: bool  # False if source document is retired
    confidence: float
    
    # Classification
    responsibility_type: str  # "primary", "secondary", "coordination", "approval", "review"
    category: str  # e.g., "Design", "Test", "Quality", "Documentation"
    
    notes: str = ""
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'RoleResponsibility':
        defaults = {
            'id': '', 'role_id': '', 'responsibility_text': '', 'action_verb': '',
            'source_document_id': '', 'source_document_name': '', 'source_location': '',
            'source_context': '', 'date_added': datetime.now().isoformat(),
            'added_by': '', 'is_active': True, 'confidence': 0.8,
            'responsibility_type': 'primary', 'category': 'General', 'notes': ''
        }
        defaults.update(data)
        return cls(**{k: v for k, v in defaults.items() if k in cls.__dataclass_fields__})


@dataclass
class StandardRole:
    """A standardized role definition."""
    id: str
    canonical_name: str
    category: str
    subcategory: str
    description: str
    
    # These are now summary fields - details are in RoleResponsibility entries
    typical_responsibilities: List[str]
    typical_actions: List[str]
    aliases: List[str]
    
    # Relationships
    reports_to: List[str]
    coordinates_with: List[str]
    supervises: List[str]
    
    # Qualifications
    required_skills: List[str]
    certifications: List[str]
    
    # Metadata
    created_date: str
    modified_date: str
    usage_count: int
    confidence_avg: float
    is_approved: bool
    approved_by: str
    notes: str
    last_modified_by: str
    
    # NEW: Document tracking
    source_document_ids: List[str]  # All documents mentioning this role
    active_document_count: int  # Count of active (non-retired) documents
    
    custom_fields: Dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'StandardRole':
        defaults = {
            'id': '', 'canonical_name': '', 'category': 'Other', 'subcategory': '',
            'description': '', 'typical_responsibilities': [], 'typical_actions': [],
            'aliases': [], 'reports_to': [], 'coordinates_with': [], 'supervises': [],
            'required_skills': [], 'certifications': [],
            'created_date': datetime.now().isoformat(),
            'modified_date': datetime.now().isoformat(),
            'usage_count': 0, 'confidence_avg': 0.0, 'is_approved': False,
            'approved_by': '', 'notes': '', 'last_modified_by': '',
            'source_document_ids': [], 'active_document_count': 0, 'custom_fields': {}
        }
        defaults.update(data)
        return cls(**{k: v for k, v in defaults.items() if k in cls.__dataclass_fields__})
    
    @classmethod
    def from_extracted(cls, name: str, data: ExtractedRole, category: str = "Other",
                      user_name: str = "", document_id: str = "") -> 'StandardRole':
        now = datetime.now().isoformat()
        
        return cls(
            id=hashlib.md5(name.lower().encode()).hexdigest()[:12],
            canonical_name=name,
            category=category,
            subcategory=cls._infer_subcategory(name),
            description="",
            typical_responsibilities=list(set(data.responsibilities))[:10],
            typical_actions=[k for k, v in sorted(data.action_types.items(), key=lambda x: -x[1]) if k != 'unknown'][:5],
            aliases=list(data.variants - {name}),
            reports_to=[],
            coordinates_with=[],
            supervises=[],
            required_skills=[],
            certifications=[],
            created_date=now,
            modified_date=now,
            usage_count=data.frequency,
            confidence_avg=data.avg_confidence,
            is_approved=False,
            approved_by="",
            notes="",
            last_modified_by=user_name,
            source_document_ids=[document_id] if document_id else [],
            active_document_count=1 if document_id else 0,
            custom_fields={}
        )
    
    @staticmethod
    def _infer_subcategory(name: str) -> str:
        name_lower = name.lower()
        subcategories = {
            'systems': ['systems', 'system'], 'software': ['software', 'sw'],
            'hardware': ['hardware', 'hw'], 'test': ['test', 'verification', 'validation'],
            'integration': ['integration'], 'safety': ['safety', 'hazard'],
            'reliability': ['reliability'], 'quality': ['quality', 'qa'],
            'configuration': ['configuration', 'cm'], 'manufacturing': ['manufacturing', 'production'],
            'program': ['program', 'project'], 'executive': ['director', 'chief'],
            'supply chain': ['supplier', 'procurement', 'supply chain'],
        }
        for subcat, keywords in subcategories.items():
            if any(kw in name_lower for kw in keywords):
                return subcat.title()
        return "General"


@dataclass
class RoleRelationship:
    """Relationship between roles."""
    source_role_id: str
    target_role_id: str
    relationship_type: str
    strength: float
    evidence: List[str]
    created_date: str
    is_inferred: bool = True
    created_by: str = ""
    source_document_id: str = ""
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'RoleRelationship':
        defaults = {
            'source_role_id': '', 'target_role_id': '', 'relationship_type': '',
            'strength': 0.5, 'evidence': [], 'created_date': datetime.now().isoformat(),
            'is_inferred': True, 'created_by': '', 'source_document_id': ''
        }
        defaults.update(data)
        return cls(**{k: v for k, v in defaults.items() if k in cls.__dataclass_fields__})


# =============================================================================
# MAIN DATABASE CLASS
# =============================================================================

class RoleDatabase:
    """
    Comprehensive role database with document registry.
    
    Structure:
    {
        "metadata": {...},
        "documents": {...},       # Document registry
        "roles": {...},           # Role definitions
        "responsibilities": {...}, # Role-document-responsibility mappings
        "relationships": [...],    # Role relationships
        "extraction_history": [...],
        "change_log": [...]
    }
    """
    
    def __init__(self, settings: StudioSettings = None):
        self.settings = settings or StudioSettings.load()
        self.filepath = self.settings.get_effective_db_path()
        self._user_id = f"{self.settings.user_name or os.environ.get('USER', 'user')}_{uuid.uuid4().hex[:6]}"
        self._data = None
        self._last_load_time = 0
        
        db_dir = os.path.dirname(self.filepath)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        self._load()
    
    def _get_lock(self) -> FileLock:
        return FileLock(
            self.settings.get_lock_file_path(),
            timeout=self.settings.lock_timeout,
            user_id=self._user_id
        )
    
    def _load(self) -> dict:
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    self._data = json.load(f)
                self._last_load_time = time.time()
                self._migrate_if_needed()
                return self._data
            except (json.JSONDecodeError, IOError) as e:
                _log(f"Could not load {self.filepath}: {e}", level='warning')
                if os.path.exists(self.filepath):
                    backup = f"{self.filepath}.corrupt_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    shutil.copy(self.filepath, backup)
        
        self._data = self._create_new_database()
        return self._data
    
    def _create_new_database(self) -> dict:
        return {
            "metadata": {
                "version": "3.0",
                "created_date": datetime.now().isoformat(),
                "modified_date": datetime.now().isoformat(),
                "description": "Role Reference Database with Document Registry",
                "last_modified_by": self.settings.user_name or os.environ.get("USER", "user")
            },
            "documents": {},
            "roles": {},
            "responsibilities": {},
            "relationships": [],
            "extraction_history": [],
            "change_log": [],
            "settings": {
                "organization": self.settings.organization,
                "categories": ["Engineering", "Management", "Quality", "Governance", "Other"],
                "document_types": ["Standard", "Specification", "Contract", "Process", "Manual", "Other"],
                "responsibility_types": ["primary", "secondary", "coordination", "approval", "review"]
            }
        }
    
    def _migrate_if_needed(self):
        """Migrate from older database versions."""
        version = self._data.get("metadata", {}).get("version", "1.0")
        
        if "documents" not in self._data:
            self._data["documents"] = {}
        
        if "responsibilities" not in self._data:
            self._data["responsibilities"] = {}
        
        # Ensure roles have new fields
        for role_id, role_data in self._data.get("roles", {}).items():
            if "source_document_ids" not in role_data:
                role_data["source_document_ids"] = role_data.get("source_documents", [])
            if "active_document_count" not in role_data:
                role_data["active_document_count"] = len(role_data.get("source_document_ids", []))
        
        self._data["metadata"]["version"] = "3.0"
    
    def refresh(self) -> bool:
        if not os.path.exists(self.filepath):
            return False
        file_mtime = os.path.getmtime(self.filepath)
        if file_mtime > self._last_load_time:
            self._load()
            return True
        return False
    
    def save(self, force: bool = False):
        with self._get_lock():
            if not force and os.path.exists(self.filepath):
                file_mtime = os.path.getmtime(self.filepath)
                if file_mtime > self._last_load_time:
                    self._merge_external_changes()
            
            self._data["metadata"]["modified_date"] = datetime.now().isoformat()
            self._data["metadata"]["last_modified_by"] = self.settings.user_name or os.environ.get("USER", "user")
            
            if self.settings.backup_on_save and os.path.exists(self.filepath):
                self._create_backup()
            
            temp_path = self.filepath + ".tmp"
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            
            shutil.move(temp_path, self.filepath)
            self._last_load_time = time.time()
    
    def _merge_external_changes(self):
        """Merge changes from external modifications."""
        with open(self.filepath, 'r', encoding='utf-8') as f:
            external_data = json.load(f)
        
        # Merge documents
        for doc_id, doc_data in external_data.get("documents", {}).items():
            if doc_id not in self._data["documents"]:
                self._data["documents"][doc_id] = doc_data
            else:
                ext_time = doc_data.get("date_modified", "")
                local_time = self._data["documents"][doc_id].get("date_modified", "")
                if ext_time > local_time:
                    self._data["documents"][doc_id] = doc_data
        
        # Merge roles
        for role_id, role_data in external_data.get("roles", {}).items():
            if role_id not in self._data["roles"]:
                self._data["roles"][role_id] = role_data
            else:
                ext_time = role_data.get("modified_date", "")
                local_time = self._data["roles"][role_id].get("modified_date", "")
                if ext_time > local_time:
                    self._data["roles"][role_id] = role_data
        
        # Merge responsibilities
        for resp_id, resp_data in external_data.get("responsibilities", {}).items():
            if resp_id not in self._data["responsibilities"]:
                self._data["responsibilities"][resp_id] = resp_data
    
    def _create_backup(self):
        backup_dir = os.path.dirname(self.filepath) or "."
        backup_name = f".{os.path.basename(self.filepath)}.backup"
        backup_path = os.path.join(backup_dir, backup_name)
        try:
            shutil.copy(self.filepath, backup_path)
        except IOError:
            pass
    
    def _log_change(self, action: str, target_id: str, details: str):
        if "change_log" not in self._data:
            self._data["change_log"] = []
        
        self._data["change_log"].append({
            "timestamp": datetime.now().isoformat(),
            "user": self.settings.user_name or os.environ.get("USER", "user"),
            "action": action,
            "target_id": target_id,
            "details": details
        })
        
        if len(self._data["change_log"]) > 1000:
            self._data["change_log"] = self._data["change_log"][-1000:]
    
    def _auto_save(self):
        if self.settings.auto_save:
            self.save()
    
    # =========================================================================
    # DOCUMENT REGISTRY OPERATIONS
    # =========================================================================
    
    def add_document(self, doc: SourceDocument) -> bool:
        """Add or update a document in the registry."""
        doc.date_modified = datetime.now().isoformat()
        doc.modified_by = self.settings.user_name or os.environ.get("USER", "user")
        
        is_new = doc.id not in self._data["documents"]
        self._data["documents"][doc.id] = doc.to_dict()
        
        self._log_change(
            "add_document" if is_new else "update_document",
            doc.id,
            f"Document: {doc.filename}"
        )
        
        self._auto_save()
        return True
    
    def get_document(self, doc_id: str) -> Optional[SourceDocument]:
        """Get a document by ID."""
        self.refresh()
        data = self._data["documents"].get(doc_id)
        return SourceDocument.from_dict(data) if data else None
    
    def get_document_by_filename(self, filename: str) -> Optional[SourceDocument]:
        """Get a document by filename."""
        self.refresh()
        for doc_data in self._data["documents"].values():
            if doc_data["filename"].lower() == filename.lower():
                return SourceDocument.from_dict(doc_data)
        return None
    
    def search_documents(self, query: str = "", status: str = "", 
                        doc_type: str = "", limit: int = 100) -> List[SourceDocument]:
        """Search documents with filters."""
        self.refresh()
        results = []
        query_lower = query.lower()
        
        for doc_data in self._data["documents"].values():
            if status and doc_data.get("status") != status:
                continue
            if doc_type and doc_data.get("document_type") != doc_type:
                continue
            if query:
                searchable = (
                    doc_data.get("filename", "").lower() +
                    doc_data.get("title", "").lower() +
                    doc_data.get("description", "").lower() +
                    " ".join(doc_data.get("tags", [])).lower()
                )
                if query_lower not in searchable:
                    continue
            results.append(SourceDocument.from_dict(doc_data))
        
        results.sort(key=lambda d: d.date_modified, reverse=True)
        return results[:limit]
    
    def get_all_documents(self) -> List[SourceDocument]:
        """Get all documents."""
        self.refresh()
        return [SourceDocument.from_dict(data) for data in self._data["documents"].values()]
    
    def update_document_status(self, doc_id: str, new_status: str, 
                              superseded_by: str = "", notes: str = "") -> bool:
        """Update document status (active, retired, superseded)."""
        doc_data = self._data["documents"].get(doc_id)
        if not doc_data:
            return False
        
        old_status = doc_data.get("status")
        doc_data["status"] = new_status
        doc_data["date_modified"] = datetime.now().isoformat()
        doc_data["modified_by"] = self.settings.user_name or os.environ.get("USER", "user")
        
        if new_status == "retired":
            doc_data["retirement_date"] = datetime.now().isoformat()
        
        if superseded_by:
            doc_data["superseded_by"] = superseded_by
        
        if notes:
            doc_data["notes"] = (doc_data.get("notes", "") + f"\n[{datetime.now().strftime('%Y-%m-%d')}] Status changed to {new_status}: {notes}").strip()
        
        # Update responsibility active flags
        self._update_responsibilities_for_document_status(doc_id, new_status == "active")
        
        # Update role active document counts
        self._recalculate_role_document_counts()
        
        self._log_change("update_document_status", doc_id, f"{old_status} -> {new_status}")
        self._auto_save()
        return True
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the registry."""
        if doc_id in self._data["documents"]:
            doc_name = self._data["documents"][doc_id].get("filename", "Unknown")
            del self._data["documents"][doc_id]
            
            # Remove related responsibilities
            self._data["responsibilities"] = {
                k: v for k, v in self._data["responsibilities"].items()
                if v.get("source_document_id") != doc_id
            }
            
            # Update roles
            for role_data in self._data["roles"].values():
                if doc_id in role_data.get("source_document_ids", []):
                    role_data["source_document_ids"].remove(doc_id)
            
            self._recalculate_role_document_counts()
            
            self._log_change("delete_document", doc_id, f"Deleted: {doc_name}")
            self._auto_save()
            return True
        return False
    
    def get_documents_for_role(self, role_id: str) -> List[SourceDocument]:
        """Get all documents that mention a specific role."""
        role_data = self._data["roles"].get(role_id)
        if not role_data:
            return []
        
        doc_ids = role_data.get("source_document_ids", [])
        return [
            SourceDocument.from_dict(self._data["documents"][doc_id])
            for doc_id in doc_ids
            if doc_id in self._data["documents"]
        ]
    
    # =========================================================================
    # RESPONSIBILITY OPERATIONS
    # =========================================================================
    
    def add_responsibility(self, resp: RoleResponsibility) -> bool:
        """Add a responsibility mapping."""
        self._data["responsibilities"][resp.id] = resp.to_dict()
        self._auto_save()
        return True
    
    def get_responsibilities_for_role(self, role_id: str, 
                                      active_only: bool = True) -> List[RoleResponsibility]:
        """Get all responsibilities for a role."""
        self.refresh()
        results = []
        
        for resp_data in self._data["responsibilities"].values():
            if resp_data.get("role_id") != role_id:
                continue
            if active_only and not resp_data.get("is_active", True):
                continue
            results.append(RoleResponsibility.from_dict(resp_data))
        
        return results
    
    def get_responsibilities_from_document(self, doc_id: str) -> List[RoleResponsibility]:
        """Get all responsibilities from a specific document."""
        self.refresh()
        return [
            RoleResponsibility.from_dict(data)
            for data in self._data["responsibilities"].values()
            if data.get("source_document_id") == doc_id
        ]
    
    def _update_responsibilities_for_document_status(self, doc_id: str, is_active: bool):
        """Update responsibility active flags when document status changes."""
        for resp_data in self._data["responsibilities"].values():
            if resp_data.get("source_document_id") == doc_id:
                resp_data["is_active"] = is_active
    
    def _recalculate_role_document_counts(self):
        """Recalculate active document counts for all roles."""
        active_doc_ids = {
            doc_id for doc_id, doc_data in self._data["documents"].items()
            if doc_data.get("status") == "active"
        }
        
        for role_data in self._data["roles"].values():
            doc_ids = set(role_data.get("source_document_ids", []))
            role_data["active_document_count"] = len(doc_ids & active_doc_ids)
    
    # =========================================================================
    # ROLE OPERATIONS
    # =========================================================================
    
    def add_role(self, role: StandardRole) -> bool:
        """Add or update a role."""
        role.modified_date = datetime.now().isoformat()
        role.last_modified_by = self.settings.user_name or os.environ.get("USER", "user")
        
        is_new = role.id not in self._data["roles"]
        self._data["roles"][role.id] = role.to_dict()
        
        self._log_change(
            "add_role" if is_new else "update_role",
            role.id,
            f"Role: {role.canonical_name}"
        )
        
        self._auto_save()
        return True
    
    def get_role(self, role_id: str) -> Optional[StandardRole]:
        """Get a role by ID."""
        self.refresh()
        data = self._data["roles"].get(role_id)
        return StandardRole.from_dict(data) if data else None
    
    def get_role_by_name(self, name: str) -> Optional[StandardRole]:
        """Get a role by name."""
        self.refresh()
        name_lower = name.lower()
        
        for role_data in self._data["roles"].values():
            if role_data["canonical_name"].lower() == name_lower:
                return StandardRole.from_dict(role_data)
            if any(alias.lower() == name_lower for alias in role_data.get("aliases", [])):
                return StandardRole.from_dict(role_data)
        return None
    
    def search_roles(self, query: str = "", category: str = "",
                    approved_only: bool = False, limit: int = 100) -> List[StandardRole]:
        """Search roles."""
        self.refresh()
        results = []
        query_lower = query.lower()
        
        for role_data in self._data["roles"].values():
            if category and role_data.get("category") != category:
                continue
            if approved_only and not role_data.get("is_approved"):
                continue
            if query:
                searchable = (
                    role_data.get("canonical_name", "").lower() +
                    " ".join(role_data.get("aliases", [])).lower() +
                    role_data.get("description", "").lower()
                )
                if query_lower not in searchable:
                    continue
            results.append(StandardRole.from_dict(role_data))
        
        results.sort(key=lambda r: -r.usage_count)
        return results[:limit]
    
    def get_all_roles(self) -> List[StandardRole]:
        """Get all roles."""
        self.refresh()
        return [StandardRole.from_dict(data) for data in self._data["roles"].values()]
    
    def delete_role(self, role_id: str) -> bool:
        """Delete a role."""
        if role_id in self._data["roles"]:
            role_name = self._data["roles"][role_id].get("canonical_name", "Unknown")
            del self._data["roles"][role_id]
            
            # Remove related responsibilities
            self._data["responsibilities"] = {
                k: v for k, v in self._data["responsibilities"].items()
                if v.get("role_id") != role_id
            }
            
            # Remove relationships
            self._data["relationships"] = [
                r for r in self._data["relationships"]
                if r["source_role_id"] != role_id and r["target_role_id"] != role_id
            ]
            
            self._log_change("delete_role", role_id, f"Deleted: {role_name}")
            self._auto_save()
            return True
        return False
    
    # =========================================================================
    # ROLE RESPONSIBILITY AGGREGATION
    # =========================================================================
    
    def get_aggregated_role_data(self, role_id: str) -> dict:
        """
        Get comprehensive aggregated data for a role.
        
        Returns a structure suitable for external tools showing:
        - Role details
        - All responsibilities grouped by document
        - All responsibilities grouped by type
        - Document status information
        """
        role = self.get_role(role_id)
        if not role:
            return None
        
        responsibilities = self.get_responsibilities_for_role(role_id, active_only=False)
        documents = self.get_documents_for_role(role_id)
        
        # Group responsibilities by document
        by_document = defaultdict(list)
        for resp in responsibilities:
            by_document[resp.source_document_id].append(resp)
        
        # Group responsibilities by type
        by_type = defaultdict(list)
        for resp in responsibilities:
            by_type[resp.responsibility_type].append(resp)
        
        # Group by action verb
        by_action = defaultdict(list)
        for resp in responsibilities:
            by_action[resp.action_verb].append(resp)
        
        # Build document details
        document_details = []
        for doc in documents:
            doc_resps = by_document.get(doc.id, [])
            document_details.append({
                "document_id": doc.id,
                "filename": doc.filename,
                "title": doc.title,
                "type": doc.document_type,
                "status": doc.status,
                "version": doc.version,
                "revision": doc.revision,
                "effective_date": doc.effective_date,
                "retirement_date": doc.retirement_date,
                "responsibility_count": len(doc_resps),
                "responsibilities": [r.to_dict() for r in doc_resps]
            })
        
        # Build unique responsibility list (deduplicated)
        unique_responsibilities = {}
        for resp in responsibilities:
            # Normalize text for comparison
            norm_text = re.sub(r'\s+', ' ', resp.responsibility_text.lower().strip())
            if norm_text not in unique_responsibilities:
                unique_responsibilities[norm_text] = {
                    "text": resp.responsibility_text,
                    "action_verb": resp.action_verb,
                    "type": resp.responsibility_type,
                    "category": resp.category,
                    "sources": [],
                    "is_active": False
                }
            unique_responsibilities[norm_text]["sources"].append({
                "document_id": resp.source_document_id,
                "document_name": resp.source_document_name,
                "location": resp.source_location,
                "is_active": resp.is_active
            })
            if resp.is_active:
                unique_responsibilities[norm_text]["is_active"] = True
        
        return {
            "role": role.to_dict(),
            "summary": {
                "total_responsibilities": len(responsibilities),
                "unique_responsibilities": len(unique_responsibilities),
                "active_responsibilities": sum(1 for r in responsibilities if r.is_active),
                "total_documents": len(documents),
                "active_documents": role.active_document_count,
                "by_type": {k: len(v) for k, v in by_type.items()},
                "by_action": {k: len(v) for k, v in by_action.items()}
            },
            "documents": document_details,
            "unique_responsibilities": list(unique_responsibilities.values()),
            "by_type": {k: [r.to_dict() for r in v] for k, v in by_type.items()},
            "by_action": {k: [r.to_dict() for r in v] for k, v in by_action.items()}
        }
    
    def export_role_responsibility_matrix(self, filepath: str):
        """Export a matrix of roles vs documents with responsibility counts."""
        roles = self.get_all_roles()
        documents = self.get_all_documents()
        
        # Build matrix
        matrix = {}
        for role in roles:
            matrix[role.id] = {
                "role_name": role.canonical_name,
                "category": role.category,
                "total_responsibilities": 0,
                "documents": {}
            }
            
            for doc in documents:
                count = sum(
                    1 for r in self._data["responsibilities"].values()
                    if r.get("role_id") == role.id and r.get("source_document_id") == doc.id
                )
                if count > 0:
                    matrix[role.id]["documents"][doc.id] = {
                        "filename": doc.filename,
                        "count": count,
                        "status": doc.status
                    }
                    matrix[role.id]["total_responsibilities"] += count
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(matrix, f, indent=2)
    
    # =========================================================================
    # RELATIONSHIP OPERATIONS
    # =========================================================================
    
    def add_relationship(self, rel: RoleRelationship) -> bool:
        """Add a relationship."""
        rel.created_by = self.settings.user_name or os.environ.get("USER", "user")
        
        for existing in self._data["relationships"]:
            if (existing["source_role_id"] == rel.source_role_id and
                existing["target_role_id"] == rel.target_role_id and
                existing["relationship_type"] == rel.relationship_type):
                if rel.strength > existing["strength"]:
                    existing["strength"] = rel.strength
                    existing["evidence"].extend(rel.evidence)
                    existing["evidence"] = existing["evidence"][:10]
                self._auto_save()
                return True
        
        self._data["relationships"].append(rel.to_dict())
        self._auto_save()
        return True
    
    def get_relationships(self, role_id: str = None) -> List[RoleRelationship]:
        """Get relationships."""
        self.refresh()
        results = []
        for rel_data in self._data["relationships"]:
            if role_id:
                if rel_data["source_role_id"] != role_id and rel_data["target_role_id"] != role_id:
                    continue
            results.append(RoleRelationship.from_dict(rel_data))
        return results
    
    # =========================================================================
    # STATISTICS
    # =========================================================================
    
    def get_statistics(self) -> dict:
        """Get comprehensive statistics."""
        self.refresh()
        
        roles = list(self._data["roles"].values())
        docs = list(self._data["documents"].values())
        resps = list(self._data["responsibilities"].values())
        
        by_category = defaultdict(int)
        by_contributor = defaultdict(int)
        for role in roles:
            by_category[role.get("category", "Other")] += 1
            by_contributor[role.get("last_modified_by", "Unknown")] += 1
        
        doc_by_status = defaultdict(int)
        doc_by_type = defaultdict(int)
        for doc in docs:
            doc_by_status[doc.get("status", "unknown")] += 1
            doc_by_type[doc.get("document_type", "Other")] += 1
        
        return {
            "database_file": self.filepath,
            "is_shared": self.settings.use_shared_drive,
            "last_modified": self._data["metadata"].get("modified_date", "Unknown"),
            "last_modified_by": self._data["metadata"].get("last_modified_by", "Unknown"),
            
            "roles": {
                "total": len(roles),
                "approved": sum(1 for r in roles if r.get("is_approved")),
                "by_category": dict(by_category),
                "by_contributor": dict(by_contributor)
            },
            
            "documents": {
                "total": len(docs),
                "by_status": dict(doc_by_status),
                "by_type": dict(doc_by_type)
            },
            
            "responsibilities": {
                "total": len(resps),
                "active": sum(1 for r in resps if r.get("is_active", True))
            },
            
            "relationships": {
                "total": len(self._data["relationships"])
            }
        }
    
    # =========================================================================
    # EXPORT METHODS
    # =========================================================================
    
    def export_for_external_tool(self, filepath: str, role_id: str = None):
        """
        Export data in a format optimized for external tools.
        
        If role_id is provided, exports data for that specific role.
        Otherwise, exports all roles with their aggregated data.
        """
        if role_id:
            data = self.get_aggregated_role_data(role_id)
            if not data:
                return False
            export_data = {
                "export_type": "single_role",
                "export_date": datetime.now().isoformat(),
                "exported_by": self.settings.user_name or os.environ.get("USER", "user"),
                "data": data
            }
        else:
            roles_data = []
            for role in self.get_all_roles():
                agg_data = self.get_aggregated_role_data(role.id)
                if agg_data:
                    roles_data.append(agg_data)
            
            export_data = {
                "export_type": "all_roles",
                "export_date": datetime.now().isoformat(),
                "exported_by": self.settings.user_name or os.environ.get("USER", "user"),
                "role_count": len(roles_data),
                "data": roles_data
            }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return True
    
    def export_to_csv(self, filepath: str):
        """Export roles to CSV."""
        roles = self.get_all_roles()
        
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow([
                'ID', 'Canonical Name', 'Category', 'Subcategory', 'Description',
                'Aliases', 'Responsibilities', 'Actions',
                'Total Documents', 'Active Documents', 'Usage Count', 'Confidence',
                'Is Approved', 'Approved By', 'Last Modified By', 'Notes'
            ])
            
            for role in roles:
                writer.writerow([
                    role.id, role.canonical_name, role.category, role.subcategory,
                    role.description, '; '.join(role.aliases),
                    '; '.join(role.typical_responsibilities), '; '.join(role.typical_actions),
                    len(role.source_document_ids), role.active_document_count,
                    role.usage_count, f"{role.confidence_avg:.2%}",
                    'Yes' if role.is_approved else 'No', role.approved_by,
                    role.last_modified_by, role.notes
                ])
    
    def export_documents_csv(self, filepath: str):
        """Export document registry to CSV."""
        docs = self.get_all_documents()
        
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow([
                'ID', 'Filename', 'Title', 'Type', 'Version', 'Revision',
                'Status', 'Effective Date', 'Retirement Date',
                'Roles Found', 'Last Processed', 'Added By', 'Tags', 'Notes'
            ])
            
            for doc in docs:
                writer.writerow([
                    doc.id, doc.filename, doc.title, doc.document_type,
                    doc.version, doc.revision, doc.status,
                    doc.effective_date, doc.retirement_date,
                    doc.roles_found, doc.last_processed,
                    doc.added_by, '; '.join(doc.tags), doc.notes
                ])


# =============================================================================
# RELATIONSHIP INFERENCE ENGINE
# =============================================================================

class RelationshipInferenceEngine:
    """Infers relationships between roles."""
    
    def infer_relationships(self, roles: Dict[str, ExtractedRole],
                           text: str, user_name: str = "",
                           document_id: str = "") -> List[RoleRelationship]:
        relationships = []
        role_names = list(roles.keys())
        now = datetime.now().isoformat()
        
        sentences = re.split(r'[.;]', text)
        co_occurrence = defaultdict(int)
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            roles_in_sentence = [n for n in role_names if n.lower() in sentence_lower]
            
            for i, role1 in enumerate(roles_in_sentence):
                for role2 in roles_in_sentence[i+1:]:
                    key = tuple(sorted([role1, role2]))
                    co_occurrence[key] += 1
        
        for (role1, role2), count in co_occurrence.items():
            if count >= 1:
                relationships.append(RoleRelationship(
                    source_role_id=hashlib.md5(role1.lower().encode()).hexdigest()[:12],
                    target_role_id=hashlib.md5(role2.lower().encode()).hexdigest()[:12],
                    relationship_type='coordinates_with',
                    strength=min(1.0, count / 5.0),
                    evidence=[f"Co-occurred {count} time(s)"],
                    created_date=now,
                    is_inferred=True,
                    created_by=user_name,
                    source_document_id=document_id
                ))
        
        seen = set()
        unique = []
        for rel in relationships:
            key = (rel.source_role_id, rel.target_role_id, rel.relationship_type)
            if key not in seen:
                seen.add(key)
                unique.append(rel)
        
        return unique


# =============================================================================
# MAIN STUDIO CLASS
# =============================================================================

class RoleManagementStudio:
    """Main integration class with document registry support."""
    
    # Action verbs for responsibility classification
    ACTION_VERBS = {
        'primary': ['shall', 'must', 'will', 'is responsible', 'performs', 'executes', 'leads', 'manages'],
        'approval': ['approves', 'authorizes', 'signs', 'certifies', 'validates'],
        'review': ['reviews', 'evaluates', 'assesses', 'examines', 'audits', 'inspects'],
        'coordination': ['coordinates', 'interfaces', 'collaborates', 'communicates', 'liaises'],
        'secondary': ['supports', 'assists', 'participates', 'contributes', 'helps']
    }
    
    def __init__(self, settings: StudioSettings = None):
        self.settings = settings or StudioSettings.load()
        self.database = RoleDatabase(self.settings)
        self.extractor = RoleExtractor()
        self.inference_engine = RelationshipInferenceEngine()
    
    def process_document(self, filepath: str, doc_type: str = "Other") -> dict:
        """
        Process a document:
        1. Register in document registry
        2. Extract roles
        3. Map responsibilities to roles
        4. Infer relationships
        """
        user_name = self.settings.user_name or os.environ.get("USER", "user")
        
        # 1. Register document
        existing_doc = self.database.get_document_by_filename(os.path.basename(filepath))
        if existing_doc:
            doc = existing_doc
            doc.last_processed = datetime.now().isoformat()
            doc.modified_by = user_name
        else:
            doc = SourceDocument.create_new(filepath, doc_type, user_name)
        
        # 2. Extract roles and text
        ext = os.path.splitext(filepath)[1].lower()
        
        if ext == '.docx':
            roles = self.extractor.extract_from_docx(filepath)
            from docx import Document
            doc_obj = Document(filepath)
            text = '\n'.join([p.text for p in doc_obj.paragraphs])
        elif ext == '.pdf':
            roles = self.extractor.extract_from_pdf(filepath)
            try:
                import pdfplumber
                with pdfplumber.open(filepath) as pdf:
                    text = '\n'.join([page.extract_text() or '' for page in pdf.pages])
            except Exception:  # Caught and handled
                text = ""
        else:
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
            roles = self.extractor.extract_from_text(text, os.path.basename(filepath))
        
        # 3. Process each role
        roles_new = 0
        roles_updated = 0
        responsibilities_added = 0
        
        for name, data in roles.items():
            category = self._categorize_role(name)
            existing_role = self.database.get_role_by_name(name)
            
            if existing_role:
                # Update existing role
                existing_role.usage_count += data.frequency
                existing_role.confidence_avg = (existing_role.confidence_avg + data.avg_confidence) / 2
                
                if doc.id not in existing_role.source_document_ids:
                    existing_role.source_document_ids.append(doc.id)
                
                existing_role.last_modified_by = user_name
                self.database.add_role(existing_role)
                role_id = existing_role.id
                roles_updated += 1
            else:
                # Create new role
                standard_role = StandardRole.from_extracted(
                    name, data, category, user_name, doc.id
                )
                self.database.add_role(standard_role)
                role_id = standard_role.id
                roles_new += 1
            
            # 4. Create responsibility entries
            for resp_text in data.responsibilities:
                resp = RoleResponsibility(
                    id=hashlib.md5(f"{role_id}{doc.id}{resp_text}".encode()).hexdigest()[:12],
                    role_id=role_id,
                    responsibility_text=resp_text,
                    action_verb=self._extract_action_verb(resp_text),
                    source_document_id=doc.id,
                    source_document_name=doc.filename,
                    source_location="",
                    source_context="",
                    date_added=datetime.now().isoformat(),
                    added_by=user_name,
                    is_active=True,
                    confidence=data.avg_confidence,
                    responsibility_type=self._classify_responsibility_type(resp_text),
                    category=self._classify_responsibility_category(resp_text),
                    notes=""
                )
                self.database.add_responsibility(resp)
                responsibilities_added += 1
        
        # 5. Update document with role count
        doc.roles_found = len(roles)
        doc.last_processed = datetime.now().isoformat()
        self.database.add_document(doc)
        
        # 6. Infer relationships
        relationships = self.inference_engine.infer_relationships(
            roles, text, user_name, doc.id
        )
        for rel in relationships:
            self.database.add_relationship(rel)
        
        # Recalculate active document counts
        self.database._recalculate_role_document_counts()
        
        return {
            'document_id': doc.id,
            'document': doc.filename,
            'roles_found': len(roles),
            'roles_new': roles_new,
            'roles_updated': roles_updated,
            'responsibilities_added': responsibilities_added,
            'relationships_inferred': len(relationships)
        }
    
    def _categorize_role(self, name: str) -> str:
        name_lower = name.lower()
        if any(x in name_lower for x in ['engineer', 'technician', 'analyst', 'scientist']):
            return 'Engineering'
        elif any(x in name_lower for x in ['manager', 'director', 'supervisor', 'lead', 'coordinator', 'chief']):
            return 'Management'
        elif any(x in name_lower for x in ['quality', 'inspector', 'auditor']):
            return 'Quality'
        elif any(x in name_lower for x in ['board', 'committee', 'team', 'group']):
            return 'Governance'
        return 'Other'
    
    def _extract_action_verb(self, text: str) -> str:
        """Extract the primary action verb from responsibility text."""
        text_lower = text.lower()
        
        for verb_type, verbs in self.ACTION_VERBS.items():
            for verb in verbs:
                if verb in text_lower:
                    return verb
        
        # Try to find first verb
        words = text_lower.split()
        common_verbs = ['ensure', 'provide', 'maintain', 'establish', 'develop', 
                       'prepare', 'conduct', 'perform', 'monitor', 'verify']
        for word in words[:5]:
            if word in common_verbs:
                return word
        
        return "performs"
    
    def _classify_responsibility_type(self, text: str) -> str:
        """Classify responsibility type based on text."""
        text_lower = text.lower()
        
        for resp_type, verbs in self.ACTION_VERBS.items():
            for verb in verbs:
                if verb in text_lower:
                    return resp_type
        
        return "primary"
    
    def _classify_responsibility_category(self, text: str) -> str:
        """Classify responsibility into a category."""
        text_lower = text.lower()
        
        categories = {
            'Design': ['design', 'architecture', 'specification', 'requirement'],
            'Test': ['test', 'verification', 'validation', 'qualification'],
            'Quality': ['quality', 'inspection', 'audit', 'compliance'],
            'Safety': ['safety', 'hazard', 'risk', 'mishap'],
            'Documentation': ['document', 'report', 'record', 'procedure'],
            'Review': ['review', 'evaluate', 'assess', 'analyze'],
            'Manufacturing': ['manufacturing', 'production', 'assembly', 'fabrication'],
            'Integration': ['integration', 'interface', 'system'],
            'Configuration': ['configuration', 'change', 'baseline', 'version']
        }
        
        for category, keywords in categories.items():
            if any(kw in text_lower for kw in keywords):
                return category
        
        return "General"
    
    def get_role_summary(self, role_id: str) -> dict:
        """
        Get a summary for a role suitable for external tools.
        
        Returns:
        {
            "role_name": "Systems Engineer",
            "role_title": "Systems Engineer",  # For job title display
            "category": "Engineering",
            "total_documents": 5,
            "active_documents": 4,
            "responsibilities": [
                {
                    "text": "Reviews system requirements",
                    "type": "review",
                    "action": "reviews",
                    "sources": ["AS6500", "MIL-STD-1521"],
                    "is_active": true
                },
                ...
            ]
        }
        """
        return self.database.get_aggregated_role_data(role_id)
    
    def get_statistics(self) -> dict:
        return self.database.get_statistics()
    
    def process_repository(self, directory: str, extensions: List[str] = None) -> dict:
        """
        Process all documents in a directory.
        
        Args:
            directory: Path to document repository
            extensions: List of extensions to process (default: ['.docx', '.pdf', '.txt'])
        
        Returns:
            Summary of processing results
        """
        if extensions is None:
            extensions = ['.docx', '.pdf', '.txt']
        
        results = {
            'directory': directory,
            'documents_processed': 0,
            'total_roles': 0,
            'total_responsibilities': 0,
            'errors': []
        }
        
        for root, dirs, files in os.walk(directory):
            for filename in files:
                ext = os.path.splitext(filename)[1].lower()
                if ext in extensions:
                    filepath = os.path.join(root, filename)
                    try:
                        result = self.process_document(filepath)
                        results['documents_processed'] += 1
                        results['total_roles'] += result['roles_found']
                        results['total_responsibilities'] += result['responsibilities_added']
                    except Exception as e:
                        results['errors'].append({
                            'file': filepath,
                            'error': str(e)
                        })
        
        return results


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Role Management Studio v3.0')
    parser.add_argument('--process', type=str, help='Process a document')
    parser.add_argument('--process-dir', type=str, help='Process all documents in directory')
    parser.add_argument('--doc-type', type=str, default='Other', help='Document type')
    parser.add_argument('--shared-drive', type=str, help='Shared drive path')
    parser.add_argument('--user', type=str, help='User name')
    parser.add_argument('--org', type=str, help='Organization')
    
    parser.add_argument('--list-docs', action='store_true', help='List all documents')
    parser.add_argument('--list-roles', action='store_true', help='List all roles')
    parser.add_argument('--role-summary', type=str, help='Get summary for role (by name)')
    
    parser.add_argument('--retire-doc', type=str, help='Retire a document (by filename)')
    parser.add_argument('--activate-doc', type=str, help='Activate a document (by filename)')
    
    parser.add_argument('--export-roles', type=str, help='Export roles to CSV')
    parser.add_argument('--export-docs', type=str, help='Export documents to CSV')
    parser.add_argument('--export-json', type=str, help='Export full data to JSON')
    parser.add_argument('--export-role', type=str, help='Export single role data (by name)')
    
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    
    args = parser.parse_args()
    
    # Setup settings
    settings = StudioSettings.load()
    
    if args.shared_drive:
        settings.use_shared_drive = True
        settings.shared_drive_path = args.shared_drive
    
    if args.user:
        settings.user_name = args.user
    
    if args.org:
        settings.organization = args.org
    
    settings.save()
    
    studio = RoleManagementStudio(settings)
    
    # Process operations
    if args.process:
        print(f"Processing: {args.process}")
        result = studio.process_document(args.process, args.doc_type)
        print(f"  Document ID: {result['document_id']}")
        print(f"  Roles found: {result['roles_found']}")
        print(f"  New: {result['roles_new']}, Updated: {result['roles_updated']}")
        print(f"  Responsibilities: {result['responsibilities_added']}")
    
    if args.process_dir:
        print(f"Processing directory: {args.process_dir}")
        result = studio.process_repository(args.process_dir)
        print(f"  Documents processed: {result['documents_processed']}")
        print(f"  Total roles: {result['total_roles']}")
        print(f"  Total responsibilities: {result['total_responsibilities']}")
        if result['errors']:
            print(f"  Errors: {len(result['errors'])}")
    
    # List operations
    if args.list_docs:
        docs = studio.database.get_all_documents()
        print(f"\n{'='*80}")
        print(f"DOCUMENT REGISTRY ({len(docs)} documents)")
        print(f"{'='*80}")
        for doc in docs:
            status_icon = {'active': '✓', 'retired': '✗', 'superseded': '→', 'draft': '○'}.get(doc.status, '?')
            print(f"  [{status_icon}] {doc.filename}")
            print(f"      Type: {doc.document_type} | Roles: {doc.roles_found} | Status: {doc.status}")
    
    if args.list_roles:
        roles = studio.database.get_all_roles()
        print(f"\n{'='*80}")
        print(f"ROLES ({len(roles)} roles)")
        print(f"{'='*80}")
        for role in sorted(roles, key=lambda r: r.canonical_name):
            approved = '✓' if role.is_approved else '○'
            print(f"  [{approved}] {role.canonical_name}")
            print(f"      Category: {role.category} | Docs: {role.active_document_count}/{len(role.source_document_ids)}")
    
    if args.role_summary:
        role = studio.database.get_role_by_name(args.role_summary)
        if role:
            summary = studio.get_role_summary(role.id)
            print(f"\n{'='*80}")
            print(f"ROLE SUMMARY: {role.canonical_name}")
            print(f"{'='*80}")
            print(f"Category: {role.category}")
            print(f"Documents: {summary['summary']['active_documents']} active / {summary['summary']['total_documents']} total")
            print(f"Responsibilities: {summary['summary']['unique_responsibilities']} unique / {summary['summary']['total_responsibilities']} total")
            print(f"\nBy Type: {summary['summary']['by_type']}")
            print(f"\nUnique Responsibilities:")
            for resp in summary['unique_responsibilities'][:10]:
                active = '✓' if resp['is_active'] else '✗'
                print(f"  [{active}] [{resp['action_verb']}] {resp['text'][:70]}...")
        else:
            print(f"Role not found: {args.role_summary}")
    
    # Document status operations
    if args.retire_doc:
        doc = studio.database.get_document_by_filename(args.retire_doc)
        if doc:
            studio.database.update_document_status(doc.id, 'retired')
            print(f"Retired: {args.retire_doc}")
        else:
            print(f"Document not found: {args.retire_doc}")
    
    if args.activate_doc:
        doc = studio.database.get_document_by_filename(args.activate_doc)
        if doc:
            studio.database.update_document_status(doc.id, 'active')
            print(f"Activated: {args.activate_doc}")
        else:
            print(f"Document not found: {args.activate_doc}")
    
    # Export operations
    if args.export_roles:
        studio.database.export_to_csv(args.export_roles)
        print(f"Exported roles to: {args.export_roles}")
    
    if args.export_docs:
        studio.database.export_documents_csv(args.export_docs)
        print(f"Exported documents to: {args.export_docs}")
    
    if args.export_json:
        studio.database.export_for_external_tool(args.export_json)
        print(f"Exported JSON to: {args.export_json}")
    
    if args.export_role:
        role = studio.database.get_role_by_name(args.export_role)
        if role:
            output = f"{role.canonical_name.replace(' ', '_')}_data.json"
            studio.database.export_for_external_tool(output, role.id)
            print(f"Exported role data to: {output}")
        else:
            print(f"Role not found: {args.export_role}")
    
    # Statistics
    if args.stats:
        stats = studio.get_statistics()
        print(f"\n{'='*80}")
        print(f"DATABASE STATISTICS")
        print(f"{'='*80}")
        print(f"Database: {stats['database_file']}")
        print(f"Shared: {'Yes' if stats['is_shared'] else 'No'}")
        print(f"\nRoles:")
        print(f"  Total: {stats['roles']['total']}")
        print(f"  Approved: {stats['roles']['approved']}")
        print(f"  By Category: {stats['roles']['by_category']}")
        print(f"\nDocuments:")
        print(f"  Total: {stats['documents']['total']}")
        print(f"  By Status: {stats['documents']['by_status']}")
        print(f"  By Type: {stats['documents']['by_type']}")
        print(f"\nResponsibilities:")
        print(f"  Total: {stats['responsibilities']['total']}")
        print(f"  Active: {stats['responsibilities']['active']}")


if __name__ == "__main__":
    main()
