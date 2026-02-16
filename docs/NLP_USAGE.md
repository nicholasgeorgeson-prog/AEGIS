# AEGIS NLP Enhancement Guide

## Overview

AEGIS v3.1.0 includes advanced NLP (Natural Language Processing) capabilities that significantly enhance document analysis beyond pattern matching. These modules provide:

- **spaCy Integration** - Linguistic analysis, dependency parsing, NER
- **LanguageTool** - Comprehensive grammar checking (3000+ rules)
- **Enhanced Spelling** - 500K+ word dictionary with domain support
- **Readability Metrics** - 8 industry-standard metrics
- **Style Checking** - Professional editorial rules (Strunk & White, etc.)
- **Verb/Tense Analysis** - Tense consistency detection
- **Semantic Analysis** - Terminology consistency via WordNet

All modules support **air-gapped operation** after initial setup.

---

## Quick Start

### Installation

```bash
# Core NLP dependencies
pip3 install spacy language-tool-python symspellpy pyenchant textstat proselint nltk

# Download spaCy model (offline after first download)
python3 -m spacy download en_core_web_md

# Download NLTK data for WordNet
python3 -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4')"
```

### Verify Installation

```python
from nlp import get_status
status = get_status()
print(status)
```

---

## Module Details

### 1. spaCy Integration

**Purpose:** Advanced linguistic analysis using dependency parsing.

**Features:**
- Subject-verb agreement detection via parse tree
- Dangling modifier detection
- Sentence complexity analysis
- Named entity recognition

**Installation:**
```bash
pip3 install spacy
python3 -m spacy download en_core_web_md
```

**Usage:**
```python
from nlp.spacy import get_analyzer, is_available

if is_available():
    analyzer = get_analyzer()
    result = analyzer.analyze("The system processes data.")
    print(result)
```

**Air-Gap Setup:**
1. Download model on connected machine
2. Copy model folder to air-gapped system
3. Link model: `python -m spacy link en_core_web_md en_core_web_md`

---

### 2. LanguageTool Integration

**Purpose:** Comprehensive grammar checking with 3000+ rules.

**Features:**
- Grammar rule checking
- Style suggestions
- Technical term whitelist
- Rule skip list to avoid overlap

**Installation:**
```bash
pip3 install language-tool-python
# Requires Java 8+ installed
```

**Usage:**
```python
from nlp.languagetool import is_available, get_status
from nlp.languagetool.checker import ComprehensiveGrammarChecker

if is_available():
    checker = ComprehensiveGrammarChecker()
    result = checker.check([(0, "Their going to the store.")])
```

**Air-Gap Setup:**
1. Run once on connected machine to download LanguageTool
2. Copy `~/.cache/language-tool-python/` to air-gapped system

**Note:** Requires Java Runtime Environment (JRE) 8+.

---

### 3. Enhanced Spelling

**Purpose:** Fast spelling with domain-specific dictionaries.

**Features:**
- SymSpell: 500K+ word dictionary, ultra-fast checking
- PyEnchant: Domain dictionary support
- Aerospace, defense, software term dictionaries
- Compound word segmentation

**Installation:**
```bash
pip3 install symspellpy pyenchant
```

**Usage:**
```python
from nlp.spelling import is_available
from nlp.spelling.checker import EnhancedSpellingChecker

checker = EnhancedSpellingChecker()
result = checker.check([(0, "This sentnce has speling errors.")])
```

**Domain Dictionaries:**
Located in `dictionaries/`:
- `aerospace.txt` - Aviation and aerospace terms
- `defense.txt` - Military and defense terms
- `software.txt` - Software development terms

**Adding Custom Terms:**
Edit the dictionary files (one term per line) or use the API:
```python
from nlp.spelling.enchant import DomainDictionaryManager
manager = DomainDictionaryManager()
manager.add_word("myterm", "custom")
```

---

### 4. Readability Metrics

**Purpose:** Calculate readability scores for technical documents.

**Features:**
- Flesch Reading Ease
- Flesch-Kincaid Grade Level
- Gunning Fog Index
- SMOG Index
- Coleman-Liau Index
- Automated Readability Index
- Dale-Chall Readability Score
- Linsear Write Formula

**Installation:**
```bash
pip3 install textstat
```

**Usage:**
```python
from nlp.readability import calculate, is_available

if is_available():
    report = calculate("Your document text here...")
    print(f"Flesch-Kincaid Grade: {report.flesch_kincaid_grade}")
    print(f"Reading Ease: {report.flesch_reading_ease}")
```

**Recommendations:**
```python
from nlp.readability.enhanced import EnhancedReadabilityCalculator

calc = EnhancedReadabilityCalculator()
report = calc.calculate(text)
recommendations = calc.get_recommendations(report)
for rec in recommendations:
    print(rec)
```

---

### 5. Style Checking (Proselint)

**Purpose:** Professional editorial style rules.

**Features:**
- Cliché detection (50+ patterns)
- Jargon identification
- Redundancy detection
- Weasel word detection
- Rules from Strunk & White, Garner, Orwell

**Installation:**
```bash
pip3 install proselint
```

**Usage:**
```python
from nlp.style import is_available
from nlp.style.checker import StyleChecker

if is_available():
    checker = StyleChecker()
    result = checker.check([(0, "At this point in time, we need to leverage our synergies.")])
```

**Skipping Rules:**
```python
checker.add_skip_check("cliches.hell")  # Skip specific check
checker.remove_skip_check("cliches.hell")  # Re-enable
```

---

### 6. Verb/Tense Analysis

**Purpose:** Detect mixed verb tenses in documents.

**Features:**
- Verb tense detection (past, present, future)
- Tense consistency checking across paragraphs
- Dominant tense identification
- Verb conjugation helpers

