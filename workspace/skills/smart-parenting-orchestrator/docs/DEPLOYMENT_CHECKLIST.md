# 🚀 Quick Deployment Checklist

## Step-by-Step Installation

```bash
cd ~/.openclaw/workspace/skills/smart-parenting-orchestrator

# Step 1: Backup current setup
cp SKILL.md SKILL.md.backup
cp -r orchestrator orchestrator.backup

# Step 2: Copy Python files
cp /path/to/api_health_checker.py orchestrator/
cp /path/to/language_detector.py orchestrator/
cp /path/to/session_cache_manager.py orchestrator/
cp /path/to/main_router.py orchestrator/

# Step 3: Create __init__.py
cat > orchestrator/__init__.py << 'EOF'
"""Smart Parenting Orchestrator - Intelligent model routing"""
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

# Step 4: Update SKILL.md dengan enhanced version (lihat file di atas)

# Step 5: Create config.yaml (lihat file di atas)

# Step 6: Verify imports
python3 -c "from orchestrator import SmartOrchestratorV2; print('✓ Imports OK')"

# Step 7: Validate YAML
python3 -c "import yaml; yaml.safe_load(open('config.yaml')); print('✓ Config valid')"

# Step 8: Clear old caches
redis-cli FLUSHDB  # ⚠️ CAUTION: Clears all OpenClaw data!

# Step 9: Restart OpenClaw
systemctl restart openclaw

# Step 10: Test
# Send message via WhatsApp
# Check logs: journalctl -u openclaw -f | grep orchestrator
```

---

## File Structure After Install

```
~/.openclaw/workspace/skills/smart-parenting-orchestrator/
├── SKILL.md                           ← Enhanced v2
├── config.yaml                        ← New file
├── orchestrator/
│   ├── __init__.py                    ← New file
│   ├── api_health_checker.py          ← New file
│   ├── language_detector.py           ← New file
│   ├── session_cache_manager.py       ← New file
│   └── main_router.py                 ← New file
├── docs/
│   ├── IMPLEMENTATION.md              ← New file
│   ├── TROUBLESHOOTING.md             ← New file
│   └── CHANGELOG.md                   ← New file
└── [backups/]
    ├── SKILL.md.backup
    └── orchestrator.backup/
```

---

## Testing After Install

### Test 1: Module Loads
```bash
python3 << 'EOF'
import sys
sys.path.insert(0, '/root/.openclaw/workspace/skills/smart-parenting-orchestrator')

from orchestrator import SmartOrchestratorV2
print("✓ SmartOrchestratorV2 imported successfully")

router = SmartOrchestratorV2()
print("✓ Orchestrator initialized")
print(f"✓ Config hash: {router.cache_manager.config_hash}")
print(f"✓ Model pool: {list(router.config['orchestrator']['api_health_check']['models'].keys())}")
EOF
```

### Test 2: Routing Works
```bash
python3 << 'EOF'
import sys
sys.path.insert(0, '/root/.openclaw/workspace/skills/smart-parenting-orchestrator')

from orchestrator import SmartOrchestratorV2

router = SmartOrchestratorV2()

# Test Indonesian parenting query
result = router.route_request(
    user_message="Anak saya berusia 2 tahun dan tidak mau tidur, apa yang harus saya lakukan?",
    session_id="test_session_001"
)

print(f"Selected model: {result['selected_model']}")
print(f"Language: {result['language_detected']}")
print(f"Parenting mode: {result['parenting_mode']}")
print(f"Confidence: {result['confidence']}")
EOF
```

### Test 3: Cache Works
```bash
python3 << 'EOF'
import sys
sys.path.insert(0, '/root/.openclaw/workspace/skills/smart-parenting-orchestrator')

from orchestrator import SmartOrchestratorV2

router = SmartOrchestratorV2()

# First request
result1 = router.route_request(
    user_message="Bagaimana cara mengajar anak membaca?",
    session_id="cache_test_001"
)
print(f"First request model: {result1['selected_model']}")

# Second request (should be cached)
result2 = router.route_request(
    user_message="Lalu bagaimana dengan menulis?",
    session_id="cache_test_001"
)
print(f"Second request model: {result2['selected_model']} (should be same as first)")
print(f"Cache used: {result1['selected_model'] == result2['selected_model']}")
EOF
```

### Test 4: Language Detection
```bash
python3 << 'EOF'
import sys
sys.path.insert(0, '/root/.openclaw/workspace/skills/smart-parenting-orchestrator')

from orchestrator import LanguageDetector

detector = LanguageDetector()

# Test Indonesian
lang_id, conf_id = detector.detect_language("Anak saya sedang sakit, bagaimana cara mengobatinya?")
print(f"Indonesian detection: {lang_id} ({conf_id:.2f})")

# Test English
lang_en, conf_en = detector.detect_language("How should I help my child with reading?")
print(f"English detection: {lang_en} ({conf_en:.2f})")
EOF
```

### Test 5: API Health Check
```bash
python3 << 'EOF'
import sys
sys.path.insert(0, '/root/.openclaw/workspace/skills/smart-parenting-orchestrator')

from orchestrator import APIHealthChecker
import yaml

with open('/root/.openclaw/workspace/skills/smart-parenting-orchestrator/config.yaml') as f:
    config = yaml.safe_load(f)

checker = APIHealthChecker(config)
healthy = checker.get_healthy_models()
print(f"Healthy models: {healthy}")

status = checker.get_all_models_status()
for model, info in status.items():
    print(f"  {model}: {info['health']}")
EOF
```

