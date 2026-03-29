#!/bin/bash
source /opt/openclaw/.env

check() {
    local name=$1
    local code=$2
    if [ "$code" = "200" ]; then echo "✅ $name"
    elif [ "$code" = "429" ]; then echo "❌ $name — rate limit"
    else echo "⚠️ $name — $code"
    fi
}

echo "🔍 API Status [$(date -u +"%H:%M UTC")]"

code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "https://integrate.api.nvidia.com/v1/chat/completions" \
    -H "Authorization: Bearer $NVIDIA_API_KEY" -H "Content-Type: application/json" \
    -d "{\"model\":\"meta/llama-3.3-70b-instruct\",\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}],\"max_tokens\":1}" --max-time 10)
check "NVIDIA llama-3.3-70b" $code

code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "https://api.cerebras.ai/v1/chat/completions" \
    -H "Authorization: Bearer $CEREBRAS_API_KEY" -H "Content-Type: application/json" \
    -d "{\"model\":\"qwen-3-235b-a22b-instruct-2507\",\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}],\"max_tokens\":1}" --max-time 10)
check "Cerebras qwen-235b" $code

code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "https://api.groq.com/openai/v1/chat/completions" \
    -H "Authorization: Bearer $GROQ_API_KEY" -H "Content-Type: application/json" \
    -d "{\"model\":\"moonshotai/kimi-k2-instruct\",\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}],\"max_tokens\":1}" --max-time 10)
check "Groq kimi-k2" $code

code=$(curl -s -o /dev/null -w "%{http_code}" "http://65.21.3.89:8765/search?q=test" --max-time 10)
check "Tavily Search" $code
