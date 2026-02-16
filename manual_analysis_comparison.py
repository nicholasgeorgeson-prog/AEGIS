#!/usr/bin/env python3
"""
Manual Analysis Comparison
==========================
Compare tool results with manual analysis to validate accuracy.
"""

import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Sample paragraph from NASA Systems Engineering Handbook for detailed analysis
SAMPLE_TEXT = """
This handbook is intended to provide general guidance and information on systems
engineering that will be useful to the NASA community. It provides a generic
description of Systems Engineering (SE) as it should be applied throughout NASA.
A goal of the handbook is to increase awareness and consistency across the Agency
and advance the practice of SE. This handbook provides perspectives relevant to
NASA and data particular to NASA.

This handbook should be used as a companion for implementing NPR 7123.1, Systems
Engineering Processes and Requirements, as well as the Center-specific handbooks
and directives developed for implementing systems engineering at NASA. It provides
a companion reference book for the various systems engineering-related training
being offered under NASA's auspices.

This handbook describes systems engineering best practices that should be incorporated
in the development and implementation of large and small NASA programs and projects.
The engineering of NASA systems requires a systematic and disciplined set of processes
that are applied recursively and iteratively for the design, development, operation,
maintenance, and closeout of systems throughout the life cycle of the programs and
projects.

At NASA, systems engineering is defined as a methodical, multi-disciplinary approach
for the design, realization, technical management, operations, and retirement of a
system. A system is the combination of elements that function together to produce
the capability required to meet a need. The elements include all hardware, software,
equipment, facilities, personnel, processes, and procedures needed for this purpose.

Systems engineering is the art and science of developing an operable system capable
of meeting requirements within often opposed constraints. Systems engineering is a
holistic, integrative discipline, wherein the contributions of structural engineers,
electrical engineers, mechanism designers, power engineers, human factors engineers,
and many more disciplines are evaluated and balanced, one against another.

The systems engineer should develop the skill for identifying and focusing efforts
on assessments to optimize the overall design and not favor one system at the expense
of another while constantly validating that the goals of the operational system will
be met. The art is in knowing when and where to probe.
"""


def manual_passive_analysis():
    """Manual passive voice analysis."""
    print("\n" + "=" * 70)
    print("MANUAL PASSIVE VOICE ANALYSIS")
    print("=" * 70)

    # Sentences I identify as passive:
    passive_sentences = [
        ("It provides a generic description", "NOT PASSIVE - 'It' is subject, 'provides' is active"),
        ("as it should be applied throughout NASA", "PASSIVE - 'be applied' passive construction"),
        ("This handbook should be used as a companion", "PASSIVE - 'should be used' passive construction"),
        ("the Center-specific handbooks and directives developed for implementing", "ADJECTIVAL - 'developed' used as adjective"),
        ("training being offered under NASA's auspices", "PASSIVE - 'being offered' passive construction"),
        ("that should be incorporated in the development", "PASSIVE - 'should be incorporated' passive construction"),
        ("processes that are applied recursively", "PASSIVE - 'are applied' passive construction"),
        ("systems engineering is defined as", "PASSIVE - 'is defined' passive construction"),
        ("capability required to meet a need", "ADJECTIVAL - 'required' used as adjective"),
        ("procedures needed for this purpose", "ADJECTIVAL - 'needed' used as adjective"),
        ("the contributions... are evaluated and balanced", "PASSIVE - 'are evaluated and balanced' passive"),
        ("the goals... will be met", "PASSIVE - 'will be met' passive construction"),
    ]

    print("\nManual identification of passive voice:")
    print("-" * 70)

    true_passives = 0
    adjectival = 0

    for phrase, analysis in passive_sentences:
        if "PASSIVE" in analysis and "ADJECTIVAL" not in analysis:
            true_passives += 1
            marker = "[PASSIVE]"
        elif "ADJECTIVAL" in analysis:
            adjectival += 1
            marker = "[ADJECT]"
        else:
            marker = "[ACTIVE]"

        print(f"  {marker} \"{phrase[:50]}...\"")
        print(f"           {analysis}")

    print(f"\nManual count: {true_passives} true passives, {adjectival} adjectival")
    return true_passives


