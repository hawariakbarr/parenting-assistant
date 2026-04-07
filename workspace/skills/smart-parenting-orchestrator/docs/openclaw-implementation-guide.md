# OpenClaw Smart Orchestrator - Implementation & Troubleshooting Guide

## 📋 Summary of 3 Main Issues & Solutions

### Issue #1: API Rate Limit Detection
**Problem:** Skill tidak mendeteksi ketika model mengalami quota limit
**Solution:** Add API health check layer sebelum routing decision

### Issue #2: Indonesian Language Priority
**Problem:** Tidak ada preference untuk language-specific model selection
**Solution:** Detect language + apply Claude-priority untuk Indonesian

### Issue #3: Session Cache not Invalidating
**Problem:** Model lama persisten meski config dirubah & gateway restart
**Solution:** Implement config sync check & smart cache TTL

---

## 🔧 Implementation Steps

### Step 1: Add API Health Check Function

```python
# openclaw/orchestrator/api_health_checker.py

import requests
import time
from typing import Dict, List
from datetime import datetime, timedelta

class APIHealthChecker:
    """Monitor API key limits and health status"""
    
    def __init__(self, config):
        self.config = config
        self.model_status_cache = {}
        self.last_check = {}
        self.error_window = 300  # 5 minutes
        
    def get_api_key_status(self, model_name: str) -> Dict:
        """Check if model/API key is rate limited"""
        
        # Check cache first (avoid hammering API)
        if self._is_cache_valid(model_name):
            return self.model_status_cache[model_name]
        
        # Perform actual health check
        health_status = {
            "model": model_name,
            "limited": False,
            "remaining_quota": None,
            "reset_at": None,
            "error_count_5min": 0,
            "health": "unknown",
            "last_check": datetime.utcnow().isoformat(),
            "api_response_time_ms": None
        }
        
        try:
            # Test API call (lightweight)
            start_time = time.time()
            response = self._test_api_call(model_name)
            response_time = (time.time() - start_time) * 1000
            
            health_status["api_response_time_ms"] = response_time
            
            if response.status_code == 429:
                # Rate limited
                health_status["limited"] = True
                health_status["health"] = "rate_limited"
                
                # Extract retry-after header if available
                retry_after = response.headers.get('Retry-After', '60')
                health_status["reset_at"] = (
                    datetime.utcnow() + timedelta(seconds=int(retry_after))
                ).isoformat()
                
            elif response.status_code == 401 or response.status_code == 403:
                # Invalid API key
                health_status["limited"] = True
                health_status["health"] = "invalid_credentials"
                
            elif response.status_code == 200:
                # Healthy
                health_status["health"] = "healthy"
                health_status["limited"] = False
                
                # Try to extract quota info from response headers
                remaining = response.headers.get('X-RateLimit-Remaining-Requests')
                if remaining:
                    health_status["remaining_quota"] = int(remaining)
                    
            elif response.status_code >= 500:
                # Server error
                health_status["health"] = "server_error"
                health_status["limited"] = True
                
            else:
                # Other error
                health_status["health"] = "unknown_error"
                health_status["limited"] = True
                
        except Exception as e:
            health_status["health"] = "check_failed"
            health_status["error"] = str(e)
            
            # On error, be conservative - assume limited
            health_status["limited"] = True
        
        # Update error count for this model
        self._update_error_count(model_name, health_status["limited"])
        health_status["error_count_5min"] = self._get_error_count(model_name)
        
        # Cache result
        self.model_status_cache[model_name] = health_status
        self.last_check[model_name] = datetime.utcnow()
        
        return health_status
    
    def get_all_models_status(self) -> Dict[str, Dict]:
        """Get status of all configured models"""
        
        models = self.config.get("available_models", [])
        status_report = {}
        
        for model in models:
            status_report[model] = self.get_api_key_status(model)
        
        return status_report
    
    def get_healthy_models(self) -> List[str]:
        """Return list of models that are NOT rate limited"""
        
        all_status = self.get_all_models_status()
        healthy = [
            model for model, status in all_status.items()
            if not status["limited"]
        ]
        
        return healthy if healthy else all_status.keys()  # Fallback: return all
    
    def _test_api_call(self, model_name: str):
        """Make lightweight test call to API"""
        
        model_config = self.config["models"][model_name]
        
        if "claude" in model_name.lower():
            # Test Anthropic Claude
            return self._test_anthropic(model_config)
        elif "gpt" in model_name.lower():
            # Test OpenAI GPT
            return self._test_openai(model_config)
        elif "gemini" in model_name.lower():
            # Test Google Gemini
            return self._test_gemini(model_config)
        else:
            raise ValueError(f"Unknown model provider: {model_name}")
    
    def _test_anthropic(self, model_config):
        """Quick Anthropic API test"""
        
        headers = {
            "x-api-key": model_config["api_key"],
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        # Send minimal request
        data = {
            "model": model_config["model_id"],
            "max_tokens": 10,
            "messages": [{"role": "user", "content": "test"}]
        }
        
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data,
            timeout=5
        )
        
        return response
    
    def _test_openai(self, model_config):
        """Quick OpenAI API test"""
        
        headers = {
            "Authorization": f"Bearer {model_config['api_key']}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model_config["model_id"],
            "messages": [{"role": "user", "content": "test"}],
            "max_tokens": 10
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=5
        )
        
        return response
    
    def _test_gemini(self, model_config):
        """Quick Google Gemini API test"""
        
        api_key = model_config["api_key"]
        
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model_config['model_id']}:generateContent?key={api_key}",
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": "test"}]}]},
            timeout=5
        )
        
        return response
    
    def _is_cache_valid(self, model_name: str) -> bool:
        """Check if cache is still fresh (< 60 seconds)"""
        
        if model_name not in self.last_check:
            return False
        
        age = datetime.utcnow() - self.last_check[model_name]
        return age.total_seconds() < 60  # 60 second cache
    
    def _update_error_count(self, model_name: str, is_error: bool):
        """Track error count for this model in 5-min window"""
        
        if model_name not in self.error_window:
            self.error_window[model_name] = []
        
        now = datetime.utcnow()
        
        # Clean old errors (> 5 minutes)
        self.error_window[model_name] = [
            err_time for err_time in self.error_window[model_name]
            if (now - err_time).total_seconds() < 300
        ]
        
        if is_error:
            self.error_window[model_name].append(now)
    
    def _get_error_count(self, model_name: str) -> int:
        """Get error count for last 5 minutes"""
        
        if model_name not in self.error_window:
            return 0
        
        now = datetime.utcnow()
        recent_errors = [
            err_time for err_time in self.error_window[model_name]
            if (now - err_time).total_seconds() < 300
        ]
        
        return len(recent_errors)
```

