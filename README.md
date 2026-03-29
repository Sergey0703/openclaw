# OpenClaw Setup

Personal AI assistant via Telegram using OpenClaw on VPS.

## Server
- Hetzner VPS (Server 2: 65.21.3.89)
- Model: nvidia/nemotron-3-super-120b-a12b:free via OpenRouter
- Telegram bot: @OpenclawSerhii_bot

## Setup
1. Install: curl -fsSL https://openclaw.ai/install.sh | bash
2. Copy openclaw.json to ~/.openclaw/
3. Copy himalaya-config.toml to ~/.config/himalaya/config.toml
4. Create .env with real keys (see .env.example)
5. systemctl start openclaw

## Features
- Web search (built-in)
- Gmail read-only via himalaya IMAP
- Weather via wttr.in
