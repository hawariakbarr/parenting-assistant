# Frequently Asked Questions

## Q: Why is Indonesian prioritized?

A: Claude models have better Indonesian training data and cultural understanding, especially for family/parenting topics. They're also cost-effective.

## Q: Can I force a specific model?

A: Not directly through the skill. The router always picks based on language, complexity, and safety. To override: modify config.yaml or the model list.

## Q: What's the difference between Haiku, Sonnet, Opus?

See `references/model-matrix.md` for comparison. Summary:
- Haiku: Fast, cheap, good for simple
- Sonnet: Balanced, good Indonesian
- Opus: Best reasoning, critical topics

## Q: How is complexity calculated?

Score = message_length + questions + topics + safety_factor
Range: 1 (simple) to 10 (critical)

See `references/routing-logic.md` for details.

## Q: Why does the same message sometimes use different models?

Possible reasons:
1. Different user (different session ID)
2. 5+ minutes passed (cache expired)
3. Config changed
4. API status changed (rate limit)

## Q: What happens if all models are rate limited?

Fallback chain tries each model. If all fail, returns error and suggests to retry later.

## Q: Is there a cost calculator?

Rough estimate: Haiku = 1 unit, Sonnet = 3 units, Opus = 10 units.
Using smart routing: ~40% cheaper than always using Opus.

## Q: How do I update the routing logic?

1. Edit `references/routing-logic.md` to document change
2. Update config.yaml if needed
3. Restart OpenClaw gateway
4. Test with WhatsApp

## Q: Can I add more languages?

Yes! Add to:
1. `references/language-detection.md` - keywords for new language
2. `references/model-matrix.md` - preferred models
3. Restart gateway

## Q: Emergency access to best model?

Use safety keywords to escalate to Claude Opus:
- "emergency", "hospital", "critical"
- "sakit", "darurat" (Indonesian)

## Q: How is user privacy handled?

Messages are processed for:
- Language detection
- Keyword scanning (safety/parenting)
- Routing decision

No message content is logged or stored.

## Q: Can sessions be shared between users?

No. Each WhatsApp user gets unique session ID. Language/routing cached per user.

## Q: What if I want Indonesian + English mixed?

Router detects dominant language (>50%) and uses that chain.
For perfect bilingual support, would need custom logic.

---

For detailed info, see references/ directory.
