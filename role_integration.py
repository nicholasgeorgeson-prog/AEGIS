#!/usr/bin/env python3
"""
Role Extraction Integration Layer v1.0.0
=========================================
Integrates role extraction into AEGIS v2.4.0

This is a STANDALONE module that:
1. Does NOT modify any existing AEGIS code
2. Can be called from core.py or app.py with minimal additions
3. Handles all errors gracefully (never breaks existing functionality)
4. Returns data in a format compatible with existing review results

Usage:
    from role_integration import RoleIntegration
    role_module = RoleIntegration()
    
    # In review_document or after document extraction:
    role_result = role_module.extract_roles(filepath, extractor.full_text, extractor.paragraphs)

Author: Nicholas Georgeson
"""

import os
import json
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

__version__ = "2.7.0"  # v2.7.0: Extraction mode support (STRICT/DISCOVERY)
MODULE_VERSION = __version__

# Structured logging support
try:
    from config_logging import get_logger
    _logger = get_logger('role_integration')
except ImportError:
    _logger = None

def _log(message: str, level: str = 'info', **kwargs):
    """Internal logging helper with fallback to print."""
    if _logger:
        getattr(_logger, level)(message, **kwargs)
    elif level in ('warning', 'error', 'critical'):
        print(f"[RoleIntegration] {level.upper()}: {message}")


@dataclass
class RoleIssue:
    """Review issue for role-related findings (compatible with ReviewIssue format)."""
    category: str
    severity: str
    message: str
    paragraph_index: int = 0
    paragraph_text: str = ""
    flagged_text: str = ""
    suggestion: str = ""
    start_offset: int = 0
    end_offset: int = 0
    
    def to_dict(self) -> dict:
        return asdict(self)


