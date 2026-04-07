# ~/.openclaw/workspace/skills/smart-parenting-orchestrator/orchestrator/language_detector.py

import re
from typing import Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger("openclaw.orchestrator.language_detector")


class LanguageDetector:
    """Detect user language and cache detection per session"""
    
    INDONESIAN_KEYWORDS = {
        'anak', 'bayi', 'balita', 'ibu', 'ayah', 'keluarga',
        'sekolah', 'guru', 'pelajaran', 'hamil', 'kehamilan',
        'menyusui', 'mpasi', 'tantrum', 'rewel', 'tidur',
        'bagaimana', 'apa', 'siapa', 'kapan', 'dimana',
        'terima kasih', 'mohon', 'tolong', 'bisa',
        'kakak', 'adik', 'keponakan', 'keamanan', 'perkembangan',
        'kami', 'saya', 'kita', 'mereka', 'merasa',
        'dan', 'atau', 'tapi', 'juga', 'tidak'
    }
    
    ENGLISH_KEYWORDS = {
        'child', 'baby', 'toddler', 'kids', 'parent', 'family',
        'school', 'teacher', 'learning', 'pregnant', 'pregnancy',
        'breastfeeding', 'weaning', 'tantrum', 'sleep', 'behavior',
        'how', 'what', 'when', 'where', 'why',
        'please', 'help', 'thank', 'advice',
        'sibling', 'safety', 'development', 'care',
        'and', 'or', 'but', 'also', 'not'
    }
    
    INDONESIAN_PATTERNS = [
        r'\byang\b',
        r'\bakan\b',
        r'\bsudah\b',
        r'\bsebenarnya\b',
        r'\bcara\s+',
        r'\bapa\s+',
    ]
    
    def __init__(self, cache_ttl_seconds: int = 3600):
        self.cache_ttl = cache_ttl_seconds
        self.session_language_cache = {}  # {session_id: {lang, confidence, timestamp}}
        logger.info(f"LanguageDetector initialized with {cache_ttl_seconds}s cache TTL")
    
    def detect_language(
        self, 
        text: str, 
        session_id: str = None,
        use_cache: bool = True
    ) -> Tuple[str, float]:
        """
        Detect language of text
        
        Args:
            text: User message text
            session_id: Unique session identifier for caching
            use_cache: Whether to use cached language for this session
        
        Returns:
            (language_code, confidence)
            - language_code: 'indonesian', 'english', or 'mixed'
            - confidence: 0.0 to 1.0
        """
        
        # Check session cache first
        if use_cache and session_id and self._is_cache_valid(session_id):
            cached = self.session_language_cache[session_id]
            logger.debug(f"Using cached language detection for session {session_id}: {cached['language']}")
            return (cached['language'], cached['confidence'])
        
        # Detect language from text
        language, confidence = self._analyze_text(text)
        
        logger.info(f"Detected language: {language} (confidence: {confidence:.2f})")
        
        # Cache result
        if session_id:
            self.session_language_cache[session_id] = {
                'language': language,
                'confidence': confidence,
                'timestamp': datetime.utcnow(),
                'enforce_until': datetime.utcnow() + timedelta(seconds=self.cache_ttl)
            }
            logger.debug(f"Cached language detection for session {session_id} until {self.session_language_cache[session_id]['enforce_until']}")
        
        return (language, confidence)
    
    def clear_session_cache(self, session_id: str):
        """Clear language cache for a session"""
        if session_id in self.session_language_cache:
            del self.session_language_cache[session_id]
            logger.info(f"Cleared language cache for session {session_id}")
    
    def _analyze_text(self, text: str) -> Tuple[str, float]:
        """Analyze text to determine language"""
        
        # Convert to lowercase for analysis
        text_lower = text.lower()
        
        # Extract words
        words = re.findall(r'\w+', text_lower)
        
        # Count matches
        id_matches = sum(1 for word in words if word in self.INDONESIAN_KEYWORDS)
        en_matches = sum(1 for word in words if word in self.ENGLISH_KEYWORDS)
        
        # Check for pattern matches (extra signals)
        id_pattern_count = sum(1 for pattern in self.INDONESIAN_PATTERNS if re.search(pattern, text_lower))
        
        total_matches = id_matches + en_matches
        
        # Debug logging
        logger.debug(f"Language analysis: ID matches={id_matches}, EN matches={en_matches}, ID patterns={id_pattern_count}, total_words={len(words)}")
        
        if total_matches == 0:
            # No keywords found, use heuristics
            language = self._heuristic_detection(text)
            confidence = 0.5  # Low confidence without keywords
            logger.debug(f"No keyword matches found, using heuristics: {language}")
            return (language, confidence)
        
        # Add pattern matches to Indonesian score
        id_matches += id_pattern_count
        total_matches += id_pattern_count
        
        # Calculate confidence
        id_ratio = id_matches / total_matches if total_matches > 0 else 0
        en_ratio = en_matches / total_matches if total_matches > 0 else 0
        
        # Determine language
        if id_ratio > en_ratio:
            language = 'indonesian'
            confidence = min(id_ratio, 1.0)
        elif en_ratio > id_ratio:
            language = 'english'
            confidence = min(en_ratio, 1.0)
        else:
            language = 'mixed'
            confidence = 0.5
        
        # Adjust confidence based on keyword count
        if total_matches < 3:
            confidence *= 0.7  # Low confidence with few keywords
        else:
            confidence = min(confidence, 1.0)
        
        logger.debug(f"Calculated: language={language}, confidence={confidence:.2f}")
        
        return (language, confidence)
    
    def _heuristic_detection(self, text: str) -> str:
        """Use heuristics when keywords don't match"""
        
        text_lower = text.lower()
        
        # Check for Indonesian patterns
        indonesian_indicators = [
            r'\byang\b',
            r'\bakan\b',
            r'\bsudah\b',
            r'\bkami\b',
            r'\bkamu\b',
            r'\binia\b',
            r'\bitu\b',
            r'[aeiou]k\b',  # Common Indonesian word endings
        ]
        
        if any(re.search(pattern, text_lower) for pattern in indonesian_indicators):
            return 'indonesian'
        
        # Check for English patterns  
        english_indicators = [
            r"can't|don't|it's|isn't|that's|won't|haven't",
            r'\b(the|a|an)\b',
            r'\b(is|are|was|were)\b',
            r'\b(ing)\b',  # -ing endings
        ]
        
        if any(re.search(pattern, text_lower) for pattern in english_indicators):
            return 'english'
        
        # Default to English
        return 'english'
    
    def _is_cache_valid(self, session_id: str) -> bool:
        """Check if session language cache is still valid"""
        
        if session_id not in self.session_language_cache:
            return False
        
        cache_entry = self.session_language_cache[session_id]
        
        is_valid = datetime.utcnow() < cache_entry['enforce_until']
        
        if not is_valid:
            logger.debug(f"Cache expired for session {session_id}")
        
        return is_valid
