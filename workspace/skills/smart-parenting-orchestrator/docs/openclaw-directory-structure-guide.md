# OpenClaw Skills Directory Structure & Deployment Guide

## 📂 Current Structure

```
~/.openclaw/workspace/skills/smart-parenting-orchestrator/
├── SKILL.md                          # Main skill definition (update ini!)
├── config.yaml                        # Skill-specific config (create baru)
├── orchestrator/
│   ├── __init__.py
│   ├── main_router.py                # Core routing logic
│   ├── api_health_checker.py          # API quota monitoring
│   ├── language_detector.py           # Language detection
│   └── session_cache_manager.py       # Cache management
├── tests/
│   ├── test_routing.py
│   ├── test_language.py
│   └── test_cache.py
└── docs/
    ├── IMPLEMENTATION.md
    ├── TROUBLESHOOTING.md
    └── CHANGELOG.md
```

---

## 🔧 Changes to Make

### Change #1: SKILL.md Location
**BEFORE:**
```
Generic SKILL.md in root
```

**AFTER:**
```
~/.openclaw/workspace/skills/smart-parenting-orchestrator/SKILL.md
```

Replace your current SKILL.md with the enhanced version.

---

### Change #2: Python Implementation Location

Your orchestrator code should live in:
```
~/.openclaw/workspace/skills/smart-parenting-orchestrator/orchestrator/
```

Not in:
```
openclaw/orchestrator/api_health_checker.py  ❌
```

---

### Change #3: Configuration File

Create:
```
~/.openclaw/workspace/skills/smart-parenting-orchestrator/config.yaml
```

This is skill-specific config, separate from global OpenClaw config.

---

### Change #4: Import Paths

In `main_router.py`, update imports:

**BEFORE (global):**
```python
from openclaw.orchestrator.api_health_checker import APIHealthChecker
from openclaw.orchestrator.language_detector import LanguageDetector
from openclaw.orchestrator.session_cache_manager import SessionCacheManager
```

**AFTER (skill-local):**
```python
from .api_health_checker import APIHealthChecker
from .language_detector import LanguageDetector
from .session_cache_manager import SessionCacheManager
```

---

### Change #5: Entry Point

OpenClaw expects skill entry point di SKILL.md. Add section:

```yaml
# SKILL.md

---
name: smart-parenting-orchestrator-v2
description: Enhanced model router with API limit detection, Indonesian language awareness, and session cache management
metadata:
  openclaw:
    emoji: "👨‍👩‍👧‍👦"
    version: "2.0"
    entry_point: "orchestrator.main_router:SmartOrchestratorV2"
    config_file: "config.yaml"
    python_version: "3.9+"
    dependencies:
      - requests
      - pyyaml
---

# Rest of SKILL.md...
```

---

## 📋 Step-by-Step Deployment

### Step 1: Backup Current Skill

```bash
cd ~/.openclaw/workspace/skills/smart-parenting-orchestrator

# Backup
cp SKILL.md SKILL.md.backup
cp -r . ~/smart-parenting-orchestrator.backup
```

### Step 2: Update SKILL.md

```bash
# Replace current SKILL.md dengan enhanced version
cat > SKILL.md << 'EOF'
[content dari smart-parenting-orchestrator-enhanced.md]
EOF
```

### Step 3: Create Python Modules Directory

```bash
mkdir -p orchestrator

# Create __init__.py
touch orchestrator/__init__.py

# Copy Python files
cat > orchestrator/api_health_checker.py << 'EOF'
[content dari api_health_checker.py]
EOF

cat > orchestrator/language_detector.py << 'EOF'
[content dari language_detector.py]
EOF

cat > orchestrator/session_cache_manager.py << 'EOF'
[content dari session_cache_manager.py]
EOF

cat > orchestrator/main_router.py << 'EOF'
[content dari main_router.py - UPDATED IMPORTS]
EOF
```

### Step 4: Create Skill Configuration