class RoleIntegration:
    """
    Wrapper class that integrates role extraction with AEGIS.
    
    Features:
    - Extract roles from document text
    - Store in shared database (optional)
    - Check for duplicate/similar roles
    - Generate role-related review issues
    - Export for external visualization tools
    """
    
    def __init__(self, database_path: Optional[str] = None, enabled: bool = True,
                 use_docling: bool = True, docling_artifacts_path: Optional[str] = None,
                 extraction_mode: str = "discovery"):
        """
        Initialize the role integration module.

        Args:
            database_path: Optional path to shared role database JSON file
            enabled: Whether role extraction is enabled (can be toggled)
            use_docling: Whether to use Docling for document extraction (v2.6.0)
            docling_artifacts_path: Path to Docling models for air-gapped (v2.6.0)
            extraction_mode: "discovery" (default) or "strict"
                             - discovery: Pattern-based extraction, may have false positives
                             - strict: Whitelist-only, 100% accuracy guarantee
        """
        self.enabled = enabled
        self.database_path = database_path
        self.use_docling = use_docling
        self.docling_artifacts_path = docling_artifacts_path
        self.extraction_mode = extraction_mode.lower()
        self._extractor = None
        self._database = None
        self._consolidation = None
        self._table_processor = None  # v3.0.86: Table extraction
        self._docling_extractor = None  # v2.6.0: Docling extraction
        self._load_modules()

    def _load_modules(self):
        """Lazy load role extraction modules (doesn't fail if not present)."""
        if not self.enabled:
            return

        # Try to import role extraction modules
        try:
            from role_extractor_v3 import RoleExtractor, ExtractionMode
            # v2.7.0: Support extraction mode
            mode = ExtractionMode.STRICT if self.extraction_mode == "strict" else ExtractionMode.DISCOVERY
            self._extractor = RoleExtractor(extraction_mode=mode)
            _log(f"Loaded RoleExtractor v3 in {self.extraction_mode.upper()} mode")
        except ImportError as e:
            _log(f"RoleExtractor not available: {e}", level='debug')
            self._extractor = None
        
        # v2.6.0: Try to load Docling extractor (advanced document parsing)
        if self.use_docling:
            try:
                from docling_extractor import DoclingExtractor
                self._docling_extractor = DoclingExtractor(
                    artifacts_path=self.docling_artifacts_path,
                    fallback_to_legacy=True
                )
                if self._docling_extractor.is_available:
                    _log(f"Loaded DoclingExtractor (backend: {self._docling_extractor.backend_name})")
                else:
                    _log("DoclingExtractor loaded but using legacy fallback", level='debug')
            except ImportError as e:
                _log(f"DoclingExtractor not available: {e}", level='debug')
                self._docling_extractor = None
        
        # v3.0.86: Try to import table processor (for PDF/DOCX table extraction)
        try:
            from table_processor import TableProcessor
            self._table_processor = TableProcessor()
            _log("Loaded TableProcessor for PDF/DOCX table extraction")
        except ImportError as e:
            _log(f"TableProcessor not available: {e}", level='debug')
            self._table_processor = None
        
        # Try to import database (optional)
        if self.database_path:
            try:
                from role_management_studio_v3 import RoleDatabase, StudioSettings
                settings = StudioSettings()
                settings.database_path = self.database_path
                self._database = RoleDatabase(settings)
                _log(f"Loaded RoleDatabase: {self.database_path}")
            except ImportError as e:
                _log(f"RoleDatabase not available: {e}", level='debug')
                self._database = None
        
        # Try to import consolidation engine (optional)
        try:
            from role_consolidation_engine import check_role_similarity
            self._consolidation = check_role_similarity
            _log("Loaded consolidation engine")
        except ImportError as e:
            _log(f"Consolidation engine not available: {e}", level='debug')
            self._consolidation = None
    
    def is_available(self) -> bool:
        """Check if role extraction is available."""
        return self.enabled and self._extractor is not None

    def set_extraction_mode(self, mode: str) -> bool:
        """
        v2.7.0: Switch extraction mode at runtime.

        Args:
            mode: "discovery" or "strict"

        Returns:
            True if mode was changed, False if invalid mode or failed
        """
        mode = mode.lower()
        if mode not in ("discovery", "strict"):
            _log(f"Invalid extraction mode: {mode}", level='warning')
            return False

        if mode == self.extraction_mode:
            return True  # Already in this mode

        self.extraction_mode = mode
        # Reload extractor with new mode
        try:
            from role_extractor_v3 import RoleExtractor, ExtractionMode
            extraction_mode = ExtractionMode.STRICT if mode == "strict" else ExtractionMode.DISCOVERY
            self._extractor = RoleExtractor(extraction_mode=extraction_mode)
            _log(f"Switched to {mode.upper()} extraction mode")
            return True
        except ImportError as e:
            _log(f"Failed to reload extractor: {e}", level='error')
            return False

    def get_extraction_mode(self) -> str:
        """Get current extraction mode."""
        return self.extraction_mode

    @property
    def docling_available(self) -> bool:
        """Check if Docling extraction is available (v2.6.0)."""
        return (self._docling_extractor is not None and 
                self._docling_extractor.is_available)
    
    @property
    def extraction_backend(self) -> str:
        """Return the active extraction backend name (v2.6.0)."""
        if self._docling_extractor:
            return self._docling_extractor.backend_name
        return "legacy"
    
    def extract_from_file(self, filepath: str, 
                          enable_table_role_boost: bool = True,
                          table_role_confidence_boost: float = 0.2) -> Dict[str, Any]:
        """
        Extract roles directly from a document file using Docling (v2.6.0).
        
        This method uses Docling's advanced document parsing when available,
        with fallback to legacy extraction. It handles the full pipeline:
        1. Document parsing (via Docling or legacy)
        2. Text extraction with structure preservation
        3. Table extraction and processing
        4. Role extraction from all content
        5. Table-based role confidence boosting
        
        Args:
            filepath: Path to the document file
            enable_table_role_boost: Boost confidence for roles found in tables
            table_role_confidence_boost: Amount to boost confidence (default 0.2)
            
        Returns:
            Dictionary with extraction results including roles, tables, and metadata
        """
        result = {
            'success': False,
            'filepath': filepath,
            'extraction_backend': 'unknown',
            'full_text': '',
            'paragraphs': [],
            'tables': [],
            'sections': [],
            'roles': {},
            'entities': {'roles': [], 'deliverables': [], 'unknown': []},
            'issues': [],
            'metadata': {},
            'docling_enhanced': False,  # v2.6.0: Whether Docling was used
            'error': None
        }
        
        try:
            # Use Docling extractor if available
            if self._docling_extractor:
                doc_result = self._docling_extractor.extract(filepath)
                result['extraction_backend'] = doc_result.backend_used
                result['docling_enhanced'] = (doc_result.backend_used == 'docling')
                result['full_text'] = doc_result.full_text
                
                # Get paragraphs in the format expected by role extractor
                # Docling provides ExtractedParagraph objects with rich metadata
                result['paragraphs'] = doc_result.get_paragraphs_for_roles()
                
                # Get tables with full structure
                result['tables'] = [t.to_dict() for t in doc_result.tables]
                
                # Get sections for context
                result['sections'] = [s.to_dict() for s in doc_result.sections]
                
                # Build comprehensive metadata
                result['metadata'] = {
                    'page_count': doc_result.page_count,
                    'word_count': doc_result.word_count,
                    'char_count': doc_result.char_count,
                    'table_count': len(doc_result.tables),
                    'section_count': len(doc_result.sections),
                    'paragraph_count': len(doc_result.paragraphs),
                    'extraction_time_ms': doc_result.extraction_time_ms,
                    'warnings': doc_result.warnings,
                    'docling_version': doc_result.docling_version,
                    'models_used': doc_result.models_used,
                    'offline_mode': doc_result.offline_mode
                }
                
                # === MAXIMIZE DOCLING: Extract roles from tables specifically ===
                table_role_names = set()
                if enable_table_role_boost and doc_result.tables:
                    table_role_names = self._extract_roles_from_tables(doc_result.tables)
                    _log(f"Docling: Found {len(table_role_names)} potential roles in tables")
                
                # Now extract roles from the full parsed content
                if self._extractor and result['full_text']:
                    role_result = self.extract_roles(
                        filepath=filepath,
                        full_text=result['full_text'],
                        paragraphs=result['paragraphs'],
                        store_in_database=True
                    )
                    result['roles'] = role_result.get('roles', {})
                    result['entities'] = role_result.get('entities', result['entities'])
                    result['issues'] = role_result.get('issues', [])
                    result['success'] = role_result.get('success', False)
                    
                    # === MAXIMIZE DOCLING: Boost confidence for table-sourced roles ===
                    if enable_table_role_boost and table_role_names:
                        boosted_count = 0
                        for role_name, role_data in result['roles'].items():
                            # Check if this role (or variant) was found in a table
                            role_lower = role_name.lower()
                            for table_role in table_role_names:
                                if (table_role.lower() == role_lower or 
                                    table_role.lower() in role_lower or
                                    role_lower in table_role.lower()):
                                    # Boost confidence
                                    old_conf = role_data.get('confidence', 0.5)
                                    new_conf = min(0.99, old_conf + table_role_confidence_boost)
                                    role_data['confidence'] = new_conf
                                    role_data['found_in_table'] = True
                                    role_data['table_boosted'] = True
                                    boosted_count += 1
                                    break
                        
                        if boosted_count > 0:
                            _log(f"Docling: Boosted confidence for {boosted_count} table-sourced roles")
                else:
                    result['success'] = True  # Document extracted, just no role extraction
                    
            else:
                # Fall back to file-based extraction
                result['extraction_backend'] = 'legacy'
                result['docling_enhanced'] = False
                ext = Path(filepath).suffix.lower()
                
                if ext == '.pdf':
                    all_roles = self._extractor.extract_from_pdf(filepath)
                elif ext in ('.docx', '.doc'):
                    all_roles = self._extractor.extract_from_docx(filepath)
                else:
                    # Try as text
                    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                        text = f.read()
                    all_roles = self._extractor.extract_from_text(text, filepath)
                
                # Convert to result format
                for role_name, role_data in all_roles.items():
                    result['roles'][role_name] = role_data.to_dict() if hasattr(role_data, 'to_dict') else role_data
                
                result['success'] = True
                
        except Exception as e:
            _log(f"File extraction error: {e}", level='error')
            result['error'] = str(e)
        
        return result
    
    def _extract_roles_from_tables(self, tables) -> set:
        """
        Extract potential role names from table structures.
        
        Docling provides high-quality table extraction. This method
        looks for roles in:
        - Table headers (column names like "Role", "Responsible Party")
        - First column (often contains role names in RACI matrices)
        - Cells containing role-like patterns
        
        Args:
            tables: List of ExtractedTable objects from Docling
            
        Returns:
            Set of potential role name strings
        """
        role_names = set()
        
        # Role-indicator column headers
        role_headers = {
            'role', 'roles', 'responsibility', 'responsibilities', 
            'responsible', 'accountable', 'owner', 'assignee',
            'party', 'stakeholder', 'position', 'title', 'function'
        }
        
        for table in tables:
            # Handle both dict and object formats
            if isinstance(table, dict):
                headers = table.get('headers', [])
                rows = table.get('rows', [])
            else:
                headers = table.headers if hasattr(table, 'headers') else []
                rows = table.rows if hasattr(table, 'rows') else []
            
            # Find which column(s) likely contain roles
            role_columns = []
            for i, header in enumerate(headers):
                header_lower = header.lower().strip() if header else ''
                if any(rh in header_lower for rh in role_headers):
                    role_columns.append(i)
            
            # If no obvious role column, check first column (common in RACI)
            if not role_columns and headers:
                first_header = headers[0].lower().strip() if headers[0] else ''
                # First column often has roles even without "role" header
                if first_header in ('', 'task', 'activity', 'item', 'function'):
                    pass  # Skip - probably task list
                else:
                    role_columns.append(0)  # First column might be roles
            
            # Extract values from role columns
            for row in rows:
                for col_idx in role_columns:
                    if col_idx < len(row):
                        cell_value = row[col_idx]
                        if cell_value and isinstance(cell_value, str):
                            cell_value = cell_value.strip()
                            # Basic validation - looks like a role
                            if (2 < len(cell_value) < 100 and 
                                not cell_value.isdigit() and
                                not cell_value.startswith(('http', 'www.'))):
                                role_names.add(cell_value)
            
            # Also check for RACI-style headers (R, A, C, I columns)
            # The cell values under these might contain role names
            raci_columns = []
            for i, header in enumerate(headers):
                if header and header.strip().upper() in ('R', 'A', 'C', 'I', 'RACI'):
                    raci_columns.append(i)
            
            # Values in RACI columns are often abbreviations/role names
            for row in rows:
                for col_idx in raci_columns:
                    if col_idx < len(row):
                        cell_value = row[col_idx]
                        if cell_value and isinstance(cell_value, str):
                            cell_value = cell_value.strip()
                            if cell_value and len(cell_value) > 1:
                                role_names.add(cell_value)
        
        return role_names
    
    def extract_roles(self, 
                      filepath: str,
                      full_text: str,
                      paragraphs: List[Tuple[int, str]],
                      store_in_database: bool = True) -> Dict[str, Any]:
        """
        Extract roles from document text.
        
        Args:
            filepath: Path to the source document
            full_text: Full document text
            paragraphs: List of (index, text) tuples
            store_in_database: Whether to store results in database
        
        Returns:
            Dictionary with role extraction results:
            {
                'success': bool,
                'roles_found': int,
                'roles': {...},  # Role name -> ExtractedRole data (all entities)
                'entities': {    # v3.0.12: Separated by kind
                    'roles': [...],        # kind === 'role' only
                    'deliverables': [...]  # kind === 'deliverable' only
                },
                'issues': [...],  # Role-related review issues
                'duplicates_detected': int,
                'error': str or None
            }
        """
        result = {
            'success': False,
            'roles_found': 0,
            'roles': {},
            'entities': {  # v3.0.12: Separated entity lists
                'roles': [],
                'deliverables': [],
                'unknown': []  # v3.0.12b: Unknowns separate for review
            },
            'issues': [],
            'duplicates_detected': 0,
            'tables_found': 0,  # v3.0.86: Table extraction stats
            'roles_from_tables': 0,  # v3.0.86: Roles found in tables
            'error': None
        }
        
        if not self.is_available():
            result['error'] = "Role extraction module not available"
            return result
        
        # v3.0.86: Extract roles from tables first (high confidence)
        table_roles = set()
        if self._table_processor and filepath:
            try:
                ext = Path(filepath).suffix.lower()
                if ext in ('.pdf', '.docx', '.doc'):
                    table_result = self._table_processor.process_document(filepath)
                    if table_result.get('success'):
                        result['tables_found'] = len(table_result.get('tables', []))
                        table_roles = set(table_result.get('roles_from_tables', []))
                        result['roles_from_tables'] = len(table_roles)
                        _log(f"Found {len(table_roles)} roles in {result['tables_found']} tables")
            except Exception as e:
                _log(f"Table extraction failed (continuing with text): {e}", level='warning')
        
        try:
            # Extract roles using the core extractor
            extracted = self._extractor.extract_from_text(full_text, filepath)
            
            result['success'] = True
            result['roles_found'] = len(extracted)
            
            # Convert to serializable format
            for role_name, role_data in extracted.items():
                # Get sample context sentences (up to 3)
                sample_contexts = []
                if hasattr(role_data, 'occurrences') and role_data.occurrences:
                    seen_contexts = set()
                    for occ in role_data.occurrences[:10]:  # Check first 10 occurrences
                        if hasattr(occ, 'context') and occ.context:
                            ctx = occ.context.strip()
                            # Truncate long contexts
                            if len(ctx) > 150:
                                ctx = ctx[:147] + '...'
                            # Avoid duplicates
                            ctx_key = ctx[:50].lower()
                            if ctx_key not in seen_contexts:
                                seen_contexts.add(ctx_key)
                                sample_contexts.append(ctx)
                                if len(sample_contexts) >= 3:
                                    break
                
                # v3.0.12: Include entity classification
                entity_kind = 'unknown'
                kind_confidence = 0.0
                kind_reason = ''
                if hasattr(role_data, 'entity_kind'):
                    entity_kind = role_data.entity_kind.value if hasattr(role_data.entity_kind, 'value') else str(role_data.entity_kind)
                    kind_confidence = getattr(role_data, 'kind_confidence', 0.0)
                    kind_reason = getattr(role_data, 'kind_reason', '')
                
                serialized_entry = {
                    'canonical_name': role_data.canonical_name,
                    'entity_kind': entity_kind,  # v3.0.12: Added
                    'kind_confidence': kind_confidence,  # v3.0.12: Added
                    'kind_reason': kind_reason,  # v3.0.12: Added
                    'frequency': role_data.frequency,
                    'confidence': role_data.avg_confidence,
                    'responsibilities': list(role_data.responsibilities),
                    'action_types': dict(role_data.action_types),
                    'variants': list(role_data.variants),
                    'occurrence_count': len(role_data.occurrences),
                    'sample_contexts': sample_contexts,
                    'found_in_table': False,  # v3.0.86: Table extraction flag
                    # v3.0.107: Add source document for filtering
                    'source_documents': [Path(filepath).name] if filepath else []
                }
                
                # v3.0.86: Boost confidence if role was found in tables
                if table_roles:
                    for table_role in table_roles:
                        if table_role.lower() == role_name.lower() or table_role.lower() in role_name.lower():
                            serialized_entry['confidence'] = min(0.99, serialized_entry['confidence'] + 0.15)
                            serialized_entry['found_in_table'] = True
                            break
                
                # Store in main roles dict (backward compat)
                result['roles'][role_name] = serialized_entry
                
                # v3.0.12: Also add to separated entity lists
                # v3.0.12b: unknowns excluded from roles export per guidance
                if entity_kind == 'role':
                    result['entities']['roles'].append(serialized_entry)
                elif entity_kind == 'deliverable':
                    result['entities']['deliverables'].append(serialized_entry)
                else:
                    # Unknown goes to separate list for manual review
                    serialized_entry['needs_review'] = True
                    result['entities']['unknown'].append(serialized_entry)
            
            # Generate review issues for role-related findings
            result['issues'] = self._generate_role_issues(extracted, paragraphs)
            
            # Check for duplicate roles if consolidation is available
            if self._consolidation and len(extracted) > 1:
                duplicates = self._check_for_duplicates(list(extracted.keys()))
                result['duplicates_detected'] = len(duplicates)
                
                # Add duplicate issues
                for dup in duplicates:
                    result['issues'].append(RoleIssue(
                        category='Roles',
                        severity='Low',
                        message=f"Potential duplicate roles: '{dup['role1']}' and '{dup['role2']}' ({dup['similarity']:.0%} similar)",
                        suggestion=f"Consider standardizing to one role name",
                        flagged_text=f"{dup['role1']} / {dup['role2']}"
                    ).to_dict())
            
            # Store in database if enabled
            if store_in_database and self._database:
                self._store_in_database(filepath, extracted)
        
        except Exception as e:
            result['error'] = str(e)
            _log(f"Error extracting roles: {e}", level='error')
        
        return result
    
    def _generate_role_issues(self, 
                              extracted: Dict,
                              paragraphs: List[Tuple[int, str]]) -> List[Dict]:
        """Generate review issues for role-related findings."""
        issues = []
        
        for role_name, role_data in extracted.items():
            # Issue: Role with no responsibilities found
            if not role_data.responsibilities:
                # Find first occurrence paragraph
                para_idx = 0
                para_text = ""
                if role_data.occurrences:
                    # Use context from first occurrence since RoleOccurrence doesn't have paragraph_index
                    para_text = role_data.occurrences[0].context[:100] if role_data.occurrences[0].context else ""
                    # Try to find the paragraph that contains this context
                    for idx, text in paragraphs:
                        if role_data.occurrences[0].context and role_data.occurrences[0].context[:50] in text:
                            para_idx = idx
                            break
                
                issues.append(RoleIssue(
                    category='Roles',
                    severity='Info',
                    message=f"Role '{role_name}' mentioned but no specific responsibilities identified",
                    paragraph_index=para_idx,
                    paragraph_text=para_text,
                    flagged_text=role_name,
                    suggestion="Consider adding explicit responsibilities for this role"
                ).to_dict())
            
            # Issue: Low confidence role extraction
            if role_data.avg_confidence < 0.5:
                issues.append(RoleIssue(
                    category='Roles',
                    severity='Info',
                    message=f"Role '{role_name}' detected with low confidence ({role_data.avg_confidence:.0%})",
                    flagged_text=role_name,
                    suggestion="Verify this is an actual role reference"
                ).to_dict())
        
        return issues
    
    def _check_for_duplicates(self, role_names: List[str]) -> List[Dict]:
        """Check for duplicate/similar role names."""
        duplicates = []
        checked_pairs = set()
        
        for i, name1 in enumerate(role_names):
            for name2 in role_names[i+1:]:
                pair_key = tuple(sorted([name1, name2]))
                if pair_key in checked_pairs:
                    continue
                checked_pairs.add(pair_key)
                
                try:
                    result = self._consolidation(name1, name2)
                    if result.get('are_similar', False):
                        duplicates.append({
                            'role1': name1,
                            'role2': name2,
                            'similarity': result.get('overall_similarity', 0),
                            'should_merge': result.get('should_merge', False)
                        })
                except Exception:
                    pass
        
        return duplicates
    
    def _store_in_database(self, filepath: str, extracted: Dict):
        """Store extracted roles in the database."""
        if not self._database:
            return
        
        try:
            # Register document
            from role_management_studio_v3 import SourceDocument, StandardRole
            
            doc = SourceDocument(
                id=os.path.basename(filepath),
                name=os.path.basename(filepath),
                path=filepath,
                doc_type="Technical",
                status="active",
                upload_date=datetime.now().isoformat(),
                processed_date=datetime.now().isoformat(),
                version="1.0",
                notes="Processed via AEGIS"
            )
            self._database.add_document(doc)
            
            # Add roles
            for role_name, role_data in extracted.items():
                role = StandardRole(
                    id=f"role_{hash(role_name) % 100000:05d}",
                    canonical_name=role_data.canonical_name,
                    category=self._categorize_role(role_name),
                    subcategory="",
                    description="",
                    typical_responsibilities=list(role_data.responsibilities)[:10],
                    typical_actions=list(role_data.action_types.keys())[:5],
                    aliases=list(role_data.variants),
                    reports_to=[],
                    coordinates_with=[],
                    supervises=[],
                    required_skills=[],
                    certifications=[],
                    created_date=datetime.now().isoformat(),
                    modified_date=datetime.now().isoformat(),
                    usage_count=role_data.frequency,
                    confidence_avg=role_data.avg_confidence,
                    is_approved=False,
                    approved_by="",
                    notes=f"Extracted from {os.path.basename(filepath)}",
                    last_modified_by="AEGIS",
                    source_document_ids=[doc.id],
                    active_document_count=1,
                    custom_fields={}
                )
                self._database.add_role(role)
            
            _log(f"Stored {len(extracted)} roles from {os.path.basename(filepath)}")
        
        except Exception as e:
            _log(f"Error storing in database: {e}", level='error')
    
    def _categorize_role(self, role_name: str) -> str:
        """Categorize a role based on its name."""
        name_lower = role_name.lower()
        
        if any(x in name_lower for x in ['engineer', 'developer', 'architect', 'designer']):
            return "Engineering"
        elif any(x in name_lower for x in ['manager', 'director', 'lead', 'supervisor', 'chief']):
            return "Management"
        elif any(x in name_lower for x in ['quality', 'qa', 'qc', 'inspector', 'auditor']):
            return "Quality"
        elif any(x in name_lower for x in ['test', 'verification', 'validation']):
            return "Test"
        elif any(x in name_lower for x in ['safety', 'security', 'compliance']):
            return "Safety"
        elif any(x in name_lower for x in ['program', 'project', 'contract']):
            return "Program"
        elif any(x in name_lower for x in ['logistics', 'supply', 'procurement']):
            return "Logistics"
        else:
            return "Other"
    
    def get_role_summary(self, role_name: str) -> Optional[Dict]:
        """Get summary for a specific role from the database."""
        if not self._database:
            return None
        
        try:
            role = self._database.get_role_by_name(role_name)
            if role:
                return self._database.get_aggregated_role_data(role.id)
        except Exception as e:
            _log(f"Error getting role summary: {e}", level='error')
        
        return None
    
    def export_roles_for_visualization(self, filepath: str) -> bool:
        """
        Export all roles to JSON format for external visualization tool.
        
        Args:
            filepath: Output JSON file path
        
        Returns:
            True if successful, False otherwise
        """
        if not self._database:
            _log("No database available for export", level='warning')
            return False
        
        try:
            self._database.export_for_external_tool(filepath)
            _log(f"Exported roles to {filepath}")
            return True
        except Exception as e:
            _log(f"Export error: {e}", level='error')
            return False
    
    def generate_consolidation_report(self, format: str = "html") -> Optional[str]:
        """
        Generate a report of potential role consolidations.
        
        Args:
            format: "text", "markdown", or "html"
        
        Returns:
            Report string or None if not available
        """
        if not self._database:
            return None
        
        try:
            from role_consolidation_engine import RoleConsolidationEngine
            
            engine = RoleConsolidationEngine(self._database)
            candidates = engine.find_consolidation_candidates()
            return engine.generate_consolidation_report(candidates, format)
        except Exception as e:
            _log(f"Error generating report: {e}", level='error')
            return None