---

## Troubleshooting Common Issues

### Issue: "No module named 'orchestrator'"

**Solution:**
```bash
# Check Python path
cd ~/.openclaw/workspace/skills/smart-parenting-orchestrator
python3 -c "import sys; print(sys.path)"

# Make sure __init__.py exists
ls -la orchestrator/__init__.py

# Try importing with full path
python3 -c "import sys; sys.path.insert(0, '.'); from orchestrator import SmartOrchestratorV2"
```

### Issue: "FileNotFoundError: config.yaml"

**Solution:**
```bash
# Check config file exists
ls -la ~/.openclaw/workspace/skills/smart-parenting-orchestrator/config.yaml

# Check file is readable
cat config.yaml | head -5

# Make sure YAML is valid
python3 -c "import yaml; yaml.safe_load(open('config.yaml')); print('OK')"
```

### Issue: "API key not found in config"

**Solution:**
```bash
# Check environment variables are set
echo $ANTHROPIC_API_KEY
echo $OPENAI_API_KEY

# Update config.yaml to use env vars properly:
# api_key: ${ANTHROPIC_API_KEY}

# Or hardcode for testing (NOT for production):
# api_key: "sk-ant-xxxxx"

# Reload environment
source ~/.bashrc  # or ~/.bash_profile
systemctl restart openclaw
```

### Issue: "Cache not invalidating after config change"

**Solution:**
```bash
# Clear all caches manually
redis-cli FLUSHDB

# Or clear specific session
redis-cli DEL "openclaw:session:*"

# Restart gateway
systemctl restart openclaw

# Check logs
journalctl -u openclaw -n 50 | grep cache
```

---

## Monitoring & Logging

### View Orchestrator Logs
```bash
# Real-time logs
journalctl -u openclaw -f | grep orchestrator

# View specific component
journalctl -u openclaw -f | grep "api_health_checker\|language_detector\|session_cache"

# View routing decisions
journalctl -u openclaw -f | grep "selected_model\|routing"

# View cache operations
journalctl -u openclaw -f | grep -i "cache"
```

### Monitor Cache Stats
```bash
python3 << 'EOF'
import sys
sys.path.insert(0, '/root/.openclaw/workspace/skills/smart-parenting-orchestrator')

from orchestrator import SmartOrchestratorV2

router = SmartOrchestratorV2()
stats = router.cache_manager.get_cache_stats()

print("Cache Statistics:")
for key, value in stats.items():
    print(f"  {key}: {value}")
EOF
```

### Check Model Health Regularly
```bash
# Add to crontab for periodic checks
*/5 * * * * python3 /root/.openclaw/check_health.py >> /var/log/openclaw-health.log 2>&1

# Create check_health.py:
cat > /root/.openclaw/check_health.py << 'EOF'
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/.openclaw/workspace/skills/smart-parenting-orchestrator')
from orchestrator import SmartOrchestratorV2
import json
from datetime import datetime

try:
    router = SmartOrchestratorV2()
    status = router.health_checker.get_all_models_status()
    
    result = {
        "timestamp": datetime.utcnow().isoformat(),
        "models": {}
    }
    
    for model, info in status.items():
        result["models"][model] = {
            "health": info["health"],
            "limited": info["limited"],
            "response_time_ms": info.get("api_response_time_ms")
        }
    
    print(json.dumps(result, indent=2))
    
except Exception as e:
    print(f"Error: {str(e)}")
    sys.exit(1)
EOF

chmod +x /root/.openclaw/check_health.py
```

---

## Verification Checklist

After deployment, verify:

- [ ] Files copied to `orchestrator/` directory
- [ ] `SKILL.md` updated with v2 content
- [ ] `config.yaml` created and valid
- [ ] `orchestrator/__init__.py` exists
- [ ] Python imports work: `from orchestrator import SmartOrchestratorV2`
- [ ] YAML config is valid
- [ ] API keys set in environment or config
- [ ] Redis cache cleared
- [ ] OpenClaw restarted: `systemctl restart openclaw`
- [ ] Test message sent via WhatsApp
- [ ] Logs show routing decision: `journalctl -u openclaw -f | grep selected_model`
- [ ] Model changed from config persists after restart ✓
- [ ] Language detection works for Indonesian ✓
- [ ] Cache invalidates on config change ✓

---

## Rollback Procedure

If something goes wrong:

```bash
cd ~/.openclaw/workspace/skills/smart-parenting-orchestrator

# Restore backup
cp SKILL.md.backup SKILL.md
rm -rf orchestrator/
cp -r orchestrator.backup orchestrator/

# Clear caches
redis-cli FLUSHDB

# Restart
systemctl restart openclaw

# Verify
journalctl -u openclaw -n 20
```

---

## Next Steps

1. Deploy to production
2. Monitor logs for 1 hour
3. Test config changes (should apply immediately)
4. Test API rate limiting (disable one API key temporarily)
5. Test Indonesian language routing
6. Once stable, remove backup files

---

## Support

If you encounter issues:

1. Check logs: `journalctl -u openclaw -f`
2. Test modules: `python3 -m orchestrator.main_router --test`
3. Verify config: `python3 -c "import yaml; yaml.safe_load(open('config.yaml'))"`
4. Clear cache: `redis-cli FLUSHDB`
5. Restart: `systemctl restart openclaw`

