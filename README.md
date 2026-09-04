# nomi
A minimal disposable chatbot for quick, temporary conversations.

Each message runs `codex exec` on your backend. Zero dependencies, plain HTML + Python stdlib.

## Files
- `index.html` — the chat UI (no framework)
- `server.py` — static server + `/api/chat` proxy (stdlib only)
- `.env.example` — copy to `.env`

## Setup
```sh
cp .env.example .env   # edit CODEX_URL, WORKDIR, SYSTEM_PROMPT
python3 server.py
# open http://localhost:3000 (or whatever PORT you set)
```

For public access:
```sh
ngrok http 3000
```

## How it works
Browser `POST /api/chat {prompt}` → `server.py` prepends the hidden
`SYSTEM_PROMPT`, builds the hardcoded body (`model`, `effort`, `sandbox`,
`timeoutMs`, `workdir`, `json`) and forwards to `$CODEX_URL/exec`.
Only `output` from the response is shown.

Config lives in `.env` (gitignored, never committed). See `.env.example`.
