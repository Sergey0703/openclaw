#!/bin/bash
# API monitor — runs every 4 hours, alerts to Telegram only on errors, only 8:00-23:00 Dublin time

BOT_TOKEN="8449030330:AAH5XqTv69P2usSg4E7TG8FGKF7LCPQuqrQ"
CHAT_ID="-1003823823665"
TOPIC_ID="1"

# Check time in Dublin timezone (8:00-23:00)
HOUR=$(TZ="Europe/Dublin" date +%H)
if [ "$HOUR" -lt 8 ] || [ "$HOUR" -ge 23 ]; then
    exit 0
fi

source /opt/openclaw/.env

errors=()
ok=()

# NVIDIA
code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "https://integrate.api.nvidia.com/v1/chat/completions" \
    -H "Authorization: Bearer $NVIDIA_API_KEY" -H "Content-Type: application/json" \
    -d '{"model":"meta/llama-3.3-70b-instruct","messages":[{"role":"user","content":"hi"}],"max_tokens":1}' --max-time 10)
[ "$code" = "200" ] && ok+=("✅ NVIDIA") || errors+=("⚠️ NVIDIA ($code)")

# Cerebras
code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "https://api.cerebras.ai/v1/chat/completions" \
    -H "Authorization: Bearer $CEREBRAS_API_KEY" -H "Content-Type: application/json" \
    -d '{"model":"qwen-3-235b-a22b-instruct-2507","messages":[{"role":"user","content":"hi"}],"max_tokens":1}' --max-time 10)
[ "$code" = "200" ] && ok+=("✅ Cerebras") || errors+=("⚠️ Cerebras ($code)")

# Groq
code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "https://api.groq.com/openai/v1/chat/completions" \
    -H "Authorization: Bearer $GROQ_API_KEY" -H "Content-Type: application/json" \
    -d '{"model":"moonshotai/kimi-k2-instruct","messages":[{"role":"user","content":"hi"}],"max_tokens":1}' --max-time 10)
[ "$code" = "200" ] && ok+=("✅ Groq") || errors+=("⚠️ Groq ($code)")

# Tavily
code=$(curl -s -o /dev/null -w "%{http_code}" "http://65.21.3.89:8765/search?q=test" --max-time 10)
[ "$code" = "200" ] && ok+=("✅ Tavily") || errors+=("⚠️ Tavily ($code)")

# Send alert only if errors
if [ ${#errors[@]} -gt 0 ]; then
    msg="🚨 <b>API Alert</b> [$(TZ="Europe/Dublin" date '+%H:%M')]"$'\n'
    for e in "${errors[@]}"; do
        msg+="$e"$'\n'
    done
    for o in "${ok[@]}"; do
        msg+="$o"$'\n'
    done
    python3 -c "
import urllib.request, json, sys
token = '$BOT_TOKEN'
payload = json.dumps({
    'chat_id': '$CHAT_ID',
    'message_thread_id': $TOPIC_ID,
    'text': sys.argv[1],
    'parse_mode': 'HTML'
}).encode()
req = urllib.request.Request(
    f'https://api.telegram.org/bot{token}/sendMessage',
    data=payload, headers={'Content-Type': 'application/json'}
)
urllib.request.urlopen(req)
" "$msg"
fi
