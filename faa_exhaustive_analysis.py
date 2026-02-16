#!/usr/bin/env python3
"""
FAA AC 120-92B Exhaustive Manual Analysis
=========================================
Detailed manual analysis of the FAA SMS document for comparison with tool results.
"""

import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Sample from FAA AC 120-92B (Chapter 1 Introduction)
FAA_SAMPLE_TEXT = """
This advisory circular (AC) provides information for Title 14 of the Code of Federal
Regulations (14 CFR) part 121 air carriers that are required to implement Safety
Management Systems (SMS) based on 14 CFR part 5. Specifically, this document provides
a description of regulatory requirements, guidance, and methods of developing and
implementing an SMS.

This AC may also be used by other aviation service providers interested in voluntarily
developing an SMS based on the requirements in part 5. An SMS is an organization-wide
comprehensive and preventive approach to managing safety. An SMS includes a safety
policy, formal methods for identifying hazards and mitigating risk, and promotion of
a positive safety culture.

An SMS also provides assurance of the overall safety performance of your organization.
An SMS is intended to be designed and developed by your own people and should be
integrated into your existing operations and business decision-making processes. The
SMS will assist your organization's leadership, management teams, and employees in
making effective and informed safety decisions.

This advisory circular provides information to assist Title 14 of the Code of Federal
Regulations part 121 certificate holders in developing a Safety Management System. It
provides guidance material that aligns with the requirements, structure, and format of
14 CFR part 5, Safety Management Systems for Certificate Holders Operating under Part 121.

It describes an acceptable means, but not the only means, to implement and maintain an
SMS. Because complying with part 5 satisfies the SMS Standards of the International
Civil Aviation Organization (ICAO), as published in ICAO Annex 19 for operations covered
under Annex 6 Part I, the material in this AC is also consistent with those ICAO standards.

An SMS is not meant to be a separate system built alongside or on top of your other
business systems. An SMS should be integrated into your existing business structure.
A properly integrated SMS fosters a fundamental and sustainable change in how you view
and analyze data and information, how you make informed decisions, and how you develop
new operational and business methods.

SMSs are necessary to comply with part 5, but they are not substitutes for compliance
with other Federal regulations. However, SMSs can assist service providers in meeting
other regulatory requirements. The SMS requirements of 14 CFR part 5 are applicable to
a wide variety of types and sizes of operators.

Therefore, those requirements are designed to be scalable, allowing operators to integrate
safety management practices into their unique business models. An SMS should be tailored
to each specific operator; therefore, this AC cannot provide a single means of compliance
that applies to all certificate holders who are required to develop and implement an SMS.
"""


def exhaustive_passive_analysis():
    """Exhaustive manual passive voice analysis."""
    print("\n" + "=" * 70)
    print("EXHAUSTIVE MANUAL PASSIVE VOICE ANALYSIS")
    print("=" * 70)

    # Sentence-by-sentence analysis
    sentences = re.split(r'(?<=[.!?])\s+', FAA_SAMPLE_TEXT.strip())

    passive_sentences = []
    active_sentences = []

    # Manual classification based on careful reading
    passive_classifications = {
        # True passives (be + past participle with implicit/explicit agent)
        "are required to implement": "PASSIVE - subject receives action",
        "is intended to be designed and developed": "PASSIVE - double passive",
        "should be integrated": "PASSIVE - modal passive",
        "is not meant to be": "PASSIVE - modal passive",
        "should be tailored": "PASSIVE - modal passive",
        "are required to develop": "PASSIVE - subject receives action",
        "are designed to be scalable": "PASSIVE - passive construction",
        "covered under Annex 6": "PASSIVE (reduced) - past participle",
    }

    true_passives = []
    for sentence in sentences:
        is_passive = False
        passive_match = ""

        for pattern, classification in passive_classifications.items():
            if pattern.lower() in sentence.lower():
                is_passive = True
                passive_match = pattern
                break

        # Also check common passive patterns
        passive_patterns = [
            r'\b(is|are|was|were|be|been|being)\s+(\w+ed)\b',
            r'\b(should|would|could|might|may|must|will|can)\s+be\s+(\w+ed)\b',
            r'\b(is|are|was|were|be|been|being)\s+(made|done|given|taken|put|met|set|held|built|found|known|shown|told|sent|brought)\b',
        ]

        if not is_passive:
            for pattern in passive_patterns:
                match = re.search(pattern, sentence, re.IGNORECASE)
                if match:
                    is_passive = True
                    passive_match = match.group(0)
                    break

        if is_passive:
            true_passives.append((sentence[:70], passive_match))
            passive_sentences.append(sentence)
        else:
            active_sentences.append(sentence)

    print("\nManual identification of passive voice sentences:")
    print("-" * 70)

    for i, (sentence, match) in enumerate(true_passives, 1):
        print(f"\n{i}. PASSIVE: \"{sentence}...\"")
        print(f"   Match: '{match}'")

    print(f"\n\nSUMMARY: {len(true_passives)} passive sentences out of {len(sentences)} total")
    return len(true_passives), len(sentences)


