# OpenClaw Session Cache Issue - Troubleshooting & Diagnosis

## 🔍 Problem: Model Change Not Persisting After Gateway Restart

### Symptoms
1. Change default model di OpenClaw config
2. Restart gateway (`systemctl restart openclaw`)
3. WhatsApp channel still uses OLD model
4. Must reset session/conversation untuk model baru terpakai
5. After session reset, baru model baru dipakai

---

## 🎯 Root Cause Analysis

### Why This Happens

OpenClaw maintains **3 levels of state**:

```
1. CONFIG STATE (disk)
   ├── /etc/openclaw/models.yaml
   └── /etc/openclaw/orchestrator.yaml
   └── PRIMARY MODEL = "claude-opus-4-5"

2. GATEWAY STATE (in-memory)
   ├── config_cache (loaded at startup)
   └── Loaded ONCE during startup
   └── NOT reloaded on file change

3. SESSION STATE (per-user/channel)
   ├── WhatsApp session for user_123
   ├── Last selected model = "gpt-4o"  ← CACHED!
   ├── Language detection = "indonesian"  ← CACHED!
   └── Valid until: [some future time]
```

**The issue:**
- Gateway startup: reads config, caches in memory
- But **session state persists across** gateway restart
- WhatsApp session stores previous routing decision
- When request comes in, orchestrator checks session cache FIRST
- Finds valid cached decision → **uses old model**
- Never re-reads updated config

---

## 📊 Sequence Diagram

```
TIME 1: Initial State
┌─────────────────────────────────────┐
│ Config: primary_model = "gpt-4o"    │
│ WhatsApp Session Cache:             │
│  - cached_model = "gpt-4o"          │
│  - valid_until = T + 5min           │
│ Gateway In-Memory: "gpt-4o"         │
└─────────────────────────────────────┘

Admin changes config:
    primary_model = "claude-opus-4-5"

TIME 2: After Config Change (before restart)
┌─────────────────────────────────────┐
│ Config: primary_model = "claude-opus-4-5" │ ← CHANGED
│ WhatsApp Session Cache:             │
│  - cached_model = "gpt-4o"          │
│  - valid_until = T + 5min           │ ← STILL VALID!
│ Gateway In-Memory: "gpt-4o"         │
└─────────────────────────────────────┘

User sends message:
  Orchestrator checks: session cache valid?
  → YES! Use cached_model = "gpt-4o"  ← WRONG!

TIME 3: After Gateway Restart
┌─────────────────────────────────────┐
│ Config: primary_model = "claude-opus-4-5" │
│ WhatsApp Session Cache:             │
│  - cached_model = "gpt-4o"          │
│  - valid_until = T + 5min           │ ← STILL VALID!
│ Gateway In-Memory: "claude-opus-4-5" │ ← RELOADED
└─────────────────────────────────────┘

User sends message:
  Orchestrator checks: session cache valid?
  → YES! Use cached_model = "gpt-4o"  ← STILL WRONG!
  
Admin: "But we restarted the gateway!"
System: "But session cache is still valid 🤷"

TIME 4: Session Reset (only solution currently)
┌─────────────────────────────────────┐
│ Config: primary_model = "claude-opus-4-5" │
│ WhatsApp Session Cache: CLEARED     │ ← RESET!
│ Gateway In-Memory: "claude-opus-4-5" │
└─────────────────────────────────────┘

User starts NEW conversation:
  Orchestrator checks: session cache?
  → NO! Re-run routing logic
  → Use updated config: "claude-opus-4-5" ✓
```

---

## 🔧 Solution: Smart Cache Invalidation

### Approach 1: CONFIG HASH CHECKING (Recommended)

Add metadata check to cache validation:

```python
def get_cached_routing(session_id):
    cached = session_cache[session_id]
    
    # NEW: Check if config changed
    current_config_hash = hash(current_config)
    
    if cached['config_hash_at_time'] != current_config_hash:
        # Config changed since cache was created
        logging.info(f"Config mismatch: cache={cached['config_hash_at_time']} current={current_config_hash}")
        del session_cache[session_id]  # Invalidate
        return None  # Force re-evaluation
    
    # OLD: Just check TTL
    if datetime.now() > cached['valid_until']:
        del session_cache[session_id]
        return None
    
    return cached['routing_decision']
```

### Approach 2: PERIODIC CONFIG SYNC

Check every 5 minutes if config changed:

```python
class SessionCacheManager:
    def __init__(self):
        self.last_config_check = time.time()
        self.known_config_hash = self.hash_config()
    
    def periodic_sync(self):
        # Called every 5 minutes by background task
        if time.time() - self.last_config_check > 300:
            current_hash = self.hash_config()
            
            if current_hash != self.known_config_hash:
                logging.warning("CONFIG CHANGED - Invalidating all session caches")
                self.session_cache.clear()
                self.known_config_hash = current_hash
            
            self.last_config_check = time.time()
```

### Approach 3: FILE WATCHER (Most Robust)

Monitor config files for changes:

