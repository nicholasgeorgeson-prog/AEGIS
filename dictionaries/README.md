# AEGIS Custom Dictionaries

This folder contains custom dictionary files that extend the built-in technical dictionary.

## File Formats

### Text Files (.txt)
One term per line. Lines starting with `#` are comments.

```
# My custom aerospace terms
ablator
aerocapture
aerobraking
```

### JSON Files

#### technical_corrections.json
```json
{
    "mispelled": "misspelled",
    "accomodate": "accommodate"
}
```

#### acronyms.json
```json
{
    "SEMP": "Systems Engineering Management Plan",
    "CDR": "Critical Design Review"
}
```

## Built-in Dictionaries

The `technical_dictionary.py` module includes:
- 5,000+ aerospace/defense terms
- 2,000+ government contracting terms
- 1,500+ systems engineering terms
- 1,000+ software/IT terms
- 500+ common misspelling corrections
- 800+ standard acronym expansions
- 200+ proper nouns (companies, programs)

## Adding Custom Terms

### Option 1: Add dictionary files here
Create `.txt` or `.json` files in this folder. They will be automatically loaded.

### Option 2: Use the API
```python
from technical_dictionary import get_technical_dictionary

dict = get_technical_dictionary()
dict.add_custom_term("myterm")
```

### Option 3: Use the UI
Settings → Dictionary → Add Custom Term

## Priority Order

1. Custom terms (highest priority)
2. External dictionary files
3. Built-in dictionaries (lowest priority)