**Installation:**
```bash
pip3 install spacy  # Uses spaCy for POS tagging
# OR pattern library (Python 3.9 and below)
pip3 install pattern
```

**Usage:**
```python
from nlp.verbs import is_available, analyze_tenses
from nlp.verbs.checker import TenseConsistencyChecker

if is_available():
    checker = TenseConsistencyChecker()
    result = checker.check([
        (0, "The user clicked the button and waits for a response.")
    ])
```

**Tense Report:**
```python
report = checker.get_paragraph_tense_report(text)
print(f"Dominant tense: {report['dominant_tense']}")
print(f"Consistency: {report['consistency_score']}")
```

---

### 7. Semantic Analysis (WordNet)

**Purpose:** Detect terminology inconsistency via synonyms.

**Features:**
- Synonym detection
- Semantic similarity calculation
- Terminology consistency checking
- Synonym group identification

**Installation:**
```bash
pip3 install nltk
python3 -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4')"
```

**Usage:**
```python
from nlp.semantics import is_available, similarity, get_synonyms
from nlp.semantics.checker import TerminologyConsistencyChecker

if is_available():
    # Check word similarity
    sim = similarity("car", "automobile")
    print(f"Similarity: {sim}")  # ~1.0

    # Get synonyms
    syns = get_synonyms("begin")
    print(f"Synonyms: {syns}")

    # Check terminology consistency
    checker = TerminologyConsistencyChecker()
    result = checker.check([
        (0, "The application starts. The program begins.")
    ])
```

**Air-Gap Setup:**
1. Download WordNet data on connected machine:
   ```python
   import nltk
   nltk.download('wordnet')
   nltk.download('omw-1.4')
   ```
2. Copy `~/nltk_data/` to air-gapped system

---

## Configuration

### Enable/Disable Modules

Edit `config.json`:
```json
{
    "nlp_settings": {
        "enabled": true,
        "checkers": {
            "spacy": true,
            "languagetool": true,
            "spelling": true,
            "style": true,
            "verbs": true,
            "semantics": true
        }
    }
}
```

### Programmatic Configuration

```python
from nlp import config

# Enable/disable modules
config.set_enabled('spacy', True)
config.set_enabled('languagetool', False)

# Get current settings
print(config.is_enabled('spelling'))
```

---

## API Endpoints

### GET /api/nlp/status
Returns status of all NLP modules.

```json
{
    "success": true,
    "data": {
        "version": "1.0.0",
        "modules": {
            "spacy": {"enabled": true, "available": true},
            "languagetool": {"enabled": true, "available": false, "error": "Java not installed"},
            ...
        },
        "checker_count": 8
    }
}
```

### GET /api/nlp/checkers
Returns list of available NLP checkers.

```json
{
    "success": true,
    "data": [
        {"name": "nlp_subject-verb_agreement", "display_name": "Subject-Verb Agreement (Enhanced)", "version": "1.0.0"},
        ...
    ]
}
```

### GET/POST /api/nlp/config
Get or update NLP configuration.

---

## Troubleshooting

### spaCy Model Not Found
```bash
# Reinstall model
python3 -m spacy download en_core_web_md

# Verify installation
python3 -c "import spacy; nlp = spacy.load('en_core_web_md'); print('OK')"
```

### LanguageTool Java Error
```bash
# Check Java installation
java -version

# Install Java (macOS)
brew install openjdk@11

# Install Java (Ubuntu)
sudo apt install openjdk-11-jre
```

### NLTK Data Missing
```python
import nltk
import ssl

# Workaround for SSL issues
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

nltk.download('wordnet')
nltk.download('omw-1.4')
nltk.download('cmudict')  # For readability
```

### PyEnchant Installation Issues

**macOS:**
```bash
brew install enchant
pip3 install pyenchant
```

**Ubuntu:**
```bash
sudo apt install libenchant-2-dev
pip3 install pyenchant
```

---

## Air-Gap Deployment

For environments without internet access:

### 1. Prepare on Connected Machine
```bash
# Create packages directory
mkdir nlp_packages && cd nlp_packages

# Download all dependencies
pip3 download spacy language-tool-python symspellpy pyenchant textstat proselint nltk

# Download spaCy model
python3 -m spacy download en_core_web_md
cp -r $(python3 -c "import spacy; print(spacy.util.get_package_path('en_core_web_md'))") .

# Download NLTK data
python3 -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4'); nltk.download('cmudict')"
cp -r ~/nltk_data .
```

### 2. Transfer to Air-Gapped System
Copy the `nlp_packages` directory to the air-gapped system.

### 3. Install on Air-Gapped System
```bash
cd nlp_packages

# Install Python packages
pip3 install --no-index --find-links=. spacy language-tool-python symspellpy pyenchant textstat proselint nltk

# Link spaCy model
python3 -m spacy link ./en_core_web_md en_core_web_md

# Set NLTK data path
export NLTK_DATA=/path/to/nlp_packages/nltk_data
```

---

## Testing

Run the NLP test suite:
```bash
# All NLP tests
python3 -m pytest tests/nlp/ -v

# Specific module
python3 -m pytest tests/nlp/test_spacy.py -v

# With coverage
python3 -m pytest tests/nlp/ --cov=nlp --cov-report=html
```

---

## Version History

- **v3.1.0** - Initial NLP integration
  - spaCy analyzer and checkers
  - LanguageTool grammar checking
  - Enhanced spelling with domain dictionaries
  - Readability metrics (8 formulas)
  - Proselint style checking
  - Verb/tense analysis
  - WordNet semantic analysis
  - Core integration with review pipeline
  - REST API endpoints

---

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify dependencies with `python3 -c "from nlp import get_status; print(get_status())"`
3. Review test output: `python3 -m pytest tests/nlp/ -v`
