# TOOLS.md - Локальные настройки

## Whisper (STT)
- Движок: mlx-whisper (Apple Silicon GPU)
- Скрипт: ~/.openclaw/whisper-env/bin/python3 ~/.openclaw/whisper-env/transcribe.py <файл> ru
- Модель: mlx-community/whisper-small-mlx
- Скорость: ~1.5 сек на короткое сообщение

## TTS (голосовые ответы)
- Движок: edge-tts (Microsoft, бесплатно)
- Голос: ru-RU-DmitryNeural (мужской, пониженный тон)
- Команда: ~/.openclaw/whisper-env/bin/edge-tts --voice "ru-RU-DmitryNeural" --pitch="-10Hz" --rate="-5%" --text "текст" --write-media output.mp3
- Потом конвертация: ffmpeg -y -i output.mp3 -c:a libopus -b:a 64k output.ogg

## Напоминания
Все напоминания → sessionTarget: "isolated" + payload.kind: "agentTurn"
НИКОГДА sessionTarget: "main" + systemEvent!

## После обновления OpenClaw
1. Запустить: scripts/post-update-check.sh
2. Или сказать: "продиагностируй себя" (Agent Doctor)
3. Скилл: skills/agent-doctor/SKILL.md

НЕ openclaw gateway restart из сессии!
Mac: launchctl kickstart -k gui/$(id -u) ai.openclaw.gateway

## Маршрутизация моделей
- Мощная (Opus): разговор, стратегия, тексты
- Быстрая (Sonnet): данные, черновики, кроны
Кроны: полное имя модели (anthropic/claude-sonnet-4-6)
SQLite WAL обязателен!

## Браузеры

### 1. Google Chrome (основной)
- Путь: /Applications/Google Chrome.app
- Для: проверка лимитов Claude, интерфейсы, сайты с авторизацией
- Профиль openclaw для сохранения куки и сессий
- Запуск: open -a "Google Chrome" или через agent-browser --executable-path

### 2. agent-browser (Chromium, автоматизация)
- Путь: /opt/homebrew/bin/agent-browser
- Для: сложные автоматизации, Accessibility Tree, скриншоты с номерами
- Workflow: open → snapshot -i → click @e1 → fill @e2 "text"

### 3. Lightpanda (ультралёгкий headless)
- Путь: scripts/lightpanda
- Для: быстрый парсинг текста, HTML для субагентов/кронов
- 11x быстрее Chrome, 9x меньше памяти
- Пример: scripts/lightpanda fetch --dump markdown https://example.com

## Агент-доктор (DoktorMike)
- Папка: ~/Desktop/agent-doctor/
- Бот: @DoktorMike_bot
- Движок: ClaudeClaw (Claude Code CLI)
- Сервис: com.claudeclaw.doctor (LaunchAgent)
- Логи: ~/Desktop/agent-doctor/logs/
- Перезапуск: launchctl kickstart -k gui/$(id -u) com.claudeclaw.doctor
- Работает по подписке Max (claude login)
- У меня полный доступ к его папке, у него - к моей

## Web Search (ОБЯЗАТЕЛЬНО)
НИКОГДА не использовать web_search — требует платный Perplexity (402 ошибка).
НИКОГДА не вызывать google.com, bing.com или любой поисковик напрямую — они не работают.
Для ЛЮБОГО поиска (новости, события, мероприятия, информация) — ТОЛЬКО наш эндпоинт:
web_fetch("http://65.21.3.89:8765/search?q=QUERY") — URL-encode запрос (пробелы = +)
Пример: web_fetch("http://65.21.3.89:8765/search?q=events+Killarney+weekend")
ОТВЕТ: показать каждый результат с URL в формате: Название (https://...) - описание
НИКОГДА не убирать URL из ответа пользователю.

## Gmail (READ ONLY — ОБЯЗАТЕЛЬНО)
Для чтения почты вызвать web_fetch напрямую:
- Последнее письмо: web_fetch("http://65.21.3.89:8765/email?action=latest")
- Список писем: web_fetch("http://65.21.3.89:8765/email?action=list")
- Конкретное по ID: web_fetch("http://65.21.3.89:8765/email?action=read&id=ID")

НИКОГДА не говорить «мне нужен доступ к почте» — доступ уже есть через endpoint выше.
НИКОГДА не просить credentials — просто вызвать web_fetch.

## Погода
Для ЛЮБОГО запроса о погоде — вызвать наш эндпоинт:
web_fetch("http://65.21.3.89:8765/weather?city=CITY")
Пример: web_fetch("http://65.21.3.89:8765/weather?city=Killarney")
Для прогноза на несколько дней: web_fetch("http://65.21.3.89:8765/weather?city=CITY&days=2")
ОБЯЗАТЕЛЬНО: скопируй поле text из ответа ДОСЛОВНО, без сокращений и пересказа.
НЕ использовать wttr.in напрямую.

## YouTube транскрипции
web_fetch("http://65.21.3.89:8765/transcript?url=YOUTUBE_URL&lang=ru")