### Step 2: Add Language Detection Function

```python
# openclaw/orchestrator/language_detector.py

import re
from typing import Tuple
from datetime import datetime, timedelta

class LanguageDetector:
    """Detect user language and cache detection per session"""
    
    INDONESIAN_KEYWORDS = {
        'anak', 'bayi', 'balita', 'ibu', 'ayah', 'keluarga',
        'sekolah', 'guru', 'pelajaran', 'hamil', 'kehamilan',
        'menyusui', 'mpasi', 'tantrum', 'rewel', 'tidur',
        'bagaimana', 'apa', 'siapa', 'kapan', 'dimana',
        'terima kasih', 'mohon', 'tolong', 'bisa',
        'kakak', 'adik', 'keponakan', 'keamanan', 'perkembangan'
    }
    
    ENGLISH_KEYWORDS = {
        'child', 'baby', 'toddler', 'kids', 'parent', 'family',
        'school', 'teacher', 'learning', 'pregnant', 'pregnancy',
        'breastfeeding', 'weaning', 'tantrum', 'sleep', 'behavior',
        'how', 'what', 'when', 'where', 'why',
        'please', 'help', 'thank you', 'advice',
        'sibling', 'safety', 'development'
    }
    
    INDONESIAN_PUNCTUATION = r'[Cc]ara\s+|[Bb]agaimana\s+|[Aa]pa\s+|[Tt]olongaku'
    
    def __init__(self, cache_ttl_seconds=3600):
        self.cache_ttl = cache_ttl_seconds
        self.session_language_cache = {}  # {session_id: {lang, confidence, timestamp}}
    
    def detect_language(
        self, 
        text: str, 
        session_id: str = None,
        use_cache: bool = True
    ) -> Tuple[str, float]:
        """
        Detect language of text
        
        Returns:
            (language_code, confidence)
            - language_code: 'indonesian', 'english', or 'mixed'
            - confidence: 0.0 to 1.0
        """
        
        # Check session cache first
        if use_cache and session_id and self._is_cache_valid(session_id):
            cached = self.session_language_cache[session_id]
            return (cached['language'], cached['confidence'])
        
        # Detect language from text
        language, confidence = self._analyze_text(text)
        
        # Cache result
        if session_id:
            self.session_language_cache[session_id] = {
                'language': language,
                'confidence': confidence,
                'timestamp': datetime.utcnow(),
                'enforce_until': datetime.utcnow() + timedelta(seconds=self.cache_ttl)
            }
        
        return (language, confidence)
    
    def clear_session_cache(self, session_id: str):
        """Clear language cache for a session"""
        if session_id in self.session_language_cache:
            del self.session_language_cache[session_id]
    
    def _analyze_text(self, text: str) -> Tuple[str, float]:
        """Analyze text to determine language"""
        
        # Convert to lowercase for analysis
        text_lower = text.lower()
        words = re.findall(r'\w+', text_lower)
        
        # Count matches
        id_matches = sum(1 for word in words if word in self.INDONESIAN_KEYWORDS)
        en_matches = sum(1 for word in words if word in self.ENGLISH_KEYWORDS)
        
        total_matches = id_matches + en_matches
        
        if total_matches == 0:
            # No keywords found, use heuristics
            return self._heuristic_detection(text), 0.5
        
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
        
        return (language, confidence)
    
    def _heuristic_detection(self, text: str) -> str:
        """Use heuristics when keywords don't match"""
        
        # Check for Indonesian patterns
        if re.search(r'[Kk]ak\s|[Aa]dik\s|[Mm]asalah\s|[Bb]entuk', text):
            return 'indonesian'
        
        # Check for common English patterns  
        if re.search(r"can't|don't|it's|isn't|that's", text, re.IGNORECASE):
            return 'english'
        
        # Default to English
        return 'english'
    
    def _is_cache_valid(self, session_id: str) -> bool:
        """Check if session language cache is still valid"""
        
        if session_id not in self.session_language_cache:
            return False
        
        cache_entry = self.session_language_cache[session_id]
        
        return datetime.utcnow() < cache_entry['enforce_until']
```

