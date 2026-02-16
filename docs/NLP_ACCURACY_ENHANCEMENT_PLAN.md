# NLP Accuracy Enhancement Plan v1.0.0

## Project: Maximum Accuracy NLP Enhancement for AEGIS
**Version:** 1.0.0
**Date:** 2026-02-03
**Target Version:** 3.3.0

---

## Executive Summary

This document outlines a comprehensive enhancement plan to achieve near-100% accuracy for role extraction, acronym detection, grammar checking, and all other document analysis capabilities in AEGIS. All solutions are 100% offline-capable for air-gapped network deployment.

### Target Accuracy Improvements

| Category | Current | Target | Method |
|----------|---------|--------|--------|
| Role Extraction | 56.7% | 95%+ | Transformer NER + EntityRuler + Learning |
| Acronym Detection | 75% | 95%+ | Domain dictionaries + Context analysis |
| Passive Voice | 70% | 88%+ | Dependency parsing (not regex) |
| Grammar (general) | 75% | 92%+ | Full spaCy + LanguageTool |
| Spelling | 85% | 98%+ | SymSpell + Technical dictionary |
| Requirements Language | 80% | 95%+ | Pattern expansion + Atomicity |
| Ambiguous Pronouns | 70% | 90%+ | Coreference resolution |
| Sentence Fragments | 50% | 85%+ | Syntactic parsing |
| Terminology Consistency | 70% | 92%+ | Variant detection + Semantic |

---

## Phase 1: Technical Dictionary System

### 1.1 Components
- `technical_dictionary.py` - Master dictionary with 10,000+ terms
- Aerospace/defense terminology (5,000+ terms)
- Government contracting vocabulary (2,000+ terms)
- Technical corrections (500+ misspellings)
- Proper nouns (companies, programs, standards)

### 1.2 Deliverables
- [ ] `technical_dictionary.py` - Main dictionary module
- [ ] `dictionaries/aerospace_terms.txt` - Aerospace vocabulary
- [ ] `dictionaries/defense_terms.txt` - Defense vocabulary
- [ ] `dictionaries/government_terms.txt` - Government contracting
- [ ] `dictionaries/software_terms.txt` - Software/IT terms
- [ ] `dictionaries/technical_corrections.json` - Misspelling corrections

### 1.3 Integration Points
- `spell_checker.py` - Use dictionary for validation
- `extended_checkers.py` - Integrate corrections
- `acronym_checker.py` - Use acronym database

---

## Phase 2: Adaptive Learning System

### 2.1 Components
- `adaptive_learner.py` - Unified learning system
- Role adjudication tracking
- Acronym decision tracking
- Grammar/style pattern learning
- Context-aware confidence adjustment
- Export/import for team sharing

### 2.2 Database Schema
```sql
-- decisions: Individual user decisions
-- patterns: Aggregated statistics
-- role_patterns: Role-specific learning
-- acronym_patterns: Acronym-specific learning
-- context_patterns: Context-based confidence
-- user_preferences: Global user settings
```

### 2.3 Deliverables
- [ ] `adaptive_learner.py` - Main learning module
- [ ] Database migration for `adaptive_learning.db`
- [ ] API endpoints for adjudication
- [ ] Integration with `role_extractor_v3.py`
- [ ] Integration with `acronym_checker.py`
- [ ] UI components for feedback

---

## Phase 3: Enhanced spaCy Pipeline

### 3.1 Components
- Upgrade to `en_core_web_trf` (transformer model)
- Add `coreferee` for coreference resolution
- Add `EntityRuler` with 500+ aerospace patterns
- Add `PhraseMatcher` for role/acronym gazetteer
- Enhanced confidence scoring

### 3.2 Deliverables
- [ ] `nlp_enhanced.py` - Enhanced NLP processor
- [ ] `aerospace_patterns.json` - EntityRuler patterns
- [ ] Updated `install_nlp_offline.py`
- [ ] Updated `requirements-nlp.txt`
- [ ] Coreference integration
- [ ] Ensemble extraction method

### 3.3 Offline Package Requirements
- spacy 3.7.4 (~10MB)
- en_core_web_trf 3.7.x (~460MB)
- en_core_web_lg 3.7.x (~746MB, fallback)
- spacy-transformers 1.3.x (~5MB)
- coreferee 2.4.x (~20MB)
- sentence-transformers 2.2.x + models (~500MB)
- torch 2.1.x (~800MB)

**Total offline package: ~2.5GB**

---

## Phase 4: Advanced Checkers

### 4.1 Enhanced Passive Voice Checker
- Uses dependency parsing instead of regex
- Distinguishes true passives from adjectival uses
- 300+ adjectival participles whitelist
- Active voice suggestions when possible

