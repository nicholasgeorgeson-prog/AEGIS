"""
AEGIS Demo Audio Generator
===========================
Generates voice narration MP3 files for the AEGIS guide demo system.

Provider chain:
  1. edge-tts (Microsoft Neural voices) — high quality, requires internet
  2. pyttsx3 (System voices) — offline, lower quality
  3. Web Speech API (browser-side) — fallback handled by frontend

Usage:
    from demo_audio_generator import generate_demo_audio
    result = generate_demo_audio(scenes_data, output_dir='static/audio/demo')
"""

import os
import json
import asyncio
import logging
import hashlib
from pathlib import Path

logger = logging.getLogger('AEGIS.DemoAudio')

# Try importing TTS libraries (both optional)
EDGE_TTS_AVAILABLE = False
PYTTSX3_AVAILABLE = False

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
    logger.info('edge-tts available for neural voice generation')
except ImportError:
    pass

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
    logger.info('pyttsx3 available for offline voice generation')
except ImportError:
    pass


# Default voice options
EDGE_TTS_VOICES = {
    'male_us': 'en-US-GuyNeural',
    'female_us': 'en-US-JennyNeural',
    'male_uk': 'en-GB-RyanNeural',
    'female_uk': 'en-GB-SoniaNeural',
    'male_au': 'en-AU-WilliamNeural',
    'female_au': 'en-AU-NatashaNeural',
}

DEFAULT_VOICE = 'en-US-JennyNeural'  # v5.9.30: Female neural voice — natural, warm tone
DEFAULT_RATE = '+0%'
DEFAULT_PITCH = '+0Hz'


def get_tts_status():
    """Return available TTS providers and their capabilities."""
    return {
        'edge_tts': {
            'available': EDGE_TTS_AVAILABLE,
            'quality': 'neural',
            'offline': False,
            'voices': list(EDGE_TTS_VOICES.keys()) if EDGE_TTS_AVAILABLE else []
        },
        'pyttsx3': {
            'available': PYTTSX3_AVAILABLE,
            'quality': 'system',
            'offline': True,
            'voices': []  # Populated dynamically
        },
        'webspeech': {
            'available': True,  # Always available (browser-side)
            'quality': 'varies',
            'offline': True,
            'voices': []  # Browser-specific
        }
    }


async def _generate_edge_tts(text, output_path, voice=DEFAULT_VOICE, rate=DEFAULT_RATE):
    """Generate audio using edge-tts (Microsoft Neural voices)."""
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate)
    await communicate.save(str(output_path))

    # Get file size for manifest
    size = os.path.getsize(output_path)
    return {'success': True, 'size': size, 'provider': 'edge-tts', 'voice': voice}


def _generate_pyttsx3(text, output_path, rate=150):
    """Generate audio using pyttsx3 (system voices, offline)."""
    engine = pyttsx3.init()
    engine.setProperty('rate', rate)

    # v5.9.30: Select best available FEMALE voice (natural sounding)
    voices = engine.getProperty('voices')
    # Priority: female English voices first, then any English voice
    female_patterns = ('zira', 'jenny', 'hazel', 'susan', 'samantha', 'karen', 'female')
    selected = None
    for v in voices:
        vname = v.name.lower()
        vid = v.id.lower()
        is_english = 'english' in vname or 'en_' in vid or 'en-' in vid
        if is_english and any(p in vname or p in vid for p in female_patterns):
            selected = v
            break
    if not selected:
        # Fallback: any English voice
        for v in voices:
            if 'english' in v.name.lower() or 'en_' in v.id.lower() or 'en-' in v.id.lower():
                selected = v
                break
    if selected:
        engine.setProperty('voice', selected.id)

    engine.save_to_file(text, str(output_path))
    engine.runAndWait()

    size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
    return {'success': size > 0, 'size': size, 'provider': 'pyttsx3'}


def _text_hash(text):
    """Generate short hash of text for cache-busting."""
    return hashlib.md5(text.encode()).hexdigest()[:8]


