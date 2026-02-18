#!/usr/bin/env python3
"""
Style Guide Presets for AEGIS
=========================================
Pre-configured checker settings for common technical writing style guides.

Supported Presets:
- microsoft: Microsoft Writing Style Guide
- google: Google Developer Documentation Style Guide
- plain_language: US Plain Language Guidelines
- asd_ste100: ASD Simplified Technical English
- government: US Government/Federal style
- aerospace: Aerospace/Defense technical documentation
- all_checks: Enable all available checkers
- minimal: Basic grammar and spelling only

Usage:
    from style_presets import get_preset, apply_preset, list_presets

    # Get preset configuration
    config = get_preset('microsoft')

    # Apply preset to review options
    options = apply_preset('google', custom_overrides={'check_passive_voice': False})
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import json
from pathlib import Path

try:
    from config_logging import get_logger
    _logger = get_logger('style_presets')
except ImportError:
    import logging
    _logger = logging.getLogger('style_presets')


@dataclass
class StylePreset:
    """Represents a style guide preset configuration."""
    name: str
    display_name: str
    description: str
    target_audience: str
    checkers: Dict[str, bool] = field(default_factory=dict)
    severity_overrides: Dict[str, str] = field(default_factory=dict)
    custom_rules: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'target_audience': self.target_audience,
            'checkers': self.checkers,
            'severity_overrides': self.severity_overrides,
            'custom_rules': self.custom_rules
        }


# =============================================================================
# PRESET DEFINITIONS
# =============================================================================

PRESETS: Dict[str, StylePreset] = {}

# -----------------------------------------------------------------------------
# Microsoft Writing Style Guide
# -----------------------------------------------------------------------------
PRESETS['microsoft'] = StylePreset(
    name='microsoft',
    display_name='Microsoft Style',
    description='Microsoft Writing Style Guide - Clear, friendly, and inclusive technical documentation',
    target_audience='Software developers and end users',
    checkers={
        # Core checks - enabled
        'check_spelling': True,
        'check_grammar': True,
        'check_punctuation': True,
        'check_capitalization': True,

        # Style - Microsoft preferences
        'check_passive_voice': True,  # Microsoft prefers active voice
        'check_contractions': False,  # Microsoft ALLOWS contractions (friendly tone)
        'check_contraction_consistency': True,  # But be consistent
        'check_second_person': True,  # "You" preferred over "the user"
        'check_future_tense': True,  # Present tense preferred
        'check_sentence_length': True,  # Short sentences

        # Clarity
        'check_wordy_phrases': True,
        'check_jargon': True,
        'check_nominalization': True,
        'check_weak_language': True,
        'check_hedging': True,

        # Accessibility
        'check_gender_language': True,  # Inclusive language
        'check_link_text_quality': True,  # Descriptive link text

        # Technical
        'check_acronyms': True,
        'check_acronym_first_use': True,
        'check_product_name_consistency': True,
        'check_code_formatting': True,

        # Disable for Microsoft style
        'check_latin_abbreviations': False,  # Microsoft style uses e.g., i.e.
        'check_oxford_comma': False,  # Microsoft doesn't require it
        'check_sentence_initial_conjunction': False,  # Allowed in modern MS style
    },
    severity_overrides={
        'passive_voice': 'warning',  # Not error, but flagged
        'contractions': 'info',  # Just informational
    },
    custom_rules={
        'max_sentence_length': 25,
        'preferred_tone': 'friendly',
        'allow_first_person': False,
    }
)

# -----------------------------------------------------------------------------
# Google Developer Documentation Style Guide
# -----------------------------------------------------------------------------
PRESETS['google'] = StylePreset(
    name='google',
    display_name='Google Style',
    description='Google Developer Documentation Style Guide - Clear, concise, and accessible',
    target_audience='Software developers',
    checkers={
        # Core checks
        'check_spelling': True,
        'check_grammar': True,
        'check_punctuation': True,
        'check_capitalization': True,

        # Style - Google preferences
        'check_passive_voice': True,  # Active voice strongly preferred
        'check_contractions': False,  # Google allows contractions
        'check_contraction_consistency': True,
        'check_second_person': True,  # "You" is standard
        'check_future_tense': True,  # Present tense preferred
        'check_sentence_length': True,

        # Clarity
        'check_wordy_phrases': True,
        'check_jargon': True,
        'check_nominalization': True,
        'check_weak_language': True,
        'check_directional_language': True,  # Avoid "above"/"below"
        'check_time_sensitive_language': True,  # Avoid "currently"

        # Accessibility & Inclusion
        'check_gender_language': True,
        'check_link_text_quality': True,

        # Technical
        'check_acronyms': True,
        'check_acronym_first_use': True,
        'check_product_name_consistency': True,
        'check_code_formatting': True,

        # Google-specific
        'check_oxford_comma': True,  # Google requires serial comma
        'check_latin_abbreviations': True,  # Avoid i.e., e.g.
        'check_sentence_initial_conjunction': False,  # Allowed
    },
    severity_overrides={
        'passive_voice': 'warning',
        'latin_abbreviations': 'warning',
    },
    custom_rules={
        'max_sentence_length': 26,
        'require_oxford_comma': True,
    }
)

# -----------------------------------------------------------------------------
# US Plain Language Guidelines
# -----------------------------------------------------------------------------
PRESETS['plain_language'] = StylePreset(
    name='plain_language',
    display_name='Plain Language',
    description='US Plain Language Guidelines (plainlanguage.gov) - Clear government communication',
    target_audience='General public',
    checkers={
        # Core checks
        'check_spelling': True,
        'check_grammar': True,
        'check_punctuation': True,
        'check_capitalization': True,

        # Readability - critical for plain language
        'check_sentence_length': True,
        'check_dale_chall': True,  # Readability scoring
        'check_spache': True,
        'check_ari': True,

        # Style
        'check_passive_voice': True,  # Active voice required
        'check_contractions': False,  # Contractions encouraged
        'check_second_person': True,  # Address reader directly
        'check_future_tense': True,

        # Clarity - maximum
        'check_wordy_phrases': True,
        'check_jargon': True,  # Critical - avoid jargon
        'check_nominalization': True,  # Use verbs, not nominalizations
        'check_weak_language': True,
        'check_hedging': True,
        'check_latin_abbreviations': True,  # Spell out

        # Accessibility
        'check_gender_language': True,
        'check_link_text_quality': True,

        # Structure
        'check_document_structure': True,
        'check_heading_case': True,
        'check_lists': True,
    },
    severity_overrides={
        'passive_voice': 'error',  # Strict in plain language
        'jargon': 'error',
        'wordy_phrases': 'warning',
    },
    custom_rules={
        'max_sentence_length': 20,  # Shorter sentences
        'target_grade_level': 8,  # 8th grade reading level
        'require_active_voice': True,
    }
)

# -----------------------------------------------------------------------------
# ASD-STE100 Simplified Technical English
# -----------------------------------------------------------------------------
PRESETS['asd_ste100'] = StylePreset(
    name='asd_ste100',
    display_name='ASD-STE100',
    description='Simplified Technical English for aerospace maintenance documentation',
    target_audience='Aircraft maintenance technicians',
    checkers={
        # Core checks
        'check_spelling': True,
        'check_grammar': True,
        'check_punctuation': True,
        'check_capitalization': True,

        # STE Requirements - STRICT
        'check_passive_voice': True,  # Active voice required
        'check_sentence_length': True,  # Max 20 words procedural, 25 descriptive
        'check_contractions': True,  # NO contractions in STE
        'check_future_tense': True,  # Present tense only

        # Vocabulary control
        'check_jargon': True,
        'check_wordy_phrases': True,
        'check_nominalization': True,
        'check_weak_language': True,

        # Procedural writing
        'check_imperative_mood': True,  # Required for procedures
        'check_numbered_list_sequence': True,

        # Technical
        'check_acronyms': True,
        'check_acronym_first_use': True,
        'check_product_name_consistency': True,

        # Compliance
        'check_mil_std_40051': True,
        'check_s1000d': True,

        # Disable
        'check_second_person': False,  # STE uses imperative, not "you"
        'check_oxford_comma': False,
    },
    severity_overrides={
        'passive_voice': 'error',
        'contractions': 'error',
        'sentence_length': 'error',
        'imperative_mood': 'error',
    },
    custom_rules={
        'max_sentence_length_procedural': 20,
        'max_sentence_length_descriptive': 25,
        'require_approved_words': True,
        'one_topic_per_sentence': True,
    }
)

# -----------------------------------------------------------------------------
# US Government / Federal Style
# -----------------------------------------------------------------------------
PRESETS['government'] = StylePreset(
    name='government',
    display_name='Government Style',
    description='US Federal Government technical documentation standards',
    target_audience='Government agencies and contractors',
    checkers={
        # Core checks
        'check_spelling': True,
        'check_grammar': True,
        'check_punctuation': True,
        'check_capitalization': True,

        # Style
        'check_passive_voice': True,
        'check_contractions': True,  # Formal - avoid contractions
        'check_sentence_length': True,
        'check_future_tense': True,

        # Clarity
        'check_wordy_phrases': True,
        'check_jargon': True,
        'check_nominalization': True,
        'check_weak_language': True,
        'check_hedging': True,

        # Requirements language
        'check_requirements_language': True,
        'check_testability': True,
        'check_atomicity': True,
        'check_escape_clauses': True,
        'check_tbd': True,

        # Compliance
        'check_mil_std_40051': True,

        # Structure
        'check_document_structure': True,
        'check_cross_references': True,
        'check_references': True,

        # Accessibility
        'check_gender_language': True,
    },
    severity_overrides={
        'requirements_language': 'error',
        'tbd': 'error',
        'escape_clauses': 'warning',
    },
    custom_rules={
        'require_shall_statements': True,
        'formal_tone': True,
    }
)

# -----------------------------------------------------------------------------
# Aerospace / Defense Documentation
# -----------------------------------------------------------------------------
PRESETS['aerospace'] = StylePreset(
    name='aerospace',
    display_name='Aerospace/Defense',
    description='Aerospace and defense technical documentation (MIL-STD, DO-178, AS9100)',
    target_audience='Engineers, technicians, and auditors',
    checkers={
        # Core checks
        'check_spelling': True,
        'check_grammar': True,
        'check_punctuation': True,
        'check_capitalization': True,

        # Style - formal
        'check_passive_voice': True,
        'check_contractions': True,  # Avoid in formal docs
        'check_sentence_length': True,
        'check_future_tense': True,

        # Clarity
        'check_wordy_phrases': True,
        'check_jargon': False,  # Technical jargon expected
        'check_nominalization': True,
        'check_weak_language': True,

        # Requirements - critical
        'check_requirements_language': True,
        'check_testability': True,
        'check_atomicity': True,
        'check_escape_clauses': True,
        'check_tbd': True,

        # Compliance - all standards
        'check_mil_std_40051': True,
        'check_s1000d': True,
        'check_as9100': True,

        # Technical
        'check_acronyms': True,
        'check_acronym_first_use': True,
        'check_acronym_multiple_definition': True,
        'check_product_name_consistency': True,

        # Structure
        'check_document_structure': True,
        'check_cross_references': True,
        'check_cross_reference_targets': True,
        'check_references': True,
        'check_tables_figures': True,

        # Procedural
        'check_imperative_mood': True,
        'check_numbered_list_sequence': True,
    },
    severity_overrides={
        'requirements_language': 'error',
        'tbd': 'error',
        'mil_std_40051': 'error',
        's1000d': 'error',
        'as9100': 'error',
    },
    custom_rules={
        'strict_compliance': True,
        'require_traceability': True,
    }
)

# -----------------------------------------------------------------------------
# All Checks (Maximum Coverage)
# -----------------------------------------------------------------------------
PRESETS['all_checks'] = StylePreset(
    name='all_checks',
    display_name='All Checks',
    description='Enable all 105+ checkers for maximum coverage',
    target_audience='Comprehensive review',
    checkers={checker: True for checker in [
        'check_spelling', 'check_grammar', 'check_acronyms', 'check_passive_voice',
        'check_weak_language', 'check_wordy_phrases', 'check_nominalization',
        'check_jargon', 'check_ambiguous_pronouns', 'check_requirements_language',
        'check_gender_language', 'check_punctuation', 'check_sentence_length',
        'check_repeated_words', 'check_capitalization', 'check_contractions',
        'check_references', 'check_document_structure', 'check_tables_figures',
        'check_track_changes', 'check_consistency', 'check_lists', 'check_tbd',
        'check_testability', 'check_atomicity', 'check_escape_clauses',
        'check_hyperlinks', 'check_orphan_headings', 'check_empty_sections',
        'check_semantic_analysis', 'check_enhanced_acronyms', 'check_prose_linting',
        'check_structure_analysis', 'check_text_statistics', 'check_enhanced_passive',
        'check_fragments_v2', 'check_requirements_analysis', 'check_terminology_consistency',
        'check_cross_references', 'check_technical_dictionary', 'check_heading_case',
        'check_contraction_consistency', 'check_oxford_comma', 'check_ari',
        'check_spache', 'check_dale_chall', 'check_future_tense',
        'check_latin_abbreviations', 'check_sentence_initial_conjunction',
        'check_directional_language', 'check_time_sensitive_language',
        'check_acronym_first_use', 'check_acronym_multiple_definition',
        'check_imperative_mood', 'check_second_person', 'check_link_text_quality',
        'check_numbered_list_sequence', 'check_product_name_consistency',
        'check_cross_reference_targets', 'check_code_formatting',
        'check_mil_std_40051', 'check_s1000d', 'check_as9100',
    ]},
    severity_overrides={},
    custom_rules={}
)

# -----------------------------------------------------------------------------
# Minimal (Basic Checks Only)
# -----------------------------------------------------------------------------
PRESETS['minimal'] = StylePreset(
    name='minimal',
    display_name='Minimal',
    description='Basic grammar and spelling checks only - fastest performance',
    target_audience='Quick review',
    checkers={
        'check_spelling': True,
        'check_grammar': True,
        'check_punctuation': True,
        'check_capitalization': True,
        'check_acronyms': True,
        # Everything else disabled
    },
    severity_overrides={},
    custom_rules={}
)


# =============================================================================
# API FUNCTIONS
# =============================================================================

def list_presets() -> List[Dict]:
    """
    List all available style presets.

    Returns:
        List of preset info dictionaries
    """
    return [
        {
            'name': preset.name,
            'display_name': preset.display_name,
            'description': preset.description,
            'target_audience': preset.target_audience,
            'checker_count': sum(1 for v in preset.checkers.values() if v),
        }
        for preset in PRESETS.values()
    ]


def get_preset(name: str) -> Optional[StylePreset]:
    """
    Get a style preset by name.

    Args:
        name: Preset name (e.g., 'microsoft', 'google', 'plain_language')

    Returns:
        StylePreset object or None if not found
    """
    return PRESETS.get(name.lower())


def get_preset_options(name: str) -> Dict[str, bool]:
    """
    Get just the checker options for a preset.

    Args:
        name: Preset name

    Returns:
        Dictionary of checker_name: enabled pairs
    """
    preset = get_preset(name)
    if preset:
        return preset.checkers.copy()
    return {}


def apply_preset(name: str, custom_overrides: Optional[Dict[str, bool]] = None) -> Dict[str, bool]:
    """
    Apply a preset with optional custom overrides.

    Args:
        name: Preset name
        custom_overrides: Optional dict to override specific checker settings

    Returns:
        Final options dictionary
    """
    preset = get_preset(name)
    if not preset:
        _logger.warning(f"Unknown preset '{name}', using default options")
        return {}

    options = preset.checkers.copy()

    if custom_overrides:
        options.update(custom_overrides)

    _logger.info(f"Applied preset '{name}' with {sum(1 for v in options.values() if v)} checkers enabled")

    return options


def get_preset_severity_overrides(name: str) -> Dict[str, str]:
    """
    Get severity overrides for a preset.

    Args:
        name: Preset name

    Returns:
        Dictionary of checker_name: severity pairs
    """
    preset = get_preset(name)
    if preset:
        return preset.severity_overrides.copy()
    return {}


def get_preset_custom_rules(name: str) -> Dict[str, Any]:
    """
    Get custom rules for a preset.

    Args:
        name: Preset name

    Returns:
        Dictionary of custom rule settings
    """
    preset = get_preset(name)
    if preset:
        return preset.custom_rules.copy()
    return {}


def save_custom_preset(name: str, preset: StylePreset, filepath: Optional[str] = None) -> bool:
    """
    Save a custom preset to a JSON file.

    Args:
        name: Preset name
        preset: StylePreset object
        filepath: Optional file path (defaults to data/presets/{name}.json)

    Returns:
        True if saved successfully
    """
    if filepath is None:
        preset_dir = Path(__file__).parent / 'data' / 'presets'
        preset_dir.mkdir(parents=True, exist_ok=True)
        filepath = preset_dir / f'{name}.json'

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(preset.to_dict(), f, indent=2)
        _logger.info(f"Saved custom preset '{name}' to {filepath}")
        return True
    except Exception as e:
        _logger.error(f"Failed to save preset: {e}")
        return False


def load_custom_preset(filepath: str) -> Optional[StylePreset]:
    """
    Load a custom preset from a JSON file.

    Args:
        filepath: Path to preset JSON file

    Returns:
        StylePreset object or None if failed
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        preset = StylePreset(
            name=data['name'],
            display_name=data['display_name'],
            description=data['description'],
            target_audience=data['target_audience'],
            checkers=data.get('checkers', {}),
            severity_overrides=data.get('severity_overrides', {}),
            custom_rules=data.get('custom_rules', {})
        )
        _logger.info(f"Loaded custom preset '{preset.name}' from {filepath}")
        return preset
    except Exception as e:
        _logger.error(f"Failed to load preset: {e}")
        return None


# =============================================================================
# CLI INTERFACE
# =============================================================================

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        preset_name = sys.argv[1]
        preset = get_preset(preset_name)
        if preset:
            print(f"\nPreset: {preset.display_name}")
            print(f"Description: {preset.description}")
            print(f"Target: {preset.target_audience}")
            print(f"\nEnabled Checkers ({sum(1 for v in preset.checkers.values() if v)}):")
            for checker, enabled in sorted(preset.checkers.items()):
                status = "ON" if enabled else "off"
                print(f"  [{status:3}] {checker}")
            if preset.severity_overrides:
                print(f"\nSeverity Overrides:")
                for checker, severity in preset.severity_overrides.items():
                    print(f"  {checker}: {severity}")
        else:
            print(f"Unknown preset: {preset_name}")
            print(f"Available: {', '.join(PRESETS.keys())}")
    else:
        print("AEGIS Style Presets")
        print("=" * 50)
        for preset in list_presets():
            print(f"\n{preset['display_name']} ({preset['name']})")
            print(f"  {preset['description']}")
            print(f"  Target: {preset['target_audience']}")
            print(f"  Checkers: {preset['checker_count']} enabled")
