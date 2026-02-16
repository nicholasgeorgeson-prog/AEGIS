/**
 * Style Presets Feature Module
 * ============================
 * Handles style guide preset selection and application.
 *
 * v3.4.0: Initial implementation
 *
 * Available Presets:
 * - microsoft: Microsoft Writing Style Guide
 * - google: Google Developer Documentation Style Guide
 * - plain_language: US Plain Language Guidelines
 * - asd_ste100: ASD Simplified Technical English
 * - government: US Government/Federal style
 * - aerospace: Aerospace/Defense documentation
 * - all_checks: Enable all 84 checkers
 * - minimal: Basic grammar and spelling only
 */

(function() {
    'use strict';

    const MODULE_NAME = 'StylePresets';
    const LOG_PREFIX = '[TWR StylePresets]';

    // Preset metadata for UI display
    const PRESET_INFO = {
        microsoft: {
            name: 'Microsoft Style',
            description: 'Clear, friendly, and inclusive technical documentation',
            icon: 'file-text'
        },
        google: {
            name: 'Google Style',
            description: 'Clear, concise, and accessible developer documentation',
            icon: 'code'
        },
        plain_language: {
            name: 'Plain Language',
            description: 'US Plain Language Guidelines - Clear government communication',
            icon: 'users'
        },
        asd_ste100: {
            name: 'ASD-STE100',
            description: 'Simplified Technical English for aerospace maintenance',
            icon: 'plane'
        },
        government: {
            name: 'Government Style',
            description: 'US Federal Government technical documentation standards',
            icon: 'landmark'
        },
        aerospace: {
            name: 'Aerospace/Defense',
            description: 'MIL-STD, DO-178, AS9100 compliant documentation',
            icon: 'rocket'
        },
        all_checks: {
            name: 'All Checks',
            description: 'Enable all 84 checkers for maximum coverage',
            icon: 'check-circle'
        },
        minimal: {
            name: 'Minimal',
            description: 'Basic grammar and spelling only - fastest performance',
            icon: 'zap'
        }
    };

    // Currently selected preset
    let currentPreset = null;

    /**
     * Initialize style presets feature
     */
    function init() {
        console.log(`${LOG_PREFIX} Initializing style presets`);

        // Bind preset button click handlers
        const presetButtons = document.querySelectorAll('.preset-btn[data-preset]');
        presetButtons.forEach(btn => {
            btn.addEventListener('click', handlePresetClick);
        });

        // Load saved preset preference
        loadSavedPreset();

        console.log(`${LOG_PREFIX} Initialized with ${presetButtons.length} preset buttons`);
    }

    /**
     * Handle preset button click
     */
    async function handlePresetClick(event) {
        const btn = event.currentTarget;
        const presetName = btn.dataset.preset;

        if (!presetName) return;

        console.log(`${LOG_PREFIX} Selected preset: ${presetName}`);

        // Update button states
        document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        // Show preset description
        showPresetDescription(presetName);

        // Apply preset
        await applyPreset(presetName);
    }

    /**
     * Show preset description in the UI
     */
    function showPresetDescription(presetName) {
        const descContainer = document.getElementById('preset-description');
        const nameEl = document.getElementById('preset-name');
        const descEl = document.getElementById('preset-desc');
        const countEl = document.getElementById('preset-checker-count');

        if (!descContainer) return;

        const info = PRESET_INFO[presetName];
        if (info) {
            if (nameEl) nameEl.textContent = info.name;
            if (descEl) descEl.textContent = info.description;
            if (countEl) countEl.textContent = 'Loading checker count...';
            descContainer.style.display = 'block';

            // Fetch checker count from API
            fetchPresetDetails(presetName);
        }
    }

    /**
     * Fetch preset details from API
     */
    async function fetchPresetDetails(presetName) {
        try {
            const response = await fetch(`/api/presets/${presetName}`, {
                headers: {
                    'X-CSRF-Token': window.CSRF_TOKEN || ''
                }
            });

            if (response.ok) {
                const data = await response.json();
                if (data.success && data.data) {
                    const checkerCount = Object.values(data.data.checkers || {}).filter(v => v).length;
                    const countEl = document.getElementById('preset-checker-count');
                    if (countEl) {
                        countEl.textContent = `${checkerCount} checkers enabled`;
                    }
                }
            }
        } catch (error) {
            console.warn(`${LOG_PREFIX} Failed to fetch preset details:`, error);
        }
    }

    /**
     * Apply a style preset
     */
    async function applyPreset(presetName) {
        try {
            // Call API to apply preset
            const response = await fetch(`/api/presets/${presetName}/apply`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': window.CSRF_TOKEN || ''
                },
                body: JSON.stringify({})
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();

            if (data.success && data.data) {
                // Update checker checkboxes in the profile grid
                updateCheckerGrid(data.data);

                // Save preset preference
                savePresetPreference(presetName);

                // Update current preset
                currentPreset = presetName;

                // Show success notification
                showNotification(`Applied ${PRESET_INFO[presetName]?.name || presetName} preset`, 'success');

                console.log(`${LOG_PREFIX} Applied preset: ${presetName}`);
            } else {
                throw new Error(data.error?.message || 'Failed to apply preset');
            }
        } catch (error) {
            console.error(`${LOG_PREFIX} Failed to apply preset:`, error);
            showNotification(`Failed to apply preset: ${error.message}`, 'error');
        }
    }

    /**
     * Update checker checkboxes based on preset options
     */
    function updateCheckerGrid(options) {
        const grid = document.getElementById('profile-checker-grid');
        if (!grid) return;

        // Map of option names to data-check values
        const optionToCheck = {
            'check_spelling': 'spelling',
            'check_grammar': 'grammar',
            'check_acronyms': 'acronyms',
            'check_passive_voice': 'passive_voice',
            'check_enhanced_passive': 'enhanced_passive',
            'check_weak_language': 'weak_language',
            'check_wordy_phrases': 'wordy_phrases',
            'check_nominalization': 'nominalization',
            'check_jargon': 'jargon',
            'check_ambiguous_pronouns': 'ambiguous_pronouns',
            'check_requirements_language': 'requirements_language',
            'check_gender_language': 'gender_language',
            'check_punctuation': 'punctuation',
            'check_sentence_length': 'sentence_length',
            'check_repeated_words': 'repeated_words',
            'check_capitalization': 'capitalization',
            'check_contractions': 'contractions',
            'check_references': 'references',
            'check_document_structure': 'document_structure',
            'check_tables_figures': 'tables_figures',
            'check_consistency': 'consistency',
            'check_lists': 'lists',
            'check_tbd': 'tbd',
            'check_testability': 'testability',
            'check_atomicity': 'atomicity',
            'check_escape_clauses': 'escape_clauses',
            'check_hyperlinks': 'hyperlinks',
            'check_orphan_headings': 'orphan_headings',
            'check_empty_sections': 'empty_sections',
            // v3.2.4 Enhanced Analyzers
            'check_semantic_analysis': 'semantic_analysis',
            'check_enhanced_acronyms': 'enhanced_acronyms',
            'check_prose_linting': 'prose_linting',
            'check_structure_analysis': 'structure_analysis',
            'check_text_statistics': 'text_statistics',
            // v3.3.0 NLP Suite
            'check_fragments_v2': 'fragments_v2',
            'check_requirements_analysis': 'requirements_analysis',
            'check_terminology_consistency': 'terminology_consistency',
            'check_cross_references': 'cross_references',
            'check_technical_dictionary': 'technical_dictionary',
            // v3.4.0 Maximum Coverage Suite
            'check_heading_case': 'heading_case',
            'check_contraction_consistency': 'contraction_consistency',
            'check_oxford_comma': 'oxford_comma',
            'check_ari': 'ari',
            'check_spache': 'spache',
            'check_dale_chall': 'dale_chall',
            'check_future_tense': 'future_tense',
            'check_latin_abbreviations': 'latin_abbreviations',
            'check_sentence_initial_conjunction': 'sentence_initial_conjunction',
            'check_directional_language': 'directional_language',
            'check_time_sensitive_language': 'time_sensitive_language',
            'check_acronym_first_use': 'acronym_first_use',
            'check_acronym_multiple_definition': 'acronym_multiple_definition',
            'check_imperative_mood': 'imperative_mood',
            'check_second_person': 'second_person',
            'check_link_text_quality': 'link_text_quality',
            'check_numbered_list_sequence': 'numbered_list_sequence',
            'check_product_name_consistency': 'product_name_consistency',
            'check_cross_reference_targets': 'cross_reference_targets',
            'check_code_formatting': 'code_formatting',
            'check_mil_std_40051': 'mil_std_40051',
            'check_s1000d': 's1000d',
            'check_as9100': 'as9100',
            'check_mil_std': 'mil_std',
            'check_do178': 'do178',
            'check_accessibility': 'accessibility',
            'check_hedging': 'hedging',
            'check_weasel_words': 'weasel_words',
            'check_cliches': 'cliches',
            'check_redundancy': 'redundancy',
            'check_units': 'units',
            'check_terminology': 'terminology',
            'check_roles': 'roles'
        };

        // Update each checkbox
        for (const [optionName, enabled] of Object.entries(options)) {
            const checkName = optionToCheck[optionName];
            if (checkName) {
                const checkbox = grid.querySelector(`input[data-check="${checkName}"]`);
                if (checkbox) {
                    checkbox.checked = enabled;
                }
            }
        }

        console.log(`${LOG_PREFIX} Updated checker grid with ${Object.keys(options).length} options`);
    }

    /**
     * Save preset preference to localStorage
     */
    function savePresetPreference(presetName) {
        try {
            localStorage.setItem('twr-style-preset', presetName);
        } catch (e) {
            console.warn(`${LOG_PREFIX} Failed to save preset preference:`, e);
        }
    }

    /**
     * Load saved preset preference
     */
    function loadSavedPreset() {
        try {
            const savedPreset = localStorage.getItem('twr-style-preset');
            if (savedPreset && PRESET_INFO[savedPreset]) {
                // Mark the saved preset button as active
                const btn = document.querySelector(`.preset-btn[data-preset="${savedPreset}"]`);
                if (btn) {
                    btn.classList.add('active');
                    showPresetDescription(savedPreset);
                    currentPreset = savedPreset;
                    console.log(`${LOG_PREFIX} Restored saved preset: ${savedPreset}`);
                }
            }
        } catch (e) {
            console.warn(`${LOG_PREFIX} Failed to load preset preference:`, e);
        }
    }

    /**
     * Show notification
     */
    function showNotification(message, type = 'info') {
        // Use TWR notification system if available
        if (window.TWR?.Utils?.showNotification) {
            TWR.Utils.showNotification(message, type);
        } else if (window.showNotification) {
            window.showNotification(message, type);
        } else {
            console.log(`${LOG_PREFIX} [${type}] ${message}`);
        }
    }

    /**
     * Get current preset
     */
    function getCurrentPreset() {
        return currentPreset;
    }

    /**
     * Get preset options for a preset name
     */
    async function getPresetOptions(presetName) {
        try {
            const response = await fetch(`/api/presets/${presetName}`, {
                headers: {
                    'X-CSRF-Token': window.CSRF_TOKEN || ''
                }
            });

            if (response.ok) {
                const data = await response.json();
                if (data.success && data.data) {
                    return data.data.checkers || {};
                }
            }
        } catch (error) {
            console.warn(`${LOG_PREFIX} Failed to get preset options:`, error);
        }
        return {};
    }

    // Initialize on DOMContentLoaded
    document.addEventListener('DOMContentLoaded', init);

    // Export to window for external access
    window.TWR = window.TWR || {};
    window.TWR.StylePresets = {
        init,
        applyPreset,
        getCurrentPreset,
        getPresetOptions,
        PRESET_INFO
    };

})();
