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

For public access — tunnel with ngrok (expose localhost:3000):

For your mobile app → Mac Mini:

```sh
# 1. Install ngrok
brew install ngrok          # macOS
# or: npm i -g ngrok  |  download from https://ngrok.com/download

# 2. Auth (once) — get token at https://dashboard.ngrok.com/get-started/your-authtoken
ngrok config add-authtoken <YOUR_TOKEN>

# 3. Run nomi + tunnel (two terminals)
python3 server.py           # terminal 1
ngrok http 3000             # terminal 2 → gives https://xxxx.ngrok-free.app
```

Then open the `https://xxxx.ngrok-free.app` URL on your phone.
If you changed `PORT` in `.env`, tunnel that port instead (`ngrok http <PORT>`).

## How it works
Browser `POST /api/chat {prompt}` → `server.py` prepends the hidden
`SYSTEM_PROMPT`, builds the hardcoded body (`model`, `effort`, `sandbox`,
`timeoutMs`, `workdir`, `json`) and forwards to `$CODEX_URL/exec`.
Only `output` from the response is shown.

Config lives in `.env` (gitignored, never committed). See `.env.example`.
