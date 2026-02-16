"""
AEGIS - Enhanced Text Statistics Module
Version: 1.0.0
Created: February 3, 2026

Provides comprehensive text analysis and statistics using textacy and other NLP tools.
Designed for technical document quality assessment.

Features:
- Readability metrics (Flesch, Gunning Fog, SMOG, etc.)
- Text complexity analysis
- Vocabulary richness metrics (TTR, Hapax Legomena, etc.)
- Sentence structure analysis
- Technical writing metrics
- Keyword extraction
- N-gram analysis
- Air-gap compatible (no external API calls)

Usage:
    from text_statistics import TextStatistics

    stats = TextStatistics()
    results = stats.analyze(document_text)

    # Get specific metrics
    readability = stats.get_readability_scores(document_text)
    complexity = stats.get_complexity_metrics(document_text)
"""

import re
import math
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import Counter, defaultdict
from dataclasses import dataclass
import string

# Optional imports - graceful degradation
try:
    import textstat
    TEXTSTAT_AVAILABLE = True
except ImportError:
    TEXTSTAT_AVAILABLE = False

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import nltk
    from nltk.tokenize import word_tokenize, sent_tokenize
    from nltk.corpus import stopwords
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False


class TextStatistics:
    """
    Comprehensive text statistics and analysis.
    """

    VERSION = '1.0.0'

    # Dale-Chall easy word list (subset - full list has ~3000 words)
    EASY_WORDS = {
        'a', 'about', 'above', 'after', 'again', 'all', 'also', 'always', 'am',
        'an', 'and', 'any', 'are', 'as', 'at', 'back', 'be', 'been', 'before',
        'being', 'below', 'between', 'both', 'but', 'by', 'came', 'can', 'come',
        'could', 'did', 'do', 'does', 'done', 'down', 'each', 'even', 'every',
        'few', 'first', 'for', 'from', 'get', 'go', 'going', 'good', 'got',
        'had', 'has', 'have', 'he', 'her', 'here', 'him', 'his', 'how', 'i',
        'if', 'in', 'into', 'is', 'it', 'its', 'just', 'know', 'last', 'left',
        'let', 'like', 'little', 'long', 'look', 'made', 'make', 'man', 'many',
        'may', 'me', 'men', 'might', 'more', 'most', 'much', 'must', 'my',
        'name', 'never', 'new', 'no', 'not', 'now', 'of', 'off', 'old', 'on',
        'once', 'one', 'only', 'or', 'other', 'our', 'out', 'over', 'own',
        'part', 'people', 'place', 'put', 'right', 'said', 'same', 'saw', 'say',
        'see', 'she', 'should', 'show', 'small', 'so', 'some', 'still', 'such',
        'take', 'tell', 'than', 'that', 'the', 'their', 'them', 'then', 'there',
        'these', 'they', 'thing', 'think', 'this', 'those', 'three', 'through',
        'time', 'to', 'too', 'two', 'under', 'up', 'upon', 'us', 'use', 'very',
        'want', 'was', 'way', 'we', 'well', 'went', 'were', 'what', 'when',
        'where', 'which', 'while', 'who', 'will', 'with', 'without', 'work',
        'would', 'year', 'yes', 'yet', 'you', 'your'
    }

    # Technical writing stopwords to exclude from keyword analysis
    TECH_STOPWORDS = {
        'shall', 'will', 'must', 'should', 'may', 'can', 'could', 'would',
        'including', 'included', 'include', 'following', 'follows', 'per',
        'via', 'i.e.', 'e.g.', 'etc.', 'et al.', 'ibid.', 'op. cit.',
        'see', 'refer', 'reference', 'noted', 'note', 'notes',
        'section', 'paragraph', 'chapter', 'appendix', 'figure', 'table',
        'item', 'items', 'part', 'parts', 'page', 'pages',
    }

    # Syllable counting exceptions
    SYLLABLE_EXCEPTIONS = {
        'simile': 3, 'forever': 3, 'shoreline': 2, 'define': 2,
        'everything': 4, 'another': 3, 'higher': 2, 'business': 3,
        'area': 3, 'idea': 3, 'real': 1, 'create': 2, 'science': 2,
    }

    def __init__(self, use_spacy: bool = True):
        """
        Initialize text statistics analyzer.

        Args:
            use_spacy: Whether to use spaCy for enhanced analysis
        """
        self.nlp = None
        self.stopwords = set()

        # Initialize spaCy
        if use_spacy and SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load('en_core_web_sm')
            except OSError:
                pass

        # Initialize stopwords
        if NLTK_AVAILABLE:
            try:
                self.stopwords = set(stopwords.words('english'))
            except LookupError:
                # v5.0.0: Try offline download only (raise_on_error=False prevents network calls
                # when NLTK_DATA env var points to local data). Never call out to internet.
                try:
                    nltk.download('stopwords', quiet=True, raise_on_error=False)
                    nltk.download('punkt', quiet=True, raise_on_error=False)
                    self.stopwords = set(stopwords.words('english'))
                except Exception:
                    pass  # Fallback stopwords will be used below

        # Fallback stopwords if NLTK not available
        if not self.stopwords:
            self.stopwords = {
                'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
                'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are',
                'were', 'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did',
                'will', 'would', 'could', 'should', 'may', 'might', 'can',
                'this', 'that', 'these', 'those', 'it', 'its', 'they', 'them',
                'their', 'we', 'our', 'you', 'your', 'he', 'she', 'his', 'her',
            }

        self.stopwords.update(self.TECH_STOPWORDS)

    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Perform comprehensive text analysis.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with all analysis results
        """
        if not text or not text.strip():
            return {'error': 'Empty text provided'}

        # Basic counts
        basic = self._basic_statistics(text)

        # Readability
        readability = self.get_readability_scores(text)

        # Complexity
        complexity = self.get_complexity_metrics(text)

        # Vocabulary
        vocabulary = self.get_vocabulary_metrics(text)

        # Sentence analysis
        sentences = self.get_sentence_analysis(text)

        # Keywords
        keywords = self.extract_keywords(text)

        # N-grams
        ngrams = self.get_ngram_analysis(text)

        # Technical writing metrics
        technical = self.get_technical_writing_metrics(text)

        return {
            'version': self.VERSION,
            'basic': basic,
            'readability': readability,
            'complexity': complexity,
            'vocabulary': vocabulary,
            'sentences': sentences,
            'keywords': keywords,
            'ngrams': ngrams,
            'technical': technical,
            'summary': self._generate_summary(basic, readability, complexity, vocabulary)
        }

    # ==========================================================================
    # BASIC STATISTICS
    # ==========================================================================

    def _basic_statistics(self, text: str) -> Dict[str, Any]:
        """Calculate basic text statistics."""
        # Character counts
        char_count = len(text)
        char_count_no_spaces = len(text.replace(' ', '').replace('\n', '').replace('\t', ''))

        # Word counts
        words = self._tokenize_words(text)
        word_count = len(words)

        # Sentence counts
        sentences = self._tokenize_sentences(text)
        sentence_count = len(sentences)

        # Paragraph counts
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        paragraph_count = len(paragraphs)

        # Syllable count
        syllable_count = sum(self._count_syllables(w) for w in words)

        # Averages
        avg_word_length = char_count_no_spaces / word_count if word_count else 0
        avg_sentence_length = word_count / sentence_count if sentence_count else 0
        avg_syllables_per_word = syllable_count / word_count if word_count else 0
        avg_paragraph_length = word_count / paragraph_count if paragraph_count else 0

        return {
            'character_count': char_count,
            'character_count_no_spaces': char_count_no_spaces,
            'word_count': word_count,
            'sentence_count': sentence_count,
            'paragraph_count': paragraph_count,
            'syllable_count': syllable_count,
            'avg_word_length': round(avg_word_length, 2),
            'avg_sentence_length': round(avg_sentence_length, 2),
            'avg_syllables_per_word': round(avg_syllables_per_word, 2),
            'avg_paragraph_length': round(avg_paragraph_length, 2),
            'reading_time_minutes': round(word_count / 200, 1),  # 200 WPM average
            'speaking_time_minutes': round(word_count / 150, 1),  # 150 WPM average
        }

    # ==========================================================================
    # READABILITY METRICS
    # ==========================================================================

    def get_readability_scores(self, text: str) -> Dict[str, Any]:
        """
        Calculate readability scores.

        Returns multiple readability metrics suitable for different audiences.
        """
        if TEXTSTAT_AVAILABLE:
            return self._readability_with_textstat(text)
        else:
            return self._readability_manual(text)

    def _readability_with_textstat(self, text: str) -> Dict[str, Any]:
        """Calculate readability using textstat library."""
        return {
            'flesch_reading_ease': textstat.flesch_reading_ease(text),
            'flesch_kincaid_grade': textstat.flesch_kincaid_grade(text),
            'smog_index': textstat.smog_index(text),
            'coleman_liau_index': textstat.coleman_liau_index(text),
            'automated_readability_index': textstat.automated_readability_index(text),
            'dale_chall_readability_score': textstat.dale_chall_readability_score(text),
            'linsear_write_formula': textstat.linsear_write_formula(text),
            'gunning_fog': textstat.gunning_fog(text),
            'text_standard': textstat.text_standard(text),
            'difficult_words': textstat.difficult_words(text),
            'interpretation': self._interpret_readability(
                textstat.flesch_reading_ease(text),
                textstat.flesch_kincaid_grade(text)
            )
        }

    def _readability_manual(self, text: str) -> Dict[str, Any]:
        """Calculate readability manually (fallback)."""
        words = self._tokenize_words(text)
        sentences = self._tokenize_sentences(text)

        word_count = len(words)
        sentence_count = len(sentences)
        syllable_count = sum(self._count_syllables(w) for w in words)

        # Complex words (3+ syllables)
        complex_words = sum(1 for w in words if self._count_syllables(w) >= 3)

        # Calculate metrics
        if word_count == 0 or sentence_count == 0:
            return {'error': 'Insufficient text for readability analysis'}

        # Flesch Reading Ease
        # 206.835 - 1.015 * (words/sentences) - 84.6 * (syllables/words)
        fre = 206.835 - 1.015 * (word_count / sentence_count) - 84.6 * (syllable_count / word_count)

        # Flesch-Kincaid Grade Level
        # 0.39 * (words/sentences) + 11.8 * (syllables/words) - 15.59
        fkg = 0.39 * (word_count / sentence_count) + 11.8 * (syllable_count / word_count) - 15.59

        # Gunning Fog Index
        # 0.4 * ((words/sentences) + 100 * (complex_words/words))
        fog = 0.4 * ((word_count / sentence_count) + 100 * (complex_words / word_count))

        # SMOG Index (Simple Measure of Gobbledygook)
        # 1.043 * sqrt(complex_words * (30/sentences)) + 3.1291
        smog = 1.043 * math.sqrt(complex_words * (30 / sentence_count)) + 3.1291 if sentence_count >= 30 else None

        # Automated Readability Index
        # 4.71 * (characters/words) + 0.5 * (words/sentences) - 21.43
        char_count = sum(len(w) for w in words)
        ari = 4.71 * (char_count / word_count) + 0.5 * (word_count / sentence_count) - 21.43

        # Coleman-Liau Index
        # 0.0588 * L - 0.296 * S - 15.8
        # L = avg letters per 100 words, S = avg sentences per 100 words
        L = (char_count / word_count) * 100
        S = (sentence_count / word_count) * 100
        cli = 0.0588 * L - 0.296 * S - 15.8

        return {
            'flesch_reading_ease': round(fre, 2),
            'flesch_kincaid_grade': round(fkg, 2),
            'gunning_fog': round(fog, 2),
            'smog_index': round(smog, 2) if smog else None,
            'automated_readability_index': round(ari, 2),
            'coleman_liau_index': round(cli, 2),
            'complex_word_count': complex_words,
            'complex_word_percentage': round(complex_words / word_count * 100, 2),
            'interpretation': self._interpret_readability(fre, fkg),
            'note': 'Install textstat for additional metrics'
        }

    def _interpret_readability(self, flesch_ease: float, flesch_grade: float) -> Dict[str, str]:
        """Interpret readability scores."""
        # Flesch Reading Ease interpretation
        if flesch_ease >= 90:
            ease_level = "Very Easy"
            ease_audience = "5th grade"
        elif flesch_ease >= 80:
            ease_level = "Easy"
            ease_audience = "6th grade"
        elif flesch_ease >= 70:
            ease_level = "Fairly Easy"
            ease_audience = "7th grade"
        elif flesch_ease >= 60:
            ease_level = "Standard"
            ease_audience = "8th-9th grade"
        elif flesch_ease >= 50:
            ease_level = "Fairly Difficult"
            ease_audience = "10th-12th grade"
        elif flesch_ease >= 30:
            ease_level = "Difficult"
            ease_audience = "College"
        else:
            ease_level = "Very Difficult"
            ease_audience = "College graduate"

        # Grade level interpretation
        if flesch_grade <= 6:
            grade_level = "Elementary school"
        elif flesch_grade <= 8:
            grade_level = "Middle school"
        elif flesch_grade <= 12:
            grade_level = "High school"
        elif flesch_grade <= 16:
            grade_level = "College"
        else:
            grade_level = "Graduate level"

        return {
            'flesch_level': ease_level,
            'flesch_audience': ease_audience,
            'grade_level': grade_level,
            'recommendation': self._get_readability_recommendation(flesch_ease)
        }

    def _get_readability_recommendation(self, flesch_ease: float) -> str:
        """Get recommendation based on readability."""
        if flesch_ease < 30:
            return "Consider simplifying: use shorter sentences and common words"
        elif flesch_ease < 50:
            return "Acceptable for technical documents; consider simplifying for general audience"
        elif flesch_ease < 60:
            return "Good readability for professional documents"
        elif flesch_ease < 70:
            return "Good readability; appropriate for most audiences"
        else:
            return "Excellent readability"

    # ==========================================================================
    # COMPLEXITY METRICS
    # ==========================================================================

    def get_complexity_metrics(self, text: str) -> Dict[str, Any]:
        """Calculate text complexity metrics."""
        words = self._tokenize_words(text)
        sentences = self._tokenize_sentences(text)

        if not words or not sentences:
            return {'error': 'Insufficient text'}

        # Sentence length distribution
        sentence_lengths = [len(self._tokenize_words(s)) for s in sentences]

        # Word length distribution
        word_lengths = [len(w) for w in words]

        # Long words (7+ characters)
        long_words = [w for w in words if len(w) >= 7]

        # Very long sentences (30+ words)
        long_sentences = [s for s in sentences if len(self._tokenize_words(s)) >= 30]

        # Sentence complexity via clause detection (approximation)
        clause_markers = ['which', 'who', 'that', 'because', 'although', 'while',
                         'when', 'where', 'if', 'unless', 'whereas', 'whereby']
        complex_sentences = sum(1 for s in sentences
                               if any(marker in s.lower() for marker in clause_markers))

        return {
            'avg_sentence_length': round(sum(sentence_lengths) / len(sentence_lengths), 2),
            'sentence_length_std': round(self._std_dev(sentence_lengths), 2),
            'max_sentence_length': max(sentence_lengths),
            'min_sentence_length': min(sentence_lengths),
            'long_sentence_count': len(long_sentences),
            'long_sentence_percentage': round(len(long_sentences) / len(sentences) * 100, 2),
            'avg_word_length': round(sum(word_lengths) / len(word_lengths), 2),
            'long_word_count': len(long_words),
            'long_word_percentage': round(len(long_words) / len(words) * 100, 2),
            'complex_sentence_count': complex_sentences,
            'complex_sentence_percentage': round(complex_sentences / len(sentences) * 100, 2),
            'sentence_length_distribution': self._get_distribution(sentence_lengths),
            'word_length_distribution': self._get_distribution(word_lengths)
        }

    def _get_distribution(self, values: List[int]) -> Dict[str, int]:
        """Get distribution of values in buckets."""
        if not values:
            return {}

        counter = Counter(values)
        return dict(sorted(counter.items()))

    def _std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance)

    # ==========================================================================
    # VOCABULARY METRICS
    # ==========================================================================

    def get_vocabulary_metrics(self, text: str) -> Dict[str, Any]:
        """Calculate vocabulary richness metrics."""
        words = self._tokenize_words(text)
        words_lower = [w.lower() for w in words]

        if not words:
            return {'error': 'No words found'}

        word_count = len(words)
        unique_words = set(words_lower)
        unique_count = len(unique_words)

        # Type-Token Ratio (TTR)
        ttr = unique_count / word_count

        # Standardized TTR (per 100 words) - more stable for varying text lengths
        sttr = self._calculate_sttr(words_lower)

        # Hapax Legomena (words appearing exactly once)
        word_freq = Counter(words_lower)
        hapax = [w for w, c in word_freq.items() if c == 1]
        hapax_ratio = len(hapax) / unique_count if unique_count else 0

        # Dis Legomena (words appearing exactly twice)
        dis = [w for w, c in word_freq.items() if c == 2]

        # Yule's K (vocabulary richness measure)
        yules_k = self._calculate_yules_k(word_freq)

        # Most common words (excluding stopwords)
        content_words = [w for w in words_lower if w not in self.stopwords and len(w) > 2]
        most_common = Counter(content_words).most_common(20)

        # Difficult words (not in easy word list)
        difficult_words = [w for w in words_lower
                         if w not in self.EASY_WORDS and len(w) > 2 and w.isalpha()]

        return {
            'total_words': word_count,
            'unique_words': unique_count,
            'type_token_ratio': round(ttr, 4),
            'standardized_ttr': round(sttr, 4) if sttr else None,
            'hapax_legomena_count': len(hapax),
            'hapax_legomena_ratio': round(hapax_ratio, 4),
            'dis_legomena_count': len(dis),
            'yules_k': round(yules_k, 2) if yules_k else None,
            'vocabulary_density': round(unique_count / word_count * 100, 2),
            'most_common_words': most_common,
            'difficult_word_count': len(set(difficult_words)),
            'difficult_word_percentage': round(len(set(difficult_words)) / unique_count * 100, 2) if unique_count else 0,
            'avg_word_frequency': round(word_count / unique_count, 2) if unique_count else 0
        }

    def _calculate_sttr(self, words: List[str], window: int = 100) -> Optional[float]:
        """Calculate Standardized Type-Token Ratio."""
        if len(words) < window:
            return None

        ttrs = []
        for i in range(0, len(words) - window + 1, window):
            segment = words[i:i + window]
            ttrs.append(len(set(segment)) / len(segment))

        return sum(ttrs) / len(ttrs) if ttrs else None

    def _calculate_yules_k(self, word_freq: Counter) -> Optional[float]:
        """
        Calculate Yule's K (vocabulary richness).
        Lower K means richer vocabulary.
        """
        freq_of_freq = Counter(word_freq.values())
        N = sum(word_freq.values())

        if N == 0:
            return None

        M1 = N
        M2 = sum(freq * (count ** 2) for freq, count in freq_of_freq.items())

        if M1 == M2:
            return 0

        K = 10000 * (M2 - M1) / (M1 ** 2)
        return K

    # ==========================================================================
    # SENTENCE ANALYSIS
    # ==========================================================================

    def get_sentence_analysis(self, text: str) -> Dict[str, Any]:
        """Analyze sentence structures."""
        sentences = self._tokenize_sentences(text)

        if not sentences:
            return {'error': 'No sentences found'}

        # Sentence type classification (approximation)
        sentence_types = {
            'declarative': 0,  # Ends with period
            'interrogative': 0,  # Ends with ?
            'exclamatory': 0,  # Ends with !
            'imperative': 0,  # Starts with verb (approximation)
        }

        # Starting word analysis
        starting_words = []

        for s in sentences:
            s = s.strip()
            if not s:
                continue

            # Classify by ending punctuation
            if s.endswith('?'):
                sentence_types['interrogative'] += 1
            elif s.endswith('!'):
                sentence_types['exclamatory'] += 1
            else:
                sentence_types['declarative'] += 1

            # Get starting word
            words = s.split()
            if words:
                starting_words.append(words[0].lower())

        # Sentence starters diversity
        starter_diversity = len(set(starting_words)) / len(starting_words) if starting_words else 0

        # Common sentence starters
        starter_counter = Counter(starting_words)
        common_starters = starter_counter.most_common(10)

        # Repeated starters (appearing 3+ times)
        repeated_starters = [(w, c) for w, c in starter_counter.items() if c >= 3]

        return {
            'total_sentences': len(sentences),
            'sentence_types': sentence_types,
            'sentence_type_percentages': {
                k: round(v / len(sentences) * 100, 2) for k, v in sentence_types.items()
            },
            'starter_diversity': round(starter_diversity, 4),
            'common_starters': common_starters,
            'repeated_starters': repeated_starters,
            'recommendation': self._get_sentence_recommendation(starter_diversity, repeated_starters)
        }

    def _get_sentence_recommendation(self, diversity: float, repeated: List) -> str:
        """Get recommendation for sentence variety."""
        if diversity < 0.5:
            return "Low sentence variety. Consider varying sentence beginnings."
        elif repeated and any(c > 5 for _, c in repeated):
            return f"Consider reducing repetition of sentence starters."
        elif diversity < 0.7:
            return "Moderate sentence variety. Some room for improvement."
        else:
            return "Good sentence variety."

    # ==========================================================================
    # KEYWORD EXTRACTION
    # ==========================================================================

    def extract_keywords(self, text: str, top_n: int = 20) -> Dict[str, Any]:
        """Extract keywords using multiple methods."""
        words = self._tokenize_words(text)
        words_lower = [w.lower() for w in words]

        # Method 1: Frequency-based (excluding stopwords)
        content_words = [w for w in words_lower
                        if w not in self.stopwords and len(w) > 2 and w.isalpha()]
        freq_keywords = Counter(content_words).most_common(top_n)

        # Method 2: TF-IDF (if sklearn available)
        tfidf_keywords = []
        if SKLEARN_AVAILABLE:
            tfidf_keywords = self._extract_tfidf_keywords(text, top_n)

        # Method 3: Noun phrases (if spaCy available)
        noun_phrases = []
        if self.nlp:
            noun_phrases = self._extract_noun_phrases(text, top_n)

        # Combine and rank
        combined = self._combine_keywords(freq_keywords, tfidf_keywords, noun_phrases)

        return {
            'frequency_based': freq_keywords,
            'tfidf_based': tfidf_keywords,
            'noun_phrases': noun_phrases,
            'combined_top': combined[:top_n],
            'keyword_density': self._calculate_keyword_density(text, [k for k, _ in combined[:10]])
        }

    def _extract_tfidf_keywords(self, text: str, top_n: int) -> List[Tuple[str, float]]:
        """Extract keywords using TF-IDF."""
        try:
            # Split into sentences as "documents"
            sentences = self._tokenize_sentences(text)
            if len(sentences) < 2:
                return []

            vectorizer = TfidfVectorizer(
                stop_words='english',
                max_features=100,
                ngram_range=(1, 2)
            )
            tfidf_matrix = vectorizer.fit_transform(sentences)

            # Get feature names and their average TF-IDF scores
            feature_names = vectorizer.get_feature_names_out()
            avg_scores = tfidf_matrix.mean(axis=0).A1

            # Sort by score
            sorted_indices = avg_scores.argsort()[::-1]
            keywords = [(feature_names[i], round(avg_scores[i], 4))
                       for i in sorted_indices[:top_n]]

            return keywords
        except Exception:
            return []

    def _extract_noun_phrases(self, text: str, top_n: int) -> List[Tuple[str, int]]:
        """Extract noun phrases using spaCy."""
        try:
            doc = self.nlp(text)
            noun_chunks = [chunk.text.lower() for chunk in doc.noun_chunks
                         if len(chunk.text) > 3 and chunk.text.lower() not in self.stopwords]
            return Counter(noun_chunks).most_common(top_n)
        except Exception:
            return []

    def _combine_keywords(self,
                         freq: List[Tuple[str, int]],
                         tfidf: List[Tuple[str, float]],
                         nouns: List[Tuple[str, int]]) -> List[Tuple[str, float]]:
        """Combine keywords from different methods."""
        scores = defaultdict(float)

        # Normalize and combine
        for i, (word, _) in enumerate(freq):
            scores[word] += (len(freq) - i) / len(freq)  # Higher rank = higher score

        for i, (word, score) in enumerate(tfidf):
            scores[word] += score * 2  # Weight TF-IDF higher

        for i, (phrase, count) in enumerate(nouns):
            scores[phrase] += (len(nouns) - i) / len(nouns)

        # Sort by combined score
        sorted_keywords = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_keywords

    def _calculate_keyword_density(self, text: str, keywords: List[str]) -> Dict[str, float]:
        """Calculate density of top keywords."""
        words = self._tokenize_words(text)
        word_count = len(words)
        text_lower = text.lower()

        densities = {}
        for keyword in keywords:
            count = text_lower.count(keyword.lower())
            densities[keyword] = round(count / word_count * 100, 3) if word_count else 0

        return densities

    # ==========================================================================
    # N-GRAM ANALYSIS
    # ==========================================================================

    def get_ngram_analysis(self, text: str, max_n: int = 4) -> Dict[str, Any]:
        """Analyze n-grams in text."""
        words = self._tokenize_words(text)
        words_lower = [w.lower() for w in words]

        results = {}

        for n in range(2, max_n + 1):
            ngrams = self._get_ngrams(words_lower, n)

            # Filter out ngrams with stopwords at start/end
            filtered = [(ng, c) for ng, c in ngrams
                       if ng[0] not in self.stopwords and ng[-1] not in self.stopwords]

            results[f'{n}_grams'] = [(' '.join(ng), c) for ng, c in filtered[:15]]

        # Find repeated phrases (3+ occurrences)
        repeated_phrases = []
        for n in range(3, 6):  # 3 to 5 word phrases
            ngrams = self._get_ngrams(words_lower, n)
            repeated = [(ng, c) for ng, c in ngrams if c >= 3]
            repeated_phrases.extend([(' '.join(ng), c) for ng, c in repeated])

        results['repeated_phrases'] = sorted(repeated_phrases, key=lambda x: (-x[1], -len(x[0].split())))[:20]

        return results

    def _get_ngrams(self, words: List[str], n: int) -> List[Tuple[Tuple[str, ...], int]]:
        """Get n-grams and their frequencies."""
        if len(words) < n:
            return []

        ngrams = [tuple(words[i:i+n]) for i in range(len(words) - n + 1)]
        return Counter(ngrams).most_common(50)

    # ==========================================================================
    # TECHNICAL WRITING METRICS
    # ==========================================================================

    def get_technical_writing_metrics(self, text: str) -> Dict[str, Any]:
        """Calculate metrics specific to technical writing."""
        words = self._tokenize_words(text)
        sentences = self._tokenize_sentences(text)

        # Passive voice detection
        passive_count = self._count_passive_voice(text)
        passive_percentage = passive_count / len(sentences) * 100 if sentences else 0

        # Shall/will/must usage
        requirements_words = {
            'shall': 0, 'will': 0, 'must': 0, 'should': 0, 'may': 0, 'can': 0
        }
        for word in words:
            if word.lower() in requirements_words:
                requirements_words[word.lower()] += 1

        # Acronym detection
        acronyms = re.findall(r'\b[A-Z]{2,}\b', text)
        acronym_count = len(acronyms)
        unique_acronyms = set(acronyms)

        # Numbers and measurements
        numbers = re.findall(r'\b\d+(?:\.\d+)?\b', text)
        measurements = re.findall(r'\b\d+(?:\.\d+)?\s*(?:mm|cm|m|km|in|ft|yd|mi|g|kg|lb|oz|ml|L|gal|°[CF]|%)\b', text)

        # Lists detection
        bullet_points = len(re.findall(r'^\s*[•●○◦▪▫-]\s', text, re.MULTILINE))
        numbered_items = len(re.findall(r'^\s*\d+[.)]\s', text, re.MULTILINE))

        # Jargon density (long words as proxy)
        jargon_words = [w for w in words if len(w) > 10]

        return {
            'passive_voice_count': passive_count,
            'passive_voice_percentage': round(passive_percentage, 2),
            'requirements_language': requirements_words,
            'acronym_count': acronym_count,
            'unique_acronyms': len(unique_acronyms),
            'acronym_list': list(unique_acronyms)[:20],
            'number_count': len(numbers),
            'measurement_count': len(measurements),
            'bullet_points': bullet_points,
            'numbered_items': numbered_items,
            'list_usage': bullet_points + numbered_items,
            'jargon_word_count': len(jargon_words),
            'jargon_percentage': round(len(jargon_words) / len(words) * 100, 2) if words else 0,
            'recommendations': self._get_technical_recommendations(
                passive_percentage, requirements_words, len(unique_acronyms)
            )
        }

    def _count_passive_voice(self, text: str) -> int:
        """Count passive voice constructions."""
        passive_patterns = [
            r'\b(is|are|was|were|been|being|be)\s+\w+ed\b',
            r'\b(is|are|was|were|been|being|be)\s+\w+en\b',
            r'\bhas been\s+\w+ed\b',
            r'\bhave been\s+\w+ed\b',
        ]

        count = 0
        for pattern in passive_patterns:
            count += len(re.findall(pattern, text, re.IGNORECASE))
        return count

    def _get_technical_recommendations(self,
                                       passive_pct: float,
                                       requirements: Dict[str, int],
                                       acronym_count: int) -> List[str]:
        """Get recommendations for technical writing."""
        recommendations = []

        if passive_pct > 30:
            recommendations.append(f"High passive voice usage ({passive_pct:.1f}%). Consider using more active voice.")

        if requirements['shall'] > 0 and requirements['must'] > 0:
            recommendations.append("Mixed 'shall' and 'must' usage. Consider standardizing on one for consistency.")

        if requirements['should'] > requirements['shall']:
            recommendations.append("More 'should' than 'shall'. Verify requirements clarity - 'shall' indicates mandatory.")

        if acronym_count > 20:
            recommendations.append(f"High acronym count ({acronym_count}). Consider a glossary or definitions section.")

        if not recommendations:
            recommendations.append("Technical writing metrics look good.")

        return recommendations

    # ==========================================================================
    # UTILITY METHODS
    # ==========================================================================

    def _tokenize_words(self, text: str) -> List[str]:
        """Tokenize text into words."""
        if NLTK_AVAILABLE:
            try:
                return word_tokenize(text)
            except:
                pass

        # Fallback: simple tokenization
        words = re.findall(r'\b[a-zA-Z]+(?:\'[a-zA-Z]+)?\b', text)
        return words

    def _tokenize_sentences(self, text: str) -> List[str]:
        """Tokenize text into sentences."""
        if NLTK_AVAILABLE:
            try:
                return sent_tokenize(text)
            except:
                pass

        # Fallback: simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        return [s.strip() for s in sentences if s.strip()]

    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word."""
        word = word.lower().strip()

        # Check exceptions
        if word in self.SYLLABLE_EXCEPTIONS:
            return self.SYLLABLE_EXCEPTIONS[word]

        # Remove non-letters
        word = re.sub(r'[^a-z]', '', word)

        if not word:
            return 0

        # Count vowel groups
        count = 0
        vowels = 'aeiouy'
        prev_was_vowel = False

        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_was_vowel:
                count += 1
            prev_was_vowel = is_vowel

        # Adjust for silent e
        if word.endswith('e') and count > 1:
            count -= 1

        # Adjust for -le ending
        if word.endswith('le') and len(word) > 2 and word[-3] not in vowels:
            count += 1

        # Ensure at least one syllable
        return max(count, 1)

    def _generate_summary(self,
                         basic: Dict,
                         readability: Dict,
                         complexity: Dict,
                         vocabulary: Dict) -> Dict[str, Any]:
        """Generate an executive summary of the analysis."""
        return {
            'word_count': basic.get('word_count', 0),
            'reading_time': basic.get('reading_time_minutes', 0),
            'grade_level': readability.get('interpretation', {}).get('grade_level', 'Unknown'),
            'readability_level': readability.get('interpretation', {}).get('flesch_level', 'Unknown'),
            'vocabulary_richness': 'High' if vocabulary.get('type_token_ratio', 0) > 0.5 else 'Moderate' if vocabulary.get('type_token_ratio', 0) > 0.3 else 'Low',
            'complexity_level': 'High' if complexity.get('complex_sentence_percentage', 0) > 40 else 'Moderate' if complexity.get('complex_sentence_percentage', 0) > 20 else 'Low',
            'overall_assessment': self._get_overall_assessment(readability, complexity, vocabulary)
        }

    def _get_overall_assessment(self,
                               readability: Dict,
                               complexity: Dict,
                               vocabulary: Dict) -> str:
        """Get overall document assessment."""
        flesch = readability.get('flesch_reading_ease', 50)
        complex_pct = complexity.get('complex_sentence_percentage', 0)
        ttr = vocabulary.get('type_token_ratio', 0)

        if flesch >= 60 and complex_pct < 30 and ttr > 0.4:
            return "Well-balanced: readable, appropriately complex, varied vocabulary"
        elif flesch < 40:
            return "Consider simplifying for broader audience"
        elif complex_pct > 40:
            return "High complexity - may benefit from shorter sentences"
        elif ttr < 0.3:
            return "Low vocabulary diversity - consider varying word choice"
        else:
            return "Acceptable for technical documentation"


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def analyze_text(text: str) -> Dict[str, Any]:
    """Quick function to analyze text."""
    stats = TextStatistics()
    return stats.analyze(text)