def exhaustive_ste100_analysis():
    """Exhaustive manual STE-100 analysis."""
    print("\n" + "=" * 70)
    print("EXHAUSTIVE MANUAL STE-100 ANALYSIS")
    print("=" * 70)

    # Manual identification of unapproved words per STE-100
    # These are words that have simpler alternatives
    unapproved_words = {
        "provides": "gives",
        "information": "data (if countable)",
        "description": "explanation",
        "implementing": "doing, putting in effect",
        "comprehensive": "complete",
        "preventive": "that prevents",
        "promotion": "support",
        "assurance": "certainty, guarantee",
        "overall": "total",
        "performance": "how well it works",
        "integrated": "combined",
        "existing": "current",
        "operations": "work",
        "assist": "help",
        "effective": "good, that works",
        "informed": "with information",
        "guidance": "help, direction",
        "aligns": "matches",
        "acceptable": "good enough",
        "implement": "do, start",
        "maintain": "keep",
        "complying": "following",
        "satisfies": "meets",
        "consistent": "the same",
        "fundamental": "basic",
        "sustainable": "lasting",
        "analyze": "study",
        "develop": "make, create",
        "operational": "working",
        "necessary": "needed",
        "compliance": "following rules",
        "substitutes": "replacements",
        "applicable": "that apply",
        "variety": "range, types",
        "scalable": "that can change size",
        "integrate": "combine",
        "unique": "special",
        "tailored": "made for",
        "specific": "particular",
        "single": "one",
    }

    print("\nManual identification of STE-100 unapproved words:")
    print("-" * 70)

    found_unapproved = []
    text_lower = FAA_SAMPLE_TEXT.lower()

    for word, alternative in unapproved_words.items():
        if word.lower() in text_lower:
            count = text_lower.count(word.lower())
            found_unapproved.append((word, alternative, count))
            print(f"  '{word}' (x{count}) -> Consider: {alternative}")

    print(f"\n\nSUMMARY: {len(found_unapproved)} unique unapproved words found")

    # Sentence length analysis
    sentences = [s for s in re.split(r'(?<=[.!?])\s+', FAA_SAMPLE_TEXT) if s.strip()]
    long_sentences = []

    for sentence in sentences:
        words = sentence.split()
        if len(words) > 25:
            long_sentences.append((len(words), sentence[:60]))

    print(f"\nSentences over 25 words: {len(long_sentences)}")
    for word_count, preview in long_sentences[:5]:
        print(f"  [{word_count} words] \"{preview}...\"")

    return len(found_unapproved), len(long_sentences)


