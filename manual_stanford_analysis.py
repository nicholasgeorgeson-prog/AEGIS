#!/usr/bin/env python3
"""
Manual Stanford Robotics SOP Analysis
=====================================
Detailed manual analysis compared with tool output.
"""

import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Stanford Robotics SOP sample
STANFORD_SAMPLE = """
Consult your PI and/or lab supervisor if experiments involve high-risk operations
that can potentially result in serious injury or illness, to ensure safety precautions
are taken. Retain a record of their prior approval for at least one year.

High-risk operations may involve working with exposed electrical conductors carrying
50 Volts and 15 milli-Amps or more, confined space entry, custom-made pressure vessels,
Cobot interaction, high-speed or large payload robotics studies, Robotic Control
Software or Firmware Studies, etc. as may be determined by the PI.

Consultation can include discussion of special hazards and safety precautions and
review of applicable standard operating procedures. Your PI or lab supervisor's prior
approval may be documented by their signature in the Approval Signature field at the
end of this Section.

For granting prior approval to individuals other than the procedure author, use one
of the following forms of documentation: Complete the Documenting SOP Review and PI
Approval. Have the PI or lab supervisor sign and date the staff member's notebook and
indicate approval for the process, procedure, or activity. Use another form of written
approval, such as an e-mail or memo.

Conduct a hazard assessment using this checklist below. Check any hazards that may be
part of your intended research. Then, provide details in Section VI regarding the hazards.

Physical Hazards include exposed electrical conductors carrying 50 Volts or more, and
15 milli-Amps or more which present Electric Shock and Physical Contact hazard. Capacitors
and Capacitor Banks that are not self-grounding with a total stored capacitance of 5
joules or more present Electric Shock, Physical Contact, Explosion, and Arc Flash hazard.

High pressures or vacuum that can result in equipment structural failure or potential
safety risk. Extreme surface temperatures below zero degrees or in excess of 50 degrees
Celsius present Contact, Radiant Heat, and Cold hazards.

Cryogens and extremely cold fluids or gases present BLEVE, material embrittlement, and
contact frost bite hazards. Open Flame and Combustion Processes present Fire or explosion
hazard. Noise in excess of 85dB presents Noise hazard.

Vibration can cause Ergonomics and Structural Failure issues. Shockwave and Explosion
present Body Impact, Fire, and Equipment Damage Hazard. Lifting, Carrying, and Manual
Material Handling of 20 lbs or greater repetitively presents Ergonomics concerns.
"""


def manual_passive_analysis():
    """Manual passive voice identification."""
    print("\n" + "=" * 70)
    print("MANUAL PASSIVE VOICE ANALYSIS - STANFORD SOP")
    print("=" * 70)

    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', STANFORD_SAMPLE) if s.strip()]

    # Manual identification of passive sentences
    passive_sentences = []

    for i, sent in enumerate(sentences, 1):
        # Check each sentence for passive constructions
        passive_indicators = [
            ('are taken', 'passive - precautions are taken'),
            ('may be documented', 'passive - approval may be documented'),
            ('are not self-grounding', 'active - banks are self-grounding (predicate adj)'),
            ('can result in', 'active - can result'),
            ('may involve', 'active - operations involve'),
            ('can include', 'active - consultation can include'),
            ('may be determined', 'passive - determined by PI'),
        ]

        is_passive = False
        match_found = ""

        # Passive patterns
        passive_patterns = [
            r'\bare\s+taken\b',
            r'\bmay\s+be\s+documented\b',
            r'\bmay\s+be\s+determined\b',
            r'\b(is|are|was|were|be|been|being)\s+\w+ed\b',
            r'\b(should|would|could|might|may|must|will|can)\s+be\s+\w+ed\b',
        ]

        for pattern in passive_patterns:
            match = re.search(pattern, sent, re.IGNORECASE)
            if match:
                # Filter out false positives
                matched = match.group(0).lower()
                # Skip adjectival uses
                if 'self-grounding' in sent.lower():
                    continue
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
    """Manual STE-100 analysis."""
    print("\n" + "=" * 70)
    print("MANUAL STE-100 ANALYSIS - STANFORD SOP")
    print("=" * 70)

    # Unapproved words I identify
    unapproved_found = {
        "consult": "ask, check with",
        "involve": "use, include",
        "potentially": "possibly",
        "result": "cause, lead to",
        "ensure": "make sure",
        "precautions": "safety steps",
        "retain": "keep",
        "prior": "before, earlier",
        "approval": "permission, OK",
        "operations": "work, activities",
        "exposed": "open, uncovered",
        "confined": "small, limited",
        "determined": "decided",
        "consultation": "discussion, talk",
        "applicable": "that apply, relevant",
        "documented": "recorded, written",
        "granting": "giving",
        "individuals": "people, persons",
        "procedure": "steps, method",
        "indicate": "show",
        "conduct": "do, perform",
        "assessment": "check, review",
        "intended": "planned",
        "provide": "give",
        "regarding": "about",
        "present": "show, have",
        "structural": "of structure",
        "potential": "possible",
        "extreme": "very high/low",
        "excess": "more than",
        "combustion": "burning",
        "repetitively": "again and again",
    }

    print(f"\nManual identification of unapproved words:")
    print("-" * 70)

    text_lower = STANFORD_SAMPLE.lower()
    found = []

    for word, alt in unapproved_found.items():
        count = len(re.findall(r'\b' + word + r'\b', text_lower, re.IGNORECASE))
        if count > 0:
            found.append((word, alt, count))
            print(f"  '{word}' (x{count}) -> {alt}")

    print(f"\n\nMANUAL COUNT: {len(found)} unique unapproved words")
    return len(found)


def manual_long_sentence_analysis():
    """Manual long sentence identification."""
    print("\n" + "=" * 70)
    print("MANUAL LONG SENTENCE ANALYSIS - STANFORD SOP")
    print("=" * 70)

    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', STANFORD_SAMPLE) if s.strip()]

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
    print("TOOL ANALYSIS - STANFORD SOP")
    print("=" * 70)

    from passivepy_checker import check_passive_voice
    from ste100_checker import check_ste100_compliance

    # Passive
    passive_results = check_passive_voice(STANFORD_SAMPLE)
    print(f"\nPassive sentences (tool): {len(passive_results)}")
    for r in passive_results[:5]:
        print(f"  - {r['sentence'][:50]}...")
    if len(passive_results) > 5:
        print(f"  ... and {len(passive_results) - 5} more")

    # STE-100
    ste_results = check_ste100_compliance(STANFORD_SAMPLE)
    unapproved = [v for v in ste_results['violations'] if v['type'] == 'unapproved_word']
    long_sent = [v for v in ste_results['violations'] if v['type'] == 'sentence_length']

    print(f"\nSTE-100 unapproved (tool): {len(unapproved)}")
    print(f"Long sentences (tool): {len(long_sent)}")

    return len(passive_results), len(unapproved), len(long_sent)


def main():
    print("\n" + "=" * 70)
    print("STANFORD ROBOTICS SOP - MANUAL VS TOOL COMPARISON")
    print("=" * 70)

    word_count = len(STANFORD_SAMPLE.split())
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