def manual_ste100_analysis():
    """Manual STE-100 analysis."""
    print("\n" + "=" * 70)
    print("MANUAL STE-100 ANALYSIS")
    print("=" * 70)

    # Words I identify as unapproved per STE-100:
    unapproved_words = [
        ("intended", "planned, meant"),
        ("provide", "give, supply"),
        ("guidance", "guidelines, directions"),
        ("generic", "general, common"),
        ("applied", "used"),
        ("throughout", "in all of"),
        ("awareness", "knowledge"),
        ("advance", "improve, move forward"),
        ("perspectives", "views, opinions"),
        ("particular", "specific"),
        ("implementing", "doing, putting into effect"),
        ("incorporated", "included"),
        ("requires", "needs"),
        ("systematic", "organized, orderly"),
        ("recursively", "repeatedly"),
        ("iteratively", "repeatedly"),
        ("methodical", "systematic, organized"),
        ("multi-disciplinary", "many-discipline"),
        ("realization", "making, building"),
        ("retirement", "end of use, closeout"),
        ("capability", "ability"),
        ("holistic", "complete, whole"),
        ("integrative", "combining"),
        ("wherein", "in which"),
        ("contributions", "inputs, work"),
        ("constraints", "limits"),
        ("optimize", "make best, improve"),
        ("validating", "confirming, proving"),
    ]

    print("\nManual identification of STE-100 unapproved words:")
    print("-" * 70)

    for word, suggestion in unapproved_words[:15]:
        print(f"  '{word}' -> Consider: {suggestion}")

    print(f"\n  ... and {len(unapproved_words) - 15} more")
    print(f"\nManual count: {len(unapproved_words)} potential STE-100 violations")

    # Sentence length analysis
    sentences = re.split(r'(?<=[.!?])\s+', SAMPLE_TEXT)
    long_sentences = []
    for s in sentences:
        words = s.split()
        if len(words) > 25:  # STE-100 limit for descriptive
            long_sentences.append((len(words), s[:60]))

    print(f"\nSentences over 25 words (STE-100 limit): {len(long_sentences)}")
    for word_count, preview in long_sentences[:5]:
        print(f"  [{word_count} words] \"{preview}...\"")

    return len(unapproved_words)


def manual_acronym_analysis():
    """Manual acronym analysis."""
    print("\n" + "=" * 70)
    print("MANUAL ACRONYM ANALYSIS")
    print("=" * 70)

    # Acronyms I identify:
    acronyms_found = {
        "NASA": "Defined (National Aeronautics and Space Administration)",
        "SE": "Defined in text (Systems Engineering)",
        "NPR": "NOT DEFINED - NASA Procedural Requirement",
        "PP&C": "Partially defined in later section (Project Planning and Control)",
    }

    print("\nManual identification of acronyms:")
    print("-" * 70)

    defined = 0
    undefined = 0

    for acr, status in acronyms_found.items():
        if "NOT DEFINED" in status or "Partially" in status:
            undefined += 1
            marker = "[ISSUE]"
        else:
            defined += 1
            marker = "[OK]"

        print(f"  {marker} {acr}: {status}")

    print(f"\nManual count: {defined} defined, {undefined} issues")
    return undefined


def manual_readability_analysis():
    """Manual readability analysis."""
    print("\n" + "=" * 70)
    print("MANUAL READABILITY ANALYSIS")
    print("=" * 70)

    words = SAMPLE_TEXT.split()
    sentences = [s for s in re.split(r'(?<=[.!?])\s+', SAMPLE_TEXT) if s.strip()]

    word_count = len(words)
    sentence_count = len(sentences)
    avg_words = word_count / sentence_count if sentence_count else 0

    # Count syllables (simple estimation)
    def count_syllables(word):
        word = word.lower()
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

    # Flesch Reading Ease (manual calculation)
    fre = 206.835 - 1.015 * avg_words - 84.6 * avg_syllables

    # Flesch-Kincaid Grade Level
    fkg = 0.39 * avg_words + 11.8 * avg_syllables - 15.59

    print(f"\nManual text statistics:")
    print("-" * 70)
    print(f"  Word count: {word_count}")
    print(f"  Sentence count: {sentence_count}")
    print(f"  Avg words/sentence: {avg_words:.1f}")
    print(f"  Avg syllables/word: {avg_syllables:.2f}")
    print(f"\n  Flesch Reading Ease (manual calc): {fre:.1f}")
    print(f"  Flesch-Kincaid Grade (manual calc): {fkg:.1f}")

    # Assessment
    print(f"\n  Manual assessment:")
    if fre < 30:
        print("  - Text is VERY DIFFICULT to read (college graduate level)")
    elif fre < 50:
        print("  - Text is DIFFICULT to read (college level)")
    elif fre < 60:
        print("  - Text is FAIRLY DIFFICULT (high school level)")
    else:
        print("  - Text is STANDARD readability")

    return fkg