def exhaustive_acronym_analysis():
    """Exhaustive manual acronym analysis."""
    print("\n" + "=" * 70)
    print("EXHAUSTIVE MANUAL ACRONYM ANALYSIS")
    print("=" * 70)

    # Manual identification of acronyms
    acronyms_found = {
        "AC": {"defined": True, "definition": "Advisory Circular", "first_use_defined": True},
        "CFR": {"defined": True, "definition": "Code of Federal Regulations", "first_use_defined": True},
        "SMS": {"defined": True, "definition": "Safety Management Systems", "first_use_defined": True},
        "ICAO": {"defined": True, "definition": "International Civil Aviation Organization", "first_use_defined": True},
        "SMSs": {"defined": False, "definition": "plural of SMS (implied)", "first_use_defined": False},
    }

    print("\nManual identification of acronyms:")
    print("-" * 70)

    defined = 0
    undefined = 0

    for acr, info in acronyms_found.items():
        if info["defined"]:
            defined += 1
            marker = "[DEFINED]"
        else:
            undefined += 1
            marker = "[NOT DEFINED]"

        print(f"  {marker} {acr}: {info['definition']}")

    print(f"\n\nSUMMARY: {defined} defined, {undefined} issues")
    return defined, undefined


def exhaustive_readability_analysis():
    """Exhaustive manual readability analysis."""
    print("\n" + "=" * 70)
    print("EXHAUSTIVE MANUAL READABILITY ANALYSIS")
    print("=" * 70)

    words = FAA_SAMPLE_TEXT.split()
    sentences = [s for s in re.split(r'(?<=[.!?])\s+', FAA_SAMPLE_TEXT) if s.strip()]

    word_count = len(words)
    sentence_count = len(sentences)
    avg_words = word_count / sentence_count if sentence_count else 0

    # Count syllables
    def count_syllables(word):
        word = word.lower().strip('.,!?;:')
        vowels = 'aeiouy'
        count = 0
        prev_vowel = False
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel
        return max(1, count)

    total_syllables = sum(count_syllables(w) for w in words)
    avg_syllables = total_syllables / word_count if word_count else 0

    # Flesch Reading Ease
    fre = 206.835 - 1.015 * avg_words - 84.6 * avg_syllables

    # Flesch-Kincaid Grade Level
    fkg = 0.39 * avg_words + 11.8 * avg_syllables - 15.59

    # Gunning Fog Index
    complex_words = sum(1 for w in words if count_syllables(w) >= 3)
    complex_ratio = complex_words / word_count if word_count else 0
    fog = 0.4 * (avg_words + 100 * complex_ratio)

    print(f"\nManual text statistics:")
    print("-" * 70)
    print(f"  Word count: {word_count}")
    print(f"  Sentence count: {sentence_count}")
    print(f"  Avg words/sentence: {avg_words:.1f}")
    print(f"  Avg syllables/word: {avg_syllables:.2f}")
    print(f"  Complex words (3+ syllables): {complex_words} ({complex_ratio*100:.1f}%)")
    print(f"\n  Flesch Reading Ease: {fre:.1f}")
    print(f"  Flesch-Kincaid Grade: {fkg:.1f}")
    print(f"  Gunning Fog Index: {fog:.1f}")

    return fkg, fre


