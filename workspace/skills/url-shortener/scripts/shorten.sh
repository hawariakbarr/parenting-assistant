#!/bin/bash
# URL Shortener Helper Script
# Usage: ./shorten.sh <url> [custom_alias]

set -e

URL="$1"
CUSTOM_ALIAS="${2:-}"

if [ -z "$URL" ]; then
    echo "Usage: $0 <url> [custom_alias]"
    echo "Example: $0 http://167.99.73.86:8000/dashboard.html"
    echo "Example: $0 https://example.com/long/path mydash"
    exit 1
fi

# URL encode the input
ENCODED=$(printf %s "$URL" | jq -sRr @uri)

# Check if URL contains IP address
if echo "$URL" | grep -qE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+'; then
    # IP address detected - use TinyURL (is.gd blocks IPs)
    echo "🔍 Detected IP address - using TinyURL..."
    SHORT=$(curl -s "http://tinyurl.com/api-create.php?url=$ENCODED")
    
    if [ -n "$SHORT" ] && [ "$SHORT" != "Error" ]; then
        echo "✅ Shortened URL:"
        echo "Original: $URL"
        echo "Short: $SHORT"
        echo ""
        echo "The link is ready to share! 🌸"
    else
        echo "❌ Error: TinyURL failed to shorten the URL"
        exit 1
    fi
else
    # Try is.gd first (supports custom aliases)
    if [ -n "$CUSTOM_ALIAS" ]; then
        echo "🔍 Creating custom short link: is.gd/$CUSTOM_ALIAS ..."
        SHORT=$(curl -s "https://is.gd/create.php?format=simple&url=$ENCODED&shorturl=$CUSTOM_ALIAS")
    else
        echo "🔍 Shortening with is.gd..."
        SHORT=$(curl -s "https://is.gd/create.php?format=simple&url=$ENCODED")
    fi
    
    # Check if is.gd returned an error
    if echo "$SHORT" | grep -qi "error"; then
        echo "⚠️  is.gd failed: $SHORT"
        echo "🔄 Trying TinyURL instead..."
        SHORT=$(curl -s "http://tinyurl.com/api-create.php?url=$ENCODED")
    fi
    
    if [ -n "$SHORT" ] && [ "$SHORT" != "Error" ]; then
        echo "✅ Shortened URL:"
        echo "Original: $URL"
        echo "Short: $SHORT"
        echo ""
        echo "The link is ready to share! 🌸"
    else
        echo "❌ Error: Failed to shorten URL"
        exit 1
    fi
fi

# Verify the shortened URL works
echo ""
echo "🔗 Verifying redirect..."
if curl -sI "$SHORT" | grep -qi "location:"; then
    echo "✅ Link verified and working!"
else
    echo "⚠️  Warning: Unable to verify redirect"
fi