### 4.2 Sentence Fragment Detector
- Full syntactic analysis via spaCy
- Subject and finite verb detection
- Subordinate clause identification
- Imperative sentence handling

### 4.3 Requirements Analyzer
- Atomicity checking (one shall per requirement)
- Testability validation (measurable criteria)
- Escape clause detection
- Ambiguous term flagging
- Modal verb consistency (shall/will/must)

### 4.4 Deliverables
- [ ] `enhanced_passive_checker.py`
- [ ] `fragment_checker.py`
- [ ] `requirements_analyzer.py`
- [ ] Integration with `core.py`
- [ ] Unit tests for each checker

---

## Phase 5: Terminology & Table Validation

### 5.1 Terminology Consistency Checker
- Spelling variant detection (backend/back-end)
- British/American English consistency
- Abbreviation consistency
- Requirements language consistency (shall/will)

### 5.2 Enhanced Table Validator
- RACI matrix validation
- Caption quality checking
- Header row detection
- Cross-reference validation
- Numbering sequence checking

### 5.3 Cross-Reference Validator
- Section reference validation
- Table/Figure reference validation
- Requirement ID validation
- Unreferenced item detection

### 5.4 Deliverables
- [ ] `terminology_checker.py`
- [ ] `enhanced_table_validator.py`
- [ ] `cross_reference_validator.py`
- [ ] Integration with `document_checker.py`

---

## Phase 6: Integration, Testing & Documentation

### 6.1 Testing Requirements
- Unit tests for all new modules (pytest)
- Integration tests with existing checkers
- Accuracy benchmarks on test documents
- Performance benchmarks (processing time)
- Air-gap deployment testing

### 6.2 Documentation Updates
- [ ] `CHANGELOG.md` - Version history
- [ ] `README.md` - Feature updates
- [ ] `docs/NLP_USAGE.md` - Enhanced NLP guide
- [ ] `docs/TWR_PROJECT_STATE.md` - Project state
- [ ] `version.json` - Version bump to 3.3.0
- [ ] In-app Help documentation
- [ ] API documentation updates

### 6.3 Code Review Checklist
- [ ] All functions have docstrings
- [ ] Type hints on all public functions
- [ ] Error handling with specific exceptions
- [ ] Logging with appropriate levels
- [ ] No hardcoded paths or credentials
- [ ] Thread safety for database operations
- [ ] Memory efficiency for large documents
- [ ] Graceful degradation when dependencies missing

---

## Sprint Structure

### Sprint 1: Foundation (Phase 1 + 2)
**Duration:** ~1 hour
- Technical Dictionary System
- Adaptive Learning System
- Database schema and migrations
- Basic API endpoints

### Sprint 2: NLP Enhancement (Phase 3)
**Duration:** ~1 hour
- Enhanced spaCy pipeline
- EntityRuler patterns
- Coreference integration
- Offline package updates

### Sprint 3: Advanced Checkers (Phase 4)
**Duration:** ~1 hour
- Passive voice enhancement
- Fragment detection
- Requirements analysis
- Integration testing

### Sprint 4: Validation & Polish (Phase 5 + 6)
**Duration:** ~1 hour
- Terminology consistency
- Table validation
- Cross-references
- Documentation
- Final testing

---

## Success Criteria

1. **Accuracy Targets Met:** All categories meet or exceed target accuracy
2. **100% Offline:** All features work without network access
3. **Backward Compatible:** Existing functionality preserved
4. **All Tests Pass:** 117+ existing tests + new tests pass
5. **Documentation Complete:** All MD files updated
6. **Code Review Passed:** All checklist items verified

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Model size too large | Provide fallback to smaller models |
| Dependencies conflict | Pin specific versions in requirements |
| Performance degradation | Add processing time limits, chunking |
| Breaking changes | Comprehensive test suite, feature flags |

---

## Appendix: File Changes Summary

### New Files
- `adaptive_learner.py`
- `technical_dictionary.py`
- `nlp_enhanced.py`
- `enhanced_passive_checker.py`
- `fragment_checker.py`
- `requirements_analyzer.py`
- `terminology_checker.py`
- `enhanced_table_validator.py`
- `cross_reference_validator.py`
- `aerospace_patterns.json`
- `dictionaries/*.txt`

### Modified Files
- `role_extractor_v3.py` - Learning integration
- `acronym_checker.py` - Learning + dictionary
- `nlp_utils.py` - Enhanced pipeline
- `core.py` - New checker integration
- `app.py` - New API endpoints
- `install_nlp_offline.py` - New packages
- `requirements-nlp.txt` - Dependencies
- `CHANGELOG.md` - Version history
- `README.md` - Documentation
- `version.json` - Version bump
- `docs/*.md` - All documentation

---

*Document created: 2026-02-03*
*Last updated: 2026-02-03*