### Step 3: Add Session Cache Manager

```python
# openclaw/orchestrator/session_cache_manager.py

import hashlib
from typing import Dict, Any
from datetime import datetime, timedelta
import json

class SessionCacheManager:
    """Manage routing decision cache with config sync"""
    
    def __init__(self, config, cache_ttl_seconds=300):
        self.config = config
        self.cache_ttl = cache_ttl_seconds
        self.routing_cache = {}  # {session_id: {decision, ttl, metadata}}
        self.config_hash = None
        self.model_pool_hash = None
        self._update_hashes()
    
    def get_cached_routing(self, session_id: str) -> Dict[str, Any]:
        """
        Get cached routing decision if valid
        
        Returns:
            routing_decision or None if expired/invalid
        """
        
        # Check if config changed (cache invalidation signal)
        if not self._is_config_in_sync():
            # Config changed - clear all cache
            self.routing_cache.clear()
            self._update_hashes()
            return None
        
        # Check session cache
        if session_id not in self.routing_cache:
            return None
        
        cached = self.routing_cache[session_id]
        
        # Check TTL
        if datetime.utcnow() > cached['valid_until']:
            del self.routing_cache[session_id]
            return None
        
        # Verify metadata still matches
        if not self._verify_metadata(cached['metadata']):
            del self.routing_cache[session_id]
            return None
        
        return cached['decision']
    
    def cache_routing_decision(
        self,
        session_id: str,
        routing_decision: Dict[str, Any],
        metadata: Dict[str, Any]
    ):
        """Cache a routing decision with TTL and metadata"""
        
        self.routing_cache[session_id] = {
            'decision': routing_decision,
            'metadata': metadata,
            'cached_at': datetime.utcnow(),
            'valid_until': datetime.utcnow() + timedelta(seconds=self.cache_ttl),
            'config_hash_at_cache': self.config_hash,
            'model_pool_hash_at_cache': self.model_pool_hash
        }
    
    def invalidate_session(self, session_id: str):
        """Manually invalidate cache for a session"""
        
        if session_id in self.routing_cache:
            del self.routing_cache[session_id]
    
    def invalidate_all(self):
        """Clear all routing cache"""
        
        self.routing_cache.clear()
    
    def _is_config_in_sync(self) -> bool:
        """Check if current config matches cached config"""
        
        current_hash = self._calculate_config_hash()
        
        if current_hash != self.config_hash:
            # Config changed
            return False
        
        current_pool = self._calculate_model_pool_hash()
        
        if current_pool != self.model_pool_hash:
            # Model pool changed
            return False
        
        return True
    
    def _update_hashes(self):
        """Update config and model pool hashes"""
        
        self.config_hash = self._calculate_config_hash()
        self.model_pool_hash = self._calculate_model_pool_hash()
    
    def _calculate_config_hash(self) -> str:
        """Calculate hash of current config"""
        
        config_str = json.dumps(
            self.config,
            sort_keys=True,
            default=str
        )
        
        return hashlib.md5(config_str.encode()).hexdigest()
    
    def _calculate_model_pool_hash(self) -> str:
        """Calculate hash of available models list"""
        
        models = sorted(self.config.get('available_models', []))
        models_str = json.dumps(models)
        
        return hashlib.md5(models_str.encode()).hexdigest()
    
    def _verify_metadata(self, metadata: Dict[str, Any]) -> bool:
        """Verify cached metadata still valid"""
        
        # Check if config hash matches
        if metadata.get('config_hash') != self.config_hash:
            return False
        
        # Check if model pool hash matches
        if metadata.get('model_pool_hash') != self.model_pool_hash:
            return False
        
        return True
```

