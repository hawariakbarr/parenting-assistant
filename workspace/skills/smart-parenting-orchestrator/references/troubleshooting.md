# Troubleshooting Guide

## Skill Not Showing in `openclaw skills list`

### Check 1: Directory Structure
```bash
ls -la ~/.openclaw/workspace/skills/smart-parenting-orchestrator/
```

Should show: SKILL.md, config.yaml, references/, scripts/

### Check 2: SKILL.md Format
```bash
head -20 SKILL.md | grep "^---"
# Should see: --- at start
```

### Check 3: Restart OpenClaw
```bash
systemctl restart openclaw
sleep 3
openclaw skills list | grep smart-parenting
```

## Model Not Changing

### Issue 1: Config Not Updated
```bash
# Check config.yaml exists
cat config.yaml | grep primary_model

# Restart gateway
systemctl restart openclaw
```

### Issue 2: Session Cache
```bash
# Session may be cached for 5 minutes
# Either: wait 5 minutes or reset WhatsApp session

# Or clear Redis cache
redis-cli FLUSHDB
systemctl restart openclaw
```

### Issue 3: API Key Issue
```bash
# Check environment
echo $ANTHROPIC_API_KEY
echo $OPENAI_API_KEY

# If missing, set and restart
export ANTHROPIC_API_KEY="your-key"
systemctl restart openclaw
```

## Language Detection Wrong

### Check Language Keywords
```bash
# See: references/language-detection.md
# Message must have 3+ keywords for high confidence
# Haiku, Sonnet vs Opus → depends on language detected
```

### Mixed Language Issues
```bash
# If user mixes Indonesian + English
# Dominant language (>50%) is selected
# Can trigger re-detection with new message
```

## Rate Limiting Errors

### Check API Status
```bash
# Look for 429 errors in logs
journalctl -u openclaw -f | grep 429
journalctl -u openclaw -f | grep rate_limit
```

### Fallback Not Working
```bash
# Check all API keys are valid
echo $ANTHROPIC_API_KEY
echo $OPENAI_API_KEY

# If one is down, fallback should work
# If multiple down, may see errors
```

## Logs

### View Real-Time Logs
```bash
journalctl -u openclaw -f | grep orchestrator
journalctl -u openclaw -f | grep routing
journalctl -u openclaw -f | grep selected_model
```

### Find Specific Errors
```bash
# Find route decisions
journalctl -u openclaw | grep "selected_model"

# Find API errors
journalctl -u openclaw | grep "429\|rate_limit\|quota"

# Find safety escalations
journalctl -u openclaw | grep "safety\|critical"
```

## Performance Issues

### Slow Response

1. Check API latency: `cat references/api-limits.md`
2. Check model load: May need better model
3. Check gateway resources: Free up disk/memory

### High Token Usage

1. Shorter responses = lower cost
2. Haiku for simple questions = major savings
3. Cache hits = zero additional API calls

---

See `references/routing-logic.md` for detailed algorithm.
See `references/model-matrix.md` for quick reference.