# =============================================================================
# STATEMENT FORGE INTEGRATION (v3.0.41)
# =============================================================================

    def map_statements_to_roles(
        self,
        statements: List[Dict],
        extracted_roles: Dict
    ) -> Dict[str, Any]:
        """
        Map Statement Forge statements to extracted roles.
        
        v3.0.41: Batch H - Statement Forge → Role Responsibilities mapping.
        
        This creates a bidirectional mapping:
        - role → list of statements that mention/relate to that role
        - statement → list of roles it mentions
        
        Args:
            statements: List of statement dicts from Statement Forge
                       (each has 'id', 'description', 'role', 'directive', etc.)
            extracted_roles: Dict from role extraction
                            {'roles': {role_name: {variants, responsibilities, ...}}}
        
        Returns:
            {
                'role_to_statements': {role_name: [statement_info, ...]},
                'statement_to_roles': {statement_id: [role_names]},
                'unmapped_statements': [statement_ids with no role match],
                'stats': {
                    'total_statements': N,
                    'mapped_statements': N,
                    'coverage_percent': N.N
                }
            }
        """
        if not self.is_available():
            return {
                'role_to_statements': {},
                'statement_to_roles': {},
                'unmapped_statements': [],
                'stats': {'total_statements': 0, 'mapped_statements': 0, 'coverage_percent': 0},
                'error': 'Role extraction module not available'
            }
        
        role_to_statements = {}
        statement_to_roles = {}
        unmapped_statements = []
        
        # Get role data
        roles_dict = extracted_roles.get('roles', {})
        if not roles_dict:
            _log("No roles available for mapping", level='warning')
            return {
                'role_to_statements': {},
                'statement_to_roles': {},
                'unmapped_statements': [s.get('id', '') for s in statements],
                'stats': {
                    'total_statements': len(statements),
                    'mapped_statements': 0,
                    'coverage_percent': 0
                }
            }
        
        # Build role name lookup (canonical + variants)
        role_lookup = {}  # lowercase name → canonical name
        for role_name, role_data in roles_dict.items():
            canonical = role_name.lower().strip()
            role_lookup[canonical] = role_name
            # Add variants
            for variant in role_data.get('variants', []):
                role_lookup[variant.lower().strip()] = role_name
        
        # Initialize role_to_statements
        for role_name in roles_dict.keys():
            role_to_statements[role_name] = []
        
        # Process each statement
        for stmt in statements:
            stmt_id = stmt.get('id', '')
            description = stmt.get('description', '')
            explicit_role = stmt.get('role', '')  # SF may have extracted a role
            directive = stmt.get('directive', '')
            number = stmt.get('number', '')
            
            found_roles = set()
            
            # 1. Check explicit role field from Statement Forge
            if explicit_role:
                explicit_lower = explicit_role.lower().strip()
                if explicit_lower in role_lookup:
                    found_roles.add(role_lookup[explicit_lower])
                else:
                    # Try partial match
                    for lookup_name, canonical in role_lookup.items():
                        if lookup_name in explicit_lower or explicit_lower in lookup_name:
                            found_roles.add(canonical)
                            break
            
            # 2. Search description for role mentions
            desc_lower = description.lower()
            for lookup_name, canonical in role_lookup.items():
                # Avoid very short matches (< 3 chars) causing false positives
                if len(lookup_name) >= 3 and lookup_name in desc_lower:
                    # Verify it's a word boundary match (not substring of another word)
                    import re
                    pattern = r'\b' + re.escape(lookup_name) + r'\b'
                    if re.search(pattern, desc_lower):
                        found_roles.add(canonical)
            
            # Record mapping
            if found_roles:
                statement_to_roles[stmt_id] = list(found_roles)
                stmt_info = {
                    'id': stmt_id,
                    'number': number,
                    'description': description[:200] + ('...' if len(description) > 200 else ''),
                    'directive': directive,
                    'full_description': description
                }
                for role_name in found_roles:
                    if role_name in role_to_statements:
                        role_to_statements[role_name].append(stmt_info)
            else:
                unmapped_statements.append(stmt_id)
        
        # Calculate stats
        total = len(statements)
        mapped = total - len(unmapped_statements)
        coverage = (mapped / total * 100) if total > 0 else 0
        
        _log(f"Statement-to-role mapping complete: {mapped}/{total} statements mapped ({coverage:.1f}%)")
        
        return {
            'role_to_statements': role_to_statements,
            'statement_to_roles': statement_to_roles,
            'unmapped_statements': unmapped_statements,
            'stats': {
                'total_statements': total,
                'mapped_statements': mapped,
                'coverage_percent': round(coverage, 1)
            }
        }


