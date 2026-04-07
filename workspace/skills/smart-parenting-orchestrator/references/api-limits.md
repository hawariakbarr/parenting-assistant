# API Rate Limit Handling

## Detection

Router detects rate limits by:
1. HTTP 429 response code
2. "quota_exceeded" error messages
3. API header: X-RateLimit-Remaining
4. Error tracking (5-minute window)

## Response

When rate limit detected:
1. Mark model as unavailable
2. Use fallback model
3. Check again in 60 seconds
4. Log for monitoring

## Fallback Chain

**Indonesian Priority:**
Claude Opus → Claude Sonnet → Claude Haiku → Gemini 3.1 → GPT-4o

**English Priority:**
Claude Opus → GPT-4o → Claude Sonnet → Claude Haiku → Gemini 3.1

## Configuration

Set API keys via environment:
```bash
export ANTHROPIC_API_KEY="sk-ant-xxxxx"
export OPENAI_API_KEY="sk-xxxxx"
export GOOGLE_API_KEY="xxxxx"
```
