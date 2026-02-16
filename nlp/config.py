"""
NLP Configuration Module
========================
Centralized configuration for all NLP integrations.

Configuration can be set via:
1. Environment variables (NLP_SPACY_ENABLED=true)
2. Config file (nlp_config.json)
3. Direct API calls (config.set('spacy.enabled', True))

All settings have sensible defaults for air-gapped operation.
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field

__version__ = "1.0.0"

# Default configuration path
CONFIG_FILE = Path(__file__).parent.parent / "nlp_config.json"


@dataclass
class SpacyConfig:
    """spaCy configuration."""
    enabled: bool = True
    model: str = "en_core_web_md"  # sm, md, or lg
    disable_components: list = field(default_factory=lambda: ["textcat"])
    batch_size: int = 1000


@dataclass
class LanguageToolConfig:
    """LanguageTool configuration."""
    enabled: bool = True
    language: str = "en-US"
    disabled_rules: list = field(default_factory=lambda: [
        "PASSIVE_VOICE",      # We have our own checker
        "WHITESPACE_RULE",    # Too noisy
        "COMMA_PARENTHESIS_WHITESPACE",
    ])
    enabled_only: list = field(default_factory=list)  # Empty = all rules
    cache_size: int = 1000


@dataclass
class SpellingConfig:
    """Spelling checker configuration."""
    enabled: bool = True
    max_edit_distance: int = 2
    prefix_length: int = 7
    custom_dictionary: Optional[str] = None
    domain_dictionaries: list = field(default_factory=lambda: [
        "aerospace", "defense", "software"
    ])
    personal_dictionary: Optional[str] = None


@dataclass
class ReadabilityConfig:
    """Readability analysis configuration."""
    enabled: bool = True
    target_grade_level: int = 12  # Flag documents above this
    warn_on_difficult_words: bool = True
    difficult_word_threshold: int = 50  # Flag if more than this many


@dataclass
class StyleConfig:
    """Style checker (Proselint) configuration."""
    enabled: bool = True
    skip_checks: list = field(default_factory=lambda: [
        "passive_voice",      # We have our own
        "contractions",       # We have our own
    ])


@dataclass
class VerbsConfig:
    """Verb/tense analysis configuration."""
    enabled: bool = True
    check_tense_consistency: bool = True
    flag_mixed_tenses: bool = True


@dataclass
class SemanticsConfig:
    """Semantic analysis (WordNet) configuration."""
    enabled: bool = True
    similarity_threshold: float = 0.8  # Flag synonyms above this similarity
    check_terminology_consistency: bool = True


@dataclass
class NLPConfig:
    """Master NLP configuration."""
    spacy: SpacyConfig = field(default_factory=SpacyConfig)
    languagetool: LanguageToolConfig = field(default_factory=LanguageToolConfig)
    spelling: SpellingConfig = field(default_factory=SpellingConfig)
    readability: ReadabilityConfig = field(default_factory=ReadabilityConfig)
    style: StyleConfig = field(default_factory=StyleConfig)
    verbs: VerbsConfig = field(default_factory=VerbsConfig)
    semantics: SemanticsConfig = field(default_factory=SemanticsConfig)


# Global configuration instance
_config: Optional[NLPConfig] = None


def get_config() -> NLPConfig:
    """Get the global NLP configuration."""
    global _config
    if _config is None:
        _config = _load_config()
    return _config


def _load_config() -> NLPConfig:
    """Load configuration from file and environment."""
    config = NLPConfig()

    # Load from file if exists
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
            _apply_dict_to_config(config, file_config)
        except (json.JSONDecodeError, IOError) as e:
            print(f"[NLP Config] Warning: Could not load config file: {e}")

    # Override with environment variables
    _apply_env_to_config(config)

    return config


def _apply_dict_to_config(config: NLPConfig, data: Dict[str, Any]):
    """Apply dictionary values to config object."""
    for section_name, section_data in data.items():
        if hasattr(config, section_name) and isinstance(section_data, dict):
            section = getattr(config, section_name)
            for key, value in section_data.items():
                if hasattr(section, key):
                    setattr(section, key, value)


def _apply_env_to_config(config: NLPConfig):
    """Apply environment variables to config."""
    env_mappings = {
        'NLP_SPACY_ENABLED': ('spacy', 'enabled', _parse_bool),
        'NLP_SPACY_MODEL': ('spacy', 'model', str),
        'NLP_LANGUAGETOOL_ENABLED': ('languagetool', 'enabled', _parse_bool),
        'NLP_LANGUAGETOOL_LANGUAGE': ('languagetool', 'language', str),
        'NLP_SPELLING_ENABLED': ('spelling', 'enabled', _parse_bool),
        'NLP_SPELLING_MAX_EDIT_DISTANCE': ('spelling', 'max_edit_distance', int),
        'NLP_READABILITY_ENABLED': ('readability', 'enabled', _parse_bool),
        'NLP_READABILITY_TARGET_GRADE': ('readability', 'target_grade_level', int),
        'NLP_STYLE_ENABLED': ('style', 'enabled', _parse_bool),
        'NLP_VERBS_ENABLED': ('verbs', 'enabled', _parse_bool),
        'NLP_SEMANTICS_ENABLED': ('semantics', 'enabled', _parse_bool),
    }

    for env_var, (section, key, converter) in env_mappings.items():
        value = os.environ.get(env_var)
        if value is not None:
            try:
                section_obj = getattr(config, section)
                setattr(section_obj, key, converter(value))
            except (ValueError, AttributeError) as e:
                print(f"[NLP Config] Warning: Invalid env var {env_var}={value}: {e}")


def _parse_bool(value: str) -> bool:
    """Parse boolean from string."""
    return value.lower() in ('true', '1', 'yes', 'on')


def is_enabled(module_name: str) -> bool:
    """Check if a module is enabled."""
    config = get_config()
    if hasattr(config, module_name):
        section = getattr(config, module_name)
        return getattr(section, 'enabled', False)
    return False


def get(key: str, default: Any = None) -> Any:
    """
    Get a configuration value by dot-notation key.

    Example: get('spacy.model') -> 'en_core_web_md'
    """
    config = get_config()
    parts = key.split('.')

    obj = config
    for part in parts:
        if hasattr(obj, part):
            obj = getattr(obj, part)
        else:
            return default

    return obj


def set(key: str, value: Any):
    """
    Set a configuration value by dot-notation key.

    Example: set('spacy.enabled', False)
    """
    config = get_config()
    parts = key.split('.')

    if len(parts) < 2:
        raise ValueError(f"Key must be in format 'section.key': {key}")

    section_name = parts[0]
    attr_name = parts[1]

    if hasattr(config, section_name):
        section = getattr(config, section_name)
        if hasattr(section, attr_name):
            setattr(section, attr_name, value)
        else:
            raise ValueError(f"Unknown config key: {attr_name}")
    else:
        raise ValueError(f"Unknown config section: {section_name}")


def save_config(path: Optional[Path] = None):
    """Save current configuration to file."""
    config = get_config()
    path = path or CONFIG_FILE

    data = {
        'spacy': {
            'enabled': config.spacy.enabled,
            'model': config.spacy.model,
            'disable_components': config.spacy.disable_components,
        },
        'languagetool': {
            'enabled': config.languagetool.enabled,
            'language': config.languagetool.language,
            'disabled_rules': config.languagetool.disabled_rules,
        },
        'spelling': {
            'enabled': config.spelling.enabled,
            'max_edit_distance': config.spelling.max_edit_distance,
            'domain_dictionaries': config.spelling.domain_dictionaries,
        },
        'readability': {
            'enabled': config.readability.enabled,
            'target_grade_level': config.readability.target_grade_level,
        },
        'style': {
            'enabled': config.style.enabled,
            'skip_checks': config.style.skip_checks,
        },
        'verbs': {
            'enabled': config.verbs.enabled,
            'check_tense_consistency': config.verbs.check_tense_consistency,
        },
        'semantics': {
            'enabled': config.semantics.enabled,
            'similarity_threshold': config.semantics.similarity_threshold,
        },
    }

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def reset_config():
    """Reset configuration to defaults."""
    global _config
    _config = NLPConfig()


def disable_all():
    """Disable all NLP modules (useful for testing)."""
    config = get_config()
    config.spacy.enabled = False
    config.languagetool.enabled = False
    config.spelling.enabled = False
    config.readability.enabled = False
    config.style.enabled = False
    config.verbs.enabled = False
    config.semantics.enabled = False


def enable_all():
    """Enable all NLP modules."""
    config = get_config()
    config.spacy.enabled = True
    config.languagetool.enabled = True
    config.spelling.enabled = True
    config.readability.enabled = True
    config.style.enabled = True
    config.verbs.enabled = True
    config.semantics.enabled = True