# =============================================================================
# CONVENIENCE FUNCTIONS (for direct use without instantiation)
# =============================================================================

_default_integration = None

def get_integration(database_path: Optional[str] = None) -> RoleIntegration:
    """Get or create a default RoleIntegration instance."""
    global _default_integration
    if _default_integration is None:
        _default_integration = RoleIntegration(database_path)
    return _default_integration


def extract_roles_from_document(filepath: str, full_text: str, paragraphs: List[Tuple[int, str]]) -> Dict:
    """
    Convenience function to extract roles without managing instance.
    
    Usage in core.py:
        from role_integration import extract_roles_from_document
        role_result = extract_roles_from_document(filepath, extractor.full_text, extractor.paragraphs)
    """
    return get_integration().extract_roles(filepath, full_text, paragraphs)


# =============================================================================
# CHECKER CLASS (for seamless integration with AEGIS checker system)
# =============================================================================

class RoleChecker:
    """
    Role checker that follows AEGIS's BaseChecker pattern.
    Can be added to core.py's checkers dict like any other checker.
    """
    
    CATEGORY = "Roles"
    SEVERITY_DEFAULT = "Info"
    
    def __init__(self, database_path: Optional[str] = None):
        self.integration = RoleIntegration(database_path)
        self.enabled = True
    
    def check(self, paragraphs: List[Tuple[int, str]], full_text: str = "",
              filepath: str = "", **kwargs) -> List[Dict]:
        """
        Check method compatible with AEGIS's checker interface.
        
        Returns list of issue dictionaries.
        """
        if not self.enabled or not self.integration.is_available():
            return []
        
        try:
            result = self.integration.extract_roles(filepath, full_text, paragraphs, store_in_database=False)
            return result.get('issues', [])
        except Exception as e:
            _log(f"RoleChecker error: {e}", level='error')
            return []
    
    def safe_check(self, **kwargs) -> List[Dict]:
        """Safe wrapper that catches all exceptions."""
        try:
            return self.check(**kwargs)
        except Exception as e:
            _log(f"RoleChecker safe check error: {e}", level='error')
            return []


# =============================================================================
# MAIN (for testing)
# =============================================================================

if __name__ == "__main__":
    print(f"Role Integration Module v{__version__}")
    print("=" * 50)
    
    integration = RoleIntegration()
    print(f"Available: {integration.is_available()}")
    
    # Test with sample text
    test_text = """
    The Systems Engineer shall review all design documents.
    The Quality Manager approves all test procedures.
    The Program Manager coordinates with all stakeholders.
    The Configuration Manager maintains the baseline.
    """
    
    if integration.is_available():
        result = integration.extract_roles("test.docx", test_text, [(0, test_text)])
        print(f"\nRoles found: {result['roles_found']}")
        for name, data in result['roles'].items():
            print(f"  - {name}: {data['frequency']} occurrences")
        print(f"\nIssues: {len(result['issues'])}")
        print(f"Duplicates detected: {result['duplicates_detected']}")
    else:
        print("\nRole extraction modules not installed.")
        print("To enable, copy these files to the AEGIS directory:")
        print("  - role_extractor_v3.py")
        print("  - role_management_studio_v3.py (optional)")
        print("  - role_consolidation_engine.py (optional)")