def get_readability(text: str) -> Dict[str, Any]:
    """Quick function to get readability scores."""
    stats = TextStatistics()
    return stats.get_readability_scores(text)


def get_keywords(text: str, top_n: int = 20) -> List[Tuple[str, Any]]:
    """Quick function to extract keywords."""
    stats = TextStatistics()
    result = stats.extract_keywords(text, top_n)
    return result.get('combined_top', [])


# =============================================================================
# CLI INTERFACE
# =============================================================================

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()

        print(f"Analyzing: {filepath}\n")
        results = analyze_text(text)

        print("=== Summary ===")
        summary = results['summary']
        print(f"Word Count: {summary['word_count']}")
        print(f"Reading Time: {summary['reading_time']} minutes")
        print(f"Grade Level: {summary['grade_level']}")
        print(f"Readability: {summary['readability_level']}")
        print(f"Vocabulary: {summary['vocabulary_richness']}")
        print(f"Complexity: {summary['complexity_level']}")
        print(f"Assessment: {summary['overall_assessment']}")

        print("\n=== Readability ===")
        read = results['readability']
        print(f"Flesch Reading Ease: {read.get('flesch_reading_ease', 'N/A')}")
        print(f"Flesch-Kincaid Grade: {read.get('flesch_kincaid_grade', 'N/A')}")
        print(f"Gunning Fog: {read.get('gunning_fog', 'N/A')}")

        print("\n=== Top Keywords ===")
        for word, score in results['keywords']['combined_top'][:10]:
            print(f"  {word}: {score:.3f}")

    else:
        # Demo
        sample_text = """
        The software development lifecycle (SDLC) encompasses several phases that
        shall be followed to ensure successful project delivery. Requirements
        gathering must be completed before design begins. The development team
        will implement features according to the approved specifications.

        Testing should include unit tests, integration tests, and user acceptance
        testing (UAT). All defects must be documented in the issue tracking system.
        The project manager is responsible for coordinating activities between teams.

        Documentation requirements include user manuals, API specifications, and
        deployment guides. The system shall support a minimum of 1000 concurrent
        users with response times not exceeding 500 milliseconds.
        """

        print("Demo: Analyzing sample text\n")
        results = analyze_text(sample_text)

        print("=== Summary ===")
        for key, value in results['summary'].items():
            print(f"  {key}: {value}")
