"""
Statement Forge Models
======================
Data classes for statement extraction and representation.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum
import uuid


class DocumentType(Enum):
    """Document type enumeration."""
    PROCEDURES = "procedures"
    REQUIREMENTS = "requirements"
    WORK_INSTRUCTION = "work_instruction"
    UNKNOWN = "unknown"


class DirectiveType(Enum):
    """Directive word types for requirements."""
    SHALL = "shall"
    MUST = "must"
    WILL = "will"
    SHOULD = "should"
    MAY = "may"
    NONE = ""


@dataclass
class Statement:
    """
    Represents an extracted statement.

    Attributes:
        id: Unique identifier for the statement
        number: Display number (e.g., "4.1(i)" or "A.1")
        title: Short title/summary
        description: Full statement text
        level: Hierarchy level (1-6)
        section: Parent section identifier
        directive: Directive word (shall/must/etc) or empty
        role: Responsible party (for Work Instructions)
        step_number: Step number (for Work Instructions)
        notes: Associated notes
        source_line: Original line number in document
        is_header: True if this is a section header
        is_note: True if this is a NOTE
        children: Child statements (for tree structure)
        modified: True if user has edited this statement
        selected: True if selected in UI

        ENH-006 Source Context Fields:
        source_document: Name of the source document
        source_char_start: Character offset where statement begins
        source_char_end: Character offset where statement ends
        source_context_before: Text before the statement (for preview)
        source_context_after: Text after the statement (for preview)
        source_page: Page number if available
        source_section_title: Section/heading title where found
    """
    id: str = ""
    number: str = ""
    title: str = ""
    description: str = ""
    level: int = 1
    section: str = ""
    directive: str = ""
    role: str = ""
    step_number: str = ""
    notes: List[str] = field(default_factory=list)
    source_line: int = 0
    is_header: bool = False
    is_note: bool = False
    children: List['Statement'] = field(default_factory=list)
    modified: bool = False
    selected: bool = False
    # ENH-006: Source context fields
    source_document: str = ""
    source_char_start: int = -1
    source_char_end: int = -1
    source_context_before: str = ""
    source_context_after: str = ""
    source_page: int = 0
    source_section_title: str = ""
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'number': self.number,
            'title': self.title,
            'description': self.description,
            'level': self.level,
            'section': self.section,
            'directive': self.directive,
            'role': self.role,
            'step_number': self.step_number,
            'notes': self.notes,
            'source_line': self.source_line,
            'is_header': self.is_header,
            'is_note': self.is_note,
            'children': [c.to_dict() for c in self.children],
            'modified': self.modified,
            'selected': self.selected,
            # ENH-006: Source context fields
            'source_document': self.source_document,
            'source_char_start': self.source_char_start,
            'source_char_end': self.source_char_end,
            'source_context_before': self.source_context_before,
            'source_context_after': self.source_context_after,
            'source_page': self.source_page,
            'source_section_title': self.source_section_title
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Statement':
        """Create Statement from dictionary."""
        children_data = data.pop('children', [])
        stmt = cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        stmt.children = [cls.from_dict(c) for c in children_data]
        return stmt
    
    def clone(self) -> 'Statement':
        """Create a deep copy of this statement."""
        new_stmt = Statement(
            id=str(uuid.uuid4())[:8],  # New ID
            number=self.number,
            title=self.title,
            description=self.description,
            level=self.level,
            section=self.section,
            directive=self.directive,
            role=self.role,
            step_number=self.step_number,
            notes=self.notes.copy(),
            source_line=self.source_line,
            is_header=self.is_header,
            is_note=self.is_note,
            children=[c.clone() for c in self.children],
            modified=True,
            # ENH-006: Copy source context
            source_document=self.source_document,
            source_char_start=self.source_char_start,
            source_char_end=self.source_char_end,
            source_context_before=self.source_context_before,
            source_context_after=self.source_context_after,
            source_page=self.source_page,
            source_section_title=self.source_section_title
        )
        return new_stmt


@dataclass
class ExtractionResult:
    """Result of statement extraction."""
    statements: List[Statement] = field(default_factory=list)
    document_type: DocumentType = DocumentType.UNKNOWN
    source_filename: str = ""
    extraction_time: float = 0.0
    total_statements: int = 0
    directive_counts: dict = field(default_factory=dict)
    section_count: int = 0
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'statements': [s.to_dict() for s in self.statements],
            'document_type': self.document_type.value,
            'source_filename': self.source_filename,
            'extraction_time': self.extraction_time,
            'total_statements': self.total_statements,
            'directive_counts': self.directive_counts,
            'section_count': self.section_count,
            'error': self.error
        }


@dataclass
class UndoState:
    """State for undo/redo functionality."""
    statements: List[dict]  # Serialized statements
    description: str = ""
    timestamp: float = 0.0