```python
import watchdog.observers

class ConfigFileWatcher:
    def __init__(self, config_path):
        self.observer = watchdog.observers.Observer()
        self.handler = ConfigChangeHandler(config_path, self.on_config_changed)
        self.observer.schedule(self.handler, path=config_path)
        self.observer.start()
    
    def on_config_changed(self):
        logging.warning("CONFIG FILE CHANGED - Clearing session caches")
        session_cache_manager.invalidate_all()  # Clear ALL sessions
```

---

## 🛠️ Implementation: The 3-Layer Fix

### Layer 1: Cache Entry Metadata

Enhance cache entries with config information:

```python
# OLD cache entry structure
cache_entry = {
    "routing_decision": {...},
    "cached_at": timestamp,
    "valid_until": timestamp
}

# NEW cache entry structure
cache_entry = {
    "routing_decision": {...},
    "cached_at": timestamp,
    "valid_until": timestamp,
    
    # NEW: Config/state metadata
    "config_hash": "abc123def456",           # Config state at cache time
    "model_pool_hash": "xyz789",             # Model list at cache time  
    "gateway_startup_time": 1711000000,      # When gateway started
    "config_last_modified": 1711005000,      # Config modification time
}
```

### Layer 2: Validation Before Use

Check metadata when retrieving from cache:

```python
def get_cached_routing(session_id):
    if session_id not in cache:
        return None
    
    cached = cache[session_id]
    now = time.time()
    
    # Check 1: Has TTL expired?
    if now > cached['valid_until']:
        logging.info(f"Cache expired for {session_id}")
        del cache[session_id]
        return None
    
    # Check 2: Has config changed since cache?
    current_config_hash = compute_hash(current_config)
    if cached['config_hash'] != current_config_hash:
        logging.info(f"Config changed for {session_id} - invalidating cache")
        logging.debug(f"  Old hash: {cached['config_hash']}")
        logging.debug(f"  New hash: {current_config_hash}")
        del cache[session_id]
        return None
    
    # Check 3: Has model pool changed?
    current_pool = compute_model_pool_hash(current_models)
    if cached['model_pool_hash'] != current_pool:
        logging.info(f"Model pool changed for {session_id} - invalidating")
        del cache[session_id]
        return None
    
    # Check 4: Has gateway restarted?
    if cached['gateway_startup_time'] != gateway_startup_time:
        logging.info(f"Gateway restarted - invalidating cache for {session_id}")
        del cache[session_id]
        return None
    
    # All checks passed - cache is valid
    return cached['routing_decision']
```

### Layer 3: Monitoring & Logging

Add detailed logging to track cache operations:

```python
import logging

logger = logging.getLogger("openclaw.orchestrator.cache")

def cache_operation_log(operation, session_id, details):
    """Log cache operations for debugging"""
    
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "operation": operation,  # get, set, invalidate, expire
        "session_id": session_id,
        "details": details,
        "cache_size": len(cache),
        "config_hash": current_config_hash,
        "model_pool_hash": current_model_pool_hash
    }
    
    if operation == "invalidate":
        logger.warning(f"Cache invalidated: {details}")
    elif operation == "get" and details.get("hit"):
        logger.debug(f"Cache hit: {session_id}")
    elif operation == "get" and not details.get("hit"):
        logger.debug(f"Cache miss: {session_id} - {details.get('reason')}")
    elif operation == "set":
        logger.debug(f"Cache set: {session_id}")
```

---

## 📋 Diagnostic Checklist

When model change doesn't work:

### Step 1: Verify Config Change

```bash
# Check config file was actually modified
cat /etc/openclaw/orchestrator.yaml | grep primary_model

# Check file timestamp
stat /etc/openclaw/orchestrator.yaml | grep Modify
```

### Step 2: Check Gateway Startup Time

```bash
# When did gateway start?
systemctl status openclaw | grep "Active:"

# Check if it auto-restart
journalctl -u openclaw -n 20
```

### Step 3: Inspect Session Cache

```bash
# Connect to OpenClaw Redis/storage backend
redis-cli

# List all sessions
KEYS openclaw:session:*

# Check specific session cache
GET openclaw:session:whatsapp_user_123:routing_cache

# Expected output: JSON with cached_routing_decision
# Check if 'config_hash' field matches current config hash
```

### Step 4: Manual Cache Clear

```bash
# Clear all session cache (NUCLEAR OPTION)
redis-cli FLUSHDB  # ⚠️ This clears everything!

# Or clear specific session
redis-cli DEL openclaw:session:whatsapp_user_123:routing_cache

# Then restart gateway
systemctl restart openclaw
```

### Step 5: Check Logs

```bash
# Look for cache invalidation logs
journalctl -u openclaw -n 100 | grep -i "cache\|invalid"

# Look for config hash mismatches
journalctl -u openclaw -n 100 | grep -i "config.*hash"

# Look for model selection logs
journalctl -u openclaw -n 100 | grep -i "selected.*model\|routing"
```

---

## 🚨 Emergency Procedures

### Quick Fix: Clear Session Cache