```bash
cat > config.yaml << 'EOF'
orchestrator:
  version: "smart-parenting-v2"
  enabled: true
  
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
        
      claude-haiku-4-5:
        provider: anthropic
        model_id: claude-haiku-4-5-20250514
        api_key: ${ANTHROPIC_API_KEY}
        
      gpt-4o:
        provider: openai
        model_id: gpt-4o
        api_key: ${OPENAI_API_KEY}
        
      gemini-3.1-pro:
        provider: google
        model_id: gemini-3.1-pro
        api_key: ${GOOGLE_API_KEY}
  
  language_detection:
    enabled: true
    supported_languages: [indonesian, english]
    cache_ttl_seconds: 3600
    supported_channels: [whatsapp, telegram]
  
  session_cache:
    enabled: true
    cache_ttl_seconds: 300
    periodic_sync_interval_seconds: 300
    invalidate_on_config_change: true
    invalidate_on_model_pool_change: true
  
  model_preferences:
    indonesian:
      primary: [claude-opus-4-5, claude-sonnet-4-5, claude-haiku-4-5]
      fallback: [gemini-3.1-pro, gpt-4o]
    english:
      primary: [claude-opus-4-5, claude-sonnet-4-5]
      fallback: [gpt-4o, gemini-3.1-pro]
  
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
EOF
```

### Step 5: Create Documentation

```bash
mkdir -p docs

cat > docs/IMPLEMENTATION.md << 'EOF'
[content dari openclaw-implementation-guide.md]
EOF

cat > docs/TROUBLESHOOTING.md << 'EOF'
[content dari openclaw-session-cache-fix.md]
EOF

cat > docs/CHANGELOG.md << 'EOF'
# Changelog - Smart Parenting Orchestrator v2

## [2.0] - 2025-03-26

### Added
- API Rate Limit Detection (429 handling, quota monitoring)
- Indonesian Language Priority with session caching
- Smart Session Cache with config hash validation
- Multi-layer cache invalidation strategy
- Comprehensive error handling and fallbacks

### Changed
- Enhanced SKILL.md with detailed routing logic
- Session cache validation now checks: TTL, config hash, model pool, gateway state
- Language detection cached for 1 hour per session
- Cache TTL reduced from indefinite to 5 minutes for faster config updates

### Fixed
- Session cache persisting old model after config change
- Missing API health checks before routing decision
- No language-specific model preferences
- Gateway restart not clearing session cache properly

## [1.0] - Previous Version
- Original parenting context detection
- Basic model selection matrix
- Safety override rules
EOF
```

### Step 6: Update Imports in Python Files

**File: orchestrator/main_router.py**

Change all imports from global to local:

```python
# orchestrator/main_router.py

from .api_health_checker import APIHealthChecker
from .language_detector import LanguageDetector
from .session_cache_manager import SessionCacheManager

import yaml
import os
from datetime import datetime, timedelta
from typing import Dict, Any

class SmartOrchestratorV2:
    """Enhanced model router with health checks, language detection, cache management"""
    
    def __init__(self, skill_dir: str = None):
        # Load config from skill directory
        if skill_dir is None:
            skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        config_path = os.path.join(skill_dir, 'config.yaml')
        
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.health_checker = APIHealthChecker(self.config)
        self.language_detector = LanguageDetector(cache_ttl_seconds=3600)
        self.cache_manager = SessionCacheManager(self.config, cache_ttl_seconds=300)
    
    # ... rest of implementation
```

### Step 7: Create __init__.py for Package

```bash
cat > orchestrator/__init__.py << 'EOF'
"""Smart Parenting Orchestrator - Intelligent model routing for family-related AI"""

from .main_router import SmartOrchestratorV2
from .api_health_checker import APIHealthChecker
from .language_detector import LanguageDetector
from .session_cache_manager import SessionCacheManager

__version__ = "2.0.0"
__all__ = [
    "SmartOrchestratorV2",
    "APIHealthChecker",
    "LanguageDetector",
    "SessionCacheManager"
]
EOF
```

---

## 🔗 Integration with OpenClaw

### Option A: Skill-Based Integration (Recommended)

OpenClaw will automatically:
1. Load `SKILL.md` from skill directory
2. Parse `metadata.openclaw.entry_point`
3. Import `orchestrator.main_router:SmartOrchestratorV2`
4. Load config from `config.yaml`

**File: ~/.openclaw/workspace/skills/smart-parenting-orchestrator/SKILL.md**
```yaml
metadata:
  openclaw:
    entry_point: "orchestrator.main_router:SmartOrchestratorV2"
    config_file: "config.yaml"
```

