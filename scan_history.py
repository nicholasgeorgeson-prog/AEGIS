#!/usr/bin/env python3
"""
Scan History & Role Aggregation System v1.0
============================================
Tracks document scans over time and aggregates roles across documents.

Features:
- Document scan history with change detection
- Role aggregation across all scanned documents
- Custom scan profiles (saved check configurations)
- Document-Role relationship tracking
- SHAREABLE ROLE DICTIONARIES for team distribution

Author: TechWriterReview
"""

import os
import re
import json
import sqlite3
import hashlib
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# Import version from centralized config
try:
    from config_logging import VERSION, get_logger
    __version__ = VERSION
    _logger = get_logger('scan_history')
except ImportError:
    __version__ = "2.6.0"
    _logger = None


def _log(msg: str, level: str = 'info'):
    if _logger:
        getattr(_logger, level)(msg)
    else:
        print(f"[ScanHistory] {msg}")


# ============================================================
# DATABASE CONNECTION CONTEXT MANAGER
# ============================================================

@contextmanager
def db_connection(db_path):
    """Context manager for SQLite database operations.

    Creates a connection with Row factory and WAL mode enabled.
    Auto-commits on success, auto-rolls-back on exception,
    and always closes the connection.

    Usage:
        with db_connection(db.db_path) as (conn, cursor):
            cursor.execute('SELECT ...')
            rows = cursor.fetchall()

    Yields:
        Tuple of (connection, cursor)
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    cursor = conn.cursor()
    try:
        yield (conn, cursor)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ============================================================
# SHAREABLE DICTIONARY FILE SUPPORT
# ============================================================

MASTER_DICT_FILENAME = "role_dictionary_master.json"
LOCAL_DICT_FILENAME = "role_dictionary_local.json"

def get_dictionary_paths() -> Dict[str, Path]:
    """
    Get paths for dictionary files.
    
    Returns dict with:
    - master: Shared/team dictionary file (read-only baseline)
    - local: User's local additions
    - shared: Network/shared folder location (if configured)
    """
    app_dir = Path(__file__).parent
    
    paths = {
        'master': app_dir / MASTER_DICT_FILENAME,
        'local': app_dir / LOCAL_DICT_FILENAME,
        'shared': None
    }
    
    # Check for shared folder configuration
    config_file = app_dir / 'config.json'
    if config_file.exists():
        try:
            with open(config_file, encoding='utf-8') as f:
                config = json.load(f)
                shared_path = config.get('shared_dictionary_path')
                if shared_path:
                    shared_path = Path(shared_path)
                    # Check if path is accessible (handles network paths better)
                    try:
                        # For network paths, check if parent directory is accessible
                        if str(shared_path).startswith('\\\\') or str(shared_path).startswith('//'):
                            # UNC path - try to access it
                            if shared_path.exists():
                                paths['shared'] = shared_path / MASTER_DICT_FILENAME
                            elif shared_path.parent.exists():
                                paths['shared'] = shared_path / MASTER_DICT_FILENAME
                            else:
                                _log(f"Network path not accessible: {shared_path}. "
                                     "Ensure you have network access and proper credentials.", 'warning')
                        else:
                            # Local path
                            if shared_path.exists() or shared_path.parent.exists():
                                paths['shared'] = shared_path / MASTER_DICT_FILENAME
                    except PermissionError:
                        _log(f"Permission denied accessing: {shared_path}. "
                             "Check network credentials or run 'net use' to authenticate.", 'warning')
                    except OSError as e:
                        _log(f"Cannot access network path {shared_path}: {e}. "
                             "Ensure network drive is mapped or use 'net use' command.", 'warning')
        except Exception as e:
            _log(f"Could not read config for shared path: {e}", 'warning')
    
    return paths


def export_dictionary_to_file(roles: List[Dict], filepath: str, 
                               include_metadata: bool = True) -> Dict:
    """
    Export roles to a shareable JSON file.
    
    Args:
        roles: List of role dictionaries
        filepath: Output file path
        include_metadata: Include export timestamp and version
    
    Returns:
        Dict with success status
    """
    try:
        export_data = {
            'roles': roles,
            'version': '1.0',
            'format': 'twr_role_dictionary'
        }
        
        if include_metadata:
            export_data['exported_at'] = datetime.now().isoformat()
            export_data['exported_by'] = os.environ.get('USERNAME', os.environ.get('USER', 'unknown'))
            export_data['role_count'] = len(roles)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return {'success': True, 'path': filepath, 'count': len(roles)}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def load_dictionary_from_file(filepath: str) -> Dict:
    """
    Load roles from a dictionary file.
    
    Args:
        filepath: Path to JSON dictionary file
    
    Returns:
        Dict with roles list and metadata
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle both formats: raw list or wrapped object
        if isinstance(data, list):
            roles = data
            metadata = {}
        else:
            roles = data.get('roles', [])
            metadata = {k: v for k, v in data.items() if k != 'roles'}
        
        return {
            'success': True,
            'roles': roles,
            'metadata': metadata,
            'count': len(roles)
        }
    except FileNotFoundError:
        return {'success': False, 'error': 'File not found', 'roles': []}
    except json.JSONDecodeError as e:
        return {'success': False, 'error': f'Invalid JSON: {e}', 'roles': []}
    except Exception as e:
        return {'success': False, 'error': str(e), 'roles': []}


