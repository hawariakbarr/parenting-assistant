# ~/.openclaw/workspace/skills/smart-parenting-orchestrator/orchestrator/main_router.py

from .api_health_checker import APIHealthChecker
from .language_detector import LanguageDetector
from .session_cache_manager import SessionCacheManager

import yaml
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

logger = logging.getLogger("openclaw.orchestrator.main_router")


class SmartOrchestratorV2:
    """
    Enhanced model router with health checks, language detection, and cache management
    
    Features:
    - API rate limit detection
    - Indonesian language priority
    - Smart session cache with config validation
    - Safety escalation for critical topics
    """
    
    def __init__(self, skill_dir: str = None):
        """
        Initialize orchestrator
        
        Args:
            skill_dir: Path to skill directory (auto-detected if None)
        """
        
        # Auto-detect skill directory if not provided
        if skill_dir is None:
            # Get parent directory of this file (orchestrator/) then parent again (skill root/)
            skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        self.skill_dir = skill_dir
        
        # Load config
        config_path = os.path.join(skill_dir, 'config.yaml')
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found at {config_path}")
        
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        logger.info(f"Loaded config from {config_path}")
        
        # Initialize components
        self.health_checker = APIHealthChecker(self.config)
        self.language_detector = LanguageDetector(cache_ttl_seconds=3600)
        self.cache_manager = SessionCacheManager(self.config, cache_ttl_seconds=300)
        
        logger.info("SmartOrchestratorV2 initialized successfully")
    
    def route_request(
        self, 
        user_message: str, 
        session_id: str,
        channel: str = "whatsapp"
    ) -> Dict[str, Any]:
        """
        Main routing function - determines which model to use
        
        Args:
            user_message: User's input text
            session_id: Unique session identifier
            channel: Channel name (whatsapp, telegram, etc)
        
        Returns:
            Routing decision dict with selected model and fallbacks
        
        Raises:
            Exception: If no healthy models available
        """
        
        logger.info(f"Routing request from session {session_id} (channel: {channel})")
        
        # Step 1: Check cache first
        cached_decision = self.cache_manager.get_cached_routing(session_id)
        if cached_decision:
            return cached_decision
        
        # Step 2: Check API health
        available_models = self.health_checker.get_healthy_models()
        if not available_models:
            logger.error("No healthy models available!")
            raise Exception("No healthy models available")
        
        logger.info(f"Available models: {available_models}")
        
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
        
        logger.info(
            f"Analysis: language={language}, parenting={parenting_mode}, "
            f"complexity={complexity_score}"
        )
        
        # Step 6: Safety check (ALWAYS FIRST)
        if self._is_safety_critical(user_message):
            logger.warning("Safety critical message detected - escalating")
            selected_model = self._select_safe_model(available_models, language)
        else:
            # Step 7: Apply routing logic
            selected_model = self._apply_routing_logic(
                parenting_mode=parenting_mode,
                complexity=complexity_score,
                language=language,
                available_models=available_models
            )
        
        logger.info(f"Selected model: {selected_model}")
        
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
                'channel': channel,
                'language': language,
                'parenting_mode': parenting_mode,
                'complexity_score': complexity_score
            }
        )
        
        logger.info(f"Routing decision cached for session {session_id}")
        
        return routing_decision
    
    def _detect_parenting_mode(self, text: str, language: str) -> bool:
        """Detect if message is parenting-related"""
        
        parenting_keywords_id = {
            'anak', 'bayi', 'balita', 'sekolah', 'hamil', 'menyusui',
            'tantrum', 'rewel', 'tumbuh kembang', 'asuh', 'didik',
            'ibu', 'ayah', 'orang tua', 'keluarga'
        }
        
        parenting_keywords_en = {
            'child', 'baby', 'toddler', 'school', 'pregnant', 'breastfeed',
            'parenting', 'tantrum', 'behavior', 'sleep', 'potty',
            'mom', 'dad', 'parent', 'family', 'kids'
        }
        
        text_lower = text.lower()
        
        if language == 'indonesian':
            matches = sum(1 for kw in parenting_keywords_id if kw in text_lower)
        else:
            matches = sum(1 for kw in parenting_keywords_en if kw in text_lower)
        
        parenting_mode = matches >= 1
        
        logger.debug(f"Parenting mode detection: {parenting_mode} (matches: {matches})")
        
        return parenting_mode
    
    def _calculate_complexity(self, text: str) -> int:
        """Score message complexity 1-10"""
        
        score = 1
        
        # Length factor
        score += min(len(text.split()) // 20, 3)
        
        # Question count
        score += text.count('?')
        score += text.count('？')  # Indonesian question mark variant
        
        # Conjunction indicators (multiple topics)
        conjunctions = text.lower().count('and') + text.lower().count('dan')
        score += min(conjunctions, 2)
        
        # Capitalization (multiple sentences)
        score += min(text.count('.') + text.count('。'), 2)
        
        # Final score
        final_score = min(max(score, 1), 10)
        
        logger.debug(f"Complexity score calculated: {final_score}")
        
        return final_score
    
    def _is_safety_critical(self, text: str) -> bool:
        """Check for safety keywords indicating critical situation"""
        
        safety_keywords_en = {
            'illness', 'emergency', 'sick', 'hospital', 'doctor',
            'injury', 'hurt', 'pain', 'dying', 'death',
            'suicide', 'self-harm', 'abuse', 'violence',
            'overdose', 'poison', 'allergy', 'bleeding'
        }
        
        safety_keywords_id = {
            'sakit', 'darurat', 'penyakit', 'rumah sakit', 'dokter',
            'luka', 'cedera', 'sakit berat', 'mati', 'meninggal',
            'bunuh diri', 'sakiti diri', 'kekerasan', 'pukulan',
            'overdosis', 'racun', 'alergi', 'perdarahan'
        }
        
        text_lower = text.lower()
        
        # Check for safety keywords
        en_matches = any(kw in text_lower for kw in safety_keywords_en)
        id_matches = any(kw in text_lower for kw in safety_keywords_id)
        
        is_critical = en_matches or id_matches
        
        if is_critical:
            logger.warning(f"Safety critical message detected")
        
        return is_critical
    
    def _apply_routing_logic(
        self,
        parenting_mode: bool,
        complexity: int,
        language: str,
        available_models: List[str]
    ) -> str:
        """Apply routing decision tree"""
        
        logger.debug(f"Applying routing logic: parenting={parenting_mode}, complexity={complexity}, lang={language}")
        
        # Indonesian priority
        if language == 'indonesian':
            if parenting_mode:
                if complexity <= 2:
                    preferred = ['claude-haiku-4.5']
                elif complexity <= 5:
                    preferred = ['claude-sonnet-4-5', 'claude-opus-4-5']
                else:
                    preferred = ['claude-opus-4-5', 'claude-sonnet-4-5']
            else:
                if complexity >= 8:
                    preferred = ['claude-opus-4-5']
                elif complexity >= 5:
                    preferred = ['claude-sonnet-4-5']
                else:
                    preferred = ['claude-haiku-4.5']
        
        # English routing
        else:
            if parenting_mode:
                if complexity >= 6:
                    preferred = ['claude-opus-4-5', 'gpt-4o']
                else:
                    preferred = ['claude-sonnet-4-5', 'claude-haiku-4.5']
            else:
                if complexity >= 8:
                    preferred = ['claude-opus-4-5', 'gpt-4o']
                elif complexity >= 5:
                    preferred = ['claude-sonnet-4-5']
                else:
                    preferred = ['claude-haiku-4.5']
        
        # Get best available model from preferred list
        selected = self._get_best_model(preferred, available_models)
        
        logger.debug(f"Routing logic result: preferred={preferred}, selected={selected}")
        
        return selected
    
    def _get_best_model(self, preferred: List[str], available: List[str]) -> str:
        """Get first preferred model that's available"""
        
        for model in preferred:
            if model in available:
                logger.debug(f"Found preferred model in available list: {model}")
                return model
        
        # Fallback to first available
        if available:
            logger.warning(f"No preferred model available, using fallback: {available[0]}")
            return available[0]
        
        # Ultimate fallback
        logger.error("No models available, using default fallback")
        return 'claude-haiku-4.5'
    
    def _select_safe_model(self, available_models: List[str], language: str) -> str:
        """Select best model for safety-critical messages"""
        
        # Prefer Opus for safety
        safe_preference = ['claude-opus-4-5', 'claude-sonnet-4-5', 'gpt-4o']
        
        for model in safe_preference:
            if model in available_models:
                logger.info(f"Safety escalation: selected {model}")
                return model
        
        # Ultimate fallback
        if available_models:
            logger.warning(f"Safety escalation: using available model {available_models[0]}")
            return available_models[0]
        
        logger.error("Safety escalation: no models available!")
        return 'claude-opus-4-5'
    
    def _get_fallback(self, model: str, language: str) -> str:
        """Get first fallback model"""
        
        fallback_chains = {
            'indonesian': {
                'claude-opus-4-5': 'claude-sonnet-4-5',
                'claude-sonnet-4-5': 'claude-haiku-4.5',
                'claude-haiku-4.5': 'gemini-3.1-pro',
                'gemini-3.1-pro': 'gpt-4o'
            },
            'english': {
                'claude-opus-4-5': 'gpt-4o',
                'gpt-4o': 'claude-sonnet-4-5',
                'claude-sonnet-4-5': 'claude-haiku-4.5',
                'claude-haiku-4.5': 'gemini-3.1-pro'
            }
        }
        
        chains = fallback_chains.get(language, fallback_chains['english'])
        return chains.get(model, 'gpt-4o')
    
    def _get_tertiary_fallback(self, language: str) -> str:
        """Get tertiary fallback"""
        
        return 'gemini-3.1-pro' if language == 'indonesian' else 'gpt-4o'