### Option B: Channel Integration

Update your WhatsApp channel config to use this orchestrator:

**File: ~/.openclaw/config/channels/whatsapp.yaml**
```yaml
whatsapp:
  # ... existing config ...
  
  routing:
    orchestrator: "smart-parenting-orchestrator"  # Reference to skill
    skill_path: "~/.openclaw/workspace/skills/smart-parenting-orchestrator"
    
    api_key_monitoring: true
    language_detection: true
    session_cache: true
```

---

## 📂 Final Directory Structure

```
~/.openclaw/workspace/skills/smart-parenting-orchestrator/
├── SKILL.md                          ✅ Enhanced with v2 logic
├── config.yaml                       ✅ Skill-specific configuration
├── orchestrator/
│   ├── __init__.py                   ✅ Package initialization
│   ├── main_router.py                ✅ SmartOrchestratorV2 class
│   ├── api_health_checker.py          ✅ API quota monitoring
│   ├── language_detector.py           ✅ Language detection + caching
│   └── session_cache_manager.py       ✅ Cache with config validation
├── docs/
│   ├── IMPLEMENTATION.md              ✅ Detailed implementation guide
│   ├── TROUBLESHOOTING.md             ✅ Session cache fix + diagnosis
│   └── CHANGELOG.md                   ✅ Version history
└── tests/
    ├── test_routing.py                (optional)
    ├── test_language.py               (optional)
    └── test_cache.py                  (optional)
```

---

## ✅ Verification Checklist

After deployment:

```bash
cd ~/.openclaw/workspace/skills/smart-parenting-orchestrator

# Check directory structure
ls -la
# Should see: SKILL.md, config.yaml, orchestrator/, docs/

# Check Python module
python3 -c "from orchestrator import SmartOrchestratorV2; print('✓ Module loads correctly')"

# Validate YAML config
python3 -c "import yaml; yaml.safe_load(open('config.yaml')); print('✓ Config is valid')"

# Check OpenClaw recognizes skill
openclaw skill list | grep smart-parenting-orchestrator
# Should show: smart-parenting-orchestrator-v2 (enabled)
```

---

## 🔄 Migration from v1 to v2

If upgrading from v1:

### Backward Compatibility

Old skill will still work, but:
- ❌ No API rate limit detection
- ❌ No Indonesian language priority
- ❌ Session cache not invalidating properly

### Migration Steps

```bash
# 1. Backup v1
cp SKILL.md SKILL.md.v1

# 2. Update to v2
# Use enhanced SKILL.md

# 3. Add new Python modules
mkdir -p orchestrator
# Add api_health_checker.py, etc.

# 4. Create config.yaml

# 5. Clear old session caches
redis-cli FLUSHDB

# 6. Restart OpenClaw
systemctl restart openclaw

# 7. Test with new message
# Should see new model in logs
journalctl -u openclaw -n 50 | grep selected_model
```

---

## 🐛 Debugging

If something not working:

### Check if skill loaded
```bash
openclaw skill show smart-parenting-orchestrator-v2
# Should show all metadata and entry point

# Check if orchestrator module exists
python3 -c "from orchestrator.main_router import SmartOrchestratorV2"
```

### Check if config loaded
```bash
python3 << 'EOF'
import yaml
import os

skill_dir = os.path.expanduser("~/.openclaw/workspace/skills/smart-parenting-orchestrator")
config_path = os.path.join(skill_dir, "config.yaml")

with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

print("Config loaded successfully:")
print(f"  API Health Check: {config['orchestrator']['api_health_check']['enabled']}")
print(f"  Language Detection: {config['orchestrator']['language_detection']['enabled']}")
print(f"  Session Cache: {config['orchestrator']['session_cache']['enabled']}")
EOF
```

### Check logs for routing decisions
```bash
journalctl -u openclaw -f | grep -i "orchestrator\|routing\|cache"
```

---

## 📞 Support

If integration fails:

1. Check `~/.openclaw/logs/orchestrator.log`
2. Run diagnostic: `python3 -m orchestrator.main_router --test`
3. Check config matches OpenClaw expectations
4. Verify all environment variables (API keys) are set