class ScanHistoryDB:
    """Database for tracking document scans and roles."""
    
    def __init__(self, db_path: str = None):
        """Initialize the database."""
        if db_path is None:
            # Default to app directory
            app_dir = Path(__file__).parent
            db_path = str(app_dir / "scan_history.db")
        
        self.db_path = db_path
        self._init_database()

    def connection(self):
        """Get a managed database connection context manager.

        Usage:
            with self.connection() as (conn, cursor):
                cursor.execute('SELECT ...')
        """
        return db_connection(self.db_path)

    def _create_table_safe(self, name: str, *statements):
        """Create a table (and optional extra statements) in its own transaction.

        If any statement fails, only this table's transaction is rolled back,
        not the entire database initialization.
        """
        try:
            with self.connection() as (conn, cursor):
                for sql in statements:
                    cursor.execute(sql)
        except Exception as e:
            _log(f"Warning: Could not create/migrate table '{name}': {e}", level='warning')

    def _init_database(self):
        """Initialize database tables.

        v5.0.0: Each table creation is in its own transaction to prevent
        a failure in one table (or seed data) from rolling back ALL tables.
        This is critical for fresh installs on Windows where any single
        migration issue would leave the entire database empty.
        """
        self._create_table_safe('documents', '''
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    filepath TEXT,
                    file_hash TEXT,
                    first_scan TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_scan TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    scan_count INTEGER DEFAULT 1,
                    word_count INTEGER,
                    paragraph_count INTEGER,
                    UNIQUE(filename, file_hash)
                )
            ''')

        self._create_table_safe('scans', '''
                CREATE TABLE IF NOT EXISTS scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER,
                    scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    options_json TEXT,
                    issue_count INTEGER,
                    score INTEGER,
                    grade TEXT,
                    word_count INTEGER,
                    paragraph_count INTEGER,
                    results_json TEXT,
                    FOREIGN KEY (document_id) REFERENCES documents(id)
                )
            ''')

        self._create_table_safe('roles', '''
                CREATE TABLE IF NOT EXISTS roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role_name TEXT UNIQUE,
                    normalized_name TEXT,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    document_count INTEGER DEFAULT 1,
                    total_mentions INTEGER DEFAULT 1,
                    description TEXT,
                    is_deliverable INTEGER DEFAULT 0,
                    category TEXT,
                    role_source TEXT DEFAULT 'discovered'
                )
            ''')

        # v5.0.5: Ensure roles table has role_source column (migration for older databases)
        try:
            with self.connection() as (conn, cursor):
                cursor.execute("ALTER TABLE roles ADD COLUMN role_source TEXT DEFAULT 'discovered'")
        except Exception as e:
            if 'duplicate column' not in str(e).lower():
                logger.warning(f'Migration: could not add role_source to roles: {e}')

        self._create_table_safe('role_dictionary', '''
                CREATE TABLE IF NOT EXISTS role_dictionary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role_name TEXT NOT NULL,
                    normalized_name TEXT NOT NULL,
                    aliases TEXT,
                    category TEXT DEFAULT 'Custom',
                    source TEXT NOT NULL,
                    source_document TEXT,
                    description TEXT,
                    is_active INTEGER DEFAULT 1,
                    is_deliverable INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT DEFAULT 'user',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_by TEXT,
                    notes TEXT,
                    tracings TEXT DEFAULT '[]',
                    role_type TEXT DEFAULT '',
                    role_disposition TEXT DEFAULT '',
                    org_group TEXT DEFAULT '',
                    hierarchy_level TEXT DEFAULT '',
                    baselined INTEGER DEFAULT 0,
                    UNIQUE(normalized_name)
                )
            ''',
            "CREATE INDEX IF NOT EXISTS idx_role_dict_normalized ON role_dictionary(normalized_name)",
            "CREATE INDEX IF NOT EXISTS idx_role_dict_active ON role_dictionary(is_active)")

        # v5.0.0: Ensure role_dictionary has all required columns (migration for older databases)
        for col_name, col_type in [
            ('tracings', "TEXT DEFAULT '[]'"),
            ('role_type', "TEXT DEFAULT ''"),
            ('role_disposition', "TEXT DEFAULT ''"),
            ('org_group', "TEXT DEFAULT ''"),
            ('hierarchy_level', "TEXT DEFAULT ''"),
            ('baselined', "INTEGER DEFAULT 0"),
        ]:
            try:
                with self.connection() as (conn, cursor):
                    cursor.execute(f'ALTER TABLE role_dictionary ADD COLUMN {col_name} {col_type}')
            except Exception as e:
                if 'duplicate column' not in str(e).lower():
                    logger.warning(f'Migration: could not add column {col_name}: {e}')

        self._create_table_safe('document_roles', '''
                CREATE TABLE IF NOT EXISTS document_roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER,
                    role_id INTEGER,
                    mention_count INTEGER DEFAULT 1,
                    responsibilities_json TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES documents(id),
                    FOREIGN KEY (role_id) REFERENCES roles(id),
                    UNIQUE(document_id, role_id)
                )
            ''')

        self._create_table_safe('scan_profiles', '''
                CREATE TABLE IF NOT EXISTS scan_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    options_json TEXT NOT NULL,
                    is_default INTEGER DEFAULT 0,
                    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP
                )
            ''')

        self._create_table_safe('issue_changes', '''
                CREATE TABLE IF NOT EXISTS issue_changes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER,
                    scan_id INTEGER,
                    previous_scan_id INTEGER,
                    issues_added INTEGER DEFAULT 0,
                    issues_removed INTEGER DEFAULT 0,
                    issues_unchanged INTEGER DEFAULT 0,
                    change_summary_json TEXT,
                    FOREIGN KEY (document_id) REFERENCES documents(id),
                    FOREIGN KEY (scan_id) REFERENCES scans(id)
                )
            ''')

        self._create_table_safe('scan_statements', '''
                CREATE TABLE IF NOT EXISTS scan_statements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_id INTEGER NOT NULL,
                    document_id INTEGER NOT NULL,
                    statement_number TEXT,
                    title TEXT,
                    description TEXT NOT NULL DEFAULT '',
                    level INTEGER DEFAULT 1,
                    role TEXT DEFAULT '',
                    directive TEXT DEFAULT '',
                    section TEXT DEFAULT '',
                    is_header INTEGER DEFAULT 0,
                    notes_json TEXT,
                    position_index INTEGER DEFAULT 0,
                    FOREIGN KEY (scan_id) REFERENCES scans(id),
                    FOREIGN KEY (document_id) REFERENCES documents(id)
                )
            ''',
            'CREATE INDEX IF NOT EXISTS idx_scan_statements_scan ON scan_statements(scan_id)',
            'CREATE INDEX IF NOT EXISTS idx_scan_statements_doc ON scan_statements(document_id)',
            'CREATE INDEX IF NOT EXISTS idx_scan_statements_directive ON scan_statements(directive)')

        self._create_table_safe('function_categories', '''
                CREATE TABLE IF NOT EXISTS function_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    parent_code TEXT,
                    sort_order INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    color TEXT DEFAULT '#3b82f6',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parent_code) REFERENCES function_categories(code)
                )
            ''')

        self._create_table_safe('role_function_tags', '''
                CREATE TABLE IF NOT EXISTS role_function_tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role_id INTEGER,
                    role_name TEXT,
                    function_code TEXT NOT NULL,
                    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    assigned_by TEXT DEFAULT 'system',
                    FOREIGN KEY (role_id) REFERENCES roles(id),
                    FOREIGN KEY (function_code) REFERENCES function_categories(code),
                    UNIQUE(role_id, function_code),
                    UNIQUE(role_name, function_code)
                )
            ''',
            'CREATE INDEX IF NOT EXISTS idx_role_function_tags_role ON role_function_tags(role_name)',
            'CREATE INDEX IF NOT EXISTS idx_role_function_tags_function ON role_function_tags(function_code)')

        self._create_table_safe('document_category_types', '''
                CREATE TABLE IF NOT EXISTS document_category_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    doc_number_patterns TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

        self._create_table_safe('document_categories', '''
                CREATE TABLE IF NOT EXISTS document_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER,
                    document_name TEXT,
                    category_type TEXT NOT NULL,
                    function_code TEXT,
                    doc_number TEXT,
                    document_owner TEXT,
                    auto_detected INTEGER DEFAULT 0,
                    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    assigned_by TEXT DEFAULT 'system',
                    FOREIGN KEY (document_id) REFERENCES documents(id),
                    FOREIGN KEY (function_code) REFERENCES function_categories(code)
                )
            ''',
            'CREATE INDEX IF NOT EXISTS idx_document_categories_doc ON document_categories(document_id)',
            'CREATE INDEX IF NOT EXISTS idx_document_categories_function ON document_categories(function_code)')

        self._create_table_safe('role_required_actions', '''
                CREATE TABLE IF NOT EXISTS role_required_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role_id INTEGER,
                    role_name TEXT NOT NULL,
                    statement_text TEXT NOT NULL,
                    statement_type TEXT DEFAULT 'requirement',
                    source_document_id INTEGER,
                    source_document_name TEXT,
                    source_location TEXT,
                    confidence_score REAL DEFAULT 1.0,
                    is_verified INTEGER DEFAULT 0,
                    verified_by TEXT,
                    verified_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (role_id) REFERENCES roles(id),
                    FOREIGN KEY (source_document_id) REFERENCES documents(id)
                )
            ''',
            'CREATE INDEX IF NOT EXISTS idx_role_required_actions_role ON role_required_actions(role_name)')

        # Seed function categories if empty (in its own transaction)
        self._seed_function_categories()

        _log("Database initialized")

    def _seed_function_categories(self):
        """Seed function categories table with NGC function codes."""
        try:
            with self.connection() as (conn, cursor):
                cursor.execute('SELECT COUNT(*) FROM function_categories')
                if cursor.fetchone()[0] > 0:
                    return  # Already seeded
                _seed_categories = [
                    ('BM', 'Bus Mgmt', 'Business Management', None, 1, '#6366f1'),
                    ('BD', 'Bus Dev', 'Business Development', None, 2, '#8b5cf6'),
                    ('ENG', 'Engineering', 'Engineering functions', None, 3, '#3b82f6'),
                    ('AW', 'AW', 'Airworthiness', 'ENG', 4, '#60a5fa'),
                    ('AVI', 'AvI', 'Avionics Integration', 'ENG', 5, '#60a5fa'),
                    ('EPT', 'EP&T', 'Engineering Planning & Technology', 'ENG', 6, '#60a5fa'),
                    ('FS', 'FS', 'Flight Sciences', 'ENG', 7, '#2563eb'),
                    ('FS-AERO', 'FS-Aerodynamics', 'Aerodynamics', 'FS', 8, '#3b82f6'),
                    ('FS-AD', 'FS-Aircraft Dynamics', 'Aircraft Dynamics', 'FS', 9, '#3b82f6'),
                    ('FS-AL', 'FS-Aircraft Loads', 'Aircraft Loads', 'FS', 10, '#3b82f6'),
                    ('FS-CFD', 'FS-CFD', 'Computational Fluid Dynamics', 'FS', 11, '#3b82f6'),
                    ('FS-CONFIG', 'FS-Configuration', 'Configuration', 'FS', 12, '#3b82f6'),
                    ('FS-MP', 'FS-Mass Prop', 'Mass Properties', 'FS', 13, '#3b82f6'),
                    ('FS-MDAO', 'FS-MDAO', 'Multidisciplinary Design Analysis & Optimization', 'FS', 14, '#3b82f6'),
                    ('FS-PROP', 'FS-Propulsion', 'Propulsion', 'FS', 15, '#3b82f6'),
                    ('FS-VP', 'FS-Vehicle Perf', 'Vehicle Performance', 'FS', 16, '#3b82f6'),
                    ('PMP', 'PM&P', 'Program Management & Planning', 'ENG', 17, '#2563eb'),
                    ('PS', 'PS', 'Product Support', 'ENG', 18, '#2563eb'),
                    ('PS-FFS', 'PS-FFS', 'Field & Fleet Support', 'PS', 19, '#3b82f6'),
                    ('PS-FHR', 'PS-FHR', 'Fleet Health & Reliability', 'PS', 20, '#3b82f6'),
                    ('PS-LSA', 'PS-LSA/MaPL', 'Logistics Support Analysis', 'PS', 21, '#3b82f6'),
                    ('PS-MS', 'PS-M&S', 'Modeling & Simulation', 'PS', 22, '#3b82f6'),
                    ('PS-OBS', 'PS-OBS Mgmt', 'Obsolescence Management', 'PS', 23, '#3b82f6'),
                    ('PS-PHM', 'PS-PhM', 'Prognostics & Health Management', 'PS', 24, '#3b82f6'),
                    ('PS-PSM', 'PS-PSM', 'Product Support Management', 'PS', 25, '#3b82f6'),
                    ('PS-RM', 'PS-R&M', 'Reliability & Maintainability', 'PS', 26, '#3b82f6'),
                    ('PS-SEE', 'PS-SEE', 'Support Equipment Engineering', 'PS', 27, '#3b82f6'),
                    ('PS-SSH', 'PS-SSH', 'Spares & Supply Support', 'PS', 28, '#3b82f6'),
                    ('PS-SLO', 'PS-SLO', 'Support Logistics Operations', 'PS', 29, '#3b82f6'),
                    ('PS-TD', 'PS-TD', 'Technical Data', 'PS', 30, '#3b82f6'),
                    ('PS-TTS', 'PS-TTS', 'Training & Training Systems', 'PS', 31, '#3b82f6'),
                    ('SW', 'SW', 'Software', 'ENG', 32, '#2563eb'),
                    ('SIO', 'SI&O', 'Systems Integration & Operations', 'ENG', 33, '#2563eb'),
                    ('SRV', 'SRV', 'Survivability', 'ENG', 34, '#2563eb'),
                    ('SE', 'SE', 'Systems Engineering', 'ENG', 35, '#2563eb'),
                    ('SE-CDM', 'SE-CDM', 'Configuration & Data Management', 'SE', 36, '#3b82f6'),
                    ('SE-COMMS', 'SE-Comms', 'Communications', 'SE', 37, '#3b82f6'),
                    ('SE-COST', 'SE-Cost Eng (LCC)', 'Cost Engineering / Life Cycle Cost', 'SE', 38, '#3b82f6'),
                    ('SE-DI', 'SE-Design Int', 'Design Integration', 'SE', 39, '#3b82f6'),
                    ('SE-EEE', 'SE-EEE', 'Electrical/Electronic Engineering', 'SE', 40, '#3b82f6'),
                    ('SE-HSI', 'SE-Human Sys Int (HSI)', 'Human Systems Integration', 'SE', 41, '#3b82f6'),
                    ('SE-IFC', 'SE-IFC', 'Interface Control', 'SE', 42, '#3b82f6'),
                    ('SE-MBSE', 'SE-MBSE', 'Model-Based Systems Engineering', 'SE', 43, '#3b82f6'),
                    ('SE-MES', 'SE-Mission Eng/M&S', 'Mission Engineering / M&S', 'SE', 44, '#3b82f6'),
                    ('SE-NS', 'SE-Nuclear Surety', 'Nuclear Surety', 'SE', 45, '#3b82f6'),
                    ('SE-RV', "SE-Req'ts & Verif (R&V)", 'Requirements & Verification', 'SE', 46, '#3b82f6'),
                    ('SE-SEI', 'SE-SE&I', 'Systems Engineering & Integration', 'SE', 47, '#3b82f6'),
                    ('SE-SS', 'SE-Sys Safety', 'System Safety', 'SE', 48, '#3b82f6'),
                    ('SE-VLF', 'SE-Vuln & Live Fire', 'Vulnerability & Live Fire', 'SE', 49, '#3b82f6'),
                    ('SE-HIVE', 'SE-HIVE', 'HIVE', 'SE', 50, '#3b82f6'),
                    ('TE', 'T&E', 'Test & Evaluation', 'ENG', 51, '#2563eb'),
                    ('TE-AGILE', 'T&E-Agile', 'Agile', 'TE', 52, '#3b82f6'),
                    ('TE-EAM', 'T&E-Eng Asset Mgmt (EAM)', 'Engineering Asset Management', 'TE', 53, '#3b82f6'),
                    ('TE-FT', 'T&E-Flight Test', 'Flight Test', 'TE', 54, '#3b82f6'),
                    ('TE-INST', 'T&E-Instrumentation', 'Instrumentation', 'TE', 55, '#3b82f6'),
                    ('TE-LD', 'T&E-Lab Design', 'Lab Design', 'TE', 56, '#3b82f6'),
                    ('TE-LO', 'T&E-Lab Ops', 'Lab Operations', 'TE', 57, '#3b82f6'),
                    ('TE-PROC', 'T&E-Process', 'Process', 'TE', 58, '#3b82f6'),
                    ('TE-SKT', 'T&E-Skills&Training', 'Skills & Training', 'TE', 59, '#3b82f6'),
                    ('TE-ST', 'T&E-Specialty Test (ST)', 'Specialty Test', 'TE', 60, '#3b82f6'),
                    ('TE-TLDP', 'T&E-Staffing (TLDP)', 'Staffing (TLDP)', 'TE', 61, '#3b82f6'),
                    ('TE-STE', 'T&E-System Test Eng', 'System Test Engineering', 'TE', 62, '#3b82f6'),
                    ('TE-TOOLS', 'T&E-Tools', 'Tools', 'TE', 63, '#3b82f6'),
                    ('TE-TPR', 'T&E-TP&R', 'Test Planning & Reporting', 'TE', 64, '#3b82f6'),
                    ('VE', 'VE', 'Vehicle Engineering', 'ENG', 65, '#2563eb'),
                    ('VE-CTRL', 'VE-Controls', 'Controls', 'VE', 66, '#3b82f6'),
                    ('VE-ELEC', 'VE-Electrical', 'Electrical', 'VE', 67, '#3b82f6'),
                    ('VE-FT', 'VE-Fluid/Therm', 'Fluid/Thermal', 'VE', 68, '#3b82f6'),
                    ('VE-LIAS', 'VE-Liaison', 'Liaison', 'VE', 69, '#3b82f6'),
                    ('VE-MECH', 'VE-Mechanical', 'Mechanical', 'VE', 70, '#3b82f6'),
                    ('VE-SATMP', 'VE-SATMP', 'SATMP', 'VE', 71, '#3b82f6'),
                    ('VE-STRD', 'VE-Struct Design', 'Structural Design', 'VE', 72, '#3b82f6'),
                    ('VE-WEAP', 'VE-Weapons', 'Weapons', 'VE', 73, '#3b82f6'),
                    ('WSC', 'WSC', 'Weapon System Cybersecurity', 'ENG', 74, '#2563eb'),
                    ('HR', 'HR', 'Human Resources', None, 75, '#ec4899'),
                    ('IT', 'Info Tech (IT)', 'Information Technology', None, 76, '#8b5cf6'),
                    ('MA', 'Mission Assurance', 'Mission Assurance', None, 77, '#f59e0b'),
                    ('NAT', 'NAT', 'NAT', None, 78, '#06b6d4'),
                    ('PM', 'Prog Mgmt (PM)', 'Program Management', None, 79, '#10b981'),
                    ('PROD', 'Production', 'Production', None, 80, '#22c55e'),
                    ('SC', 'Supply Chain (GSC)', 'Supply Chain / Global Supply Chain', None, 81, '#14b8a6'),
                    ('SEC', 'Security', 'Security', None, 82, '#ef4444'),
                    ('TBD', '(TBD)', 'To Be Determined', None, 83, '#9ca3af'),
                    ('FAC', 'Facilities', 'Facilities', None, 84, '#84cc16'),
                    ('FAC-PLAN', 'Facilities-Planning', 'Facilities Planning', 'FAC', 85, '#a3e635'),
                    ('FAC-EST', 'Facilities-Estimating', 'Facilities Estimating', 'FAC', 86, '#a3e635'),
                    ('FAC-PM', 'Facilities-Project Management', 'Facilities Project Management', 'FAC', 87, '#a3e635'),
                    ('FAC-MAINT', 'Facilities-Maintenance', 'Facilities Maintenance', 'FAC', 88, '#a3e635'),
                    ('FAC-OTH', 'Facilities-Other', 'Facilities Other', 'FAC', 89, '#a3e635'),
                    ('ESHM', 'ESH&M', 'Environmental Safety Health & Mission Assurance', None, 90, '#eab308'),
                    ('OPS', 'Operations', 'Operations', None, 91, '#f97316'),
                    ('LEGAL', 'Legal', 'Legal', None, 92, '#6366f1'),
                ]
                for code, name, desc, parent, sort_order, color in _seed_categories:
                    cursor.execute('''INSERT OR IGNORE INTO function_categories
                        (code, name, description, parent_code, sort_order, color)
                        VALUES (?, ?, ?, ?, ?, ?)''', (code, name, desc, parent, sort_order, color))
        except Exception as e:
            _log(f"Warning: Could not seed function categories: {e}", level='warning')
    
    def _get_file_hash(self, filepath: str) -> str:
        """Get MD5 hash of file for change detection."""
        try:
            with open(filepath, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            logger.warning(f'Could not hash file {filepath}: {e}')
            return ""
    
    def record_scan(self, filename: str, filepath: str, results: Dict, options: Dict) -> Dict:
        """
        Record a document scan and detect changes from previous scans.

        Returns:
            Dict with scan_id, document_id, is_rescan, changes (if rescan)
        """
        file_hash = self._get_file_hash(filepath)

        word_count = results.get('word_count', 0)
        paragraph_count = results.get('paragraph_count', 0)
        issue_count = results.get('issue_count', 0)
        score = results.get('score', 0)
        grade = results.get('grade', 'N/A')

        is_rescan = False
        changes = None
        document_id = None
        prev_scan = None

        with self.connection() as (conn, cursor):
            # Check if document exists
            cursor.execute('''
                SELECT id, file_hash FROM documents
                WHERE filename = ?
                ORDER BY last_scan DESC LIMIT 1
            ''', (filename,))
            existing = cursor.fetchone()

            if existing:
                document_id = existing[0]
                old_hash = existing[1]
                is_rescan = True

                # Update document record
                cursor.execute('''
                    UPDATE documents
                    SET last_scan = CURRENT_TIMESTAMP,
                        scan_count = scan_count + 1,
                        word_count = ?,
                        paragraph_count = ?,
                        file_hash = ?
                    WHERE id = ?
                ''', (word_count, paragraph_count, file_hash, document_id))

                # Get previous scan for comparison
                cursor.execute('''
                    SELECT id, issue_count, results_json FROM scans
                    WHERE document_id = ?
                    ORDER BY scan_time DESC LIMIT 1
                ''', (document_id,))
                prev_scan = cursor.fetchone()

                if prev_scan:
                    prev_scan_id = prev_scan[0]
                    prev_issue_count = prev_scan[1]
                    prev_results = json.loads(prev_scan[2]) if prev_scan[2] else {}

                    # Calculate changes
                    changes = self._calculate_changes(
                        prev_results.get('issues', []),
                        results.get('issues', [])
                    )
                    changes['file_changed'] = (file_hash != old_hash)
            else:
                # Insert new document
                cursor.execute('''
                    INSERT INTO documents (filename, filepath, file_hash, word_count, paragraph_count)
                    VALUES (?, ?, ?, ?, ?)
                ''', (filename, filepath, file_hash, word_count, paragraph_count))
                document_id = cursor.lastrowid

            # Record the scan
            cursor.execute('''
                INSERT INTO scans (document_id, options_json, issue_count, score, grade,
                                  word_count, paragraph_count, results_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                document_id,
                json.dumps(options),
                issue_count,
                score,
                grade,
                word_count,
                paragraph_count,
                json.dumps(results)
            ))
            scan_id = cursor.lastrowid

            # Record changes if rescan
            if is_rescan and changes:
                cursor.execute('''
                    INSERT INTO issue_changes (document_id, scan_id, previous_scan_id,
                                              issues_added, issues_removed, issues_unchanged,
                                              change_summary_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    document_id, scan_id, prev_scan_id if prev_scan else None,
                    changes['added'], changes['removed'], changes['unchanged'],
                    json.dumps(changes)
                ))

            # Process roles from results
            if results.get('roles'):
                self._process_roles(cursor, document_id, results['roles'])

        return {
            'scan_id': scan_id,
            'document_id': document_id,
            'is_rescan': is_rescan,
            'scan_count': existing[0] if existing else 1,
            'changes': changes
        }
    
    def _calculate_changes(self, old_issues: List[Dict], new_issues: List[Dict]) -> Dict:
        """Calculate differences between two issue lists."""
        # Create fingerprints for comparison
        def fingerprint(issue):
            return (
                issue.get('category', ''),
                issue.get('message', '')[:50],
                issue.get('paragraph_index', 0)
            )
        
        old_fps = set(fingerprint(i) for i in old_issues)
        new_fps = set(fingerprint(i) for i in new_issues)
        
        added = new_fps - old_fps
        removed = old_fps - new_fps
        unchanged = old_fps & new_fps
        
        return {
            'added': len(added),
            'removed': len(removed),
            'unchanged': len(unchanged),
            'added_categories': self._categorize_changes(new_issues, added),
            'removed_categories': self._categorize_changes(old_issues, removed)
        }
    
    def _categorize_changes(self, issues: List[Dict], fingerprints: set) -> Dict[str, int]:
        """Group changes by category."""
        def fingerprint(issue):
            return (
                issue.get('category', ''),
                issue.get('message', '')[:50],
                issue.get('paragraph_index', 0)
            )
        
        categories = {}
        for issue in issues:
            if fingerprint(issue) in fingerprints:
                cat = issue.get('category', 'Unknown')
                categories[cat] = categories.get(cat, 0) + 1
        
        return categories
    
    def _process_roles(self, cursor, document_id: int, roles_data: Dict):
        """Process and store role data from scan results."""
        if not roles_data:
            return
        
        # Handle both formats: {role_name: data} or {'roles': {role_name: data}}
        roles = roles_data.get('roles', roles_data)
        if not isinstance(roles, dict):
            return
        
        # Deliverables list (common document types, not roles)
        deliverables = {
            'verification cross reference matrix', 'vcr', 'verification matrix',
            'requirements document', 'specification', 'test plan', 'test report',
            'design document', 'interface control document', 'icd', 'sow',
            'statement of work', 'proposal', 'report', 'analysis', 'study',
            'plan', 'procedure', 'instruction', 'manual', 'guide'
        }
        
        for role_name, role_data in roles.items():
            if not role_name or not isinstance(role_data, dict):
                continue
            
            # Normalize role name
            normalized = role_name.lower().strip()
            
            # Check if this is likely a deliverable, not a role
            is_deliverable = any(d in normalized for d in deliverables)
            
            # Determine category
            category = 'Role'
            if is_deliverable:
                category = 'Deliverable'
            elif 'manager' in normalized or 'lead' in normalized:
                category = 'Management'
            elif 'engineer' in normalized or 'analyst' in normalized:
                category = 'Technical'
            
            # Check if role exists
            cursor.execute('SELECT id, document_count, total_mentions FROM roles WHERE normalized_name = ?',
                          (normalized,))
            existing = cursor.fetchone()
            
            mention_count = len(role_data.get('mentions', [])) or 1
            
            if existing:
                role_id = existing[0]
                cursor.execute('''
                    UPDATE roles SET 
                        document_count = document_count + 1,
                        total_mentions = total_mentions + ?
                    WHERE id = ?
                ''', (mention_count, role_id))
            else:
                cursor.execute('''
                    INSERT INTO roles (role_name, normalized_name, total_mentions, 
                                      is_deliverable, category, description)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    role_name, normalized, mention_count, 
                    1 if is_deliverable else 0, category,
                    role_data.get('description', '')
                ))
                role_id = cursor.lastrowid
            
            # Update document-role relationship
            responsibilities = role_data.get('responsibilities', [])
            cursor.execute('''
                INSERT INTO document_roles (document_id, role_id, mention_count, responsibilities_json)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(document_id, role_id) DO UPDATE SET
                    mention_count = mention_count + excluded.mention_count,
                    responsibilities_json = excluded.responsibilities_json,
                    last_updated = CURRENT_TIMESTAMP
            ''', (document_id, role_id, mention_count, json.dumps(responsibilities)))
    
    def get_scan_history(self, filename: str = None, limit: int = 50) -> List[Dict]:
        """Get scan history, optionally filtered by filename.

        v3.0.76: Added role_count to results for Document Log display.
        v3.0.110: Added document_id for document comparison feature.
        """
        with self.connection() as (conn, cursor):
            if filename:
                cursor.execute('''
                    SELECT s.id, d.filename, s.scan_time, s.issue_count, s.score, s.grade,
                           s.word_count, ic.issues_added, ic.issues_removed,
                           (SELECT COUNT(*) FROM document_roles dr WHERE dr.document_id = d.id) as role_count,
                           d.id as document_id,
                           (SELECT COUNT(*) FROM scan_statements ss WHERE ss.scan_id = s.id) as statement_count
                    FROM scans s
                    JOIN documents d ON s.document_id = d.id
                    LEFT JOIN issue_changes ic ON s.id = ic.scan_id
                    WHERE d.filename = ?
                    ORDER BY s.scan_time DESC LIMIT ?
                ''', (filename, limit))
            else:
                cursor.execute('''
                    SELECT s.id, d.filename, s.scan_time, s.issue_count, s.score, s.grade,
                           s.word_count, ic.issues_added, ic.issues_removed,
                           (SELECT COUNT(*) FROM document_roles dr WHERE dr.document_id = d.id) as role_count,
                           d.id as document_id,
                           (SELECT COUNT(*) FROM scan_statements ss WHERE ss.scan_id = s.id) as statement_count
                    FROM scans s
                    JOIN documents d ON s.document_id = d.id
                    LEFT JOIN issue_changes ic ON s.id = ic.scan_id
                    ORDER BY s.scan_time DESC LIMIT ?
                ''', (limit,))

            results = []
            for row in cursor.fetchall():
                results.append({
                    'scan_id': row[0],
                    'filename': row[1],
                    'scan_time': row[2],
                    'issue_count': row[3],
                    'score': row[4],
                    'grade': row[5],
                    'word_count': row[6],
                    'issues_added': row[7] or 0,
                    'issues_removed': row[8] or 0,
                    'role_count': row[9] or 0,
                    'document_id': row[10],
                    'statement_count': row[11] or 0
                })

        return results
    
    def get_score_trend(self, filename: str, limit: int = 10) -> List[Dict]:
        """Get quality score trend for a specific document.

        v3.0.33 Chunk E: Returns score history for sparkline visualization.

        Args:
            filename: Document filename to get trend for
            limit: Maximum number of historical scores (default: 10)

        Returns:
            List of dicts with scan_time, score, grade, issue_count
            Ordered oldest to newest for sparkline display
        """
        with self.connection() as (conn, cursor):
            cursor.execute('''
                SELECT s.scan_time, s.score, s.grade, s.issue_count
                FROM scans s
                JOIN documents d ON s.document_id = d.id
                WHERE d.filename = ?
                ORDER BY s.scan_time DESC
                LIMIT ?
            ''', (filename, limit))

            results = []
            for row in cursor.fetchall():
                results.append({
                    'scan_time': row[0],
                    'score': row[1],
                    'grade': row[2],
                    'issue_count': row[3]
                })

        # Reverse to oldest-first for sparkline display
        return list(reversed(results))
    
    def get_score_trend_by_id(self, document_id: int, limit: int = 10) -> List[Dict]:
        """Get quality score trend for a document by its ID.

        v3.0.35: More reliable than filename matching for edge cases.

        Args:
            document_id: Document ID from database
            limit: Maximum number of historical scores (default: 10)

        Returns:
            List of dicts with scan_time, score, grade, issue_count
            Ordered oldest to newest for sparkline display
        """
        with self.connection() as (conn, cursor):
            cursor.execute('''
                SELECT s.scan_time, s.score, s.grade, s.issue_count
                FROM scans s
                WHERE s.document_id = ?
                ORDER BY s.scan_time DESC
                LIMIT ?
            ''', (document_id, limit))

            results = []
            for row in cursor.fetchall():
                results.append({
                    'scan_time': row[0],
                    'score': row[1],
                    'grade': row[2],
                    'issue_count': row[3]
                })

        # Reverse to oldest-first for sparkline display
        return list(reversed(results))
    
    def get_all_roles(self, include_deliverables: bool = False) -> List[Dict]:
        """Get aggregated roles across all documents.

        v3.0.69: Added responsibility_count and unique_document_count fields.
        - responsibility_count: Total responsibilities extracted for this role
        - unique_document_count: Count of unique documents (not re-scans)
        """
        with self.connection() as (conn, cursor):
            query = '''
                SELECT r.id, r.role_name, r.normalized_name, r.document_count,
                       r.total_mentions, r.category, r.is_deliverable,
                       GROUP_CONCAT(DISTINCT d.filename) as documents,
                       GROUP_CONCAT(dr.responsibilities_json, '|||') as all_responsibilities
                FROM roles r
                LEFT JOIN document_roles dr ON r.id = dr.role_id
                LEFT JOIN documents d ON dr.document_id = d.id
            '''

            if not include_deliverables:
                query += ' WHERE r.is_deliverable = 0'

            query += ' GROUP BY r.id ORDER BY r.document_count DESC, r.total_mentions DESC'

            cursor.execute(query)

            results = []
            for row in cursor.fetchall():
                documents = row[7].split(',') if row[7] else []
                unique_docs = list(set(documents))  # Dedupe

                # v3.0.69: Count responsibilities from all document_roles entries
                # v5.0.0: Deduplicate statements to avoid inflated counts from repeated scans
                responsibility_count = 0
                seen_resp_texts = set()
                if row[8]:  # all_responsibilities concatenated with |||
                    resp_chunks = row[8].split('|||')
                    for chunk in resp_chunks:
                        if chunk and chunk.strip():
                            try:
                                resp_list = json.loads(chunk)
                                if isinstance(resp_list, list):
                                    for resp_item in resp_list:
                                        txt = ''
                                        if isinstance(resp_item, str):
                                            txt = resp_item.strip()
                                        elif isinstance(resp_item, dict):
                                            txt = (resp_item.get('text') or resp_item.get('responsibility') or '').strip()
                                        if txt and txt not in seen_resp_texts:
                                            seen_resp_texts.add(txt)
                                            responsibility_count += 1
                            except (json.JSONDecodeError, TypeError):
                                pass

                results.append({
                    'id': row[0],
                    'role_name': row[1],
                    'normalized_name': row[2],
                    'document_count': row[3],  # Legacy: total scan count
                    'unique_document_count': len(unique_docs),  # v3.0.69: Unique docs
                    'total_mentions': row[4],
                    'responsibility_count': responsibility_count,  # v3.0.69: Total responsibilities
                    'category': row[5],
                    'is_deliverable': bool(row[6]),
                    'documents': unique_docs
                })

        return results
    
    def get_document_roles(self, document_id: int) -> List[Dict]:
        """Get roles for a specific document.

        v3.0.80: Added for per-document role export functionality.

        Args:
            document_id: The ID of the document to get roles for

        Returns:
            List of role dictionaries with name, category, mentions, responsibilities
        """
        with self.connection() as (conn, cursor):
            cursor.execute('''
                SELECT r.id, r.role_name, r.normalized_name, r.category, r.is_deliverable,
                       dr.mention_count, dr.responsibilities_json
                FROM document_roles dr
                JOIN roles r ON dr.role_id = r.id
                WHERE dr.document_id = ?
                ORDER BY dr.mention_count DESC, r.role_name
            ''', (document_id,))

            results = []
            for row in cursor.fetchall():
                responsibilities = []
                if row[6]:
                    try:
                        responsibilities = json.loads(row[6])
                    except (json.JSONDecodeError, TypeError):
                        pass

                results.append({
                    'id': row[0],
                    'role_name': row[1],
                    'normalized_name': row[2],
                    'category': row[3] or 'unknown',
                    'is_deliverable': bool(row[4]),
                    'mention_count': row[5] or 0,
                    'responsibilities': responsibilities if isinstance(responsibilities, list) else []
                })

        return results

    def get_role_context(self, role_name: str) -> Optional[Dict]:
        """Get detailed context for a specific role including all occurrences.

        v4.8.3: Implemented to support Data Explorer role detail view.
        Pulls responsibility text from document_roles.responsibilities_json,
        merging across all documents the role appears in.

        Returns:
            Dict with role_name, category, documents, occurrences, total_mentions, document_count
            or None if the role is not found.
        """
        with self.connection() as (conn, cursor):
            # Find the role
            cursor.execute('SELECT id, role_name, category FROM roles WHERE role_name = ?', (role_name,))
            role = cursor.fetchone()
            if not role:
                # Try normalized name
                cursor.execute('SELECT id, role_name, category FROM roles WHERE normalized_name = ?',
                               (role_name.upper().strip(),))
                role = cursor.fetchone()
            if not role:
                return None

            role_id = role[0]
            actual_name = role[1]
            category = role[2] or 'Role'

            # Get all document_roles entries with responsibilities
            cursor.execute('''
                SELECT dr.mention_count, dr.responsibilities_json, d.filename
                FROM document_roles dr
                JOIN documents d ON d.id = dr.document_id
                WHERE dr.role_id = ?
                ORDER BY d.filename
            ''', (role_id,))

            documents = []
            occurrences = []
            total_mentions = 0
            seen_texts = set()  # v5.0.0: Deduplicate statements from repeated scans

            for row in cursor.fetchall():
                mention_count = row[0] or 0
                resp_json = row[1]
                filename = row[2]
                total_mentions += mention_count
                documents.append(filename)

                if resp_json:
                    try:
                        resps = json.loads(resp_json)
                        if isinstance(resps, list):
                            for stmt_idx, resp in enumerate(resps):
                                if isinstance(resp, str):
                                    if resp.strip() and resp.strip() not in seen_texts:
                                        seen_texts.add(resp.strip())
                                        occurrences.append({
                                            'responsibility': resp.strip(),
                                            'action_type': '',
                                            'document': filename,
                                            'section': '',
                                            'confidence': 0.8,
                                            'statement_index': stmt_idx,
                                            'review_status': '',
                                            'notes': ''
                                        })
                                elif isinstance(resp, dict):
                                    text = resp.get('text') or resp.get('responsibility') or ''
                                    if text.strip() and text.strip() not in seen_texts:
                                        seen_texts.add(text.strip())
                                        occurrences.append({
                                            'responsibility': text.strip(),
                                            'action_type': resp.get('action_type', ''),
                                            'document': filename,
                                            'section': resp.get('section', ''),
                                            'confidence': resp.get('confidence', 0.8),
                                            'statement_index': stmt_idx,
                                            'review_status': resp.get('review_status', ''),
                                            'notes': resp.get('notes', '')
                                        })
                    except (json.JSONDecodeError, TypeError):
                        pass

            return {
                'role_name': actual_name,
                'category': category,
                'documents': documents,
                'occurrences': occurrences,
                'total_mentions': total_mentions,
                'document_count': len(documents)
            }

    def get_raci_matrix(self, include_documents: bool = True) -> Dict:
        """v5.0.0: Compute RACI matrix from stored responsibilities in document_roles.

        Extracts action verbs from responsibility text and classifies each into
        R (Responsible), A (Accountable), C (Consulted), or I (Informed) using
        keyword pattern matching identical to the client-side JS logic.

        Returns:
            Dict with:
                roles: {role_name: {R, A, C, I, action_types, documents, category, ...}}
                summary: {total_R, total_A, total_C, total_I, role_count}
        """
        # RACI verb classification patterns (must match roles.js lines 1939-1949)
        raci_patterns = {
            'R': re.compile(r'^(perform|execute|implement|develop|define|lead|ensure|maintain|conduct|create|prepare|manage|oversee|verif|valid)', re.IGNORECASE),
            'A': re.compile(r'^(approv|authoriz|sign|certif|accept)', re.IGNORECASE),
            'C': re.compile(r'^(review|coordinat|support|consult|advis|assist|collaborat)', re.IGNORECASE),
            'I': re.compile(r'^(receiv|report|monitor|inform|notif|communicat|track|provid)', re.IGNORECASE),
        }

        # Common action verbs to extract from responsibility text
        verb_extract_pattern = re.compile(
            r'\b(shall|must|will|should|may)\s+(\w+)',
            re.IGNORECASE
        )

        def classify_verb(verb: str) -> str:
            """Classify a single verb into R/A/C/I category."""
            for raci_type, pattern in raci_patterns.items():
                if pattern.match(verb):
                    return raci_type
            return 'R'  # Default to Responsible

        with self.connection() as (conn, cursor):
            # Get all roles with their responsibilities and documents
            cursor.execute('''
                SELECT r.id, r.role_name, r.normalized_name, r.category,
                       dr.responsibilities_json, d.filename
                FROM roles r
                LEFT JOIN document_roles dr ON r.id = dr.role_id
                LEFT JOIN documents d ON dr.document_id = d.id
                WHERE r.is_deliverable = 0
                ORDER BY r.role_name
            ''')

            roles_data = {}
            for row in cursor.fetchall():
                role_id = row[0]
                role_name = row[1]
                normalized = row[2]
                category = row[3] or 'Role'
                resp_json = row[4]
                filename = row[5]

                if role_name not in roles_data:
                    roles_data[role_name] = {
                        'R': 0, 'A': 0, 'C': 0, 'I': 0,
                        'action_types': {},
                        'documents': [],
                        'normalized_name': (normalized or role_name).lower(),
                        'category': category,
                        'primary_type': 'R',
                        '_seen_texts': set()  # For deduplication
                    }

                rd = roles_data[role_name]

                # Track documents
                if filename and filename not in rd['documents']:
                    rd['documents'].append(filename)

                # Parse responsibilities and extract action verbs
                # v5.0.0: Deduplicate statements within each role to avoid
                # inflated counts from multiple scans of the same document
                if resp_json:
                    try:
                        resps = json.loads(resp_json)
                        if isinstance(resps, list):
                            for resp in resps:
                                text = ''
                                if isinstance(resp, str):
                                    text = resp
                                elif isinstance(resp, dict):
                                    text = resp.get('text') or resp.get('responsibility') or ''

                                if not text.strip():
                                    continue

                                # Skip duplicate statements for this role
                                if text.strip() in rd['_seen_texts']:
                                    continue
                                rd['_seen_texts'].add(text.strip())

                                # Extract action verbs from text
                                matches = verb_extract_pattern.findall(text)
                                if matches:
                                    for _, verb in matches:
                                        verb_lower = verb.lower()
                                        raci_type = classify_verb(verb_lower)
                                        rd[raci_type] += 1
                                        rd['action_types'][verb_lower] = rd['action_types'].get(verb_lower, 0) + 1
                                else:
                                    # No modal verb found, count as one R mention
                                    rd['R'] += 1
                                    rd['action_types']['_unclassified'] = rd['action_types'].get('_unclassified', 0) + 1
                    except (json.JSONDecodeError, TypeError):
                        pass

            # Compute primary type and summary
            total_R = total_A = total_C = total_I = 0
            for name, rd in roles_data.items():
                total = rd['R'] + rd['A'] + rd['C'] + rd['I']
                if total > 0:
                    max_val = max(rd['R'], rd['A'], rd['C'], rd['I'])
                    if rd['R'] == max_val:
                        rd['primary_type'] = 'R'
                    elif rd['A'] == max_val:
                        rd['primary_type'] = 'A'
                    elif rd['C'] == max_val:
                        rd['primary_type'] = 'C'
                    else:
                        rd['primary_type'] = 'I'

                total_R += rd['R']
                total_A += rd['A']
                total_C += rd['C']
                total_I += rd['I']

                if not include_documents:
                    del rd['documents']

                # Remove internal dedup set (not JSON serializable)
                rd.pop('_seen_texts', None)

            return {
                'roles': roles_data,
                'summary': {
                    'total_R': total_R,
                    'total_A': total_A,
                    'total_C': total_C,
                    'total_I': total_I,
                    'role_count': len(roles_data)
                }
            }

    def update_responsibility_statement(self, role_name: str, document_name: str,
                                         statement_index: int, updates: Dict) -> bool:
        """v4.8.4: Update an individual responsibility statement within document_roles.responsibilities_json.

        Args:
            role_name: Name of the role
            document_name: Filename of the document containing this statement
            statement_index: 0-based index of the statement within the document's responsibilities array
            updates: Dict of fields to update (text, action_type, section, review_status, notes)

        Returns True if update was successful.
        """
        with self.connection() as (conn, cursor):
            # Find the role
            cursor.execute('SELECT id FROM roles WHERE role_name = ?', (role_name,))
            role = cursor.fetchone()
            if not role:
                cursor.execute('SELECT id FROM roles WHERE normalized_name = ?',
                               (role_name.upper().strip(),))
                role = cursor.fetchone()
            if not role:
                return False

            role_id = role[0]

            # Find the document
            cursor.execute('SELECT id FROM documents WHERE filename = ?', (document_name,))
            doc = cursor.fetchone()
            if not doc:
                # Try partial match
                cursor.execute('SELECT id FROM documents WHERE filename LIKE ?',
                               (f'%{document_name}%',))
                doc = cursor.fetchone()
            if not doc:
                return False

            doc_id = doc[0]

            # Get current responsibilities_json
            cursor.execute('''
                SELECT id, responsibilities_json FROM document_roles
                WHERE role_id = ? AND document_id = ?
            ''', (role_id, doc_id))
            dr = cursor.fetchone()
            if not dr:
                return False

            dr_id = dr[0]
            resp_json = dr[1]

            try:
                resps = json.loads(resp_json) if resp_json else []
            except (json.JSONDecodeError, TypeError):
                resps = []

            if not isinstance(resps, list) or statement_index < 0 or statement_index >= len(resps):
                return False

            # Update the statement at the given index
            current = resps[statement_index]

            # Normalize to dict format
            if isinstance(current, str):
                current = {'text': current, 'action_type': '', 'section': '', 'confidence': 0.8}

            # Apply updates
            allowed_fields = {'text', 'action_type', 'section', 'review_status', 'notes', 'confidence'}
            for key, value in updates.items():
                if key in allowed_fields:
                    current[key] = value

            resps[statement_index] = current

            # Save back
            cursor.execute('''
                UPDATE document_roles SET responsibilities_json = ?, last_updated = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (json.dumps(resps), dr_id))

            return cursor.rowcount > 0

    def get_all_role_statements(self, filters: Optional[Dict] = None) -> Dict:
        """v4.9.5: Get ALL responsibility statements across ALL roles for mass review.

        Args:
            filters: Optional dict with keys:
                - review_status: str ('pending', 'reviewed', 'rejected', '' for unreviewed)
                - document: str (filename filter)
                - role: str (role name filter)
                - search: str (text search in statement)
                - flagged_only: bool (only return statements flagged as problematic)

        Returns:
            Dict with 'statements' list and 'summary' stats
        """
        filters = filters or {}
        with self.connection() as (conn, cursor):
            # Get ALL document_roles with role and document info
            cursor.execute('''
                SELECT r.role_name, r.category, r.is_deliverable,
                       d.filename, dr.responsibilities_json, dr.mention_count
                FROM document_roles dr
                JOIN roles r ON r.id = dr.role_id
                JOIN documents d ON d.id = dr.document_id
                WHERE r.is_deliverable = 0
                ORDER BY r.role_name, d.filename
            ''')

            all_statements = []
            stats = {
                'total': 0, 'reviewed': 0, 'rejected': 0,
                'pending': 0, 'unreviewed': 0,
                'flagged_fragment': 0, 'flagged_wrong': 0,
                'roles_count': 0, 'documents_count': 0
            }
            seen_roles = set()
            seen_docs = set()

            filter_status = filters.get('review_status', '')
            filter_doc = filters.get('document', '')
            filter_role = filters.get('role', '')
            filter_search = filters.get('search', '').lower()
            flagged_only = filters.get('flagged_only', False)

            for row in cursor.fetchall():
                role_name = row[0]
                category = row[1] or 'Role'
                is_deliverable = row[2]
                filename = row[3]
                resp_json = row[4]
                mention_count = row[5] or 0

                # Apply role/document filters early
                if filter_role and filter_role.lower() not in role_name.lower():
                    continue
                if filter_doc and filter_doc.lower() not in filename.lower():
                    continue

                seen_roles.add(role_name)
                seen_docs.add(filename)

                if not resp_json:
                    continue

                try:
                    resps = json.loads(resp_json)
                    if not isinstance(resps, list):
                        continue
                except (json.JSONDecodeError, TypeError):
                    continue

                for stmt_idx, resp in enumerate(resps):
                    text = ''
                    action_type = ''
                    section = ''
                    confidence = 0.8
                    review_status = ''
                    notes = ''

                    if isinstance(resp, str):
                        text = resp.strip()
                    elif isinstance(resp, dict):
                        text = (resp.get('text') or resp.get('responsibility') or '').strip()
                        action_type = resp.get('action_type', '')
                        section = resp.get('section', '')
                        confidence = resp.get('confidence', 0.8)
                        review_status = resp.get('review_status', '')
                        notes = resp.get('notes', '')

                    if not text:
                        continue

                    # Apply search filter
                    if filter_search and filter_search not in text.lower():
                        continue

                    # Apply status filter
                    if filter_status:
                        effective_status = review_status or 'unreviewed'
                        if filter_status == 'unreviewed' and review_status:
                            continue
                        elif filter_status != 'unreviewed' and effective_status != filter_status:
                            continue

                    # Smart adjudication flags
                    flags = []
                    word_count = len(text.split())

                    # Fragment detection: too short to be meaningful
                    if word_count <= 3:
                        flags.append('fragment_short')
                    # Fragment: looks like a sentence fragment (no verb-like words)
                    elif word_count <= 6 and not any(w in text.lower() for w in
                            ['shall', 'must', 'will', 'should', 'may', 'perform',
                             'manage', 'review', 'approve', 'ensure', 'maintain',
                             'provide', 'support', 'coordinate', 'develop', 'create',
                             'conduct', 'implement', 'monitor', 'verify', 'prepare',
                             'submit', 'deliver', 'execute', 'operate', 'inspect',
                             'is responsible', 'are responsible']):
                        flags.append('fragment_no_verb')

                    # Wrong: appears to be a header/title rather than a responsibility
                    if text.isupper() and word_count <= 8:
                        flags.append('wrong_header')
                    # Wrong: contains only numbers or references
                    if all(c.isdigit() or c in './-() ' for c in text):
                        flags.append('wrong_number')
                    # Wrong: very long (likely a paragraph, not a statement)
                    if word_count > 80:
                        flags.append('wrong_too_long')
                    # Wrong: starts with common non-statement patterns
                    lower_text = text.lower()
                    if lower_text.startswith(('table ', 'figure ', 'note:', 'see ', 'ref ', 'page ')):
                        flags.append('wrong_reference')
                    # Duplicate-like: exact same text within same role
                    # (handled in frontend for performance)

                    # Low confidence
                    if confidence < 0.5:
                        flags.append('low_confidence')

                    if flagged_only and not flags:
                        continue

                    stmt_record = {
                        'role_name': role_name,
                        'category': category,
                        'document': filename,
                        'text': text,
                        'statement_index': stmt_idx,
                        'action_type': action_type,
                        'section': section,
                        'confidence': confidence,
                        'review_status': review_status,
                        'notes': notes,
                        'mention_count': mention_count,
                        'word_count': word_count,
                        'flags': flags
                    }

                    all_statements.append(stmt_record)

                    # Update stats
                    stats['total'] += 1
                    if review_status == 'reviewed':
                        stats['reviewed'] += 1
                    elif review_status == 'rejected':
                        stats['rejected'] += 1
                    elif review_status == 'pending':
                        stats['pending'] += 1
                    else:
                        stats['unreviewed'] += 1

                    if 'fragment_short' in flags or 'fragment_no_verb' in flags:
                        stats['flagged_fragment'] += 1
                    if any(f.startswith('wrong_') for f in flags):
                        stats['flagged_wrong'] += 1

            stats['roles_count'] = len(seen_roles)
            stats['documents_count'] = len(seen_docs)

            return {
                'statements': all_statements,
                'summary': stats
            }

    def bulk_delete_role_statements(self, deletions: list) -> int:
        """v4.9.5: Bulk delete (or reject) responsibility statements.

        Args:
            deletions: List of dicts with {role_name, document, statement_index}
                       Sorted by role_name, document, statement_index DESC for safe removal.

        Returns: Number of statements deleted.
        """
        deleted = 0
        # Group by (role_name, document) for efficiency
        grouped = {}
        for d in deletions:
            key = (d['role_name'], d['document'])
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(d['statement_index'])

        with self.connection() as (conn, cursor):
            for (role_name, doc_name), indices in grouped.items():
                # Find role
                cursor.execute('SELECT id FROM roles WHERE role_name = ?', (role_name,))
                role = cursor.fetchone()
                if not role:
                    cursor.execute('SELECT id FROM roles WHERE normalized_name = ?',
                                   (role_name.upper().strip(),))
                    role = cursor.fetchone()
                if not role:
                    continue

                # Find document
                cursor.execute('SELECT id FROM documents WHERE filename = ?', (doc_name,))
                doc = cursor.fetchone()
                if not doc:
                    cursor.execute('SELECT id FROM documents WHERE filename LIKE ?',
                                   (f'%{doc_name}%',))
                    doc = cursor.fetchone()
                if not doc:
                    continue

                # Get current responsibilities
                cursor.execute('''
                    SELECT id, responsibilities_json FROM document_roles
                    WHERE role_id = ? AND document_id = ?
                ''', (role[0], doc[0]))
                dr = cursor.fetchone()
                if not dr:
                    continue

                dr_id = dr[0]
                try:
                    resps = json.loads(dr[1]) if dr[1] else []
                except (json.JSONDecodeError, TypeError):
                    continue

                # Remove indices in reverse order to maintain correct indices
                for idx in sorted(indices, reverse=True):
                    if 0 <= idx < len(resps):
                        resps.pop(idx)
                        deleted += 1

                cursor.execute('''
                    UPDATE document_roles SET responsibilities_json = ?, last_updated = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (json.dumps(resps), dr_id))

        return deleted

    def get_role_document_matrix(self) -> Dict:
        """Get a matrix of roles vs documents for visualization."""
        with self.connection() as (conn, cursor):
            # Get all documents
            cursor.execute('SELECT id, filename FROM documents ORDER BY filename')
            documents = {row[0]: row[1] for row in cursor.fetchall()}

            # Get all roles (excluding deliverables)
            cursor.execute('SELECT id, role_name FROM roles WHERE is_deliverable = 0 ORDER BY role_name')
            roles = {row[0]: row[1] for row in cursor.fetchall()}

            # Get relationships
            cursor.execute('''
                SELECT document_id, role_id, mention_count
                FROM document_roles
            ''')

            matrix = {}
            for row in cursor.fetchall():
                doc_id, role_id, count = row
                if doc_id in documents and role_id in roles:
                    if role_id not in matrix:
                        matrix[role_id] = {}
                    matrix[role_id][doc_id] = count

        return {
            'documents': documents,
            'roles': roles,
            'connections': matrix
        }
    
    # Scan Profile Methods
    def save_scan_profile(self, name: str, options: Dict, description: str = "",
                          set_default: bool = False) -> int:
        """Save a scan profile (check configuration)."""
        with self.connection() as (conn, cursor):
            if set_default:
                # Clear other defaults
                cursor.execute('UPDATE scan_profiles SET is_default = 0')

            cursor.execute('''
                INSERT INTO scan_profiles (name, description, options_json, is_default)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    description = excluded.description,
                    options_json = excluded.options_json,
                    is_default = excluded.is_default
            ''', (name, description, json.dumps(options), 1 if set_default else 0))

            profile_id = cursor.lastrowid

        return profile_id
    
    def get_scan_profiles(self) -> List[Dict]:
        """Get all saved scan profiles."""
        with self.connection() as (conn, cursor):
            cursor.execute('''
                SELECT id, name, description, options_json, is_default, created, last_used
                FROM scan_profiles ORDER BY is_default DESC, name
            ''')

            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'options': json.loads(row[3]),
                    'is_default': bool(row[4]),
                    'created': row[5],
                    'last_used': row[6]
                })

        return results
    
    def get_default_profile(self) -> Optional[Dict]:
        """Get the default scan profile."""
        with self.connection() as (conn, cursor):
            cursor.execute('''
                SELECT id, name, options_json FROM scan_profiles
                WHERE is_default = 1 LIMIT 1
            ''')
            row = cursor.fetchone()

        if row:
            return {
                'id': row[0],
                'name': row[1],
                'options': json.loads(row[2])
            }
        return None
    
    def delete_scan_profile(self, profile_id: int) -> bool:
        """Delete a scan profile."""
        with self.connection() as (conn, cursor):
            cursor.execute('DELETE FROM scan_profiles WHERE id = ?', (profile_id,))
            deleted = cursor.rowcount > 0
        return deleted
    
    def delete_scan(self, scan_id: int) -> Dict:
        """
        Delete a scan record and clean up related data.

        Args:
            scan_id: The ID of the scan to delete

        Returns:
            Dict with success status and message
        """
        try:
            with self.connection() as (conn, cursor):
                # First, get the document_id for this scan
                cursor.execute('SELECT document_id FROM scans WHERE id = ?', (scan_id,))
                row = cursor.fetchone()

                if not row:
                    return {'success': False, 'message': 'Scan not found'}

                document_id = row[0]

                # Delete issue_changes for this scan
                cursor.execute('DELETE FROM issue_changes WHERE scan_id = ?', (scan_id,))

                # Delete the scan itself
                cursor.execute('DELETE FROM scans WHERE id = ?', (scan_id,))
                scan_deleted = cursor.rowcount > 0

                # Check if document has any remaining scans
                cursor.execute('SELECT COUNT(*) FROM scans WHERE document_id = ?', (document_id,))
                remaining_scans = cursor.fetchone()[0]

                document_deleted = False
                if remaining_scans == 0:
                    # No more scans for this document - clean up
                    cursor.execute('DELETE FROM document_roles WHERE document_id = ?', (document_id,))
                    cursor.execute('DELETE FROM documents WHERE id = ?', (document_id,))
                    document_deleted = True
                    _log(f"Deleted document {document_id} (no remaining scans)")

            return {
                'success': scan_deleted,
                'message': 'Scan deleted successfully',
                'document_deleted': document_deleted
            }

        except Exception as e:
            _log(f"Error deleting scan {scan_id}: {e}", 'error')
            return {'success': False, 'message': str(e)}
    
    def use_profile(self, profile_id: int):
        """Mark a profile as used (update last_used timestamp)."""
        with self.connection() as (conn, cursor):
            cursor.execute('''
                UPDATE scan_profiles SET last_used = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (profile_id,))
    
    def get_role_hierarchy(self) -> Dict:
        """
        v4.7.3: Build role hierarchy tree from SIPOC inherits-from relationships.

        Uses the role_relationships table (populated by SIPOC imports) to build
        an actual inheritance tree. Roles that inherit from another role are
        children; roles with no parents are roots.

        Falls back to function-tag grouping if no SIPOC relationships exist,
        and to role categories if no function tags exist either.

        Returns:
            Dict with nodes, edges, roots, children_map, stats
        """
        with self.connection() as (conn, cursor):
            # Check if role_relationships table has SIPOC data
            try:
                cursor.execute("SELECT COUNT(*) FROM role_relationships WHERE relationship_type = 'inherits-from'")
                rel_count = cursor.fetchone()[0]
            except Exception as e:
                logger.debug(f'role_relationships table query failed (may not exist yet): {e}')
                rel_count = 0

            if rel_count == 0:
                # Fallback: try function tag grouping, then category grouping
                try:
                    cursor.execute('SELECT COUNT(*) FROM function_categories')
                    fc_count = cursor.fetchone()[0]
                except Exception as e:
                    logger.debug(f'function_categories table query failed: {e}')
                    fc_count = 0
                if fc_count > 0:
                    return self._get_role_hierarchy_by_function_tags()
                return self._get_role_hierarchy_by_category()

            # ─── Build hierarchy from SIPOC inherits-from relationships ───

            # Get all inherits-from relationships
            cursor.execute('''
                SELECT source_role_id, source_role_name,
                       target_role_id, target_role_name
                FROM role_relationships
                WHERE relationship_type = 'inherits-from'
                ORDER BY target_role_name, source_role_name
            ''')
            rels = cursor.fetchall()

            # In SIPOC: source INHERITS FROM target
            # So target is the PARENT, source is the CHILD
            parent_of = {}   # child_name -> parent_name
            children_of = {} # parent_name -> [child_names]
            all_role_names = set()

            for row in rels:
                child_name = row[1]   # source = child (inherits from parent)
                parent_name = row[3]  # target = parent
                all_role_names.add(child_name)
                all_role_names.add(parent_name)
                parent_of[child_name] = parent_name
                if parent_name not in children_of:
                    children_of[parent_name] = []
                if child_name not in children_of[parent_name]:
                    children_of[parent_name].append(child_name)

            # Get role metadata for all roles in the hierarchy
            role_ids = set()
            for row in rels:
                role_ids.add(row[0])
                role_ids.add(row[2])

            role_info = {}
            if role_ids:
                placeholders = ','.join(['?'] * len(role_ids))
                cursor.execute(f'''
                    SELECT id, role_name, document_count, total_mentions,
                           is_deliverable, category
                    FROM roles WHERE id IN ({placeholders})
                ''', list(role_ids))
                for row in cursor.fetchall():
                    role_info[row[1]] = {
                        'document_count': row[2] or 0,
                        'total_mentions': row[3] or 0,
                        'is_deliverable': bool(row[4]),
                        'category': row[5] or ''
                    }

            # Also get role_dictionary metadata (disposition, baselined, org_group)
            try:
                cursor.execute('''
                    SELECT role_name, category, source, description, is_active
                    FROM role_dictionary
                    WHERE source = 'sipoc'
                ''')
                for row in cursor.fetchall():
                    rname = row[0]
                    if rname in role_info:
                        role_info[rname]['dict_category'] = row[1] or ''
                        role_info[rname]['description'] = row[3] or ''
            except Exception as e:
                logger.warning(f'Hierarchy enrichment from dictionary failed: {e}')

            # Roots = roles that appear as parents but never as children
            roots_set = all_role_names - set(parent_of.keys())
            # Sort roots alphabetically
            roots = sorted(roots_set)

            # Build nodes and edges
            nodes = []
            edges = []
            children_map = {}

            for rname in all_role_names:
                info = role_info.get(rname, {})
                nodes.append({
                    'name': rname,
                    'type': 'role',
                    'category': info.get('category', ''),
                    'document_count': info.get('document_count', 0),
                    'total_mentions': info.get('total_mentions', 0),
                    'is_deliverable': info.get('is_deliverable', False),
                    'is_root': rname in roots_set
                })
                children_map[rname] = children_of.get(rname, [])

            for row in rels:
                child_name = row[1]
                parent_name = row[3]
                edges.append({
                    'source': parent_name,
                    'target': child_name,
                    'type': 'inherits-from'
                })

            # Also get uses-tool relationships to show in the tree
            cursor.execute('''
                SELECT source_role_name, target_role_name
                FROM role_relationships
                WHERE relationship_type = 'uses-tool'
            ''')
            tool_rels = cursor.fetchall()
            tools_added = set()
            for row in tool_rels:
                role_name = row[0]
                tool_name = row[1]
                if tool_name not in tools_added:
                    nodes.append({
                        'name': tool_name,
                        'type': 'tool',
                        'category': 'Tools & Systems',
                        'is_root': False
                    })
                    tools_added.add(tool_name)
                edges.append({
                    'source': role_name,
                    'target': tool_name,
                    'type': 'uses-tool'
                })
                if role_name in children_map:
                    if tool_name not in children_map[role_name]:
                        children_map[role_name].append(tool_name)

            return {
                'nodes': nodes,
                'edges': edges,
                'roots': roots,
                'children_map': children_map,
                'stats': {
                    'total_nodes': len(nodes),
                    'total_edges': len(edges),
                    'total_roots': len(roots),
                    'total_roles': len(all_role_names),
                    'total_tools': len(tools_added),
                    'total_inherits': rel_count,
                    'source': 'sipoc'
                }
            }

    def _get_role_hierarchy_by_function_tags(self) -> Dict:
        """Build hierarchy from function tag groupings (fallback when no SIPOC relationships)."""
        with self.connection() as (conn, cursor):
            # Build function category tree
            cursor.execute('''
                SELECT code, name, parent_code, color, description
                FROM function_categories
                WHERE is_active = 1
                ORDER BY sort_order, name
            ''')
            categories = {}
            for row in cursor.fetchall():
                categories[row[0]] = {
                    'code': row[0],
                    'name': row[1],
                    'parent_code': row[2],
                    'color': row[3] or '#3b82f6',
                    'description': row[4]
                }

            # Get role-to-function-tag mappings
            cursor.execute('''
                SELECT rft.role_id, rft.function_code, r.role_name,
                       r.document_count, r.total_mentions, r.is_deliverable, r.category
                FROM role_function_tags rft
                JOIN roles r ON rft.role_id = r.id
                ORDER BY rft.function_code, r.document_count DESC
            ''')

            func_to_roles = {}
            role_info = {}
            for row in cursor.fetchall():
                fcode = row[1]
                rname = row[2]
                if fcode not in func_to_roles:
                    func_to_roles[fcode] = []
                if rname not in func_to_roles[fcode]:
                    func_to_roles[fcode].append(rname)
                role_info[rname] = {
                    'document_count': row[3],
                    'total_mentions': row[4],
                    'is_deliverable': bool(row[5]),
                    'category': row[6]
                }

            nodes = []
            edges = []
            children_map = {}
            roots = []

            for code, cat in categories.items():
                node_name = cat['name']
                nodes.append({
                    'name': node_name,
                    'type': 'function',
                    'code': code,
                    'color': cat['color'],
                    'is_root': not cat['parent_code'],
                    'description': cat.get('description', '')
                })
                children_map[node_name] = []
                if not cat['parent_code']:
                    roots.append(node_name)

            for code, cat in categories.items():
                if cat['parent_code'] and cat['parent_code'] in categories:
                    parent_name = categories[cat['parent_code']]['name']
                    child_name = cat['name']
                    edges.append({'source': parent_name, 'target': child_name, 'type': 'subcategory'})
                    if child_name not in children_map.get(parent_name, []):
                        children_map[parent_name].append(child_name)

            roles_added = set()
            for fcode, role_names in func_to_roles.items():
                if fcode not in categories:
                    continue
                cat_name = categories[fcode]['name']
                for rname in role_names:
                    if rname not in roles_added:
                        info = role_info.get(rname, {})
                        nodes.append({
                            'name': rname, 'type': 'role',
                            'category': info.get('category', ''),
                            'document_count': info.get('document_count', 0),
                            'total_mentions': info.get('total_mentions', 0),
                            'is_deliverable': info.get('is_deliverable', False)
                        })
                        roles_added.add(rname)
                    edges.append({'source': cat_name, 'target': rname, 'type': 'function-member'})
                    if rname not in children_map.get(cat_name, []):
                        children_map[cat_name].append(rname)

            return {
                'nodes': nodes, 'edges': edges, 'roots': roots,
                'children_map': children_map,
                'stats': {
                    'total_nodes': len(nodes), 'total_edges': len(edges),
                    'total_categories': len(roots), 'total_roles': len(roles_added),
                    'source': 'function_tags'
                }
            }

    def _get_role_hierarchy_by_category(self) -> Dict:
        """Fallback hierarchy grouped by role category when no function tags exist."""
        with self.connection() as (conn, cursor):
            cursor.execute('''
                SELECT r.id, r.role_name, r.normalized_name, r.category,
                       r.document_count, r.total_mentions, r.is_deliverable
                FROM roles r
                ORDER BY r.category, r.document_count DESC
            ''')
            nodes = []
            edges = []
            children_map = {}
            roots = []
            categories_seen = set()
            for row in cursor.fetchall():
                role_name = row[1]
                category = row[3] or 'Uncategorized'
                if category not in categories_seen:
                    categories_seen.add(category)
                    roots.append(category)
                    children_map[category] = []
                    nodes.append({
                        'name': category,
                        'type': 'category',
                        'is_root': True
                    })
                children_map[category].append(role_name)
                nodes.append({
                    'name': role_name,
                    'type': 'role',
                    'category': category,
                    'document_count': row[4],
                    'total_mentions': row[5],
                    'is_deliverable': bool(row[6])
                })
                edges.append({
                    'source': category,
                    'target': role_name,
                    'type': 'category-member'
                })
            return {
                'nodes': nodes,
                'edges': edges,
                'roots': roots,
                'children_map': children_map,
                'stats': {
                    'total_nodes': len(nodes),
                    'total_edges': len(edges),
                    'total_categories': len(roots),
                    'total_roles': len(nodes) - len(roots)
                }
            }

    def get_role_relationships(self, role_name: str = None, rel_type: str = None) -> list:
        """
        v4.7.3: Get role relationships from the role_relationships table
        (populated by SIPOC imports and manual additions).

        These are actual directional relationships like inherits-from,
        uses-tool, co-performs, supplies-to, receives-from — NOT inferred
        co-occurrence from function tags.

        Args:
            role_name: Optional filter — only relationships involving this role
            rel_type: Optional filter — only relationships of this type

        Returns:
            List of dicts with source_role_id, target_role_id, source_name,
            target_name, relationship_type, source_context, import_source
        """
        with self.connection() as (conn, cursor):
            # Check if role_relationships table exists and has data
            try:
                cursor.execute('SELECT COUNT(*) FROM role_relationships')
                count = cursor.fetchone()[0]
                if count == 0:
                    return []
            except Exception:
                return []

            # Build query with optional filters
            query = '''
                SELECT id, source_role_id, source_role_name,
                       target_role_id, target_role_name,
                       relationship_type, source_context, import_source,
                       created_at
                FROM role_relationships
                WHERE 1=1
            '''
            params = []

            if role_name:
                query += ' AND (source_role_name = ? OR target_role_name = ?)'
                params.extend([role_name, role_name])

            if rel_type:
                query += ' AND relationship_type = ?'
                params.append(rel_type)

            query += ' ORDER BY relationship_type, source_role_name'
            cursor.execute(query, params)

            relationships = []
            for row in cursor.fetchall():
                relationships.append({
                    'id': row[0],
                    'source_role_id': row[1],
                    'source_name': row[2],
                    'source_role_name': row[2],
                    'target_role_id': row[3],
                    'target_name': row[4],
                    'target_role_name': row[4],
                    'relationship_type': row[5],
                    'source_context': row[6] or '',
                    'import_source': row[7] or '',
                    'created_at': row[8] or '',
                    'weight': 1
                })
            return relationships

    def add_role_relationship(self, source: str, target: str, rel_type: str = 'inherits-from',
                               context: str = '', import_source: str = 'manual') -> Dict:
        """
        v4.7.3: Add a relationship between two roles.

        Args:
            source: Source role name
            target: Target role name
            rel_type: Relationship type (inherits-from, uses-tool, etc.)
            context: Context string
            import_source: Where this came from (manual, sipoc, etc.)

        Returns:
            Dict with success status
        """
        with self.connection() as (conn, cursor):
            # Look up role IDs
            cursor.execute('SELECT id FROM roles WHERE role_name = ?', (source,))
            src_row = cursor.fetchone()
            cursor.execute('SELECT id FROM roles WHERE role_name = ?', (target,))
            tgt_row = cursor.fetchone()

            src_id = src_row[0] if src_row else None
            tgt_id = tgt_row[0] if tgt_row else None

            # Check for duplicate
            cursor.execute('''
                SELECT id FROM role_relationships
                WHERE source_role_name = ? AND target_role_name = ? AND relationship_type = ?
            ''', (source, target, rel_type))
            if cursor.fetchone():
                return {'success': False, 'error': 'Relationship already exists'}

            cursor.execute('''
                INSERT INTO role_relationships
                (source_role_id, source_role_name, target_role_id, target_role_name,
                 relationship_type, source_context, import_source, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (src_id, source, tgt_id, target, rel_type, context, import_source))
            conn.commit()
            return {'success': True, 'id': cursor.lastrowid}

    def delete_role_relationship(self, source: str, target: str, rel_type: str = None) -> Dict:
        """
        v4.7.3: Delete a relationship between two roles.

        Args:
            source: Source role name
            target: Target role name
            rel_type: Optional relationship type filter

        Returns:
            Dict with success status and count deleted
        """
        with self.connection() as (conn, cursor):
            if rel_type:
                cursor.execute('''
                    DELETE FROM role_relationships
                    WHERE source_role_name = ? AND target_role_name = ? AND relationship_type = ?
                ''', (source, target, rel_type))
            else:
                cursor.execute('''
                    DELETE FROM role_relationships
                    WHERE source_role_name = ? AND target_role_name = ?
                ''', (source, target))
            deleted = cursor.rowcount
            conn.commit()
            return {'success': True, 'deleted': deleted}

    def import_sipoc_roles(self, parsed: Dict, created_by: str = 'sipoc_import') -> Dict:
        """
        v4.7.3: Import parsed SIPOC data into role_dictionary and role_relationships.

        Args:
            parsed: Dict from sipoc_parser with 'roles' and 'relationships'
            created_by: Import source identifier

        Returns:
            Dict with counts of roles/relationships added/updated/removed
        """
        with self.connection() as (conn, cursor):
            roles_added = 0
            roles_updated = 0
            relationships_created = 0
            tags_assigned = 0

            # Import roles into role_dictionary
            for role_data in parsed.get('roles', []):
                rname = role_data.get('role_name', '').strip()
                if not rname:
                    continue

                normalized = rname.lower().strip()
                category = role_data.get('category', 'Role')
                description = role_data.get('description', '')
                is_tool = role_data.get('is_tool', False)
                baselined = role_data.get('baselined', False)

                # Check if exists in role_dictionary
                cursor.execute('SELECT id FROM role_dictionary WHERE normalized_name = ?', (normalized,))
                existing = cursor.fetchone()

                # v4.7.3: Serialize tracings (Nimbus hyperlinks) as JSON
                tracings = role_data.get('tracings', [])
                tracings_json = json.dumps(tracings) if tracings else '[]'
                role_type = role_data.get('role_type', '')
                role_disposition = role_data.get('role_disposition', '')
                org_group = role_data.get('org_group', '')
                hierarchy_level = role_data.get('hierarchy_level', '')
                baselined_int = 1 if role_data.get('baselined', False) else 0

                if existing:
                    cursor.execute('''
                        UPDATE role_dictionary SET description = ?, category = ?,
                               tracings = ?, role_type = ?, role_disposition = ?,
                               org_group = ?, hierarchy_level = ?, baselined = ?,
                               updated_at = CURRENT_TIMESTAMP, updated_by = ?
                        WHERE id = ?
                    ''', (description, category, tracings_json, role_type,
                          role_disposition, org_group, hierarchy_level,
                          baselined_int, created_by, existing[0]))
                    roles_updated += 1
                else:
                    cursor.execute('''
                        INSERT INTO role_dictionary
                        (role_name, normalized_name, category, source, description,
                         tracings, role_type, role_disposition, org_group,
                         hierarchy_level, baselined, is_active, created_at, created_by)
                        VALUES (?, ?, ?, 'sipoc', ?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, ?)
                    ''', (rname, normalized, category, description, tracings_json,
                          role_type, role_disposition, org_group, hierarchy_level,
                          baselined_int, created_by))
                    roles_added += 1

                # Ensure role exists in main roles table too
                cursor.execute('SELECT id FROM roles WHERE normalized_name = ?', (normalized,))
                role_row = cursor.fetchone()
                if not role_row:
                    cursor.execute('''
                        INSERT INTO roles (role_name, normalized_name, first_seen,
                                          document_count, total_mentions, category, role_source)
                        VALUES (?, ?, CURRENT_TIMESTAMP, 0, 0, ?, 'sipoc')
                    ''', (rname, normalized, category))

                # Handle function tags
                for ft in role_data.get('function_tags', []):
                    parent_code = ft.get('parent_code', '')
                    child_code = ft.get('child_code', '')
                    code_to_assign = child_code or parent_code
                    if code_to_assign:
                        cursor.execute('SELECT id FROM roles WHERE normalized_name = ?', (normalized,))
                        rid_row = cursor.fetchone()
                        if rid_row:
                            try:
                                cursor.execute('''
                                    INSERT OR IGNORE INTO role_function_tags
                                    (role_id, role_name, function_code, assigned_at, assigned_by)
                                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)
                                ''', (rid_row[0], rname, code_to_assign, created_by))
                                tags_assigned += cursor.rowcount
                            except Exception as e:
                                logger.warning(f'SIPOC: Failed to assign tag {code_to_assign} to {rname}: {e}')

            # Import relationships
            for rel in parsed.get('relationships', []):
                src_name = rel.get('source', '').strip()
                tgt_name = rel.get('target', '').strip()
                rtype = rel.get('type', 'inherits-from')
                context = rel.get('context', '')

                if not src_name or not tgt_name:
                    continue

                # Look up role IDs
                cursor.execute('SELECT id FROM roles WHERE role_name = ?', (src_name,))
                src_row = cursor.fetchone()
                cursor.execute('SELECT id FROM roles WHERE role_name = ?', (tgt_name,))
                tgt_row = cursor.fetchone()

                src_id = src_row[0] if src_row else None
                tgt_id = tgt_row[0] if tgt_row else None

                # Avoid duplicates
                cursor.execute('''
                    SELECT id FROM role_relationships
                    WHERE source_role_name = ? AND target_role_name = ? AND relationship_type = ?
                ''', (src_name, tgt_name, rtype))
                if not cursor.fetchone():
                    cursor.execute('''
                        INSERT INTO role_relationships
                        (source_role_id, source_role_name, target_role_id, target_role_name,
                         relationship_type, source_context, import_source, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, 'sipoc', CURRENT_TIMESTAMP)
                    ''', (src_id, src_name, tgt_id, tgt_name, rtype, context))
                    relationships_created += 1

            conn.commit()
            return {
                'success': True,
                'roles_added': roles_added,
                'roles_updated': roles_updated,
                'roles_removed': 0,
                'relationships_created': relationships_created,
                'relationships_removed': 0,
                'tags_assigned': tags_assigned,
                'tags_removed': 0
            }

    def clear_sipoc_import(self) -> Dict:
        """
        v4.7.3: Remove all SIPOC-imported data.

        Removes roles with source='sipoc' from role_dictionary,
        their relationships from role_relationships, and their function tags.

        Returns:
            Dict with counts of removed items
        """
        with self.connection() as (conn, cursor):
            # Remove SIPOC relationships
            cursor.execute("DELETE FROM role_relationships WHERE import_source = 'sipoc'")
            rels_removed = cursor.rowcount

            # Remove SIPOC function tags (assigned by sipoc_import)
            cursor.execute("DELETE FROM role_function_tags WHERE assigned_by = 'sipoc_import'")
            tags_removed = cursor.rowcount

            # Remove SIPOC dictionary entries
            cursor.execute("DELETE FROM role_dictionary WHERE source = 'sipoc'")
            roles_removed = cursor.rowcount

            conn.commit()
            return {
                'success': True,
                'roles_removed': roles_removed,
                'relationships_removed': rels_removed,
                'tags_removed': tags_removed
            }

    def get_role_graph_data(self, max_nodes: int = 100, min_weight: int = 1) -> Dict:
        """
        Get graph data for D3.js visualization of role-document relationships.

        Returns a compact graph model with:
        - nodes: roles and documents with stable IDs
        - links: role-document connections with weights
        - aggregates: counts and top terms

        Args:
            max_nodes: Maximum number of nodes to return (for performance)
            min_weight: Minimum edge weight to include

        Returns:
            Dict with nodes, links, role_counts, doc_counts
        """
        with self.connection() as (conn, cursor):
            # Get documents with their stats
            cursor.execute('''
                SELECT d.id, d.filename, COUNT(dr.id) as role_count,
                       COALESCE(SUM(dr.mention_count), 0) as total_mentions
                FROM documents d
                LEFT JOIN document_roles dr ON d.id = dr.document_id
                GROUP BY d.id
                ORDER BY role_count DESC
                LIMIT ?
            ''', (max_nodes // 2,))

            documents = []
            doc_id_map = {}
            for row in cursor.fetchall():
                stable_id = f"doc_{row[0]}"
                doc_id_map[row[0]] = stable_id
                documents.append({
                    'id': stable_id,
                    'db_id': row[0],
                    'label': row[1],
                    'type': 'document',
                    'role_count': row[2],
                    'total_mentions': row[3]
                })

            # Get roles with their stats (excluding deliverables)
            cursor.execute('''
                SELECT r.id, r.role_name, r.normalized_name, r.category,
                       r.document_count, r.total_mentions
                FROM roles r
                WHERE r.is_deliverable = 0
                ORDER BY r.document_count DESC, r.total_mentions DESC
                LIMIT ?
            ''', (max_nodes // 2,))

            roles = []
            role_id_map = {}
            for row in cursor.fetchall():
                stable_id = f"role_{row[0]}"
                role_id_map[row[0]] = stable_id
                roles.append({
                    'id': stable_id,
                    'db_id': row[0],
                    'label': row[2] or row[1],  # Prefer normalized name
                    'original_name': row[1],
                    'type': 'role',
                    'category': row[3] or 'Unknown',
                    'document_count': row[4],
                    'total_mentions': row[5]
                })

            # Get edges (document-role relationships)
            doc_ids = list(doc_id_map.keys())
            role_ids = list(role_id_map.keys())

            if doc_ids and role_ids:
                placeholders_docs = ','.join('?' * len(doc_ids))
                placeholders_roles = ','.join('?' * len(role_ids))

                cursor.execute(f'''
                    SELECT document_id, role_id, mention_count, responsibilities_json
                    FROM document_roles
                    WHERE document_id IN ({placeholders_docs})
                      AND role_id IN ({placeholders_roles})
                      AND mention_count >= ?
                    ORDER BY mention_count DESC
                ''', doc_ids + role_ids + [min_weight])

                links = []
                for row in cursor.fetchall():
                    doc_stable_id = doc_id_map.get(row[0])
                    role_stable_id = role_id_map.get(row[1])
                    if doc_stable_id and role_stable_id:
                        # Parse responsibilities for top terms
                        top_terms = []
                        if row[3]:
                            try:
                                resp_data = json.loads(row[3])
                                if isinstance(resp_data, list):
                                    for r in resp_data[:3]:
                                        if isinstance(r, dict) and 'verb' in r:
                                            top_terms.append(r['verb'])
                                        elif isinstance(r, str):
                                            words = r.split()[:2]
                                            top_terms.append(' '.join(words))
                            except (json.JSONDecodeError, TypeError):
                                pass

                        links.append({
                            'source': role_stable_id,
                            'target': doc_stable_id,
                            'weight': row[2],
                            'top_terms': top_terms[:3],
                            'link_type': 'role-document'
                        })
            else:
                links = []

            # Add role-to-role links based on co-occurrence in documents
            # This shows which roles work together
            if len(role_ids) >= 2:
                # Find roles that appear together in the same documents
                cursor.execute(f'''
                    SELECT dr1.role_id, dr2.role_id, COUNT(DISTINCT dr1.document_id) as shared_docs
                    FROM document_roles dr1
                    JOIN document_roles dr2 ON dr1.document_id = dr2.document_id
                        AND dr1.role_id < dr2.role_id
                    WHERE dr1.role_id IN ({placeholders_roles})
                      AND dr2.role_id IN ({placeholders_roles})
                    GROUP BY dr1.role_id, dr2.role_id
                    HAVING shared_docs >= ?
                    ORDER BY shared_docs DESC
                    LIMIT 50
                ''', role_ids + role_ids + [min_weight])

                for row in cursor.fetchall():
                    role1_stable_id = role_id_map.get(row[0])
                    role2_stable_id = role_id_map.get(row[1])
                    if role1_stable_id and role2_stable_id:
                        links.append({
                            'source': role1_stable_id,
                            'target': role2_stable_id,
                            'weight': row[2],
                            'link_type': 'role-role',
                            'shared_documents': row[2]
                        })

        # Combine nodes
        nodes = roles + documents
        
        # Create aggregates
        role_counts = {
            r['id']: {
                'mentions': r['total_mentions'],
                'docs': r['document_count'],
                'category': r['category']
            } for r in roles
        }
        
        doc_counts = {
            d['id']: {
                'roles_count': d['role_count'],
                'mentions_total': d['total_mentions']
            } for d in documents
        }
        
        # Count link types
        role_doc_links = sum(1 for l in links if l.get('link_type') == 'role-document')
        role_role_links = sum(1 for l in links if l.get('link_type') == 'role-role')
        
        return {
            'nodes': nodes,
            'links': links,
            'role_counts': role_counts,
            'doc_counts': doc_counts,
            'meta': {
                'total_roles': len(roles),
                'total_documents': len(documents),
                'total_links': len(links),
                'role_doc_links': role_doc_links,
                'role_role_links': role_role_links,
                'max_nodes': max_nodes,
                'min_weight': min_weight
            }
        }
    
    # ================================================================
    # ROLE DICTIONARY MANAGEMENT
    # ================================================================
    
    def get_role_dictionary(self, include_inactive: bool = False) -> List[Dict]:
        """Get all roles from the role dictionary."""
        with self.connection() as (conn, cursor):
            query = '''
                SELECT id, role_name, normalized_name, aliases, category, source,
                       source_document, description, is_active, is_deliverable,
                       created_at, created_by, updated_at, updated_by, notes,
                       tracings, role_type, role_disposition, org_group,
                       hierarchy_level, baselined
                FROM role_dictionary
            '''
            if not include_inactive:
                query += ' WHERE is_active = 1'
            query += ' ORDER BY role_name'

            cursor.execute(query)

            roles = []
            for row in cursor.fetchall():
                aliases = []
                if row[3]:
                    try:
                        aliases = json.loads(row[3])
                    except Exception:
                        aliases = [a.strip() for a in row[3].split(',') if a.strip()]

                tracings = []
                if row[15]:
                    try:
                        tracings = json.loads(row[15])
                    except Exception:
                        tracings = []

                roles.append({
                    'id': row[0],
                    'role_name': row[1],
                    'normalized_name': row[2],
                    'aliases': aliases,
                    'category': row[4],
                    'source': row[5],
                    'source_document': row[6],
                    'description': row[7],
                    'is_active': bool(row[8]),
                    'is_deliverable': bool(row[9]),
                    'created_at': row[10],
                    'created_by': row[11],
                    'updated_at': row[12],
                    'updated_by': row[13],
                    'notes': row[14],
                    'tracings': tracings,
                    'role_type': row[16] or '',
                    'role_disposition': row[17] or '',
                    'org_group': row[18] or '',
                    'hierarchy_level': row[19] or '',
                    'baselined': bool(row[20]) if row[20] else False,
                })

        return roles
    
    def add_role_to_dictionary(self, role_name: str, source: str, **kwargs) -> Dict:
        """
        Add a new role to the dictionary.

        Args:
            role_name: The role name to add
            source: Where it came from ('builtin', 'upload', 'adjudication', 'manual')
            **kwargs: Optional fields like category, aliases, description, etc.

        Returns:
            Dict with success status and role data or error
        """
        normalized = role_name.lower().strip()
        aliases = kwargs.get('aliases', [])
        if isinstance(aliases, list):
            aliases_json = json.dumps(aliases)
        else:
            aliases_json = aliases

        try:
            with self.connection() as (conn, cursor):
                cursor.execute('''
                    INSERT INTO role_dictionary
                    (role_name, normalized_name, aliases, category, source, source_document,
                     description, is_active, is_deliverable, created_by, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    role_name,
                    normalized,
                    aliases_json,
                    kwargs.get('category', 'Custom'),
                    source,
                    kwargs.get('source_document'),
                    kwargs.get('description'),
                    1 if kwargs.get('is_active', True) else 0,
                    1 if kwargs.get('is_deliverable', False) else 0,
                    kwargs.get('created_by', 'user'),
                    kwargs.get('notes')
                ))
                role_id = cursor.lastrowid

            return {
                'success': True,
                'id': role_id,
                'role_name': role_name,
                'normalized_name': normalized
            }
        except sqlite3.IntegrityError:
            return {
                'success': False,
                'error': f'Role "{role_name}" already exists in dictionary'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_role_in_dictionary(self, role_id: int, updated_by: str = 'user', **kwargs) -> Dict:
        """Update an existing role in the dictionary."""
        # Build update query dynamically based on provided fields
        allowed_fields = ['role_name', 'aliases', 'category', 'description',
                         'is_active', 'is_deliverable', 'notes']

        updates = []
        values = []

        for field in allowed_fields:
            if field in kwargs:
                value = kwargs[field]
                if field == 'aliases' and isinstance(value, list):
                    value = json.dumps(value)
                elif field in ('is_active', 'is_deliverable'):
                    value = 1 if value else 0
                updates.append(f'{field} = ?')
                values.append(value)

        if 'role_name' in kwargs:
            updates.append('normalized_name = ?')
            values.append(kwargs['role_name'].lower().strip())

        updates.append('updated_at = CURRENT_TIMESTAMP')
        updates.append('updated_by = ?')
        values.append(updated_by)

        values.append(role_id)

        try:
            with self.connection() as (conn, cursor):
                cursor.execute(f'''
                    UPDATE role_dictionary
                    SET {', '.join(updates)}
                    WHERE id = ?
                ''', values)

                success = cursor.rowcount > 0

            return {
                'success': success,
                'updated': success
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_role_from_dictionary(self, role_id: int, soft_delete: bool = True) -> Dict:
        """Delete or deactivate a role from the dictionary."""
        try:
            with self.connection() as (conn, cursor):
                if soft_delete:
                    cursor.execute('''
                        UPDATE role_dictionary
                        SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (role_id,))
                else:
                    cursor.execute('DELETE FROM role_dictionary WHERE id = ?', (role_id,))

                success = cursor.rowcount > 0

            return {'success': success, 'deleted': success}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def import_roles_to_dictionary(self, roles: List[Dict], source: str, 
                                   source_document: str = None,
                                   created_by: str = 'import') -> Dict:
        """
        Bulk import roles to the dictionary.
        
        Args:
            roles: List of role dicts with at least 'role_name'
            source: Source identifier ('upload', 'adjudication', 'builtin')
            source_document: Document name if from upload
            created_by: User identifier
        
        Returns:
            Dict with counts of added, skipped, errors
        """
        results = {
            'added': 0,
            'skipped': 0,
            'errors': [],
            'total': len(roles)
        }
        
        for role in roles:
            role_name = role.get('role_name') or role.get('name')
            if not role_name:
                results['errors'].append('Missing role_name')
                continue
            
            result = self.add_role_to_dictionary(
                role_name=role_name,
                source=source,
                source_document=source_document,
                category=role.get('category', 'Imported'),
                aliases=role.get('aliases', []),
                description=role.get('description'),
                is_deliverable=role.get('is_deliverable', False),
                created_by=created_by,
                notes=role.get('notes')
            )
            
            if result['success']:
                results['added'] += 1
            else:
                if 'already exists' in result.get('error', ''):
                    results['skipped'] += 1
                else:
                    results['errors'].append(result.get('error'))
        
        return results
    
    def get_active_role_names(self) -> List[str]:
        """Get list of active role names for use in extraction."""
        with self.connection() as (conn, cursor):
            cursor.execute('''
                SELECT role_name, aliases FROM role_dictionary
                WHERE is_active = 1 AND is_deliverable = 0
            ''')

            role_names = []
            for row in cursor.fetchall():
                role_names.append(row[0])
                # Also add aliases
                if row[1]:
                    try:
                        aliases = json.loads(row[1])
                        role_names.extend(aliases)
                    except Exception as e:
                        logger.debug(f'Could not parse aliases JSON for role {row[0]}: {e}')

        return role_names
    
    def seed_builtin_roles(self) -> Dict:
        """
        Seed the dictionary with built-in known roles.
        v2.9.1 E1: Expanded from 27 to 175 aerospace/defense roles.
        """
        builtin_roles = [
            # ================================================================
            # PROGRAM MANAGEMENT (15 roles)
            # ================================================================
            {'role_name': 'Program Manager', 'category': 'Program Management',
             'aliases': ['PM', 'Program Mgr', 'Programme Manager']},
            {'role_name': 'Deputy Program Manager', 'category': 'Program Management',
             'aliases': ['Deputy PM', 'DPM', 'Asst Program Manager']},
            {'role_name': 'Project Manager', 'category': 'Program Management',
             'aliases': ['Project Mgr', 'Project Lead']},
            {'role_name': 'IPT Lead', 'category': 'Program Management',
             'aliases': ['IPT Leader', 'Integrated Product Team Lead']},
            {'role_name': 'CAM', 'category': 'Program Management',
             'aliases': ['Control Account Manager', 'CAMs']},
            {'role_name': 'EVMS Analyst', 'category': 'Program Management',
             'aliases': ['Earned Value Analyst', 'EVM Analyst']},
            {'role_name': 'Program Control Analyst', 'category': 'Program Management',
             'aliases': ['Program Controls', 'PC Analyst']},
            {'role_name': 'Scheduler', 'category': 'Program Management',
             'aliases': ['Program Scheduler', 'Master Scheduler', 'IMS Manager']},
            {'role_name': 'Risk Manager', 'category': 'Program Management',
             'aliases': ['Risk Analyst', 'Program Risk Manager']},
            {'role_name': 'Technical Program Manager', 'category': 'Program Management',
             'aliases': ['TPM', 'Tech PM']},
            {'role_name': 'Business Manager', 'category': 'Program Management',
             'aliases': ['Business Operations Manager', 'Program Business Manager']},
            {'role_name': 'Cost Analyst', 'category': 'Program Management',
             'aliases': ['Cost Estimator', 'Pricing Analyst']},
            {'role_name': 'Resource Manager', 'category': 'Program Management',
             'aliases': ['Resource Coordinator', 'Staff Manager']},
            {'role_name': 'Program Integrator', 'category': 'Program Management',
             'aliases': ['Integration Lead', 'Program Integration Lead']},
            {'role_name': 'Transition Manager', 'category': 'Program Management',
             'aliases': ['Transition Lead', 'Program Transition Manager']},
            
            # ================================================================
            # SYSTEMS ENGINEERING (20 roles)
            # ================================================================
            {'role_name': 'Chief Systems Engineer', 'category': 'Systems Engineering',
             'aliases': ['CSE', 'Chief SE', 'Lead Systems Engineer']},
            {'role_name': 'Systems Engineer', 'category': 'Systems Engineering',
             'aliases': ['SE', 'System Engineer', 'Systems Engineers']},
            {'role_name': 'Lead Systems Engineer', 'category': 'Systems Engineering',
             'aliases': ['LSE', 'Lead SE', 'Senior SE']},
            {'role_name': 'Requirements Engineer', 'category': 'Systems Engineering',
             'aliases': ['Requirements Analyst', 'Req Engineer', 'Requirements Manager']},
            {'role_name': 'Interface Engineer', 'category': 'Systems Engineering',
             'aliases': ['Interface Control Engineer', 'ICE', 'I&I Engineer']},
            {'role_name': 'MBSE Lead', 'category': 'Systems Engineering',
             'aliases': ['Model-Based SE Lead', 'MBSE Engineer', 'Digital Engineer']},
            {'role_name': 'V&V Engineer', 'category': 'Systems Engineering',
             'aliases': ['Verification Engineer', 'Validation Engineer', 'V&V Lead']},
            {'role_name': 'Systems Architect', 'category': 'Systems Engineering',
             'aliases': ['System Architect', 'Architecture Lead', 'Technical Architect']},
            {'role_name': 'Design Engineer', 'category': 'Systems Engineering',
             'aliases': ['Designer', 'Design Engineers', 'Design Lead']},
            {'role_name': 'Integration Engineer', 'category': 'Systems Engineering',
             'aliases': ['Integrator', 'System Integrator', 'I&T Engineer']},
            {'role_name': 'Technical Lead', 'category': 'Systems Engineering',
             'aliases': ['Tech Lead', 'Technical Leads', 'Engineering Lead']},
            {'role_name': 'Chief Engineer', 'category': 'Systems Engineering',
             'aliases': ['CE', 'Chief Engineers', 'Engineering Director']},
            {'role_name': 'Systems Engineering Manager', 'category': 'Systems Engineering',
             'aliases': ['SE Manager', 'SEM', 'Systems Engineering Lead']},
            {'role_name': 'Trade Study Lead', 'category': 'Systems Engineering',
             'aliases': ['Trade Study Engineer', 'Analysis Lead']},
            {'role_name': 'Modeling & Simulation Engineer', 'category': 'Systems Engineering',
             'aliases': ['M&S Engineer', 'Simulation Engineer', 'Modeling Engineer']},
            {'role_name': 'Performance Engineer', 'category': 'Systems Engineering',
             'aliases': ['Performance Analyst', 'System Performance Engineer']},
            {'role_name': 'Specialty Engineering Lead', 'category': 'Systems Engineering',
             'aliases': ['Specialty Lead', 'Specialty Disciplines Lead']},
            {'role_name': 'Technical Data Lead', 'category': 'Systems Engineering',
             'aliases': ['TDP Lead', 'Technical Data Package Lead']},
            {'role_name': 'SETR Lead', 'category': 'Systems Engineering',
             'aliases': ['SE Technical Review Lead', 'Review Lead']},
            {'role_name': 'Deputy Chief Engineer', 'category': 'Systems Engineering',
             'aliases': ['DCE', 'Asst Chief Engineer']},
            
            # ================================================================
            # HARDWARE ENGINEERING (15 roles)
            # ================================================================
            {'role_name': 'Electrical Engineer', 'category': 'Hardware Engineering',
             'aliases': ['EE', 'Electrical Design Engineer', 'Electronics Engineer']},
            {'role_name': 'Mechanical Engineer', 'category': 'Hardware Engineering',
             'aliases': ['ME', 'Mechanical Design Engineer', 'Mech Engineer']},
            {'role_name': 'Structural Engineer', 'category': 'Hardware Engineering',
             'aliases': ['Structures Engineer', 'Stress Engineer', 'Structural Analyst']},
            {'role_name': 'Thermal Engineer', 'category': 'Hardware Engineering',
             'aliases': ['Thermal Analyst', 'Thermal Design Engineer']},
            {'role_name': 'RF Engineer', 'category': 'Hardware Engineering',
             'aliases': ['Radio Frequency Engineer', 'RF Design Engineer', 'Microwave Engineer']},
            {'role_name': 'Antenna Engineer', 'category': 'Hardware Engineering',
             'aliases': ['Antenna Design Engineer', 'Aperture Engineer']},
            {'role_name': 'Power Systems Engineer', 'category': 'Hardware Engineering',
             'aliases': ['Power Engineer', 'EPS Engineer', 'Electrical Power Engineer']},
            {'role_name': 'Avionics Engineer', 'category': 'Hardware Engineering',
             'aliases': ['Avionics Design Engineer', 'Avionics Systems Engineer']},
            {'role_name': 'Propulsion Engineer', 'category': 'Hardware Engineering',
             'aliases': ['Propulsion Systems Engineer', 'Rocket Engineer']},
            {'role_name': 'GNC Engineer', 'category': 'Hardware Engineering',
             'aliases': ['Guidance Engineer', 'Navigation Engineer', 'Control Systems Engineer']},
            {'role_name': 'Optics Engineer', 'category': 'Hardware Engineering',
             'aliases': ['Optical Engineer', 'Electro-Optical Engineer', 'EO Engineer']},
            {'role_name': 'Hardware Lead', 'category': 'Hardware Engineering',
             'aliases': ['HW Lead', 'Hardware Engineering Lead']},
            {'role_name': 'CAD Designer', 'category': 'Hardware Engineering',
             'aliases': ['CAD Engineer', 'Design Drafter', '3D Modeler']},
            {'role_name': 'Packaging Engineer', 'category': 'Hardware Engineering',
             'aliases': ['Mechanical Packaging Engineer', 'Electronic Packaging Engineer']},
            {'role_name': 'Materials Engineer', 'category': 'Hardware Engineering',
             'aliases': ['Materials Scientist', 'M&P Engineer', 'Materials & Processes']},
            
            # ================================================================
            # SOFTWARE ENGINEERING (12 roles)
            # ================================================================
            {'role_name': 'Software Lead', 'category': 'Software Engineering',
             'aliases': ['SW Lead', 'Software Engineering Lead', 'Software Manager']},
            {'role_name': 'Software Engineer', 'category': 'Software Engineering',
             'aliases': ['SW Engineer', 'Software Developer', 'Programmer']},
            {'role_name': 'DevSecOps Engineer', 'category': 'Software Engineering',
             'aliases': ['DevOps Engineer', 'CI/CD Engineer', 'Pipeline Engineer']},
            {'role_name': 'Flight Software Engineer', 'category': 'Software Engineering',
             'aliases': ['FSW Engineer', 'Flight SW Engineer', 'Embedded Flight SW']},
            {'role_name': 'Embedded Software Engineer', 'category': 'Software Engineering',
             'aliases': ['Embedded SW Engineer', 'Firmware Engineer']},
            {'role_name': 'Software Architect', 'category': 'Software Engineering',
             'aliases': ['SW Architect', 'Application Architect']},
            {'role_name': 'Software Test Engineer', 'category': 'Software Engineering',
             'aliases': ['SW Test Engineer', 'Software QA', 'SW Tester']},
            {'role_name': 'Software Safety Engineer', 'category': 'Software Engineering',
             'aliases': ['SW Safety Engineer', 'Software Assurance']},
            {'role_name': 'Algorithm Engineer', 'category': 'Software Engineering',
             'aliases': ['Algorithm Developer', 'DSP Engineer']},
            {'role_name': 'Data Engineer', 'category': 'Software Engineering',
             'aliases': ['Data Architect', 'Database Engineer']},
            {'role_name': 'AI/ML Engineer', 'category': 'Software Engineering',
             'aliases': ['Machine Learning Engineer', 'AI Engineer']},
            {'role_name': 'Ground Software Engineer', 'category': 'Software Engineering',
             'aliases': ['GSW Engineer', 'Ground System Software Engineer']},
            
            # ================================================================
            # TEST & EVALUATION (15 roles)
            # ================================================================
            {'role_name': 'Test Engineer', 'category': 'Test & Evaluation',
             'aliases': ['Test Engineers', 'Testing Engineer', 'T&E Engineer']},
            {'role_name': 'T&E Lead', 'category': 'Test & Evaluation',
             'aliases': ['Test Lead', 'Test & Evaluation Lead', 'Test Manager']},
            {'role_name': 'Integration & Test Engineer', 'category': 'Test & Evaluation',
             'aliases': ['I&T Engineer', 'Integration Engineer', 'System Integrator']},
            {'role_name': 'Environmental Test Engineer', 'category': 'Test & Evaluation',
             'aliases': ['Environmental Engineer', 'Env Test Engineer', 'Qual Test Engineer']},
            {'role_name': 'DT&E Lead', 'category': 'Test & Evaluation',
             'aliases': ['Developmental Test Lead', 'DT Lead', 'Development Test Engineer']},
            {'role_name': 'OT&E Lead', 'category': 'Test & Evaluation',
             'aliases': ['Operational Test Lead', 'OT Lead', 'Operational Test Engineer']},
            {'role_name': 'Flight Test Engineer', 'category': 'Test & Evaluation',
             'aliases': ['FTE', 'Flight Test Engineers', 'Flight Test Lead']},
            {'role_name': 'Test Conductor', 'category': 'Test & Evaluation',
             'aliases': ['Test Director', 'Test Operations Lead']},
            {'role_name': 'Test Readiness Review Lead', 'category': 'Test & Evaluation',
             'aliases': ['TRR Lead', 'Test Readiness Lead']},
            {'role_name': 'Verification Lead', 'category': 'Test & Evaluation',
             'aliases': ['Verification Engineer', 'Verification Manager']},
            {'role_name': 'Qualification Engineer', 'category': 'Test & Evaluation',
             'aliases': ['Qual Engineer', 'Qualification Test Engineer']},
            {'role_name': 'Acceptance Test Engineer', 'category': 'Test & Evaluation',
             'aliases': ['ATP Engineer', 'Acceptance Engineer']},
            {'role_name': 'Range Safety Officer', 'category': 'Test & Evaluation',
             'aliases': ['RSO', 'Range Safety']},
            {'role_name': 'Test Facility Manager', 'category': 'Test & Evaluation',
             'aliases': ['Lab Manager', 'Test Lab Manager']},
            {'role_name': 'Instrumentation Engineer', 'category': 'Test & Evaluation',
             'aliases': ['Instrumentation Specialist', 'Test Instrumentation']},
            
            # ================================================================
            # QUALITY & MISSION ASSURANCE (12 roles)
            # ================================================================
            {'role_name': 'Quality Engineer', 'category': 'Quality & Mission Assurance',
             'aliases': ['QE', 'Quality Assurance Engineer', 'QA Engineer']},
            {'role_name': 'QA Manager', 'category': 'Quality & Mission Assurance',
             'aliases': ['Quality Manager', 'Quality Assurance Manager']},
            {'role_name': 'Mission Assurance Engineer', 'category': 'Quality & Mission Assurance',
             'aliases': ['MA Engineer', 'Mission Assurance', 'MA']},
            {'role_name': 'Supplier Quality Engineer', 'category': 'Quality & Mission Assurance',
             'aliases': ['SQE', 'Supplier Quality', 'Vendor Quality']},
            {'role_name': 'MRB Chair', 'category': 'Quality & Mission Assurance',
             'aliases': ['Material Review Board Chair', 'MRB Lead']},
            {'role_name': 'Quality Assurance', 'category': 'Quality & Mission Assurance',
             'aliases': ['QA', 'Quality Assurance Representative']},
            {'role_name': 'Quality Inspector', 'category': 'Quality & Mission Assurance',
             'aliases': ['QC Inspector', 'Quality Control Inspector']},
            {'role_name': 'Process Auditor', 'category': 'Quality & Mission Assurance',
             'aliases': ['Quality Auditor', 'AS9100 Auditor']},
            {'role_name': 'Nonconformance Engineer', 'category': 'Quality & Mission Assurance',
             'aliases': ['NCR Engineer', 'Discrepancy Engineer']},
            {'role_name': 'Root Cause Analyst', 'category': 'Quality & Mission Assurance',
             'aliases': ['Failure Analyst', 'RCCA Lead']},
            {'role_name': 'Six Sigma Black Belt', 'category': 'Quality & Mission Assurance',
             'aliases': ['Black Belt', 'Lean Six Sigma']},
            {'role_name': 'Mission Assurance Manager', 'category': 'Quality & Mission Assurance',
             'aliases': ['MA Manager', 'Mission Assurance Lead']},
            
            # ================================================================
            # MANUFACTURING & PRODUCTION (10 roles)
            # ================================================================
            {'role_name': 'Manufacturing Engineer', 'category': 'Manufacturing',
             'aliases': ['Mfg Engineer', 'Production Engineer', 'Manufacturing Engineers']},
            {'role_name': 'Production Manager', 'category': 'Manufacturing',
             'aliases': ['Production Lead', 'Manufacturing Manager', 'Factory Manager']},
            {'role_name': 'Process Engineer', 'category': 'Manufacturing',
             'aliases': ['Process Development Engineer', 'Manufacturing Process Engineer']},
            {'role_name': 'Tooling Engineer', 'category': 'Manufacturing',
             'aliases': ['Tool Engineer', 'Tool Designer', 'Fixtures Engineer']},
            {'role_name': 'Assembly Technician', 'category': 'Manufacturing',
             'aliases': ['Assembler', 'Production Technician', 'Build Technician']},
            {'role_name': 'Test Technician', 'category': 'Manufacturing',
             'aliases': ['Lab Technician', 'Test Tech', 'QA Technician']},
            {'role_name': 'Production Planner', 'category': 'Manufacturing',
             'aliases': ['Manufacturing Planner', 'Production Scheduler']},
            {'role_name': 'Industrial Engineer', 'category': 'Manufacturing',
             'aliases': ['IE', 'Industrial Engineers', 'Methods Engineer']},
            {'role_name': 'Lean Manufacturing Engineer', 'category': 'Manufacturing',
             'aliases': ['Lean Engineer', 'Continuous Improvement Engineer']},
            {'role_name': 'NPI Engineer', 'category': 'Manufacturing',
             'aliases': ['New Product Introduction', 'Transition Engineer']},
            
            # ================================================================
            # LOGISTICS & SUSTAINMENT (10 roles)
            # ================================================================
            {'role_name': 'Logistics Engineer', 'category': 'Logistics & Sustainment',
             'aliases': ['Logistics Engineers', 'Log Engineer', 'Logistics Analyst']},
            {'role_name': 'ILS Manager', 'category': 'Logistics & Sustainment',
             'aliases': ['Integrated Logistics Support Manager', 'ILS Lead']},
            {'role_name': 'Reliability Engineer', 'category': 'Logistics & Sustainment',
             'aliases': ['Reliability Engineers', 'R&M Engineer', 'RAM Engineer']},
            {'role_name': 'Maintainability Engineer', 'category': 'Logistics & Sustainment',
             'aliases': ['Maintainability Analyst', 'M&R Engineer']},
            {'role_name': 'Supportability Engineer', 'category': 'Logistics & Sustainment',
             'aliases': ['Support Engineer', 'Sustainment Engineer']},
            {'role_name': 'Supply Chain Manager', 'category': 'Logistics & Sustainment',
             'aliases': ['SCM', 'Supply Chain Lead', 'Procurement Manager']},
            {'role_name': 'Spares Analyst', 'category': 'Logistics & Sustainment',
             'aliases': ['Provisioning Analyst', 'Parts Analyst']},
            {'role_name': 'Technical Writer', 'category': 'Logistics & Sustainment',
             'aliases': ['Tech Writer', 'Documentation Specialist', 'Technical Author']},
            {'role_name': 'Training Developer', 'category': 'Logistics & Sustainment',
             'aliases': ['Training Specialist', 'ISD', 'Instructional Designer']},
            {'role_name': 'Field Service Engineer', 'category': 'Logistics & Sustainment',
             'aliases': ['FSR', 'Field Engineer', 'Field Support Representative']},
            
            # ================================================================
            # SAFETY & SPECIALTY ENGINEERING (12 roles)
            # ================================================================
            {'role_name': 'Safety Engineer', 'category': 'Safety & Specialty',
             'aliases': ['Safety Engineers', 'System Safety']},
            {'role_name': 'System Safety Lead', 'category': 'Safety & Specialty',
             'aliases': ['System Safety Engineer', 'Safety Lead', 'System Safety Manager']},
            {'role_name': 'Human Factors Engineer', 'category': 'Safety & Specialty',
             'aliases': ['HFE', 'Human Systems Integration', 'Ergonomics Engineer']},
            {'role_name': 'EMI/EMC Engineer', 'category': 'Safety & Specialty',
             'aliases': ['EMC Engineer', 'EMI Engineer', 'Electromagnetic Compatibility']},
            {'role_name': 'Parts Engineer', 'category': 'Safety & Specialty',
             'aliases': ['Parts Analyst', 'Component Engineer', 'EEE Parts Engineer']},
            {'role_name': 'RHA Engineer', 'category': 'Safety & Specialty',
             'aliases': ['Radiation Hardness Assurance', 'Radiation Effects Engineer']},
            {'role_name': 'Contamination Control Engineer', 'category': 'Safety & Specialty',
             'aliases': ['CCE', 'Cleanliness Engineer']},
            {'role_name': 'Survivability Engineer', 'category': 'Safety & Specialty',
             'aliases': ['Survivability Analyst', 'Vulnerability Engineer']},
            {'role_name': 'Producibility Engineer', 'category': 'Safety & Specialty',
             'aliases': ['DFM Engineer', 'Design for Manufacturing']},
            {'role_name': 'Corrosion Engineer', 'category': 'Safety & Specialty',
             'aliases': ['Corrosion Control Engineer', 'Corrosion Prevention']},
            {'role_name': 'Loads Engineer', 'category': 'Safety & Specialty',
             'aliases': ['Loads Analyst', 'Dynamic Loads Engineer']},
            {'role_name': 'Mass Properties Engineer', 'category': 'Safety & Specialty',
             'aliases': ['Mass Properties Analyst', 'Weight Engineer']},
            
            # ================================================================
            # CONFIGURATION & DATA MANAGEMENT (8 roles)
            # ================================================================
            {'role_name': 'Configuration Manager', 'category': 'Configuration & Data',
             'aliases': ['CM', 'Config Manager', 'Configuration Management']},
            {'role_name': 'Data Manager', 'category': 'Configuration & Data',
             'aliases': ['Data Management', 'DM', 'Information Manager']},
            {'role_name': 'Document Control', 'category': 'Configuration & Data',
             'aliases': ['Document Controller', 'Records Manager', 'Document Management']},
            {'role_name': 'CDRL Manager', 'category': 'Configuration & Data',
             'aliases': ['CDRL Administrator', 'Deliverables Manager']},
            {'role_name': 'Configuration Analyst', 'category': 'Configuration & Data',
             'aliases': ['CM Analyst', 'Configuration Specialist']},
            {'role_name': 'Baseline Manager', 'category': 'Configuration & Data',
             'aliases': ['Baseline Administrator', 'Configuration Baseline Lead']},
            {'role_name': 'Change Control Administrator', 'category': 'Configuration & Data',
             'aliases': ['CCB Administrator', 'Change Administrator']},
            {'role_name': 'Product Data Manager', 'category': 'Configuration & Data',
             'aliases': ['PDM Administrator', 'PLM Administrator']},
            
            # ================================================================
            # CONTRACTS & BUSINESS (10 roles)
            # ================================================================
            {'role_name': 'Contracts Manager', 'category': 'Contracts & Business',
             'aliases': ['Contract Manager', 'Contracts Lead', 'Contract Administrator']},
            {'role_name': 'Subcontracts Manager', 'category': 'Contracts & Business',
             'aliases': ['Subcontracts Administrator', 'Subcontract Manager']},
            {'role_name': 'Proposal Manager', 'category': 'Contracts & Business',
             'aliases': ['Proposal Lead', 'Proposal Coordinator', 'Bid Manager']},
            {'role_name': 'Capture Manager', 'category': 'Contracts & Business',
             'aliases': ['Capture Lead', 'BD Manager', 'Business Development Manager']},
            {'role_name': 'Pricing Manager', 'category': 'Contracts & Business',
             'aliases': ['Pricing Analyst', 'Cost Volume Manager']},
            {'role_name': 'Contracts Administrator', 'category': 'Contracts & Business',
             'aliases': ['Contract Admin', 'CA']},
            {'role_name': 'Procurement Specialist', 'category': 'Contracts & Business',
             'aliases': ['Buyer', 'Purchasing Agent', 'Procurement Agent']},
            {'role_name': 'Export Compliance Officer', 'category': 'Contracts & Business',
             'aliases': ['ITAR Compliance', 'Export Control', 'Trade Compliance']},
            {'role_name': 'Finance Manager', 'category': 'Contracts & Business',
             'aliases': ['Financial Analyst', 'Program Finance']},
            {'role_name': 'Legal Counsel', 'category': 'Contracts & Business',
             'aliases': ['Attorney', 'Legal Advisor', 'General Counsel']},
            
            # ================================================================
            # SECURITY (8 roles)
            # ================================================================
            {'role_name': 'Security Manager', 'category': 'Security',
             'aliases': ['Security Lead', 'Industrial Security Manager']},
            {'role_name': 'FSO', 'category': 'Security',
             'aliases': ['Facility Security Officer', 'Security Officer']},
            {'role_name': 'ISSM', 'category': 'Security',
             'aliases': ['Information System Security Manager', 'IT Security Manager']},
            {'role_name': 'ISSO', 'category': 'Security',
             'aliases': ['Information System Security Officer', 'IT Security Officer']},
            {'role_name': 'Cybersecurity Engineer', 'category': 'Security',
             'aliases': ['Cyber Engineer', 'Information Security Engineer', 'IA Engineer']},
            {'role_name': 'COMSEC Manager', 'category': 'Security',
             'aliases': ['Communications Security', 'COMSEC Custodian']},
            {'role_name': 'Classification Management Officer', 'category': 'Security',
             'aliases': ['CMO', 'Classification Officer']},
            {'role_name': 'OPSEC Officer', 'category': 'Security',
             'aliases': ['Operations Security', 'OPSEC Manager']},
            
            # ================================================================
            # CUSTOMER/GOVERNMENT (12 roles)
            # ================================================================
            {'role_name': 'COR', 'category': 'Customer/Government',
             'aliases': ['Contracting Officer Representative', 'CORs', 'COTR']},
            {'role_name': 'COTR', 'category': 'Customer/Government',
             'aliases': ['Contracting Officer Technical Representative', 'Technical COR']},
            {'role_name': 'ACO', 'category': 'Customer/Government',
             'aliases': ['Administrative Contracting Officer', 'ACOs']},
            {'role_name': 'PCO', 'category': 'Customer/Government',
             'aliases': ['Procuring Contracting Officer', 'PCOs']},
            {'role_name': 'DCMA Representative', 'category': 'Customer/Government',
             'aliases': ['DCMA', 'Government QAR', 'DCMA QAR']},
            {'role_name': 'Government PM', 'category': 'Customer/Government',
             'aliases': ['Government Program Manager', 'Govt PM']},
            {'role_name': 'Contracting Officer', 'category': 'Customer/Government',
             'aliases': ['CO', 'Contracting Officers', 'KO']},
            {'role_name': 'Government Technical Representative', 'category': 'Customer/Government',
             'aliases': ['GTR', 'Technical Monitor', 'TPOC']},
            {'role_name': 'Customer', 'category': 'Customer/Government',
             'aliases': ['Client', 'End User', 'User']},
            {'role_name': 'Government Engineer', 'category': 'Customer/Government',
             'aliases': ['Govt Engineer', 'Government Technical Staff']},
            {'role_name': 'Source Selection Authority', 'category': 'Customer/Government',
             'aliases': ['SSA', 'Selection Authority']},
            {'role_name': 'Milestone Decision Authority', 'category': 'Customer/Government',
             'aliases': ['MDA', 'Decision Authority']},
            
            # ================================================================
            # BOARDS & TEAMS (10 roles)
            # ================================================================
            {'role_name': 'Configuration Control Board', 'category': 'Boards & Teams',
             'aliases': ['CCB', 'Change Control Board', 'CCB Chair']},
            {'role_name': 'Engineering Review Board', 'category': 'Boards & Teams',
             'aliases': ['ERB', 'Technical Review Board', 'ERB Chair']},
            {'role_name': 'Integrated Product Team', 'category': 'Boards & Teams',
             'aliases': ['IPT', 'Product Team']},
            {'role_name': 'Material Review Board', 'category': 'Boards & Teams',
             'aliases': ['MRB', 'Material Review']},
            {'role_name': 'Gate Review Chair', 'category': 'Boards & Teams',
             'aliases': ['Gate Review Lead', 'Phase Gate Chair']},
            {'role_name': 'IRB Member', 'category': 'Boards & Teams',
             'aliases': ['Independent Review Board', 'IRB Chair']},
            {'role_name': 'Red Team Lead', 'category': 'Boards & Teams',
             'aliases': ['Red Team Chair', 'Red Team Member']},
            {'role_name': 'Tiger Team Lead', 'category': 'Boards & Teams',
             'aliases': ['Tiger Team Member', 'Special Team Lead']},
            {'role_name': 'Working Group Lead', 'category': 'Boards & Teams',
             'aliases': ['WG Lead', 'Technical Working Group']},
            {'role_name': 'Failure Review Board', 'category': 'Boards & Teams',
             'aliases': ['FRB', 'FRB Chair', 'Anomaly Review Board']},
            
            # ================================================================
            # STAKEHOLDERS & ORGANIZATIONS (6 roles)
            # ================================================================
            {'role_name': 'Contractor', 'category': 'Stakeholders',
             'aliases': ['Prime Contractor', 'Contractors', 'Prime']},
            {'role_name': 'Subcontractor', 'category': 'Stakeholders',
             'aliases': ['Sub-Contractor', 'Subcontractors', 'Sub', 'Supplier']},
            {'role_name': 'Sector VP', 'category': 'Stakeholders',
             'aliases': ['Sector Vice President', 'SVP', 'Division VP']},
            {'role_name': 'Division Director', 'category': 'Stakeholders',
             'aliases': ['Division Manager', 'Director']},
            {'role_name': 'Technical Fellow', 'category': 'Stakeholders',
             'aliases': ['Fellow', 'Distinguished Engineer', 'Chief Scientist']},
            {'role_name': 'Subject Matter Expert', 'category': 'Stakeholders',
             'aliases': ['SME', 'Domain Expert', 'Technical Expert']},
            
            # ================================================================
            # F05: TOOLS & SYSTEMS (v2.9.3)
            # For identifying system/tool references marked with [S] prefix
            # ================================================================
            {'role_name': 'Windchill', 'category': 'Tools & Systems',
             'aliases': ['PTC Windchill', 'Windchill PDMLink'],
             'description': 'Product lifecycle management system for engineering data'},
            {'role_name': 'Teamcenter', 'category': 'Tools & Systems',
             'aliases': ['Siemens Teamcenter', 'TC'],
             'description': 'PLM software for product data management'},
            {'role_name': 'DOORS', 'category': 'Tools & Systems',
             'aliases': ['IBM DOORS', 'Rational DOORS', 'DOORS Next'],
             'description': 'Requirements management and traceability tool'},
            {'role_name': 'Jama Connect', 'category': 'Tools & Systems',
             'aliases': ['Jama', 'Jama Software'],
             'description': 'Requirements management platform'},
            {'role_name': 'Cameo Systems Modeler', 'category': 'Tools & Systems',
             'aliases': ['Cameo', 'MagicDraw', 'Catia Magic'],
             'description': 'Model-based systems engineering tool using SysML'},
            {'role_name': 'Enterprise Architect', 'category': 'Tools & Systems',
             'aliases': ['EA', 'Sparx EA', 'Sparx Systems'],
             'description': 'UML/SysML modeling and design tool'},
            {'role_name': 'CATIA', 'category': 'Tools & Systems',
             'aliases': ['Dassault CATIA', 'CATIA V5', 'CATIA V6'],
             'description': 'CAD software for aerospace and automotive design'},
            {'role_name': 'NX', 'category': 'Tools & Systems',
             'aliases': ['Siemens NX', 'Unigraphics', 'UG NX'],
             'description': 'CAD/CAM/CAE software for product development'},
            {'role_name': 'SolidWorks', 'category': 'Tools & Systems',
             'aliases': ['SW', 'Solidworks'],
             'description': 'CAD software for mechanical design'},
            {'role_name': 'Creo', 'category': 'Tools & Systems',
             'aliases': ['PTC Creo', 'Pro/Engineer', 'ProE'],
             'description': 'CAD software for product design'},
            {'role_name': 'MATLAB', 'category': 'Tools & Systems',
             'aliases': ['MathWorks MATLAB'],
             'description': 'Technical computing environment for algorithm development'},
            {'role_name': 'Simulink', 'category': 'Tools & Systems',
             'aliases': ['MathWorks Simulink'],
             'description': 'Simulation and model-based design platform'},
            {'role_name': 'ANSYS', 'category': 'Tools & Systems',
             'aliases': ['Ansys Workbench'],
             'description': 'Engineering simulation software for FEA, CFD'},
            {'role_name': 'NASTRAN', 'category': 'Tools & Systems',
             'aliases': ['MSC NASTRAN', 'NX NASTRAN'],
             'description': 'Finite element analysis software'},
            {'role_name': 'Primavera P6', 'category': 'Tools & Systems',
             'aliases': ['P6', 'Oracle Primavera'],
             'description': 'Enterprise project portfolio management software'},
            {'role_name': 'Microsoft Project', 'category': 'Tools & Systems',
             'aliases': ['MS Project', 'MSP'],
             'description': 'Project management software'},
            {'role_name': 'SAP', 'category': 'Tools & Systems',
             'aliases': ['SAP ERP', 'SAP S/4HANA'],
             'description': 'Enterprise resource planning system'},
            {'role_name': 'Deltek Costpoint', 'category': 'Tools & Systems',
             'aliases': ['Costpoint'],
             'description': 'Government contractor accounting and ERP system'},
            {'role_name': 'Deltek Cobra', 'category': 'Tools & Systems',
             'aliases': ['Cobra'],
             'description': 'Earned value management software'},
            {'role_name': 'SharePoint', 'category': 'Tools & Systems',
             'aliases': ['Microsoft SharePoint', 'SPO'],
             'description': 'Document management and collaboration platform'},
            {'role_name': 'Confluence', 'category': 'Tools & Systems',
             'aliases': ['Atlassian Confluence'],
             'description': 'Team collaboration and documentation platform'},
            {'role_name': 'Jira', 'category': 'Tools & Systems',
             'aliases': ['Atlassian Jira'],
             'description': 'Issue tracking and project management tool'},
            {'role_name': 'Git', 'category': 'Tools & Systems',
             'aliases': ['GitHub', 'GitLab', 'Bitbucket'],
             'description': 'Version control system for code and documents'},
            {'role_name': 'Tableau', 'category': 'Tools & Systems',
             'aliases': [],
             'description': 'Data visualization and business intelligence platform'},
            {'role_name': 'Power BI', 'category': 'Tools & Systems',
             'aliases': ['Microsoft Power BI'],
             'description': 'Business analytics and visualization tool'},
            
            # ================================================================
            # v2.9.4 #8: EXPANDED GOVERNMENT/DEFENSE ROLES
            # ================================================================
            {'role_name': 'Contracting Officer', 'category': 'Government',
             'aliases': ['CO', 'KO', 'Contracting Officers']},
            {'role_name': 'Contracting Officer Representative', 'category': 'Government',
             'aliases': ['COR', 'COTR', 'Contracting Technical Representative']},
            {'role_name': 'Program Executive Officer', 'category': 'Government',
             'aliases': ['PEO', 'PEOs']},
            {'role_name': 'Milestone Decision Authority', 'category': 'Government',
             'aliases': ['MDA', 'Decision Authority']},
            {'role_name': 'Technical Authority', 'category': 'Government',
             'aliases': ['TA', 'Technical Authorities']},
            {'role_name': 'Acquisition Executive', 'category': 'Government',
             'aliases': ['SAE', 'Service Acquisition Executive']},
            {'role_name': 'Defense Contract Audit Agency', 'category': 'Government',
             'aliases': ['DCAA', 'Auditor']},
            {'role_name': 'Defense Contract Management Agency', 'category': 'Government',
             'aliases': ['DCMA', 'Contract Administrator']},
            {'role_name': 'Government Property Administrator', 'category': 'Government',
             'aliases': ['GPA', 'Property Administrator']},
            {'role_name': 'Administrative Contracting Officer', 'category': 'Government',
             'aliases': ['ACO']},
            {'role_name': 'Quality Assurance Representative', 'category': 'Government',
             'aliases': ['QAR', 'Government Inspector']},
            {'role_name': 'Facility Security Officer', 'category': 'Government',
             'aliases': ['FSO', 'Industrial Security']},
            {'role_name': 'Information System Security Officer', 'category': 'Government',
             'aliases': ['ISSO', 'Cybersecurity Officer']},
            {'role_name': 'Information System Security Manager', 'category': 'Government',
             'aliases': ['ISSM', 'Cyber Manager']},
            {'role_name': 'Authorizing Official', 'category': 'Government',
             'aliases': ['AO', 'Designated Approving Authority', 'DAA']},
            
            # ================================================================
            # v2.9.4 #8: EXPANDED IT/TECHNICAL ROLES
            # ================================================================
            {'role_name': 'Network Engineer', 'category': 'IT/Technical',
             'aliases': ['Network Admin', 'Network Administrator']},
            {'role_name': 'Cloud Engineer', 'category': 'IT/Technical',
             'aliases': ['Cloud Architect', 'AWS Engineer', 'Azure Engineer']},
            {'role_name': 'Cybersecurity Engineer', 'category': 'IT/Technical',
             'aliases': ['Security Engineer', 'InfoSec Engineer']},
            {'role_name': 'Database Administrator', 'category': 'IT/Technical',
             'aliases': ['DBA', 'Database Engineer']},
            {'role_name': 'System Administrator', 'category': 'IT/Technical',
             'aliases': ['Sysadmin', 'Server Administrator']},
            {'role_name': 'IT Manager', 'category': 'IT/Technical',
             'aliases': ['IT Director', 'Information Technology Manager']},
            {'role_name': 'Solutions Architect', 'category': 'IT/Technical',
             'aliases': ['Technical Solutions Architect', 'Enterprise Architect']},
            {'role_name': 'Site Reliability Engineer', 'category': 'IT/Technical',
             'aliases': ['SRE', 'Reliability Engineer']},
            {'role_name': 'Scrum Master', 'category': 'IT/Technical',
             'aliases': ['Agile Coach', 'Agile Lead']},
            {'role_name': 'Product Owner', 'category': 'IT/Technical',
             'aliases': ['PO', 'Product Manager']},
            {'role_name': 'Technical Writer', 'category': 'IT/Technical',
             'aliases': ['Documentation Specialist', 'Tech Writer']},
            {'role_name': 'Business Analyst', 'category': 'IT/Technical',
             'aliases': ['BA', 'Systems Analyst']},
            {'role_name': 'UX Designer', 'category': 'IT/Technical',
             'aliases': ['User Experience Designer', 'UI/UX Designer']},
            
            # ================================================================
            # v2.9.4 #8: EXPANDED BUSINESS/MANAGEMENT ROLES
            # ================================================================
            {'role_name': 'Executive Director', 'category': 'Management',
             'aliases': ['ED', 'Managing Director']},
            {'role_name': 'Vice President', 'category': 'Management',
             'aliases': ['VP', 'Vice Pres']},
            {'role_name': 'General Manager', 'category': 'Management',
             'aliases': ['GM', 'General Mgr']},
            {'role_name': 'Operations Manager', 'category': 'Management',
             'aliases': ['Ops Manager', 'Operations Director']},
            {'role_name': 'Finance Manager', 'category': 'Management',
             'aliases': ['Financial Manager', 'Finance Director']},
            {'role_name': 'HR Manager', 'category': 'Management',
             'aliases': ['Human Resources Manager', 'People Manager']},
            {'role_name': 'Proposal Manager', 'category': 'Management',
             'aliases': ['Capture Manager', 'BD Manager']},
            {'role_name': 'Contracts Manager', 'category': 'Management',
             'aliases': ['Contract Administrator', 'Contracts Administrator']},
            {'role_name': 'Procurement Manager', 'category': 'Management',
             'aliases': ['Purchasing Manager', 'Supply Chain Manager']},
            {'role_name': 'Training Manager', 'category': 'Management',
             'aliases': ['Training Coordinator', 'Learning Manager']},
            
            # ================================================================
            # v2.9.4 #8: EXPANDED COMPLIANCE/QUALITY ROLES
            # ================================================================
            {'role_name': 'Compliance Officer', 'category': 'Compliance',
             'aliases': ['Compliance Manager', 'Regulatory Compliance']},
            {'role_name': 'Ethics Officer', 'category': 'Compliance',
             'aliases': ['Ethics Manager', 'Corporate Ethics']},
            {'role_name': 'Export Control Officer', 'category': 'Compliance',
             'aliases': ['ITAR Officer', 'Export Compliance']},
            {'role_name': 'Privacy Officer', 'category': 'Compliance',
             'aliases': ['Data Protection Officer', 'DPO']},
            {'role_name': 'Internal Auditor', 'category': 'Compliance',
             'aliases': ['Audit Manager', 'Quality Auditor']},
            {'role_name': 'Environmental Health Safety', 'category': 'Compliance',
             'aliases': ['EHS', 'Safety Officer', 'HSE Manager']},
            {'role_name': 'Regulatory Affairs Manager', 'category': 'Compliance',
             'aliases': ['Regulatory Manager', 'RA Manager']},
            
            # ================================================================
            # v2.9.10 #24: ADDITIONAL AEROSPACE/DEFENSE ROLES (200+ new roles)
            # ================================================================
            
            # --- AIRCRAFT/AEROSPACE SPECIFIC ---
            {'role_name': 'Aircraft Systems Engineer', 'category': 'Aerospace Engineering',
             'aliases': ['ASE', 'Aircraft Engineer']},
            {'role_name': 'Aerodynamics Engineer', 'category': 'Aerospace Engineering',
             'aliases': ['Aero Engineer', 'Aerodynamicist']},
            {'role_name': 'Structures Analyst', 'category': 'Aerospace Engineering',
             'aliases': ['Structural Analyst', 'Stress Analyst']},
            {'role_name': 'Flight Dynamics Engineer', 'category': 'Aerospace Engineering',
             'aliases': ['Stability Engineer', 'Dynamics Engineer']},
            {'role_name': 'Payload Engineer', 'category': 'Aerospace Engineering',
             'aliases': ['Payload Systems Engineer', 'Payload Integration']},
            {'role_name': 'Launch Vehicle Engineer', 'category': 'Aerospace Engineering',
             'aliases': ['LV Engineer', 'Launch Systems Engineer']},
            {'role_name': 'Satellite Engineer', 'category': 'Aerospace Engineering',
             'aliases': ['Spacecraft Engineer', 'Bus Engineer']},
            {'role_name': 'Ground Systems Engineer', 'category': 'Aerospace Engineering',
             'aliases': ['GSE Engineer', 'Ground Support Equipment']},
            {'role_name': 'Mission Operations Engineer', 'category': 'Aerospace Engineering',
             'aliases': ['Ops Engineer', 'Mission Ops']},
            {'role_name': 'Command & Control Engineer', 'category': 'Aerospace Engineering',
             'aliases': ['C2 Engineer', 'C4ISR Engineer']},
            {'role_name': 'Radar Systems Engineer', 'category': 'Aerospace Engineering',
             'aliases': ['Radar Engineer', 'AESA Engineer']},
            {'role_name': 'EW Engineer', 'category': 'Aerospace Engineering',
             'aliases': ['Electronic Warfare Engineer', 'EW Systems']},
            {'role_name': 'Countermeasures Engineer', 'category': 'Aerospace Engineering',
             'aliases': ['CM Engineer', 'ECM Engineer']},
            {'role_name': 'Targeting Engineer', 'category': 'Aerospace Engineering',
             'aliases': ['Target Acquisition', 'Targeting Systems']},
            {'role_name': 'Weapons Systems Engineer', 'category': 'Aerospace Engineering',
             'aliases': ['Weapons Engineer', 'WSO']},
            
            # --- SPACECRAFT/SATELLITE SPECIFIC ---
            {'role_name': 'Attitude Control Engineer', 'category': 'Spacecraft Engineering',
             'aliases': ['ADCS Engineer', 'ACS Engineer']},
            {'role_name': 'Orbit Analyst', 'category': 'Spacecraft Engineering',
             'aliases': ['Orbital Mechanics', 'Astrodynamics']},
            {'role_name': 'Solar Array Engineer', 'category': 'Spacecraft Engineering',
             'aliases': ['Power Generation', 'Solar Panel Engineer']},
            {'role_name': 'Thermal Control Engineer', 'category': 'Spacecraft Engineering',
             'aliases': ['TCS Engineer', 'Thermal Systems']},
            {'role_name': 'Cryogenics Engineer', 'category': 'Spacecraft Engineering',
             'aliases': ['Cryo Engineer', 'Cryogenic Systems']},
            {'role_name': 'Mechanisms Engineer', 'category': 'Spacecraft Engineering',
             'aliases': ['Deployment Engineer', 'Mechanical Systems']},
            {'role_name': 'Space Vehicle Operator', 'category': 'Spacecraft Engineering',
             'aliases': ['SVO', 'Spacecraft Operator']},
            {'role_name': 'Constellation Manager', 'category': 'Spacecraft Engineering',
             'aliases': ['Fleet Manager', 'Constellation Ops']},
            {'role_name': 'Ground Station Manager', 'category': 'Spacecraft Engineering',
             'aliases': ['Ground Station Ops', 'GSM']},
            {'role_name': 'Link Budget Analyst', 'category': 'Spacecraft Engineering',
             'aliases': ['RF Link Analyst', 'Communications Analyst']},
            
            # --- DEFENSE/MILITARY SPECIFIC ---
            {'role_name': 'Program Executive Officer', 'category': 'Defense Management',
             'aliases': ['PEO', 'Acquisition Executive']},
            {'role_name': 'Contracting Officer', 'category': 'Defense Management',
             'aliases': ['CO', 'PCO', 'ACO']},
            {'role_name': 'Contracting Officer Representative', 'category': 'Defense Management',
             'aliases': ['COR', 'COTR']},
            {'role_name': 'Technical Representative', 'category': 'Defense Management',
             'aliases': ['DCMA Representative', 'Government Rep']},
            {'role_name': 'Program Analyst', 'category': 'Defense Management',
             'aliases': ['PA', 'Defense Analyst']},
            {'role_name': 'DCMA QA', 'category': 'Defense Management',
             'aliases': ['Government QA', 'Customer QA']},
            {'role_name': 'Security Manager', 'category': 'Defense Management',
             'aliases': ['FSO', 'Facility Security Officer']},
            {'role_name': 'COMSEC Custodian', 'category': 'Defense Management',
             'aliases': ['Communications Security', 'Crypto Custodian']},
            {'role_name': 'TEMPEST Engineer', 'category': 'Defense Management',
             'aliases': ['EMSEC Engineer', 'Emanations Security']},
            {'role_name': 'Logistics Manager', 'category': 'Defense Management',
             'aliases': ['ILS Manager', 'Integrated Logistics Support']},
            {'role_name': 'Depot Manager', 'category': 'Defense Management',
             'aliases': ['Depot Operations', 'Maintenance Manager']},
            {'role_name': 'Field Service Engineer', 'category': 'Defense Management',
             'aliases': ['FSE', 'Field Engineer', 'Field Rep']},
            
            # --- NUCLEAR/CRITICAL SYSTEMS ---
            {'role_name': 'Nuclear Safety Officer', 'category': 'Nuclear Engineering',
             'aliases': ['NSO', 'Reactor Safety']},
            {'role_name': 'Criticality Safety Engineer', 'category': 'Nuclear Engineering',
             'aliases': ['Nuclear Criticality', 'CSE']},
            {'role_name': 'Radiation Protection Engineer', 'category': 'Nuclear Engineering',
             'aliases': ['Health Physics', 'RP Engineer']},
            {'role_name': 'Nuclear Quality Engineer', 'category': 'Nuclear Engineering',
             'aliases': ['NQE', 'Nuclear QA']},
            {'role_name': 'Reactor Engineer', 'category': 'Nuclear Engineering',
             'aliases': ['Nuclear Engineer', 'Core Engineer']},
            
            # --- CYBERSECURITY ---
            {'role_name': 'Cybersecurity Engineer', 'category': 'Cybersecurity',
             'aliases': ['Cyber Engineer', 'InfoSec Engineer']},
            {'role_name': 'ISSO', 'category': 'Cybersecurity',
             'aliases': ['Information System Security Officer']},
            {'role_name': 'ISSM', 'category': 'Cybersecurity',
             'aliases': ['Information System Security Manager']},
            {'role_name': 'Security Control Assessor', 'category': 'Cybersecurity',
             'aliases': ['SCA', 'RMF Assessor']},
            {'role_name': 'Penetration Tester', 'category': 'Cybersecurity',
             'aliases': ['Pen Tester', 'Red Team']},
            {'role_name': 'SOC Analyst', 'category': 'Cybersecurity',
             'aliases': ['Security Operations', 'Blue Team']},
            {'role_name': 'Incident Response Lead', 'category': 'Cybersecurity',
             'aliases': ['IR Lead', 'CERT Lead']},
            {'role_name': 'Threat Intelligence Analyst', 'category': 'Cybersecurity',
             'aliases': ['CTI Analyst', 'Threat Analyst']},
            {'role_name': 'Vulnerability Analyst', 'category': 'Cybersecurity',
             'aliases': ['Vuln Analyst', 'Security Researcher']},
            {'role_name': 'Security Architect', 'category': 'Cybersecurity',
             'aliases': ['Cybersecurity Architect', 'InfoSec Architect']},
            
            # --- MANUFACTURING & PRODUCTION ---
            {'role_name': 'Manufacturing Engineer', 'category': 'Manufacturing',
             'aliases': ['Mfg Engineer', 'Production Engineer']},
            {'role_name': 'Process Engineer', 'category': 'Manufacturing',
             'aliases': ['MPE', 'Manufacturing Process Engineer']},
            {'role_name': 'Industrial Engineer', 'category': 'Manufacturing',
             'aliases': ['IE', 'Methods Engineer']},
            {'role_name': 'Tool Designer', 'category': 'Manufacturing',
             'aliases': ['Tooling Engineer', 'Fixture Designer']},
            {'role_name': 'NC Programmer', 'category': 'Manufacturing',
             'aliases': ['CNC Programmer', 'Numerical Control']},
            {'role_name': 'Production Planner', 'category': 'Manufacturing',
             'aliases': ['Production Control', 'MRP Analyst']},
            {'role_name': 'Assembly Technician', 'category': 'Manufacturing',
             'aliases': ['Assembler', 'Production Technician']},
            {'role_name': 'Weld Engineer', 'category': 'Manufacturing',
             'aliases': ['Welding Engineer', 'Weld Inspector']},
            {'role_name': 'NDT Technician', 'category': 'Manufacturing',
             'aliases': ['NDE Technician', 'Nondestructive Testing']},
            {'role_name': 'Clean Room Technician', 'category': 'Manufacturing',
             'aliases': ['Cleanroom Operator', 'Contamination Control']},
            {'role_name': 'Composite Technician', 'category': 'Manufacturing',
             'aliases': ['Composites Engineer', 'Layup Technician']},
            {'role_name': 'Bonding Technician', 'category': 'Manufacturing',
             'aliases': ['Adhesive Specialist', 'Bond Tech']},
            {'role_name': 'Paint Technician', 'category': 'Manufacturing',
             'aliases': ['Coatings Specialist', 'Finish Tech']},
            {'role_name': 'Final Assembly Lead', 'category': 'Manufacturing',
             'aliases': ['Final Assembly', 'FAL Lead']},
            
            # --- RELIABILITY & SAFETY ---
            {'role_name': 'Reliability Engineer', 'category': 'Reliability & Safety',
             'aliases': ['R&M Engineer', 'RAMS Engineer']},
            {'role_name': 'Safety Engineer', 'category': 'Reliability & Safety',
             'aliases': ['System Safety', 'SSE']},
            {'role_name': 'FMEA Lead', 'category': 'Reliability & Safety',
             'aliases': ['FMECA Lead', 'Failure Modes']},
            {'role_name': 'FTA Analyst', 'category': 'Reliability & Safety',
             'aliases': ['Fault Tree Analysis', 'FTA Engineer']},
            {'role_name': 'Hazard Analyst', 'category': 'Reliability & Safety',
             'aliases': ['PHA Lead', 'Safety Analyst']},
            {'role_name': 'Human Factors Engineer', 'category': 'Reliability & Safety',
             'aliases': ['Ergonomics Engineer', 'HFE']},
            {'role_name': 'Maintainability Engineer', 'category': 'Reliability & Safety',
             'aliases': ['M&R Engineer', 'Supportability']},
            {'role_name': 'Availability Engineer', 'category': 'Reliability & Safety',
             'aliases': ['Ao Analyst', 'Operational Availability']},
            {'role_name': 'Sneak Circuit Analyst', 'category': 'Reliability & Safety',
             'aliases': ['SCA', 'Circuit Safety']},
            {'role_name': 'Parts Engineer', 'category': 'Reliability & Safety',
             'aliases': ['Parts Management', 'Component Engineer']},
            {'role_name': 'Derating Analyst', 'category': 'Reliability & Safety',
             'aliases': ['Parts Derating', 'Reliability Parts']},
            {'role_name': 'Radiation Effects Engineer', 'category': 'Reliability & Safety',
             'aliases': ['Rad Hard Engineer', 'SEE Analyst']},
            
            # --- DATA & DOCUMENTATION ---
            {'role_name': 'Technical Writer', 'category': 'Documentation',
             'aliases': ['Tech Writer', 'Documentation Specialist']},
            {'role_name': 'Technical Editor', 'category': 'Documentation',
             'aliases': ['Editor', 'Publications Editor']},
            {'role_name': 'Illustrator', 'category': 'Documentation',
             'aliases': ['Technical Illustrator', 'Graphics Artist']},
            {'role_name': 'Publications Manager', 'category': 'Documentation',
             'aliases': ['Pubs Manager', 'Documentation Manager']},
            {'role_name': 'Data Manager', 'category': 'Documentation',
             'aliases': ['Data Management', 'TDM']},
            {'role_name': 'Records Manager', 'category': 'Documentation',
             'aliases': ['Records Management', 'Document Control']},
            {'role_name': 'Configuration Analyst', 'category': 'Documentation',
             'aliases': ['CM Analyst', 'Config Specialist']},
            {'role_name': 'Baseline Manager', 'category': 'Documentation',
             'aliases': ['Configuration Baseline', 'Baseline Control']},
            {'role_name': 'Drawing Checker', 'category': 'Documentation',
             'aliases': ['Drawing Control', 'Drawing Release']},
            {'role_name': 'Standards Engineer', 'category': 'Documentation',
             'aliases': ['Standards Manager', 'Standardization']},
            
            # --- SUPPLY CHAIN ---
            {'role_name': 'Supply Chain Manager', 'category': 'Supply Chain',
             'aliases': ['SCM', 'Supply Chain Lead']},
            {'role_name': 'Buyer', 'category': 'Supply Chain',
             'aliases': ['Procurement Specialist', 'Purchasing Agent']},
            {'role_name': 'Subcontracts Manager', 'category': 'Supply Chain',
             'aliases': ['Subcontracts Admin', 'Subk Manager']},
            {'role_name': 'Supplier Manager', 'category': 'Supply Chain',
             'aliases': ['Vendor Manager', 'Supplier Development']},
            {'role_name': 'Source Inspector', 'category': 'Supply Chain',
             'aliases': ['Supplier Inspector', 'SQI']},
            {'role_name': 'Material Planner', 'category': 'Supply Chain',
             'aliases': ['MRP Planner', 'Materials Manager']},
            {'role_name': 'Inventory Manager', 'category': 'Supply Chain',
             'aliases': ['Inventory Control', 'Stock Manager']},
            {'role_name': 'Shipping Coordinator', 'category': 'Supply Chain',
             'aliases': ['Traffic Manager', 'Logistics Coordinator']},
            {'role_name': 'Receiving Inspector', 'category': 'Supply Chain',
             'aliases': ['Incoming QC', 'Receiving QA']},
            {'role_name': 'Counterfeit Prevention', 'category': 'Supply Chain',
             'aliases': ['DFARS Compliance', 'Parts Authentication']},
            
            # --- PROGRAM CONTROLS ---
            {'role_name': 'Earned Value Analyst', 'category': 'Program Controls',
             'aliases': ['EVM Manager', 'EVMS Lead']},
            {'role_name': 'Baseline Change Manager', 'category': 'Program Controls',
             'aliases': ['CCB Secretary', 'Change Control']},
            {'role_name': 'Schedule Analyst', 'category': 'Program Controls',
             'aliases': ['IMS Analyst', 'Schedule Lead']},
            {'role_name': 'Budget Analyst', 'category': 'Program Controls',
             'aliases': ['Financial Analyst', 'Cost Account Lead']},
            {'role_name': 'Variance Analyst', 'category': 'Program Controls',
             'aliases': ['VR Lead', 'Variance Reporting']},
            {'role_name': 'Rate Analyst', 'category': 'Program Controls',
             'aliases': ['Indirect Rate', 'Rate Development']},
            {'role_name': 'EAC Analyst', 'category': 'Program Controls',
             'aliases': ['Estimate at Completion', 'Forecasting']},
            {'role_name': 'Data Rights Analyst', 'category': 'Program Controls',
             'aliases': ['IP Manager', 'Technical Data Rights']},
            {'role_name': 'CDRL Manager', 'category': 'Program Controls',
             'aliases': ['Data Deliverables', 'DID Manager']},
            {'role_name': 'Metrics Manager', 'category': 'Program Controls',
             'aliases': ['KPI Manager', 'Performance Metrics']},
            
            # --- SPECIALIZED ENGINEERING ---
            {'role_name': 'Survivability Engineer', 'category': 'Specialized Engineering',
             'aliases': ['Vulnerability Engineer', 'Platform Survivability']},
            {'role_name': 'Signature Engineer', 'category': 'Specialized Engineering',
             'aliases': ['RCS Engineer', 'Stealth Engineer']},
            {'role_name': 'Acoustics Engineer', 'category': 'Specialized Engineering',
             'aliases': ['Noise Engineer', 'Vibration Engineer']},
            {'role_name': 'EMC Engineer', 'category': 'Specialized Engineering',
             'aliases': ['EMI Engineer', 'Electromagnetic Compatibility']},
            {'role_name': 'ESD Engineer', 'category': 'Specialized Engineering',
             'aliases': ['Electrostatic Discharge', 'Static Control']},
            {'role_name': 'Lightning Engineer', 'category': 'Specialized Engineering',
             'aliases': ['HIRF Engineer', 'Atmospheric Hazards']},
            {'role_name': 'Corrosion Engineer', 'category': 'Specialized Engineering',
             'aliases': ['Corrosion Control', 'Materials Protection']},
            {'role_name': 'Fatigue Engineer', 'category': 'Specialized Engineering',
             'aliases': ['Damage Tolerance', 'Structural Fatigue']},
            {'role_name': 'Loads Engineer', 'category': 'Specialized Engineering',
             'aliases': ['Structural Loads', 'Loads Analysis']},
            {'role_name': 'Mass Properties Engineer', 'category': 'Specialized Engineering',
             'aliases': ['Weight Engineer', 'CG Engineer']},
            {'role_name': 'Producibility Engineer', 'category': 'Specialized Engineering',
             'aliases': ['DFM Engineer', 'Design for Manufacturing']},
            {'role_name': 'Simulation Engineer', 'category': 'Specialized Engineering',
             'aliases': ['HWIL Engineer', 'Sim Engineer']},
            {'role_name': 'Certification Engineer', 'category': 'Specialized Engineering',
             'aliases': ['DER', 'Airworthiness']},
            
            # --- GOVERNMENT/CUSTOMER ---
            {'role_name': 'Government Customer', 'category': 'Customer',
             'aliases': ['Government', 'DoD Customer']},
            {'role_name': 'Prime Contractor', 'category': 'Customer',
             'aliases': ['Prime', 'OEM']},
            {'role_name': 'End User', 'category': 'Customer',
             'aliases': ['Operator', 'User']},
            {'role_name': 'Warfighter', 'category': 'Customer',
             'aliases': ['Service Member', 'Military User']},
            {'role_name': 'Program Office', 'category': 'Customer',
             'aliases': ['PMO', 'PO']},
            {'role_name': 'Stakeholder', 'category': 'Customer',
             'aliases': ['Key Stakeholder', 'External Stakeholder']},
            
            # --- ADDITIONAL ORGANIZATIONAL ROLES ---
            {'role_name': 'Board of Directors', 'category': 'Organization',
             'aliases': ['Board', 'Directors']},
            {'role_name': 'Chief Executive Officer', 'category': 'Organization',
             'aliases': ['CEO', 'Chief Executive']},
            {'role_name': 'Chief Operating Officer', 'category': 'Organization',
             'aliases': ['COO', 'Operations Executive']},
            {'role_name': 'Chief Financial Officer', 'category': 'Organization',
             'aliases': ['CFO', 'Finance Executive']},
            {'role_name': 'Chief Technology Officer', 'category': 'Organization',
             'aliases': ['CTO', 'Tech Executive']},
            {'role_name': 'Chief Information Officer', 'category': 'Organization',
             'aliases': ['CIO', 'IT Executive']},
            {'role_name': 'Chief Security Officer', 'category': 'Organization',
             'aliases': ['CSO', 'Security Executive']},
            {'role_name': 'Sector Lead', 'category': 'Organization',
             'aliases': ['Sector VP', 'Division Lead']},
            {'role_name': 'Business Unit Manager', 'category': 'Organization',
             'aliases': ['BU Manager', 'Unit Lead']},
            {'role_name': 'Functional Manager', 'category': 'Organization',
             'aliases': ['Department Manager', 'Functional Lead']},
            
            # --- REVIEW/APPROVAL AUTHORITIES ---
            {'role_name': 'Approval Authority', 'category': 'Approval',
             'aliases': ['Approver', 'Signatory']},
            {'role_name': 'Design Authority', 'category': 'Approval',
             'aliases': ['DA', 'Design Approval']},
            {'role_name': 'Technical Authority', 'category': 'Approval',
             'aliases': ['TA', 'Engineering Authority']},
            {'role_name': 'Quality Authority', 'category': 'Approval',
             'aliases': ['QA Authority', 'Quality Approval']},
            {'role_name': 'Safety Authority', 'category': 'Approval',
             'aliases': ['Safety Approval', 'Safety Concurrence']},
            {'role_name': 'Reliability Authority', 'category': 'Approval',
             'aliases': ['R&M Authority', 'Reliability Approval']},
            {'role_name': 'Review Board', 'category': 'Approval',
             'aliases': ['Board', 'Review Panel']},
            {'role_name': 'CCB Chair', 'category': 'Approval',
             'aliases': ['Configuration Control Board', 'CCB Lead']},
            {'role_name': 'MRB Chair', 'category': 'Approval',
             'aliases': ['Material Review Board', 'MRB Lead']},
            {'role_name': 'TRB Chair', 'category': 'Approval',
             'aliases': ['Technical Review Board', 'TRB Lead']},
            {'role_name': 'ERB Chair', 'category': 'Approval',
             'aliases': ['Engineering Review Board', 'ERB Lead']},
            {'role_name': 'PRB Chair', 'category': 'Approval',
             'aliases': ['Program Review Board', 'PRB Lead']},
            
            # --- TRAINING/SUPPORT ---
            {'role_name': 'Training Developer', 'category': 'Training & Support',
             'aliases': ['Instructional Designer', 'Course Developer']},
            {'role_name': 'Instructor', 'category': 'Training & Support',
             'aliases': ['Trainer', 'Subject Matter Expert']},
            {'role_name': 'Simulator Developer', 'category': 'Training & Support',
             'aliases': ['Training Device', 'Sim Developer']},
            {'role_name': 'Technical Support Engineer', 'category': 'Training & Support',
             'aliases': ['TSE', 'Product Support']},
            {'role_name': 'Help Desk', 'category': 'Training & Support',
             'aliases': ['IT Support', 'Service Desk']},
            {'role_name': 'On-Site Support', 'category': 'Training & Support',
             'aliases': ['Customer Site Rep', 'Field Support']},
            
            # --- LEGAL/CONTRACTS ---
            {'role_name': 'Legal Counsel', 'category': 'Legal',
             'aliases': ['Attorney', 'Corporate Counsel']},
            {'role_name': 'Contract Administrator', 'category': 'Legal',
             'aliases': ['Contracts Admin', 'Contract Specialist']},
            {'role_name': 'Intellectual Property Counsel', 'category': 'Legal',
             'aliases': ['IP Attorney', 'Patent Counsel']},
            {'role_name': 'Export Counsel', 'category': 'Legal',
             'aliases': ['ITAR Counsel', 'Trade Compliance']},
            {'role_name': 'Labor Relations', 'category': 'Legal',
             'aliases': ['Employee Relations', 'Union Relations']},
        ]
        
        # ================================================================
        # COMMON DELIVERABLES (as roles for detection)
        # v2.9.10: Expanded to 100+ deliverables (#24)
        # ================================================================
        deliverables = [
            # --- REQUIREMENTS DOCUMENTS ---
            {'role_name': 'SRS', 'category': 'Deliverable',
             'aliases': ['Software Requirements Specification', 'System Requirements Specification']},
            {'role_name': 'SRD', 'category': 'Deliverable',
             'aliases': ['System Requirements Document', 'Requirements Document']},
            {'role_name': 'PRD', 'category': 'Deliverable',
             'aliases': ['Product Requirements Document', 'Program Requirements']},
            {'role_name': 'IRS', 'category': 'Deliverable',
             'aliases': ['Interface Requirements Specification', 'Interface Requirements']},
            {'role_name': 'CRS', 'category': 'Deliverable',
             'aliases': ['Customer Requirements Specification', 'Customer Spec']},
            {'role_name': 'DRS', 'category': 'Deliverable',
             'aliases': ['Derived Requirements Specification', 'Derived Spec']},
            {'role_name': 'HRS', 'category': 'Deliverable',
             'aliases': ['Hardware Requirements Specification', 'HW Spec']},
            {'role_name': 'SWReqS', 'category': 'Deliverable',
             'aliases': ['Software Requirements Specification', 'SW Requirements']},
            {'role_name': 'ERS', 'category': 'Deliverable',
             'aliases': ['Environmental Requirements Specification', 'Env Spec']},
            {'role_name': 'PRS', 'category': 'Deliverable',
             'aliases': ['Performance Requirements Specification', 'Perf Spec']},
            
            # --- DESIGN DOCUMENTS ---
            {'role_name': 'SDD', 'category': 'Deliverable',
             'aliases': ['Software Design Document', 'System Design Document']},
            {'role_name': 'ICD', 'category': 'Deliverable',
             'aliases': ['Interface Control Document', 'Interface Control Drawing']},
            {'role_name': 'ADD', 'category': 'Deliverable',
             'aliases': ['Architecture Design Document', 'Architectural Description']},
            {'role_name': 'HDD', 'category': 'Deliverable',
             'aliases': ['Hardware Design Document', 'HW Design']},
            {'role_name': 'DBDD', 'category': 'Deliverable',
             'aliases': ['Database Design Document', 'Data Dictionary']},
            {'role_name': 'DDD', 'category': 'Deliverable',
             'aliases': ['Detailed Design Document', 'Detail Design']},
            {'role_name': 'PDD', 'category': 'Deliverable',
             'aliases': ['Preliminary Design Document', 'Prelim Design']},
            
            # --- PLANS ---
            {'role_name': 'SEMP', 'category': 'Deliverable',
             'aliases': ['Systems Engineering Management Plan', 'SE Management Plan']},
            {'role_name': 'TEMP', 'category': 'Deliverable',
             'aliases': ['Test & Evaluation Master Plan', 'Test Master Plan']},
            {'role_name': 'PMP', 'category': 'Deliverable',
             'aliases': ['Program Management Plan', 'Project Management Plan']},
            {'role_name': 'RMP', 'category': 'Deliverable',
             'aliases': ['Risk Management Plan', 'Risk Mitigation Plan']},
            {'role_name': 'CMP', 'category': 'Deliverable',
             'aliases': ['Configuration Management Plan', 'CM Plan']},
            {'role_name': 'QAP', 'category': 'Deliverable',
             'aliases': ['Quality Assurance Plan', 'QA Plan']},
            {'role_name': 'SQAP', 'category': 'Deliverable',
             'aliases': ['Software Quality Assurance Plan', 'SW QA Plan']},
            {'role_name': 'SDP', 'category': 'Deliverable',
             'aliases': ['Software Development Plan', 'SW Dev Plan']},
            {'role_name': 'STP', 'category': 'Deliverable',
             'aliases': ['Software Test Plan', 'System Test Plan']},
            {'role_name': 'SVVP', 'category': 'Deliverable',
             'aliases': ['Software Verification Validation Plan', 'V&V Plan']},
            {'role_name': 'SCMP', 'category': 'Deliverable',
             'aliases': ['Software Configuration Management Plan', 'SW CM Plan']},
            {'role_name': 'SSP', 'category': 'Deliverable',
             'aliases': ['System Security Plan', 'Security Plan']},
            {'role_name': 'SSPP', 'category': 'Deliverable',
             'aliases': ['System Safety Program Plan', 'Safety Plan']},
            {'role_name': 'ITP', 'category': 'Deliverable',
             'aliases': ['Integration Test Plan', 'I&T Plan']},
            {'role_name': 'ATP', 'category': 'Deliverable',
             'aliases': ['Acceptance Test Plan', 'Acceptance Procedures']},
            {'role_name': 'OTP', 'category': 'Deliverable',
             'aliases': ['Operational Test Plan', 'OT&E Plan']},
            {'role_name': 'ILSP', 'category': 'Deliverable',
             'aliases': ['Integrated Logistics Support Plan', 'Logistics Plan']},
            {'role_name': 'TMP', 'category': 'Deliverable',
             'aliases': ['Training Management Plan', 'Training Plan']},
            {'role_name': 'TRP', 'category': 'Deliverable',
             'aliases': ['Transition Plan', 'Deployment Plan']},
            {'role_name': 'DMP', 'category': 'Deliverable',
             'aliases': ['Data Management Plan', 'Data Plan']},
            {'role_name': 'CyberSP', 'category': 'Deliverable',
             'aliases': ['Cybersecurity Plan', 'Cyber Plan']},
            {'role_name': 'RAP', 'category': 'Deliverable',
             'aliases': ['Reliability Allocation Plan', 'R&M Plan']},
            {'role_name': 'MAP', 'category': 'Deliverable',
             'aliases': ['Mission Assurance Plan', 'MA Plan']},
            
            # --- SCHEDULES ---
            {'role_name': 'IMS', 'category': 'Deliverable',
             'aliases': ['Integrated Master Schedule', 'Master Schedule']},
            {'role_name': 'IMP', 'category': 'Deliverable',
             'aliases': ['Integrated Master Plan', 'Master Plan']},
            {'role_name': 'MPS', 'category': 'Deliverable',
             'aliases': ['Master Program Schedule', 'Program Schedule']},
            {'role_name': 'DTS', 'category': 'Deliverable',
             'aliases': ['Development Test Schedule', 'Test Schedule']},
            
            # --- REVIEWS ---
            {'role_name': 'SRR', 'category': 'Deliverable',
             'aliases': ['System Requirements Review', 'SRR Package']},
            {'role_name': 'SDR', 'category': 'Deliverable',
             'aliases': ['System Design Review', 'SDR Package']},
            {'role_name': 'PDR', 'category': 'Deliverable',
             'aliases': ['Preliminary Design Review', 'PDR Package']},
            {'role_name': 'CDR', 'category': 'Deliverable',
             'aliases': ['Critical Design Review', 'CDR Package']},
            {'role_name': 'TRR', 'category': 'Deliverable',
             'aliases': ['Test Readiness Review', 'TRR Package']},
            {'role_name': 'PRR', 'category': 'Deliverable',
             'aliases': ['Production Readiness Review', 'PRR Package']},
            {'role_name': 'FRR', 'category': 'Deliverable',
             'aliases': ['Flight Readiness Review', 'FRR Package']},
            {'role_name': 'ORR', 'category': 'Deliverable',
             'aliases': ['Operational Readiness Review', 'ORR Package']},
            {'role_name': 'FQR', 'category': 'Deliverable',
             'aliases': ['Formal Qualification Review', 'FQR Package']},
            {'role_name': 'SVR', 'category': 'Deliverable',
             'aliases': ['Software Version Review', 'SW Review']},
            {'role_name': 'MRR', 'category': 'Deliverable',
             'aliases': ['Mission Readiness Review', 'Launch Readiness']},
            {'role_name': 'PSR', 'category': 'Deliverable',
             'aliases': ['Program Status Review', 'Status Review']},
            
            # --- AUDITS ---
            {'role_name': 'FCA', 'category': 'Deliverable',
             'aliases': ['Functional Configuration Audit']},
            {'role_name': 'PCA', 'category': 'Deliverable',
             'aliases': ['Physical Configuration Audit']},
            {'role_name': 'SVA', 'category': 'Deliverable',
             'aliases': ['Software Version Audit', 'Code Audit']},
            
            # --- TECHNICAL DATA ---
            {'role_name': 'TDP', 'category': 'Deliverable',
             'aliases': ['Technical Data Package', 'Tech Data Package']},
            {'role_name': 'IETM', 'category': 'Deliverable',
             'aliases': ['Interactive Electronic Technical Manual', 'Electronic Manual']},
            {'role_name': 'TM', 'category': 'Deliverable',
             'aliases': ['Technical Manual', 'Tech Manual']},
            {'role_name': 'OM', 'category': 'Deliverable',
             'aliases': ['Operators Manual', 'Operations Manual']},
            {'role_name': 'MM', 'category': 'Deliverable',
             'aliases': ['Maintenance Manual', 'Service Manual']},
            {'role_name': 'IPC', 'category': 'Deliverable',
             'aliases': ['Illustrated Parts Catalog', 'Parts Catalog']},
            {'role_name': 'IPB', 'category': 'Deliverable',
             'aliases': ['Illustrated Parts Breakdown', 'Parts Breakdown']},
            {'role_name': 'SIR', 'category': 'Deliverable',
             'aliases': ['System Installation Requirements', 'Installation Doc']},
            
            # --- CONTRACT/BUSINESS ---
            {'role_name': 'SOW', 'category': 'Deliverable',
             'aliases': ['Statement of Work', 'Scope of Work']},
            {'role_name': 'WBS', 'category': 'Deliverable',
             'aliases': ['Work Breakdown Structure']},
            {'role_name': 'CWBS', 'category': 'Deliverable',
             'aliases': ['Contract Work Breakdown Structure']},
            {'role_name': 'CDRL', 'category': 'Deliverable',
             'aliases': ['Contract Data Requirements List', 'Data Item']},
            {'role_name': 'DID', 'category': 'Deliverable',
             'aliases': ['Data Item Description']},
            {'role_name': 'CPR', 'category': 'Deliverable',
             'aliases': ['Contract Performance Report', 'Cost Report']},
            {'role_name': 'CFSR', 'category': 'Deliverable',
             'aliases': ['Contract Funds Status Report', 'Funds Report']},
            {'role_name': 'EAC', 'category': 'Deliverable',
             'aliases': ['Estimate at Completion', 'Cost Estimate']},
            {'role_name': 'IBR', 'category': 'Deliverable',
             'aliases': ['Integrated Baseline Review', 'Baseline Review']},
            
            # --- ANALYSIS REPORTS ---
            {'role_name': 'FMEA', 'category': 'Deliverable',
             'aliases': ['Failure Modes Effects Analysis', 'FMECA']},
            {'role_name': 'FTA', 'category': 'Deliverable',
             'aliases': ['Fault Tree Analysis', 'Fault Tree']},
            {'role_name': 'PHA', 'category': 'Deliverable',
             'aliases': ['Preliminary Hazard Analysis', 'Hazard Analysis']},
            {'role_name': 'SHA', 'category': 'Deliverable',
             'aliases': ['System Hazard Analysis', 'Safety Analysis']},
            {'role_name': 'SSA', 'category': 'Deliverable',
             'aliases': ['System Safety Assessment', 'Safety Assessment']},
            {'role_name': 'SSHA', 'category': 'Deliverable',
             'aliases': ['Subsystem Hazard Analysis', 'SubHA']},
            {'role_name': 'OSHA', 'category': 'Deliverable',
             'aliases': ['Operating System Hazard Analysis', 'Ops Hazard']},
            {'role_name': 'RCM', 'category': 'Deliverable',
             'aliases': ['Reliability Centered Maintenance', 'Reliability Analysis']},
            {'role_name': 'LSAR', 'category': 'Deliverable',
             'aliases': ['Logistics Support Analysis Record', 'LSA Record']},
            {'role_name': 'LCC', 'category': 'Deliverable',
             'aliases': ['Life Cycle Cost', 'Cost Analysis']},
            {'role_name': 'TLCSM', 'category': 'Deliverable',
             'aliases': ['Total Life Cycle Systems Management', 'Life Cycle Analysis']},
            {'role_name': 'TCR', 'category': 'Deliverable',
             'aliases': ['Trade Study Report', 'Trade Analysis']},
            {'role_name': 'EMI/EMC', 'category': 'Deliverable',
             'aliases': ['EMI EMC Analysis', 'Electromagnetic Analysis']},
            {'role_name': 'TIR', 'category': 'Deliverable',
             'aliases': ['Test Incident Report', 'Anomaly Report']},
            
            # --- TEST DOCUMENTS ---
            {'role_name': 'STD', 'category': 'Deliverable',
             'aliases': ['Software Test Description', 'Test Description']},
            {'role_name': 'STR', 'category': 'Deliverable',
             'aliases': ['Software Test Report', 'Test Report']},
            {'role_name': 'STPR', 'category': 'Deliverable',
             'aliases': ['Software Test Procedure', 'Test Procedure']},
            {'role_name': 'QTP', 'category': 'Deliverable',
             'aliases': ['Qualification Test Procedure', 'Qual Procedure']},
            {'role_name': 'QTR', 'category': 'Deliverable',
             'aliases': ['Qualification Test Report', 'Qual Report']},
            {'role_name': 'FAT', 'category': 'Deliverable',
             'aliases': ['Factory Acceptance Test', 'FAT Procedure']},
            {'role_name': 'SAT', 'category': 'Deliverable',
             'aliases': ['Site Acceptance Test', 'SAT Procedure']},
            {'role_name': 'VCR', 'category': 'Deliverable',
             'aliases': ['Verification Cross Reference', 'VCRD']},
            {'role_name': 'RTM', 'category': 'Deliverable',
             'aliases': ['Requirements Traceability Matrix', 'Trace Matrix']},
        ]
        
        # Combine roles and deliverables
        all_roles = builtin_roles + deliverables
        
        return self.import_roles_to_dictionary(
            all_roles, 
            source='builtin',
            created_by='system'
        )
    
    # ================================================================
    # SHAREABLE DICTIONARY METHODS
    # ================================================================
    
    def export_to_master_file(self, filepath: str = None, 
                              include_inactive: bool = False) -> Dict:
        """
        Export the dictionary to a shareable master file.
        
        This creates a JSON file that can be distributed to team members.
        They can place it in their app folder or a shared network location.
        
        Args:
            filepath: Output path (defaults to app_dir/role_dictionary_master.json)
            include_inactive: Include deactivated roles
        
        Returns:
            Dict with success status and file path
        """
        if filepath is None:
            paths = get_dictionary_paths()
            filepath = str(paths['master'])
        
        roles = self.get_role_dictionary(include_inactive)
        
        # Clean up for export (remove IDs, normalize dates)
        export_roles = []
        for role in roles:
            export_role = {
                'role_name': role['role_name'],
                'normalized_name': role['normalized_name'],
                'aliases': role.get('aliases', []),
                'category': role.get('category', 'Custom'),
                'description': role.get('description'),
                'is_deliverable': role.get('is_deliverable', False),
                'source': role.get('source', 'exported'),
                'source_document': role.get('source_document'),
                'notes': role.get('notes')
            }
            # Only include non-None values
            export_role = {k: v for k, v in export_role.items() if v is not None}
            export_roles.append(export_role)
        
        return export_dictionary_to_file(export_roles, filepath)
    
    def sync_from_master_file(self, filepath: str = None, 
                               merge_mode: str = 'add_new',
                               create_if_missing: bool = False) -> Dict:
        """
        Sync the dictionary from a master file.
        
        v2.9.3 B02: Added create_if_missing option to create master file from current dictionary.
        
        Args:
            filepath: Path to master file (auto-detected if None)
            merge_mode: How to handle conflicts
                - 'add_new': Only add roles not already present (default)
                - 'replace_all': Clear and replace entire dictionary
                - 'update_existing': Update existing roles from file
            create_if_missing: If True and no master file found, create one from current dictionary
        
        Returns:
            Dict with counts of added, updated, skipped
        """
        # Find master file
        if filepath is None:
            paths = get_dictionary_paths()
            # Check shared location first, then local
            if paths['shared'] and paths['shared'].exists():
                filepath = str(paths['shared'])
            elif paths['master'].exists():
                filepath = str(paths['master'])
            else:
                # v2.9.3 B02: Create master file if requested
                if create_if_missing:
                    try:
                        # Export current dictionary to master file
                        export_result = self.export_to_master_file(str(paths['master']))
                        if export_result.get('success'):
                            return {
                                'success': True,
                                'created_new': True,
                                'filepath': str(paths['master']),
                                'message': f"Created new master dictionary with {export_result.get('count', 0)} roles"
                            }
                        else:
                            return {
                                'success': False,
                                'error': f"Failed to create master file: {export_result.get('error', 'Unknown error')}"
                            }
                    except Exception as e:
                        return {
                            'success': False,
                            'error': f"Error creating master file: {str(e)}"
                        }
                else:
                    return {
                        'success': False,
                        'error': 'No master dictionary file found',
                        'can_create': True,
                        'suggested_path': str(paths['master'])
                    }
        
        result = load_dictionary_from_file(filepath)
        if not result['success']:
            return result
        
        roles = result['roles']
        metadata = result.get('metadata', {})
        
        results = {
            'added': 0,
            'updated': 0,
            'skipped': 0,
            'errors': [],
            'source_file': filepath,
            'source_metadata': metadata
        }
        
        if merge_mode == 'replace_all':
            # Clear existing and import all
            with self.connection() as (conn, cursor):
                cursor.execute('DELETE FROM role_dictionary')
            
            import_result = self.import_roles_to_dictionary(
                roles,
                source='master_sync',
                source_document=Path(filepath).name,
                created_by='sync'
            )
            results['added'] = import_result.get('added', 0)
            results['errors'] = import_result.get('errors', [])
        
        elif merge_mode == 'update_existing':
            # Update existing, add new
            for role in roles:
                role_name = role.get('role_name') or role.get('name')
                if not role_name:
                    continue
                
                normalized = role_name.lower().strip()
                
                # Check if exists
                with self.connection() as (conn, cursor):
                    cursor.execute(
                        'SELECT id FROM role_dictionary WHERE normalized_name = ?',
                        (normalized,)
                    )
                    existing = cursor.fetchone()
                
                if existing:
                    # Update
                    update_result = self.update_role_in_dictionary(
                        existing[0],
                        updated_by='sync',
                        category=role.get('category'),
                        aliases=role.get('aliases', []),
                        description=role.get('description'),
                        notes=role.get('notes')
                    )
                    if update_result.get('success'):
                        results['updated'] += 1
                else:
                    # Add new
                    add_result = self.add_role_to_dictionary(
                        role_name=role_name,
                        source='master_sync',
                        source_document=Path(filepath).name,
                        category=role.get('category', 'Imported'),
                        aliases=role.get('aliases', []),
                        description=role.get('description'),
                        is_deliverable=role.get('is_deliverable', False),
                        created_by='sync',
                        notes=role.get('notes')
                    )
                    if add_result.get('success'):
                        results['added'] += 1
        
        else:  # add_new (default)
            import_result = self.import_roles_to_dictionary(
                roles,
                source='master_sync',
                source_document=Path(filepath).name,
                created_by='sync'
            )
            results['added'] = import_result.get('added', 0)
            results['skipped'] = import_result.get('skipped', 0)
            results['errors'] = import_result.get('errors', [])
        
        results['success'] = True
        return results
    
    def get_dictionary_status(self) -> Dict:
        """
        Get status of dictionary files and sync state.
        
        Returns info about:
        - Local database role count
        - Master file existence and role count
        - Shared folder configuration
        - Last sync time
        """
        paths = get_dictionary_paths()
        
        status = {
            'database': {
                'path': self.db_path,
                'exists': Path(self.db_path).exists(),
                'role_count': 0
            },
            'master_file': {
                'path': str(paths['master']),
                'exists': paths['master'].exists(),
                'role_count': 0,
                'metadata': {}
            },
            'shared_folder': {
                'configured': paths['shared'] is not None,
                'path': str(paths['shared']) if paths['shared'] else None,
                'exists': paths['shared'].exists() if paths['shared'] else False,
                'role_count': 0
            }
        }
        
        # Count roles in database
        try:
            roles = self.get_role_dictionary(include_inactive=True)
            status['database']['role_count'] = len(roles)
        except Exception as e:
            logger.warning(f'Could not count dictionary roles for status: {e}')
        
        # Check master file
        if paths['master'].exists():
            result = load_dictionary_from_file(str(paths['master']))
            if result['success']:
                status['master_file']['role_count'] = result['count']
                status['master_file']['metadata'] = result.get('metadata', {})
        
        # Check shared folder
        if paths['shared'] and paths['shared'].exists():
            result = load_dictionary_from_file(str(paths['shared']))
            if result['success']:
                status['shared_folder']['role_count'] = result['count']
        
        return status
    
    # ================================================================
    # v2.9.1 D1: SYNC FROM HISTORY
    # ================================================================
    
    def sync_from_history(self, min_occurrences: int = 2, 
                          min_confidence: float = 0.7) -> Dict:
        """
        Sync dictionary from roles found in scan history.
        
        This is useful when no master file exists but you have
        historical scan data with extracted roles.
        
        v2.9.1 D1: Added as alternative to sync_from_master_file
        
        Args:
            min_occurrences: Minimum times role must appear across scans
            min_confidence: Minimum confidence score threshold
        
        Returns:
            Dict with success status and counts
        """
        results = {
            'success': False,
            'added': 0,
            'skipped': 0,
            'total_found': 0,
            'errors': []
        }
        
        try:
            with self.connection() as (conn, cursor):
                # Get all roles from role_occurrences with their counts
                cursor.execute('''
                    SELECT role_name, COUNT(*) as occurrence_count,
                           AVG(confidence) as avg_confidence,
                           GROUP_CONCAT(DISTINCT category) as categories
                    FROM role_occurrences
                    GROUP BY LOWER(role_name)
                    HAVING COUNT(*) >= ? AND AVG(confidence) >= ?
                    ORDER BY occurrence_count DESC
                ''', (min_occurrences, min_confidence))

                history_roles = cursor.fetchall()
            
            results['total_found'] = len(history_roles)
            
            if not history_roles:
                results['error'] = 'No roles found in scan history meeting criteria'
                return results
            
            # Convert to role dicts for import
            roles_to_import = []
            for role_name, count, avg_conf, categories in history_roles:
                # Determine best category
                category = 'From History'
                if categories:
                    cat_list = categories.split(',')
                    # Pick most specific category (not 'Unknown' or 'Other')
                    for cat in cat_list:
                        cat = cat.strip()
                        if cat and cat not in ['Unknown', 'Other', '']:
                            category = cat
                            break
                
                roles_to_import.append({
                    'role_name': role_name,
                    'category': category,
                    'source': 'history_sync',
                    'notes': f'Auto-imported from scan history. Found {count} times with {avg_conf:.0%} avg confidence.'
                })
            
            # Import to dictionary
            import_result = self.import_roles_to_dictionary(
                roles_to_import,
                source='history_sync',
                created_by='sync'
            )
            
            results['added'] = import_result.get('added', 0)
            results['skipped'] = import_result.get('skipped', 0)
            results['errors'] = import_result.get('errors', [])
            results['success'] = True
            
        except Exception as e:
            results['error'] = str(e)
            results['errors'].append(str(e))
        
        return results

    # =========================================================================
    # v4.7.0: Statement Forge data access methods
    # =========================================================================

    def save_scan_statements(self, scan_id, document_id, statements):
        """Persist extracted statements for a scan.

        Args:
            scan_id: ID of the scan record
            document_id: ID of the document
            statements: List of statement dicts from Statement Forge extraction

        Returns:
            Number of statements saved
        """
        import json as _json
        saved = 0
        with self.connection() as (conn, cursor):
            for idx, stmt in enumerate(statements):
                try:
                    cursor.execute('''
                        INSERT INTO scan_statements
                        (scan_id, document_id, statement_number, title, description,
                         level, role, directive, section, is_header, notes_json, position_index)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        scan_id,
                        document_id,
                        stmt.get('number', stmt.get('statement_number', '')),
                        stmt.get('title', ''),
                        stmt.get('description', stmt.get('text', '')),
                        stmt.get('level', 1),
                        stmt.get('role', ''),
                        stmt.get('directive', ''),
                        stmt.get('section', ''),
                        1 if stmt.get('is_header') else 0,
                        _json.dumps(stmt.get('notes', [])) if stmt.get('notes') else None,
                        stmt.get('position_index', idx)
                    ))
                    saved += 1
                except Exception as e:
                    _log(f"Failed to save statement {idx}: {e}", level='warning')
            conn.commit()
        _log(f"Saved {saved}/{len(statements)} statements for scan {scan_id}")
        return saved

    def get_scan_statements(self, scan_id):
        """Get all statements for a specific scan."""
        with self.connection() as (conn, cursor):
            cursor.execute('''
                SELECT ss.*, d.filename as document_name
                FROM scan_statements ss
                JOIN documents d ON ss.document_id = d.id
                WHERE ss.scan_id = ?
                ORDER BY ss.position_index
            ''', (scan_id,))
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_statement_history(self, document_id):
        """Get statement history across all scans for a document."""
        with self.connection() as (conn, cursor):
            cursor.execute('''
                SELECT s.id as scan_id, s.scan_time, s.score, s.grade,
                       COUNT(ss.id) as statement_count
                FROM scans s
                LEFT JOIN scan_statements ss ON ss.scan_id = s.id
                WHERE s.document_id = ?
                GROUP BY s.id
                ORDER BY s.scan_time DESC
            ''', (document_id,))
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_statement_trends(self, document_id, limit=10):
        """Get statement trend data for a document across scans."""
        with self.connection() as (conn, cursor):
            cursor.execute('''
                SELECT s.id as scan_id, s.scan_time,
                       COUNT(ss.id) as total_statements,
                       COUNT(CASE WHEN ss.directive = 'shall' THEN 1 END) as shall_count,
                       COUNT(CASE WHEN ss.directive = 'must' THEN 1 END) as must_count,
                       COUNT(CASE WHEN ss.directive = 'will' THEN 1 END) as will_count,
                       COUNT(CASE WHEN ss.directive = 'should' THEN 1 END) as should_count,
                       COUNT(CASE WHEN ss.directive = 'may' THEN 1 END) as may_count
                FROM scans s
                LEFT JOIN scan_statements ss ON ss.scan_id = s.id
                WHERE s.document_id = ?
                GROUP BY s.id
                ORDER BY s.scan_time DESC
                LIMIT ?
            ''', (document_id, limit))
            columns = [desc[0] for desc in cursor.description]
            return list(reversed([dict(zip(columns, row)) for row in cursor.fetchall()]))

    def compare_scan_statements(self, scan_id_1, scan_id_2):
        """Compare statements between two scans for diff view.

        Returns dict with statements_1 (newer), removed, and modified lists.
        Each statement in statements_1 gets a _diff_status field:
        'unchanged', 'added', 'modified_new'.
        """
        stmts_1 = self.get_scan_statements(scan_id_1)
        stmts_2 = self.get_scan_statements(scan_id_2)

        # Build fingerprint maps for comparison
        fp_map_2 = {}
        for s in stmts_2:
            fp = s.get('fingerprint', '')
            if fp:
                fp_map_2[fp] = s

        # Description-based fallback map
        desc_map_2 = {}
        for s in stmts_2:
            desc = (s.get('description') or '').strip().lower()
            if desc:
                desc_map_2[desc] = s

        matched_2_ids = set()
        modified = []

        for s in stmts_1:
            fp = s.get('fingerprint', '')
            desc = (s.get('description') or '').strip().lower()

            # Try fingerprint match first
            old = fp_map_2.get(fp) if fp else None
            if not old and desc:
                old = desc_map_2.get(desc)

            if old:
                matched_2_ids.add(old['id'])
                # Check if fields changed
                changed = False
                for field in ('directive', 'role', 'level', 'title'):
                    if str(s.get(field, '') or '') != str(old.get(field, '') or ''):
                        changed = True
                        break
                if changed:
                    s['_diff_status'] = 'modified_new'
                    modified.append({'old': old, 'new': s})
                else:
                    s['_diff_status'] = 'unchanged'
            else:
                s['_diff_status'] = 'added'

        # Find removed statements (in scan 2 but not matched)
        removed = []
        for s in stmts_2:
            if s['id'] not in matched_2_ids:
                s['_diff_status'] = 'removed'
                removed.append(s)

        return {
            'statements_1': stmts_1,
            'removed': removed,
            'modified': modified,
            'scan_id_1': scan_id_1,
            'scan_id_2': scan_id_2,
            'summary': {
                'total_newer': len(stmts_1),
                'total_older': len(stmts_2),
                'added': sum(1 for s in stmts_1 if s.get('_diff_status') == 'added'),
                'removed': len(removed),
                'modified': len(modified),
                'unchanged': sum(1 for s in stmts_1 if s.get('_diff_status') == 'unchanged'),
            }
        }

    def update_scan_statement(self, statement_id, updates):
        """Update a single scan statement's fields.

        Allowed fields: directive, role, level, title, description,
        review_status, confirmed, notes_json.
        """
        allowed = {'directive', 'role', 'level', 'title', 'description',
                    'review_status', 'confirmed', 'notes_json'}
        filtered = {k: v for k, v in updates.items() if k in allowed}
        if not filtered:
            return False

        set_clause = ', '.join(f'{k} = ?' for k in filtered)
        values = list(filtered.values()) + [statement_id]

        with self.connection() as (conn, cursor):
            cursor.execute(
                f'UPDATE scan_statements SET {set_clause} WHERE id = ?',
                values
            )
            return cursor.rowcount > 0


# Graph cache for performance
_graph_cache = {}
_graph_cache_max_age = 300  # 5 minutes

def get_cached_graph(session_id: str, file_hash: str, db: 'ScanHistoryDB', 
                     max_nodes: int = 100, min_weight: int = 1) -> Dict:
    """Get graph data with caching based on session and file hash."""
    import time
    
    cache_key = f"{session_id}:{file_hash}:{max_nodes}:{min_weight}"
    now = time.time()
    
    if cache_key in _graph_cache:
        cached_time, cached_data = _graph_cache[cache_key]
        if now - cached_time < _graph_cache_max_age:
            return cached_data
    
    # Generate fresh data
    data = db.get_role_graph_data(max_nodes, min_weight)
    _graph_cache[cache_key] = (now, data)
    
    # Cleanup old cache entries
    expired_keys = [k for k, (t, _) in _graph_cache.items() if now - t > _graph_cache_max_age * 2]
    for k in expired_keys:
        del _graph_cache[k]
    
    return data


# Singleton instance
_db_instance = None

def get_scan_history_db() -> ScanHistoryDB:
    """Get singleton instance of scan history database."""
    global _db_instance
    if _db_instance is None:
        _db_instance = ScanHistoryDB()
    return _db_instance