def run_tool_analysis():
    """Run tool analysis for comparison."""
    print("\n" + "=" * 70)
    print("TOOL ANALYSIS FOR COMPARISON")
    print("=" * 70)

    results = {}

    # Passive voice
    try:
        from passivepy_checker import check_passive_voice
        passive_results = check_passive_voice(FAA_SAMPLE_TEXT)
        results['passive_count'] = len(passive_results)
        print(f"\nPassivePy detected: {len(passive_results)} passive sentences")
    except Exception as e:
        print(f"Passive analysis error: {e}")
        results['passive_count'] = 0

    # STE-100
    try:
        from ste100_checker import check_ste100_compliance
        ste_results = check_ste100_compliance(FAA_SAMPLE_TEXT)
        unapproved = [v for v in ste_results['violations'] if v['type'] == 'unapproved_word']
        long_sent = [v for v in ste_results['violations'] if v['type'] == 'sentence_length']
        results['ste_unapproved'] = len(unapproved)
        results['ste_long_sentences'] = len(long_sent)
        print(f"STE-100 unapproved words: {len(unapproved)}")
        print(f"STE-100 long sentences: {len(long_sent)}")
    except Exception as e:
        print(f"STE-100 analysis error: {e}")
        results['ste_unapproved'] = 0
        results['ste_long_sentences'] = 0

    # Readability
    try:
        from readability_enhanced import analyze_readability
        read_results = analyze_readability(FAA_SAMPLE_TEXT)
        results['fkg'] = read_results.get('flesch_kincaid_grade', 0)
        results['fre'] = read_results.get('flesch_reading_ease', 0)
        print(f"Flesch-Kincaid Grade: {results['fkg']:.1f}")
        print(f"Flesch Reading Ease: {results['fre']:.1f}")
    except Exception as e:
        print(f"Readability error: {e}")
        results['fkg'] = 0
        results['fre'] = 0

    # Acronyms
    try:
        from acronym_database import check_document_acronyms, extract_acronyms
        acronyms = extract_acronyms(FAA_SAMPLE_TEXT)
        issues = check_document_acronyms(FAA_SAMPLE_TEXT)
        results['acronym_count'] = len(acronyms)
        results['acronym_issues'] = len(issues)
        print(f"Acronyms found: {len(acronyms)}")
        print(f"Acronym issues: {len(issues)}")
    except Exception as e:
        print(f"Acronym error: {e}")
        results['acronym_count'] = 0
        results['acronym_issues'] = 0

    return results


def main():
    print("\n" + "=" * 70)
    print("EXHAUSTIVE FAA AC 120-92B ANALYSIS")
    print("Manual vs Tool Comparison")
    print("=" * 70)

    # Manual analyses
    manual_passive, total_sentences = exhaustive_passive_analysis()
    manual_ste_words, manual_long_sent = exhaustive_ste100_analysis()
    manual_defined, manual_undefined = exhaustive_acronym_analysis()
    manual_fkg, manual_fre = exhaustive_readability_analysis()

    # Tool analysis
    tool_results = run_tool_analysis()

    # Comparison table
    print("\n" + "=" * 70)
    print("COMPARISON SUMMARY")
    print("=" * 70)

    print(f"\n{'Metric':<40} {'Manual':>10} {'Tool':>10} {'Diff':>10}")
    print("-" * 70)

    # Passive voice
    passive_diff = abs(manual_passive - tool_results.get('passive_count', 0))
    passive_match = "✓" if passive_diff <= 2 else "X"
    print(f"{'Passive Voice Sentences':<40} {manual_passive:>10} {tool_results.get('passive_count', 0):>10} {passive_match:>10}")

    # STE-100 unapproved words
    ste_diff = abs(manual_ste_words - tool_results.get('ste_unapproved', 0))
    ste_match = "✓" if ste_diff <= 5 else "X"
    print(f"{'STE-100 Unapproved Words':<40} {manual_ste_words:>10} {tool_results.get('ste_unapproved', 0):>10} {ste_match:>10}")

    # Long sentences
    long_diff = abs(manual_long_sent - tool_results.get('ste_long_sentences', 0))
    long_match = "✓" if long_diff <= 2 else "X"
    print(f"{'Long Sentences (>25 words)':<40} {manual_long_sent:>10} {tool_results.get('ste_long_sentences', 0):>10} {long_match:>10}")

    # Flesch-Kincaid
    fkg_diff = abs(manual_fkg - tool_results.get('fkg', 0))
    fkg_match = "✓" if fkg_diff <= 2 else "X"
    print(f"{'Flesch-Kincaid Grade':<40} {manual_fkg:>10.1f} {tool_results.get('fkg', 0):>10.1f} {fkg_match:>10}")

    # Flesch Reading Ease
    fre_diff = abs(manual_fre - tool_results.get('fre', 0))
    fre_match = "✓" if fre_diff <= 5 else "X"
    print(f"{'Flesch Reading Ease':<40} {manual_fre:>10.1f} {tool_results.get('fre', 0):>10.1f} {fre_match:>10}")

    print("\n" + "=" * 70)
    print("Legend: ✓ = Within acceptable range, X = Investigate")
    print("=" * 70)


if __name__ == '__main__':
    main()