```bash
# SSH into OpenClaw server
ssh openclaw@gateway.example.com

# Option 1: Clear Redis session cache
redis-cli FLUSHDB

# Option 2: Delete specific session cache key
redis-cli DEL "openclaw:session:whatsapp_user_123:*"

# Restart gateway
sudo systemctl restart openclaw

# Test with fresh conversation
# User should get new model
```

### Permanent Fix: Add Config Watcher

```bash
# Add to systemd service or cron

# Option 1: Add to /etc/openclaw/config-watcher.sh
#!/bin/bash

CONFIG_PATH="/etc/openclaw/orchestrator.yaml"
LAST_HASH=""

while true; do
  CURRENT_HASH=$(md5sum $CONFIG_PATH | awk '{print $1}')
  
  if [ "$LAST_HASH" != "$CURRENT_HASH" ]; then
    echo "Config changed - clearing cache"
    redis-cli FLUSHDB
    LAST_HASH=$CURRENT_HASH
  fi
  
  sleep 5
done

# Run as background service
# systemctl restart openclaw-config-watcher
```

---

## 🧪 Testing the Fix

### Test Scenario 1: Config Change (No Restart)

```
1. Send message to WhatsApp → gets model A
2. Admin changes config → primary_model = B
3. Send another message within 5 minutes
4. Expected: Should get model B (not A)
5. Verify: Check logs show "Config changed - invalidating cache"
```

### Test Scenario 2: Config Change + Gateway Restart

```
1. Send message → cached with model A
2. Admin changes config + restarts gateway
3. Send new message within 5 minutes cache TTL
4. Expected: Should get model B (not A)
5. Verify: Check logs show config hash mismatch
```

### Test Scenario 3: Model Pool Change

```
1. Add new model to models.yaml
2. Send message
3. Expected: New model should be available in routing options
4. Verify: Check model pool hash changed
```

### Test Scenario 4: Session Persistence

```
1. Send message with long context
2. Model cached for 5 minutes
3. Send another message within 5 min
4. Expected: Same model used (from cache)
5. Verify: Check logs show "Cache hit"
```

---

## 📊 Configuration for Fixed Version

```yaml
# /etc/openclaw/orchestrator.yaml (ENHANCED)

orchestrator:
  version: "smart-parenting-v2-with-cache-fix"
  
  # Session caching with invalidation
  session_cache:
    enabled: true
    ttl_seconds: 300  # 5 minute cache
    
    # Cache invalidation triggers
    invalidation_strategy: "multi_layer"  # Checks: TTL + config + pool + startup
    
    # Metadata tracking
    track_config_hash: true
    track_model_pool_hash: true
    track_gateway_startup_time: true
    
    # Periodic validation
    periodic_sync_interval_seconds: 300  # Check every 5 min
    
    # File watching (if available)
    watch_config_files:
      - /etc/openclaw/orchestrator.yaml
      - /etc/openclaw/models.yaml
    watch_interval_seconds: 5

  # Logging for debugging
  cache_logging:
    enabled: true
    log_level: "DEBUG"
    log_cache_hits: true
    log_invalidations: true
    log_config_changes: true
    
  # Fallback strategies
  cache_miss_behavior: "re_route"  # Re-run routing if cache invalid
  cache_error_behavior: "safeguard"  # Use fallback model on error
```

---

## 📈 Expected Improvements After Fix

| Scenario | Before | After |
|----------|--------|-------|
| Config change without restart | ❌ Old model persists | ✅ New model within 5min |
| Config change with restart | ❌ Old model persists | ✅ New model immediately |
| Model pool change | ❌ Old models only | ✅ New models available |
| New user/conversation | ✅ Correct model | ✅ Correct model |
| Multiple config changes | ❌ Cached outdated | ✅ Each change takes effect |
| Gateway auto-restart | ❌ Old config used | ✅ New config loaded |

---

## 🔐 Best Practices Going Forward

### 1. Always Validate Cache

```python
# DON'T: Just check TTL
if cache_entry['valid_until'] > now:
    use_cache()

# DO: Check TTL + config + pool + gateway state
if all([
    cache_entry['valid_until'] > now,
    cache_entry['config_hash'] == current_config_hash,
    cache_entry['model_pool_hash'] == current_pool_hash,
    cache_entry['gateway_startup_time'] == current_startup_time
]):
    use_cache()
```

### 2. Log Cache Operations

```python
# Add to every cache operation
logger.debug({
    "operation": "cache_check",
    "session_id": sid,
    "cache_valid": decision is not None,
    "ttl_expired": ...,
    "config_changed": ...,
    "pool_changed": ....,
    "gateway_restarted": ...
})
```

### 3. Monitor Cache Efficiency

```python
# Track metrics
cache_metrics = {
    "hits": 0,
    "misses": 0,
    "invalidations": 0,
    "expirations": 0,
    "config_mismatches": 0
}

# Alert if too many config mismatches
if cache_metrics["config_mismatches"] > 10 in 5min:
    alert("Frequent config changes detected")
```