### Step 4: Integrate into Main Orchestrator

```python
# openclaw/orchestrator/main_router.py

from api_health_checker import APIHealthChecker
from language_detector import LanguageDetector
from session_cache_manager import SessionCacheManager

class SmartOrchestratorV2:
    """Enhanced model router with health checks, language detection, cache management"""
    
    def __init__(self, config):
        self.config = config
        self.health_checker = APIHealthChecker(config)
        self.language_detector = LanguageDetector(cache_ttl_seconds=3600)
        self.cache_manager = SessionCacheManager(config, cache_ttl_seconds=300)
    
    def route_request(self, user_message: str, session_id: str) -> Dict:
        """
        Main routing function
        
        Args:
            user_message: User's input text
            session_id: Unique session identifier
        
        Returns:
            Routing decision with selected model and fallbacks
        """
        
        # Step 1: Check cache first
        cached_decision = self.cache_manager.get_cached_routing(session_id)
        if cached_decision:
            return cached_decision
        
        # Step 2: Check API health
        available_models = self.health_checker.get_healthy_models()
        if not available_models:
            raise Exception("No healthy models available")
        
        # Step 3: Detect language
        language, lang_confidence = self.language_detector.detect_language(
            user_message,
            session_id=session_id,
            use_cache=True
        )
        
        # Step 4: Detect parenting context
        parenting_mode = self._detect_parenting_mode(user_message, language)
        
        # Step 5: Calculate complexity
        complexity_score = self._calculate_complexity(user_message)
        
        # Step 6: Safety check (ALWAYS FIRST)
        if self._is_safety_critical(user_message):
            selected_model = self._select_safe_model(available_models, language)
        else:
            # Step 7: Apply routing logic
            selected_model = self._apply_routing_logic(
                parenting_mode=parenting_mode,
                complexity=complexity_score,
                language=language,
                available_models=available_models
            )
        
        # Step 8: Build decision
        routing_decision = {
            "selected_model": selected_model,
            "confidence": 0.95,
            "reason": f"Language: {language}, Parenting: {parenting_mode}, Complexity: {complexity_score}",
            "complexity_score": complexity_score,
            "parenting_mode": parenting_mode,
            "language_detected": language,
            "language_confidence": lang_confidence,
            "safety_flag": self._is_safety_critical(user_message),
            "fallback_model": self._get_fallback(selected_model, language),
            "tertiary_fallback": self._get_tertiary_fallback(language),
            "api_health": self.health_checker.get_api_key_status(selected_model),
            "cache_info": {
                "ttl_seconds": 300,
                "valid_until": (datetime.utcnow() + timedelta(seconds=300)).isoformat(),
                "config_hash": self.cache_manager.config_hash,
                "model_pool_hash": self.cache_manager.model_pool_hash
            }
        }
        
        # Step 9: Cache decision
        self.cache_manager.cache_routing_decision(
            session_id=session_id,
            routing_decision=routing_decision,
            metadata={
                'config_hash': self.cache_manager.config_hash,
                'model_pool_hash': self.cache_manager.model_pool_hash,
                'language': language,
                'parenting_mode': parenting_mode
            }
        )
        
        return routing_decision
    
    def _detect_parenting_mode(self, text: str, language: str) -> bool:
        """Detect if message is parenting-related"""
        
        parenting_keywords_id = {
            'anak', 'bayi', 'balita', 'sekolah', 'hamil', 'menyusui'
        }
        parenting_keywords_en = {
            'child', 'baby', 'toddler', 'school', 'pregnant', 'breastfeed'
        }
        
        text_lower = text.lower()
        
        if language == 'indonesian':
            return any(kw in text_lower for kw in parenting_keywords_id)
        else:
            return any(kw in text_lower for kw in parenting_keywords_en)
    
    def _calculate_complexity(self, text: str) -> int:
        """Score message complexity 1-10"""
        
        score = 1
        score += min(len(text.split()) // 20, 3)  # Length
        score += text.count('?')  # Questions
        score += text.count('and') + text.count('dan')  # Conjunctions
        
        return min(score, 10)
    
    def _is_safety_critical(self, text: str) -> bool:
        """Check for safety keywords"""
        
        safety_keywords = {
            'illness', 'emergency', 'darurat', 'penyakit', 'sakit',
            'bunuh', 'self-harm', 'abuse', 'kekerasan'
        }
        
        text_lower = text.lower()
        return any(kw in text_lower for kw in safety_keywords)
    
    def _apply_routing_logic(
        self,
        parenting_mode: bool,
        complexity: int,
        language: str,
        available_models: list
    ) -> str:
        """Apply routing decision tree"""
        
        # Indonesian priority
        if language == 'indonesian':
            if parenting_mode:
                if complexity <= 2:
                    return self._get_best_model(
                        ['claude-haiku-4.5'],
                        available_models
                    )
                elif complexity <= 5:
                    return self._get_best_model(
                        ['claude-sonnet-4-5', 'claude-opus-4-5'],
                        available_models
                    )
                else:
                    return self._get_best_model(
                        ['claude-opus-4-5', 'claude-sonnet-4-5'],
                        available_models
                    )
            else:
                if complexity >= 8:
                    return self._get_best_model(
                        ['claude-opus-4-5'],
                        available_models
                    )
                elif complexity >= 5:
                    return self._get_best_model(
                        ['claude-sonnet-4-5'],
                        available_models
                    )
                else:
                    return self._get_best_model(
                        ['claude-haiku-4.5'],
                        available_models
                    )
        
        # English routing (original logic)
        else:
            if parenting_mode:
                if complexity >= 6:
                    return self._get_best_model(
                        ['claude-opus-4-5', 'gpt-4o'],
                        available_models
                    )
                else:
                    return self._get_best_model(
                        ['claude-sonnet-4-5', 'claude-haiku-4.5'],
                        available_models
                    )
            else:
                if complexity >= 8:
                    return self._get_best_model(
                        ['claude-opus-4-5', 'gpt-4o'],
                        available_models
                    )
                elif complexity >= 5:
                    return self._get_best_model(
                        ['claude-sonnet-4-5'],
                        available_models
                    )
                else:
                    return self._get_best_model(
                        ['claude-haiku-4.5'],
                        available_models
                    )
    
    def _get_best_model(self, preferred: list, available: list) -> str:
        """Get first preferred model that's available"""
        
        for model in preferred:
            if model in available:
                return model
        
        # Fallback to first available
        return available[0] if available else 'claude-haiku-4.5'
    
    def _select_safe_model(self, available_models: list, language: str) -> str:
        """Select best model for safety-critical messages"""
        
        # Prefer Opus for safety
        if 'claude-opus-4-5' in available_models:
            return 'claude-opus-4-5'
        if 'gpt-4o' in available_models:
            return 'gpt-4o'
        
        return available_models[0] if available_models else 'claude-opus-4-5'
    
    def _get_fallback(self, model: str, language: str) -> str:
        """Get first fallback model"""
        
        fallback_chains = {
            'indonesian': {
                'claude-opus-4-5': 'claude-sonnet-4-5',
                'claude-sonnet-4-5': 'claude-haiku-4.5',
                'claude-haiku-4.5': 'gemini-3.1-pro'
            },
            'english': {
                'claude-opus-4-5': 'gpt-4o',
                'gpt-4o': 'claude-sonnet-4-5'
            }
        }
        
        return fallback_chains.get(language, {}).get(model, 'gpt-4o')
    
    def _get_tertiary_fallback(self, language: str) -> str:
        """Get tertiary fallback"""
        
        return 'gemini-3.1-pro' if language == 'indonesian' else 'gpt-4o'
```

