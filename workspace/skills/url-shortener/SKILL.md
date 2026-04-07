---
name: url-shortener
description: Shorten long URLs using free public services (is.gd, TinyURL). Use when user wants to create a short link for any URL.
---

# URL Shortener

Shorten URLs using free public API services. No API key required.

## Usage

### Quick Method (Recommended)

Use the helper script that handles everything automatically:

```bash
# Simple shortening
/root/.openclaw/workspace/skills/url-shortener/scripts/shorten.sh "URL"

# With custom alias (for domains only)
/root/.openclaw/workspace/skills/url-shortener/scripts/shorten.sh "URL" "custom-name"
```

### Manual Method

When a user asks to shorten a URL, use one of these commands:

#### Using is.gd (For domains only - supports custom aliases)

```bash
curl -s "https://is.gd/create.php?format=simple&url=ENCODED_URL"
```

**With custom short code:**
```bash
curl -s "https://is.gd/create.php?format=simple&url=ENCODED_URL&shorturl=CUSTOM_CODE"
```

**⚠️ Important:** is.gd blocks URLs with IP addresses (e.g., 167.99.73.86). Use TinyURL for IPs.

#### Using TinyURL (Works with IP addresses)

```bash
curl -s "http://tinyurl.com/api-create.php?url=ENCODED_URL"
```

## URL Encoding

Always URL-encode the target URL before passing to the API:

```bash
# Example: Shorten http://167.99.73.86:8000/dashboard.html

# URL encode the URL
ENCODED=$(printf %s "http://167.99.73.86:8000/dashboard.html" | jq -sRr @uri)

# Shorten with is.gd
curl -s "https://is.gd/create.php?format=simple&url=$ENCODED"

# Result: https://is.gd/abc123
```

## Workflow

1. **Receive URL** from user
2. **URL-encode** the URL (handle special characters)
3. **Call API** (is.gd or TinyURL)
4. **Return shortened URL** to user
5. **Test the link** (optional - curl -I to verify it redirects)

## Response Format

Reply to user with:
```
✅ Shortened URL:
Original: [long URL]
Short: [shortened URL]

The link is ready to share! 🌸
```

## Error Handling

If the API returns an error:
- Check if URL is valid (starts with http:// or https://)
- Try alternative service (TinyURL if is.gd fails)
- Report error clearly to user

## Supported Services

| Service | Features | Limits |
|---------|----------|--------|
| **is.gd** | Custom aliases, statistics | 5 requests/minute per IP |
| **TinyURL** | Simple, reliable | No official limit |

## Examples

### Example 1: Simple Shortening
```bash
curl -s "https://is.gd/create.php?format=simple&url=http%3A%2F%2F167.99.73.86%3A8000%2Fdashboard.html"
```

### Example 2: With Custom Alias
```bash
curl -s "https://is.gd/create.php?format=simple&url=http%3A%2F%2F167.99.73.86%3A8000%2Fdashboard.html&shorturl=mydash"
```
Result: `https://is.gd/mydash`

### Example 3: Fallback to TinyURL
```bash
curl -s "http://tinyurl.com/api-create.php?url=http%3A%2F%2F167.99.73.86%3A8000%2Fdashboard.html"
```

## Important Notes

### URL Type Support

| URL Type | is.gd | TinyURL | Recommendation |
|----------|-------|---------|----------------|
| Domain (example.com) | ✅ Yes | ✅ Yes | Use is.gd (custom aliases) |
| IP Address (167.99.73.86) | ❌ Blocked | ✅ Yes | Use TinyURL |
| Localhost (127.0.0.1) | ❌ No | ❌ No | Not accessible from internet |

### Additional Notes

- URLs remain active indefinitely (unless reported as spam)
- No authentication required
- No usage tracking by default
- The helper script auto-detects IP addresses and picks the right service

## Tips

- Use is.gd for custom short codes
- Use TinyURL for simplicity
- Always test shortened links before sharing
- Consider privacy: shortened links are public and anyone with the link can access the target