def compare_with_tool():
    """Run tool analysis and compare."""
    print("\n" + "=" * 70)
    print("TOOL ANALYSIS FOR COMPARISON")
    print("=" * 70)

    # Run tools on same sample
    try:
        from passivepy_checker import check_passive_voice
        passive_results = check_passive_voice(SAMPLE_TEXT)
        print(f"\nPassivePy/Combined detected: {len(passive_results)} passive sentences")
    except Exception as e:
        print(f"PassivePy error: {e}")
        passive_results = []

    try:
        from ste100_checker import check_ste100_compliance
        ste_results = check_ste100_compliance(SAMPLE_TEXT)
        print(f"STE-100 violations: {ste_results.get('total_violations', 0)}")
        print(f"  - Unapproved words: {ste_results.get('unapproved_words', 0)}")
        print(f"  - Compliance score: {ste_results.get('compliance_score', 0):.1f}%")
    except Exception as e:
        print(f"STE-100 error: {e}")
        ste_results = {}

    try:
        from readability_enhanced import analyze_readability
        read_results = analyze_readability(SAMPLE_TEXT)
        print(f"Readability (tool):")
        print(f"  - Flesch-Kincaid Grade: {read_results.get('flesch_kincaid_grade', 0):.1f}")
        print(f"  - Flesch Reading Ease: {read_results.get('flesch_reading_ease', 0):.1f}")
    except Exception as e:
        print(f"Readability error: {e}")
        read_results = {}

    try:
        from acronym_database import check_document_acronyms, extract_acronyms
        acronyms = extract_acronyms(SAMPLE_TEXT)
        issues = check_document_acronyms(SAMPLE_TEXT)
        print(f"Acronyms (tool):")
        print(f"  - Found: {len(acronyms)}")
        print(f"  - Issues: {len(issues)}")
    except Exception as e:
        print(f"Acronym error: {e}")

    return passive_results, ste_results, read_results


def main():
    print("\n" + "=" * 70)
    print("MANUAL VS TOOL ANALYSIS COMPARISON")
    print("Sample: NASA Systems Engineering Handbook excerpt")
    print("=" * 70)

    print(f"\nSample text length: {len(SAMPLE_TEXT)} characters, {len(SAMPLE_TEXT.split())} words")

    # Run manual analyses
    manual_passive = manual_passive_analysis()
    manual_ste = manual_ste100_analysis()
    manual_acronym = manual_acronym_analysis()
    manual_grade = manual_readability_analysis()

    # Run tool analyses
    tool_passive, tool_ste, tool_read = compare_with_tool()

    # Comparison summary
    print("\n" + "=" * 70)
    print("COMPARISON SUMMARY")
    print("=" * 70)

    print(f"\n{'Metric':<35} {'Manual':>12} {'Tool':>12} {'Match':>10}")
    print("-" * 69)

    tool_passive_count = len(tool_passive) if tool_passive else 0
    tool_ste_count = tool_ste.get('total_violations', 0) if tool_ste else 0
    tool_grade = tool_read.get('flesch_kincaid_grade', 0) if tool_read else 0

    # Calculate match scores
    passive_match = "~" if abs(manual_passive - tool_passive_count) <= 3 else "X"
    ste_match = "~" if abs(manual_ste - tool_ste_count) <= 10 else "X"
    grade_match = "~" if abs(manual_grade - tool_grade) <= 2 else "X"

    print(f"{'Passive Voice Sentences':<35} {manual_passive:>12} {tool_passive_count:>12} {passive_match:>10}")
    print(f"{'STE-100 Potential Violations':<35} {manual_ste:>12} {tool_ste_count:>12} {ste_match:>10}")
    print(f"{'Flesch-Kincaid Grade Level':<35} {manual_grade:>12.1f} {tool_grade:>12.1f} {grade_match:>10}")

    print("\n~ = Within acceptable range")
    print("X = Significant difference (investigate)")

    # Recommendations
    print("\n" + "=" * 70)
    print("ANALYSIS NOTES")
    print("=" * 70)

    notes = []

    if passive_match == "X":
        if tool_passive_count < manual_passive:
            notes.append("- Passive voice: Tool may be UNDER-detecting. Check adjectival filtering.")
        else:
            notes.append("- Passive voice: Tool may be OVER-detecting. Check false positives.")
    else:
        notes.append("- Passive voice: Tool detection is within acceptable range.")

    if ste_match == "X":
        if tool_ste_count < manual_ste:
            notes.append("- STE-100: Tool may be missing some unapproved words. Check dictionary.")
        else:
            notes.append("- STE-100: Tool may be flagging too many. Check false positives.")
    else:
        notes.append("- STE-100: Tool detection is within acceptable range.")

    if grade_match == "X":
        notes.append("- Readability: Significant variance. Check syllable counting algorithm.")
    else:
        notes.append("- Readability: Tool calculation matches manual within expected variance.")

    for note in notes:
        print(note)


if __name__ == '__main__':
    main()
