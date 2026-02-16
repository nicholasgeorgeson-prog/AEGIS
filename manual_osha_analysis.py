#!/usr/bin/env python3
"""
Manual OSHA Document Analysis
=============================
Detailed manual analysis compared with tool output.
"""

import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# OSHA sample text (from first section - "The Problem")
OSHA_SAMPLE = """
This informational booklet is intended to provide a generic, non-exhaustive overview
of a particular standards-related topic. This publication does not itself alter or
determine compliance responsibilities, which are set forth in OSHA standards themselves
and the Occupational Safety and Health Act. Moreover, because interpretations and
enforcement policy may change over time, for additional guidance on OSHA compliance
requirements, the reader should consult current and administrative interpretations
and decisions by the Occupational Safety and Health Review Commission and the Courts.

Unexpected releases of toxic, reactive, or flammable liquids and gases in processes
involving highly hazardous chemicals have been reported for many years. Incidents
continue to occur in various industries that use highly hazardous chemicals which
may be toxic, reactive, flammable, or explosive, or may exhibit a combination of
these properties.

Regardless of the industry that uses these highly hazardous chemicals, there is a
potential for an accidental release any time they are not properly controlled. This,
in turn, creates the possibility of disaster.

Recent major disasters include the 1984 Bhopal, India, incident resulting in more
than 2,000 deaths; the October 1989 Phillips Petroleum Company, Pasadena, TX, incident
resulting in 23 deaths and 132 injuries; the July 1990 BASF, Cincinnati, OH, incident
resulting in 2 deaths, and the May 1991 IMC, Sterlington, LA, incident resulting in
8 deaths and 128 injuries.

Although these major disasters involving highly hazardous chemicals drew national
attention to the potential for major catastrophes, the public record is replete with
information concerning many other less notable releases of highly hazardous chemicals.

Hazardous chemical releases continue to pose a significant threat to employees and
provide impetus, internationally and nationally, for authorities to develop or consider
developing legislation and regulations to eliminate or minimize the potential for
such events.

On July 17, 1990, OSHA published in the Federal Register a proposed standard, Process
Safety Management of Highly Hazardous Chemicals, containing requirements for the
management of hazards associated with processes using highly hazardous chemicals to
help assure safe and healthful workplaces.

OSHA's proposed standard emphasized the management of hazards associated with highly
hazardous chemicals and established a comprehensive management program that integrated
technologies, procedures, and management practices.
"""


def manual_passive_analysis():
    """Manual sentence-by-sentence passive voice identification."""
    print("\n" + "=" * 70)
    print("MANUAL PASSIVE VOICE ANALYSIS - OSHA SAMPLE")
    print("=" * 70)

    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', OSHA_SAMPLE) if s.strip()]

    # Manual identification - going through each sentence
    passive_sentences = []

    for i, sent in enumerate(sentences, 1):
        # Check for passive constructions
        passive_patterns = [
            (r'is intended to', 'is intended'),
            (r'are set forth', 'are set forth'),
            (r'have been reported', 'have been reported'),
            (r'are not properly controlled', 'are not properly controlled'),
            (r'is replete with', 'is replete (adjectival, not passive)'),
            (r'OSHA published', 'active - OSHA is subject'),
            (r'emphasized', 'active - standard emphasized'),
            (r'established', 'active - standard established'),
            (r'integrated', 'active - program integrated'),
        ]

        is_passive = False
        match_found = ""

        # True passive patterns
        true_passive_patterns = [
            r'\b(is|are|was|were|be|been|being)\s+intended\b',
            r'\bare\s+set\s+forth\b',
            r'\bhave\s+been\s+reported\b',
            r'\bare\s+not\s+properly\s+controlled\b',
            r'\b(should|would|could|might|may|must|will|can)\s+be\s+\w+ed\b',
        ]

        for pattern in true_passive_patterns:
            match = re.search(pattern, sent, re.IGNORECASE)
            if match:
                is_passive = True
                match_found = match.group(0)
                break

        if is_passive:
            passive_sentences.append((i, sent[:60], match_found))

    print(f"\nSentences analyzed: {len(sentences)}")
    print(f"\nManual passive identification:")
    print("-" * 70)

    for num, preview, match in passive_sentences:
        print(f"\n{num}. \"{preview}...\"")
        print(f"   Passive match: '{match}'")

    print(f"\n\nMANUAL COUNT: {len(passive_sentences)} passive sentences")
    return len(passive_sentences), len(sentences)


