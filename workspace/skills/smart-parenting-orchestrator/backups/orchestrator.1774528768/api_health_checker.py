# ~/.openclaw/workspace/skills/smart-parenting-orchestrator/orchestrator/api_health_checker.py

import requests
import time
from typing import Dict, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger("openclaw.orchestrator.api_health_checker")


class APIHealthChecker:
    """Monitor API key limits and health status for all models"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.model_status_cache = {}
        self.last_check = {}
        self.error_count_window = {}  # Track errors in 5-minute window
        self.error_window_duration = 300  # 5 minutes
        
        logger.info("APIHealthChecker initialized")
        
    def get_api_key_status(self, model_name: str) -> Dict:
        """Check if model/API key is rate limited"""
        
        # Check cache first (avoid hammering API)
        if self._is_cache_valid(model_name):
            logger.debug(f"Using cached health status for {model_name}")
            return self.model_status_cache[model_name]
        
        logger.info(f"Checking health status for {model_name}")
        
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
                logger.warning(f"{model_name}: Rate limited (429)")
                
                # Extract retry-after header if available
                retry_after = response.headers.get('Retry-After', '60')
                try:
                    retry_seconds = int(retry_after)
                except ValueError:
                    retry_seconds = 60
                
                health_status["reset_at"] = (
                    datetime.utcnow() + timedelta(seconds=retry_seconds)
                ).isoformat()
                
            elif response.status_code == 401 or response.status_code == 403:
                # Invalid API key
                health_status["limited"] = True
                health_status["health"] = "invalid_credentials"
                logger.error(f"{model_name}: Invalid credentials ({response.status_code})")
                
            elif response.status_code == 200:
                # Healthy
                health_status["health"] = "healthy"
                health_status["limited"] = False
                logger.info(f"{model_name}: Healthy")
                
                # Try to extract quota info from response headers
                remaining = response.headers.get('X-RateLimit-Remaining-Requests')
                if remaining:
                    health_status["remaining_quota"] = int(remaining)
                    
            elif response.status_code >= 500:
                # Server error
                health_status["health"] = "server_error"
                health_status["limited"] = True
                logger.warning(f"{model_name}: Server error ({response.status_code})")
                
            else:
                # Other error
                health_status["health"] = "unknown_error"
                health_status["limited"] = True
                logger.warning(f"{model_name}: Unknown error ({response.status_code})")
                
        except requests.exceptions.Timeout:
            health_status["health"] = "timeout"
            health_status["limited"] = True
            logger.warning(f"{model_name}: API call timeout")
            
        except Exception as e:
            health_status["health"] = "check_failed"
            health_status["error"] = str(e)
            health_status["limited"] = True
            logger.warning(f"{model_name}: Health check failed - {str(e)}")
        
        # Update error count for this model
        self._update_error_count(model_name, health_status["limited"])
        health_status["error_count_5min"] = self._get_error_count(model_name)
        
        # Cache result
        self.model_status_cache[model_name] = health_status
        self.last_check[model_name] = datetime.utcnow()
        
        return health_status
    
    def get_all_models_status(self) -> Dict[str, Dict]:
        """Get status of all configured models"""
        
        orchestrator_config = self.config.get("orchestrator", {})
        api_health_config = orchestrator_config.get("api_health_check", {})
        models_config = api_health_config.get("models", {})
        
        models = list(models_config.keys())
        status_report = {}
        
        logger.info(f"Checking health for {len(models)} models")
        
        for model in models:
            status_report[model] = self.get_api_key_status(model)
        
        return status_report
    
    def get_healthy_models(self) -> List[str]:
        """Return list of models that are NOT rate limited"""
        
        all_status = self.get_all_models_status()
        healthy = [
            model for model, status in all_status.items()
            if not status["limited"] and status["health"] == "healthy"
        ]
        
        logger.info(f"Healthy models: {healthy}")
        
        # If no healthy models, return all (fallback)
        if not healthy:
            logger.warning("No healthy models found, returning all available models")
            return list(all_status.keys())
        
        return healthy
    
    def _test_api_call(self, model_name: str):
        """Make lightweight test call to API"""
        
        orchestrator_config = self.config.get("orchestrator", {})
        api_health_config = orchestrator_config.get("api_health_check", {})
        models_config = api_health_config.get("models", {})
        
        if model_name not in models_config:
            raise ValueError(f"Model {model_name} not in config")
        
        model_config = models_config[model_name]
        provider = model_config.get("provider", "").lower()
        
        if "claude" in provider or "anthropic" in provider:
            return self._test_anthropic(model_config)
        elif "gpt" in provider or "openai" in provider:
            return self._test_openai(model_config)
        elif "gemini" in provider or "google" in provider:
            return self._test_gemini(model_config)
        else:
            raise ValueError(f"Unknown provider for model {model_name}: {provider}")
    
    def _test_anthropic(self, model_config: Dict):
        """Quick Anthropic API test"""
        
        api_key = model_config.get("api_key", "")
        model_id = model_config.get("model_id", "claude-opus-4-5")
        
        if not api_key:
            raise ValueError("Missing Anthropic API key")
        
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        # Send minimal request
        data = {
            "model": model_id,
            "max_tokens": 10,
            "messages": [{"role": "user", "content": "test"}]
        }
        
        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=data,
                timeout=5
            )
            return response
        except requests.exceptions.Timeout:
            raise requests.exceptions.Timeout(f"Anthropic API timeout for {model_id}")
    
    def _test_openai(self, model_config: Dict):
        """Quick OpenAI API test"""
        
        api_key = model_config.get("api_key", "")
        model_id = model_config.get("model_id", "gpt-4o")
        
        if not api_key:
            raise ValueError("Missing OpenAI API key")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model_id,
            "messages": [{"role": "user", "content": "test"}],
            "max_tokens": 10
        }
        
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=5
            )
            return response
        except requests.exceptions.Timeout:
            raise requests.exceptions.Timeout(f"OpenAI API timeout for {model_id}")
    
    def _test_gemini(self, model_config: Dict):
        """Quick Google Gemini API test"""
        
        api_key = model_config.get("api_key", "")
        model_id = model_config.get("model_id", "gemini-3.1-pro")
        
        if not api_key:
            raise ValueError("Missing Google API key")
        
        try:
            response = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={api_key}",
                headers={"Content-Type": "application/json"},
                json={"contents": [{"parts": [{"text": "test"}]}]},
                timeout=5
            )
            return response
        except requests.exceptions.Timeout:
            raise requests.exceptions.Timeout(f"Gemini API timeout for {model_id}")
    
    def _is_cache_valid(self, model_name: str) -> bool:
        """Check if cache is still fresh (< 60 seconds)"""
        
        if model_name not in self.last_check:
            return False
        
        age = datetime.utcnow() - self.last_check[model_name]
        cache_ttl = 60  # 60 second cache
        
        return age.total_seconds() < cache_ttl
    
    def _update_error_count(self, model_name: str, is_error: bool):
        """Track error count for this model in 5-min window"""
        
        if model_name not in self.error_count_window:
            self.error_count_window[model_name] = []
        
        now = datetime.utcnow()
        
        # Clean old errors (> 5 minutes)
        self.error_count_window[model_name] = [
            err_time for err_time in self.error_count_window[model_name]
            if (now - err_time).total_seconds() < self.error_window_duration
        ]
        
        if is_error:
            self.error_count_window[model_name].append(now)
    
    def _get_error_count(self, model_name: str) -> int:
        """Get error count for last 5 minutes"""
        
        if model_name not in self.error_count_window:
            return 0
        
        now = datetime.utcnow()
        recent_errors = [
            err_time for err_time in self.error_count_window[model_name]
            if (now - err_time).total_seconds() < self.error_window_duration
        ]
        
        return len(recent_errors)
