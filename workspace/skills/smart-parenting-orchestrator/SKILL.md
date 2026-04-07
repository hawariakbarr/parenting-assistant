---
name: smart-parenting-orchestrator
version: "2.2.0"
description: "Intelligent model routing for parenting queries with language awareness and safety escalation"
keywords:
  - parenting
  - routing
  - indonesian
  - language-aware
category: "routing"
metadata:
  openclaw:
    enabled: true
    emoji: "👨‍👩‍👧‍👦"
    type: "instruction-skill"
---

# 🧑‍👩‍👧‍👦 Smart Parenting AI Orchestrator

Intelligent routing for parenting-related queries with **language awareness**, **API health monitoring**, and **safety escalation**.

## ⚡ Quick Summary

This skill routes user messages to the **optimal AI model** based on:

- 🌐 **Language** (Indonesian vs English)
- 🎯 **Query Complexity** (simple → complex)  
- 👨‍👩‍👧 **Parenting Context** (is this parenting-related?)
- 🚨 **Safety** (critical topics escalate)
- 💚 **API Health** (model availability)

## 📖 Documentation

- **Model Selection**: See `references/model-matrix.md`
- **Routing Algorithm**: See `references/routing-logic.md`
- **Language Detection**: See `references/language-detection.md`
- **API Limits**: See `references/api-limits.md`
- **Troubleshooting**: See `references/troubleshooting.md`
- **FAQ**: See `references/faq.md`

## 🔄 How It Works

```
User Message (via WhatsApp)
    ↓
1. Detect Language (Indonesian? English?)
    ↓
2. Check API Health (which models available?)
    ↓
3. Analyze Context (complexity? parenting? safe?)
    ↓
4. Apply Routing Rules
    ↓
5. Return: Selected Model + Fallbacks
    ↓
Message sent to optimal model
```

## 🇮🇩 Indonesian Language Priority (UPDATED)

For **Indonesian users asking about parenting:**

| Complexity | Model | Why |
|-----------|-------|-----|
| Very Simple (1-2) | Claude **Haiku** | Greetings, simple questions |
| Medium (3-4) | Claude **Sonnet** | **PRIMARY** — better Indonesian + accuracy |
| Complex (5+) | Claude **Opus** | Best reasoning + safety |

**Key Changes:**
- **26 Mar:** Base complexity raised to 3 → Sonnet for most Kal logs (accuracy fix)
- **27 Mar v2.2:** Base lowered to 2, added greeting penalty (-1) → Haiku for "hai"/"hello"
- Data tracking still gets +2 bonus → Sonnet for feed/weight/diaper logs

**Key Point:** Claude models have better Indonesian training data and cultural understanding.

## 🔴 API Rate Limit Handling

If a model hits rate limits (HTTP 429):
1. ✓ Automatically switch to fallback model
2. ✓ No interruption to user
3. ✓ Check again in 60 seconds

Fallback chain: Opus → Sonnet → Haiku → Gemini → GPT-4o

## ⚠️ Safety Escalation

**Always** escalate to best model when message contains:
- Medical emergency keywords
- Mental health crisis indicators
- Abuse or violence mentions

**Indonesian Keywords:** sakit darurat, bunuh diri, kekerasan
**English Keywords:** emergency, suicide, abuse

Crisis resources provided with response.

## 💾 Caching

- **Session Cache:** 5 minutes (reuse decision for same user)
- **Language Cache:** 1 hour (don't re-detect language)

Cache auto-invalidates when:
- Config changes
- Model list changes
- TTL expires

## 📊 Example Scenarios

### Example 1: Simple Indonesian

Input: "Bagaimana cara menyapih bayi?"  
→ Detected: Indonesian, parenting, complexity 2  
→ Selected: **Claude Haiku** (fast + cheap)

### Example 2: Complex with Safety

Input: "Bayi saya sakit dan suhu tinggi, kapan harus ke rumah sakit?"  
→ Detected: Indonesian, parenting, complexity 7, **safety concern**  
→ Selected: **Claude Opus** (escalated for medical safety)  
→ Added: Professional help recommendation

## ⚙️ Configuration

See `config.yaml` for configuration options.

**Required environment variables:**
```bash
export ANTHROPIC_API_KEY="sk-ant-xxxxx"
export OPENAI_API_KEY="sk-xxxxx"
export GOOGLE_API_KEY="xxxxx"
```

## 🆘 Troubleshooting

### Skill not showing?
- Check: `references/troubleshooting.md`
- Run: `openclaw skills list`
- Restart: `systemctl restart openclaw`

### Model not changing?
- Check: `references/troubleshooting.md#model-not-changing`
- Cache expires in 5 minutes
- Or clear cache: `redis-cli FLUSHDB`

### API Key issues?
- Check environment variables
- See: `references/api-limits.md`

## 📞 Support

1. Check relevant reference in `references/` directory
2. See `references/faq.md` for common questions
3. Check `references/troubleshooting.md` for issues
4. Review logs: `journalctl -u openclaw -f | grep orchestrator`

## 📝 Version Info

**Status:** ✓ Production Ready  
**Version:** 2.1.0 (26 Mar 2026)  
**Last Updated:** 2026-03-26

### 📋 Changelog

**v2.1.0 (26 Mar 2026):**
- ✅ Raised parenting base complexity from 1 → 3 (forces Sonnet routing)
- ✅ Added +2 bonus for data tracking logs (feed/weight/diaper)
- ✅ Raised safety escalation score from +2 → +3
- ✅ Result: Most Kal logs now route to Claude **Sonnet** (better accuracy)

---

See the `references/` directory for detailed documentation.