def manual_ste100_analysis():
    """Manual STE-100 unapproved word identification."""
    print("\n" + "=" * 70)
    print("MANUAL STE-100 ANALYSIS - OSHA SAMPLE")
    print("=" * 70)

    # Words I identify as unapproved per STE-100:
    unapproved_found = {
        "intended": "planned, meant",
        "provide": "give",
        "generic": "general",
        "overview": "summary",
        "particular": "specific",
        "alter": "change",
        "determine": "find, decide",
        "compliance": "following rules",
        "responsibilities": "duties",
        "interpretations": "explanations",
        "enforcement": "applying rules",
        "additional": "more",
        "guidance": "help, direction",
        "consult": "ask, check",
        "administrative": "management",
        "unexpected": "not expected",
        "releases": "escapes, outputs",
        "involving": "that use, with",
        "various": "different",
        "exhibit": "show",
        "combination": "mix",
        "regardless": "no matter",
        "potential": "possible, chance",
        "accidental": "not planned",
        "properly": "correctly",
        "possibility": "chance",
        "resulting": "causing",
        "disasters": "accidents, events",
        "attention": "notice",
        "catastrophes": "disasters",
        "replete": "full",
        "concerning": "about",
        "notable": "important",
        "significant": "important, large",
        "threat": "danger",
        "impetus": "push, reason",
        "internationally": "worldwide",
        "nationally": "countrywide",
        "authorities": "officials",
        "develop": "make, create",
        "legislation": "laws",
        "regulations": "rules",
        "eliminate": "remove",
        "minimize": "reduce",
        "proposed": "suggested",
        "containing": "with, having",
        "requirements": "needs, rules",
        "associated": "connected, related",
        "assure": "make sure",
        "emphasized": "stressed, highlighted",
        "comprehensive": "complete",
        "integrated": "combined",
        "practices": "methods, ways",
    }

    print(f"\nManual identification of unapproved words:")
    print("-" * 70)

    text_lower = OSHA_SAMPLE.lower()
    found = []

    for word, alt in unapproved_found.items():
        if word.lower() in text_lower:
            count = len(re.findall(r'\b' + word + r'\b', text_lower, re.IGNORECASE))
            if count > 0:
                found.append((word, alt, count))
                print(f"  '{word}' (x{count}) -> {alt}")

    print(f"\n\nMANUAL COUNT: {len(found)} unique unapproved words")
    return len(found)


def manual_long_sentence_analysis():
    """Manual long sentence identification."""
    print("\n" + "=" * 70)
    print("MANUAL LONG SENTENCE ANALYSIS - OSHA SAMPLE")
    print("=" * 70)

    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', OSHA_SAMPLE) if s.strip()]

    long_sentences = []
    for i, sent in enumerate(sentences, 1):
        word_count = len(sent.split())
        if word_count > 25:
            long_sentences.append((i, word_count, sent[:50]))

    print(f"\nSentences over 25 words:")
    print("-" * 70)
    for num, wc, preview in long_sentences:
        print(f"  {num}. [{wc} words] \"{preview}...\"")

    print(f"\n\nMANUAL COUNT: {len(long_sentences)} long sentences")
    return len(long_sentences)


def run_tool_analysis():
    """Run tool analysis on same sample."""
    print("\n" + "=" * 70)
    print("TOOL ANALYSIS - OSHA SAMPLE")
    print("=" * 70)

    from passivepy_checker import check_passive_voice
    from ste100_checker import check_ste100_compliance

    # Passive
    passive_results = check_passive_voice(OSHA_SAMPLE)
    print(f"\nPassive sentences (tool): {len(passive_results)}")
    for r in passive_results[:5]:
        print(f"  - {r['sentence'][:50]}...")

    # STE-100
    ste_results = check_ste100_compliance(OSHA_SAMPLE)
    unapproved = [v for v in ste_results['violations'] if v['type'] == 'unapproved_word']
    long_sent = [v for v in ste_results['violations'] if v['type'] == 'sentence_length']

    print(f"\nSTE-100 unapproved (tool): {len(unapproved)}")
    print(f"Long sentences (tool): {len(long_sent)}")

    print("\nUnapproved words found by tool:")
    for v in unapproved[:10]:
        print(f"  - {v['word']}")
    if len(unapproved) > 10:
        print(f"  ... and {len(unapproved) - 10} more")

    return len(passive_results), len(unapproved), len(long_sent)


def main():
    print("\n" + "=" * 70)
    print("OSHA DOCUMENT - MANUAL VS TOOL COMPARISON")
    print("=" * 70)

    word_count = len(OSHA_SAMPLE.split())
    print(f"\nSample size: {word_count} words")

    # Manual analyses
    manual_passive, total_sent = manual_passive_analysis()
    manual_ste = manual_ste100_analysis()
    manual_long = manual_long_sentence_analysis()

    # Tool analyses
    tool_passive, tool_ste, tool_long = run_tool_analysis()

    # Comparison
    print("\n" + "=" * 70)
    print("COMPARISON SUMMARY")
    print("=" * 70)

    print(f"\n{'Metric':<30} {'Manual':>10} {'Tool':>10} {'Diff':>10}")
    print("-" * 60)
    print(f"{'Passive sentences':<30} {manual_passive:>10} {tool_passive:>10} {tool_passive - manual_passive:>+10}")
    print(f"{'STE-100 unapproved':<30} {manual_ste:>10} {tool_ste:>10} {tool_ste - manual_ste:>+10}")
    print(f"{'Long sentences (>25)':<30} {manual_long:>10} {tool_long:>10} {tool_long - manual_long:>+10}")


if __name__ == '__main__':
    main()
