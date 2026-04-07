# ~/.openclaw/workspace/skills/smart-parenting-orchestrator/orchestrator/session_cache_manager.py

import hashlib
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json
import logging
import os

logger = logging.getLogger("openclaw.orchestrator.session_cache_manager")


class SessionCacheManager:
    """
    Manage routing decision cache with config sync and smart invalidation
    
    Handles:
    - Cache TTL (5 minutes default)
    - Config hash validation (detect config changes)
    - Model pool hash validation (detect model list changes)
    - Gateway startup tracking (detect restarts)
    - Periodic sync checks
    """
    
    def __init__(self, config: Dict, cache_ttl_seconds: int = 300):
        self.config = config
        self.cache_ttl = cache_ttl_seconds
        self.routing_cache = {}  # {session_id: {decision, ttl, metadata}}
        self.config_hash = None
        self.model_pool_hash = None
        self.gateway_startup_time = datetime.utcnow().timestamp()
        
        self._update_hashes()
        
        logger.info(f"SessionCacheManager initialized with TTL={cache_ttl_seconds}s")
        logger.info(f"Gateway startup time: {self.gateway_startup_time}")
    
    def get_cached_routing(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached routing decision if valid
        
        Performs multi-layer validation:
        1. Check if config changed
        2. Check if model pool changed  
        3. Check if gateway restarted
        4. Check if TTL expired
        5. Verify metadata consistency
        
        Returns:
            routing_decision dict if valid, None if expired/invalid
        """
        
        # Step 1: Check if config changed (cache invalidation signal)
        if not self._is_config_in_sync():
            logger.warning(f"Config mismatch detected for session {session_id} - invalidating cache")
            self.routing_cache.clear()
            self._update_hashes()
            return None
        
        # Step 2: Check session cache existence
        if session_id not in self.routing_cache:
            logger.debug(f"Cache miss for session {session_id} (no entry)")
            return None
        
        cached = self.routing_cache[session_id]
        now = datetime.utcnow()
        
        # Step 3: Check TTL expiration
        if now > cached['valid_until']:
            logger.info(f"Cache expired for session {session_id}")
            del self.routing_cache[session_id]
            return None
        
        # Step 4: Verify metadata still matches
        if not self._verify_metadata(cached['metadata']):
            logger.warning(f"Metadata mismatch for session {session_id} - invalidating cache")
            del self.routing_cache[session_id]
            return None
        
        # Cache is valid - return decision
        logger.debug(f"Cache hit for session {session_id} - returning cached decision")
        return cached['decision']
    
    def cache_routing_decision(
        self,
        session_id: str,
        routing_decision: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Cache a routing decision with TTL and metadata
        
        Args:
            session_id: Unique session identifier
            routing_decision: The routing decision to cache
            metadata: Additional metadata (language, parenting_mode, etc)
        """
        
        if metadata is None:
            metadata = {}
        
        # Add config/state information
        metadata.update({
            'config_hash': self.config_hash,
            'model_pool_hash': self.model_pool_hash,
            'gateway_startup_time': self.gateway_startup_time
        })
        
        cache_entry = {
            'decision': routing_decision,
            'metadata': metadata,
            'cached_at': datetime.utcnow(),
            'valid_until': datetime.utcnow() + timedelta(seconds=self.cache_ttl),
            'ttl_seconds': self.cache_ttl,
            'config_hash_at_cache': self.config_hash,
            'model_pool_hash_at_cache': self.model_pool_hash,
            'gateway_startup_time_at_cache': self.gateway_startup_time
        }
        
        self.routing_cache[session_id] = cache_entry
        
        logger.info(
            f"Cached routing for session {session_id}: "
            f"model={routing_decision.get('selected_model')}, "
            f"ttl={self.cache_ttl}s, "
            f"expires_at={cache_entry['valid_until']}"
        )
    
    def invalidate_session(self, session_id: str):
        """Manually invalidate cache for a specific session"""
        
        if session_id in self.routing_cache:
            del self.routing_cache[session_id]
            logger.info(f"Manually invalidated cache for session {session_id}")
    
    def invalidate_all(self):
        """Clear all routing cache (use after config change)"""
        
        count = len(self.routing_cache)
        self.routing_cache.clear()
        logger.warning(f"Invalidated all caches ({count} sessions)")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get current cache statistics"""
        
        now = datetime.utcnow()
        
        valid_count = sum(
            1 for cache in self.routing_cache.values()
            if now < cache['valid_until']
        )
        
        expired_count = len(self.routing_cache) - valid_count
        
        return {
            'total_entries': len(self.routing_cache),
            'valid_entries': valid_count,
            'expired_entries': expired_count,
            'config_hash': self.config_hash,
            'model_pool_hash': self.model_pool_hash,
            'gateway_startup_time': self.gateway_startup_time
        }
    
    def _is_config_in_sync(self) -> bool:
        """Check if current config matches cached config"""
        
        current_hash = self._calculate_config_hash()
        
        if current_hash != self.config_hash:
            logger.warning(
                f"Config hash mismatch: "
                f"cached={self.config_hash}, current={current_hash}"
            )
            return False
        
        current_pool = self._calculate_model_pool_hash()
        
        if current_pool != self.model_pool_hash:
            logger.warning(
                f"Model pool hash mismatch: "
                f"cached={self.model_pool_hash}, current={current_pool}"
            )
            return False
        
        return True
    
    def _update_hashes(self):
        """Update config and model pool hashes"""
        
        old_config_hash = self.config_hash
        old_pool_hash = self.model_pool_hash
        
        self.config_hash = self._calculate_config_hash()
        self.model_pool_hash = self._calculate_model_pool_hash()
        
        if old_config_hash and old_config_hash != self.config_hash:
            logger.warning(f"Config hash changed: {old_config_hash} -> {self.config_hash}")
        
        if old_pool_hash and old_pool_hash != self.model_pool_hash:
            logger.warning(f"Model pool hash changed: {old_pool_hash} -> {self.model_pool_hash}")
    
    def _calculate_config_hash(self) -> str:
        """Calculate hash of current config"""
        
        try:
            # Serialize config to JSON (deterministic)
            config_str = json.dumps(
                self.config,
                sort_keys=True,
                default=str
            )
            
            # Calculate MD5 hash
            hash_value = hashlib.md5(config_str.encode()).hexdigest()
            
            return hash_value
            
        except Exception as e:
            logger.error(f"Failed to calculate config hash: {str(e)}")
            return "error"
    
    def _calculate_model_pool_hash(self) -> str:
        """Calculate hash of available models list"""
        
        try:
            # Get available models from config
            orchestrator_config = self.config.get("orchestrator", {})
            api_health_config = orchestrator_config.get("api_health_check", {})
            models_config = api_health_config.get("models", {})
            
            # Get sorted model names
            models = sorted(models_config.keys())
            
            # Serialize to JSON
            models_str = json.dumps(models)
            
            # Calculate MD5 hash
            hash_value = hashlib.md5(models_str.encode()).hexdigest()
            
            return hash_value
            
        except Exception as e:
            logger.error(f"Failed to calculate model pool hash: {str(e)}")
            return "error"
    
    def _verify_metadata(self, metadata: Dict[str, Any]) -> bool:
        """Verify cached metadata is still valid"""
        
        # Check if config hash matches
        if metadata.get('config_hash') != self.config_hash:
            logger.debug(
                f"Config hash mismatch in metadata: "
                f"cached={metadata.get('config_hash')}, current={self.config_hash}"
            )
            return False
        
        # Check if model pool hash matches
        if metadata.get('model_pool_hash') != self.model_pool_hash:
            logger.debug(
                f"Model pool hash mismatch in metadata: "
                f"cached={metadata.get('model_pool_hash')}, current={self.model_pool_hash}"
            )
            return False
        
        # Check if gateway startup time is same
        if metadata.get('gateway_startup_time') != self.gateway_startup_time:
            logger.debug(
                f"Gateway startup time mismatch - possible restart detected"
            )
            return False
        
        return True