---

## 🧪 Testing Checklist

### API Limit Detection
```bash
# Test rate limiting detection
python -c "
from api_health_checker import APIHealthChecker
config = {...}
checker = APIHealthChecker(config)

# Test with healthy model
status = checker.get_api_key_status('claude-opus-4-5')
print('Healthy:', status['health'] == 'healthy')

# Test with limited model
status = checker.get_api_key_status('gpt-4o')  # Assume limited
print('Limited:', status['health'] == 'rate_limited')
"
```

### Language Detection
```bash
# Test Indonesian detection
python -c "
from language_detector import LanguageDetector
detector = LanguageDetector()

lang, conf = detector.detect_language('Anak saya berusia 2 tahun dan rewel saat tidur')
print(f'Language: {lang}, Confidence: {conf}')
# Should output: Language: indonesian, Confidence: 0.9+
"
```

### Session Cache
```bash
# Test cache invalidation
python -c "
from session_cache_manager import SessionCacheManager
cache = SessionCacheManager(config)

# Cache a decision
cache.cache_routing_decision('session_123', {'model': 'claude-opus'}, {})

# Modify config (simulate)
# config changes...

# Cache should be invalid
result = cache.get_cached_routing('session_123')
print('Cache invalidated:', result is None)
"
```

---

## 📝 Configuration Example