def generate_demo_audio(scenes_data, output_dir='static/audio/demo',
                         voice=DEFAULT_VOICE, force=False):
    """
    Generate audio files for all demo scenes.

    Args:
        scenes_data: dict of {section_id: [{narration: str, ...}, ...]}
        output_dir: directory to save audio files
        voice: edge-tts voice name
        force: regenerate even if files exist

    Returns:
        dict with manifest data and generation stats
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    manifest = {
        'version': '1.0',
        'generated_by': 'AEGIS Demo Audio Generator',
        'voice': voice,
        'provider': None,
        'sections': {}
    }

    stats = {'total': 0, 'generated': 0, 'skipped': 0, 'errors': 0}

    # Determine provider
    provider = None
    if EDGE_TTS_AVAILABLE:
        provider = 'edge-tts'
    elif PYTTSX3_AVAILABLE:
        provider = 'pyttsx3'
    else:
        return {
            'success': False,
            'error': 'No TTS provider available. Install edge-tts (pip install edge-tts) or pyttsx3 (pip install pyttsx3).',
            'stats': stats,
            'manifest': manifest
        }

    manifest['provider'] = provider
    logger.info(f'Generating demo audio using {provider} ({voice})')

    for section_id, steps in scenes_data.items():
        section_manifest = {'steps': []}

        for idx, step in enumerate(steps):
            text = step.get('narration', '')
            if not text:
                section_manifest['steps'].append(None)
                continue

            stats['total'] += 1

            # Generate filename
            filename = f'{section_id}__step{idx}.mp3'
            filepath = output_path / filename

            # Skip if file exists and text hasn't changed (unless force)
            text_hash = _text_hash(text)
            if filepath.exists() and not force:
                # Check if text changed by comparing hashes in existing manifest
                existing_manifest_path = output_path / 'manifest.json'
                if existing_manifest_path.exists():
                    try:
                        with open(existing_manifest_path) as f:
                            existing = json.load(f)
                        existing_steps = existing.get('sections', {}).get(section_id, {}).get('steps', [])
                        if idx < len(existing_steps) and existing_steps[idx]:
                            if existing_steps[idx].get('hash') == text_hash:
                                section_manifest['steps'].append(existing_steps[idx])
                                stats['skipped'] += 1
                                continue
                    except Exception:
                        pass

            # Generate audio
            try:
                if provider == 'edge-tts':
                    result = asyncio.run(_generate_edge_tts(text, filepath, voice))
                else:
                    result = _generate_pyttsx3(text, filepath)

                if result.get('success'):
                    step_data = {
                        'file': filename,
                        'text': text,
                        'hash': text_hash,
                        'size': result.get('size', 0)
                    }
                    section_manifest['steps'].append(step_data)
                    stats['generated'] += 1
                    logger.info(f'  Generated: {filename} ({result.get("size", 0)} bytes)')
                else:
                    section_manifest['steps'].append(None)
                    stats['errors'] += 1
                    logger.warning(f'  Failed: {filename}')

            except Exception as e:
                section_manifest['steps'].append(None)
                stats['errors'] += 1
                logger.error(f'  Error generating {filename}: {e}')

        manifest['sections'][section_id] = section_manifest

    # Save manifest
    manifest_path = output_path / 'manifest.json'
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    logger.info(f'Audio generation complete: {stats["generated"]} generated, '
                f'{stats["skipped"]} skipped, {stats["errors"]} errors')

    return {
        'success': stats['errors'] == 0,
        'stats': stats,
        'manifest': manifest,
        'manifest_path': str(manifest_path)
    }


def get_cinema_scenes():
    """
    Return cinema showcase scene narrations for audio generation.
    Each scene maps to one narration clip in the cinematic video.

    Returns: dict of {scene_id: [{narration: str}]}
    """
    return {
        'cinema_doc_chaos': [{'narration': 'Aerospace teams are drowning in documents. Thousands of pages across hundreds of deliverables. Each one could contain a mission-grounding error hidden in plain sight.'}],
        'cinema_standards_wall': [{'narration': 'The standards are endless. MIL-STD-498. DO-178C. IEEE 830. AS9100. Manual review takes weeks and still misses twenty percent of critical issues.'}],
        'cinema_breaking_point': [{'narration': 'A missed requirement cascades. A defective deliverable ships. The cost to fix grows ten times with every phase. The old way is broken.'}],
        'cinema_aegis_boot': [{'narration': 'Introducing AEGIS. The Aerospace Engineering Governance and Inspection System. Purpose-built for secure networks. Zero cloud dependency. Completely air-gapped.'}],
        'cinema_hud_activates': [{'narration': 'One hundred and five quality checkers activate. Four extraction strategies. Twelve integrated modules working in concert. The system comes alive.'}],
        'cinema_document_scan': [{'narration': 'Drop a document. AEGIS dissects every sentence. Grammar. Compliance. Ambiguity. Acronyms. Over one hundred categories, analyzed in under sixty seconds.'}],
        'cinema_review_engine': [{'narration': 'Seventy-four configurable quality checkers. Grammar, compliance, style, readability, acronyms, cross-references. Every issue deduplicated and severity-graded. Typical review: under sixty seconds.'}],
        'cinema_statement_forge': [{'narration': 'Statement Forge extracts every shall, must, and will statement. Categorizes by directive type. Assigns responsible roles. Compares across document versions to track what changed.'}],
        'cinema_roles_studio': [{'narration': 'Every role discovered. Project Manager. Systems Engineer. Quality Lead. A living dictionary built automatically. Adjudication, RACI matrix, inheritance mapping. Zero manual data entry.'}],
        'cinema_proposal_compare': [{'narration': 'Side-by-side proposal analysis. Financial extraction from any format. Red flag detection per FAR 15.404. Deviation heatmaps. Vendor scores from A through F. All data, no guesswork.'}],
        'cinema_hyperlink_validator': [{'narration': 'Every URL in the document, tested automatically. Multiple validation strategies including SSL bypass, single sign-on authentication, and headless browser rendering for government and enterprise sites. Six thousand links validated, with zero false positives.'}],
        'cinema_learning_system': [{'narration': 'Five learning modules that remember your corrections. Document review. Statement forge. Roles. Hyperlink validator. Proposal compare. Every pattern stored locally. Zero data ever leaves your machine.'}],
        'cinema_stat_cascade': [{'narration': 'One hundred and five checkers. One hundred ninety-three API endpoints. Five hundred forty-five audio narration clips. One hundred thirty-seven version releases. Twelve integrated modules. Seven file formats. Four extraction strategies.'}],
        'cinema_architecture_overview': [{'narration': 'Pure Flask and vanilla JavaScript. No frameworks. No dependencies you cannot control. SQLite for persistence. Canvas for visualization. Every single line of code serves one purpose.'}],
        'cinema_fortress': [{'narration': 'No internet required. No cloud dependency. No telemetry. One hundred ninety-five prepackaged wheel files. Complete offline installation. Your data never leaves the building.'}],
        'cinema_classified_ready': [{'narration': 'Ready for classified environments and secure enterprise networks. Government facilities. Defense contractor enclaves. Windows single sign-on authentication. SharePoint integration. Built for the environments that need it most.'}],
        'cinema_convergence': [{'narration': 'Twelve modules. One hundred and five checkers. Five learning systems. One mission. Helping engineers write better documents. Faster. More accurately. Every single time.'}],
        'cinema_logo_reveal': [{'narration': 'AEGIS. Built by engineers. For engineers.'}],
    }


def generate_cinema_audio(voice=DEFAULT_VOICE, force=False):
    """
    Generate audio files for the cinematic technology showcase.

    Args:
        voice: edge-tts voice name (default: JennyNeural)
        force: regenerate even if files exist

    Returns:
        dict with manifest data and generation stats
    """
    scenes_data = get_cinema_scenes()
    return generate_demo_audio(
        scenes_data,
        output_dir='static/audio/cinema',
        voice=voice,
        force=force
    )


def get_demo_scenes_from_js():
    """
    Extract demo scene narration text from guide-system.js.
    This is a best-effort parser — it reads the demoScenes arrays.

    Returns: dict of {section_id: [{narration: str}, ...]}
    """
    js_path = Path('static/js/features/guide-system.js')
    if not js_path.exists():
        return {}

    content = js_path.read_text()
    scenes = {}

    # Parse sections with demoScenes
    import re

    # Find section definitions
    section_pattern = re.compile(
        r"(?:^|\n)\s+(\w+):\s*\{[^}]*?id:\s*'(\w+)'",
        re.MULTILINE
    )

    # Find demoScenes arrays
    demo_pattern = re.compile(
        r"demoScenes:\s*\[(.*?)\](?=,?\s*\n\s*\})",
        re.DOTALL
    )

    # Find narration strings
    narration_pattern = re.compile(
        r"narration:\s*['\"](.+?)['\"](?:\s*,|\s*\})",
        re.DOTALL
    )

    # Split content by section blocks
    # Each section starts with a key like "landing: {" and ends with "},"
    section_blocks = re.findall(
        r"(\w+):\s*\{[^{]*?id:\s*'(\w+)'.*?demoScenes:\s*\[(.*?)\]\s*\}",
        content,
        re.DOTALL
    )

    for _, section_id, demo_block in section_blocks:
        narrations = narration_pattern.findall(demo_block)
        if narrations:
            scenes[section_id] = [{'narration': n.replace("\\'", "'")} for n in narrations]

    return scenes