```yaml
# openclaw-config.yaml

orchestrator:
  version: "smart-parenting-v2"
  enabled: true
  
  # API Health Checking
  api_health_check:
    enabled: true
    check_interval_seconds: 60
    cache_ttl_seconds: 60
    error_threshold: 5
    
    models:
      claude-opus-4-5:
        provider: anthropic
        model_id: claude-opus-4-5-20250514
        api_key: ${ANTHROPIC_API_KEY}
        
      claude-sonnet-4-5:
        provider: anthropic
        model_id: claude-sonnet-4-20250514
        api_key: ${ANTHROPIC_API_KEY}
        
      gpt-4o:
        provider: openai
        model_id: gpt-4o
        api_key: ${OPENAI_API_KEY}
        
      gemini-3.1-pro:
        provider: google
        model_id: gemini-3.1-pro
        api_key: ${GOOGLE_API_KEY}
  
  # Language Detection
  language_detection:
    enabled: true
    supported_languages: [indonesian, english]
    cache_ttl_seconds: 3600
    supported_channels: [whatsapp, telegram]
  
  # Session Cache Management
  session_cache:
    enabled: true
    cache_ttl_seconds: 300
    periodic_sync_interval_seconds: 300
    invalidate_on_config_change: true
    invalidate_on_model_pool_change: true
  
  # Routing preferences
  model_preferences:
    indonesian:
      primary: [claude-opus-4-5, claude-sonnet-4-5, claude-haiku-4.5]
      fallback: [gemini-3.1-pro, gpt-4o]
    english:
      primary: [claude-opus-4-5, claude-sonnet-4-5]
      fallback: [gpt-4o, gemini-3.1-pro]
  
  # Safety config
  safety:
    enabled: true
    escalation_model: claude-opus-4-5
    crisis_hotlines:
      id:
        domestic_abuse: "+62-812-2800-1100"
        mental_health: "1500567"
      en:
        crisis: "988"
        suicide: "1-800-273-8255"
```

---

## 🚀 Deployment Steps

1. **Update SKILL.md** dengan file `smart-parenting-orchestrator-enhanced.md`
2. **Add Python modules** ke OpenClaw:
   - `api_health_checker.py`
   - `language_detector.py`
   - `session_cache_manager.py`
   - `main_router.py`
3. **Update config** dengan settings baru
4. **Restart OpenClaw gateway**
5. **Test dengan WhatsApp channel** - seharusnya model langsung berubah tanpa session reset
6. **Monitor logs** untuk health checks dan cache invalidations

