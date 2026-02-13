# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react/README.md) uses [Babel](https://babeljs.io/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## Live Voice + Vision Smoke Test

### 1) Backend environment

Set these environment variables in backend `.env` before starting server:

- `GOOGLE_API_KEY` (required, backend only)
- `GEMINI_LIVE_MODEL` (optional, default in config)
- `LIVE_FRAME_FPS` (optional, default `1.0`)
- `TOOL_GATEWAY_SCHEME` (optional, default `http`)
- `TOOL_GATEWAY_HOST` (optional, if missing tool calls become no-op)
- `TOOL_GATEWAY_PORT` (optional)
- `TOOL_GATEWAY_PATH` (optional, default `/execute`)
- `TOOL_GATEWAY_TOKEN` (optional bearer token)

### 2) Start backend and client

Backend:

```bash
python main.py
```

Client:

```bash
cd client
npm install
npm run dev
```

### 3) Test without gateway (no-op tool calls)

Leave `TOOL_GATEWAY_HOST` unset. Tool calls are acknowledged and return a no-op response so session keeps running.

### 4) Test with gateway

Set `TOOL_GATEWAY_HOST`/`TOOL_GATEWAY_PORT`/`TOOL_GATEWAY_TOKEN`, then verify gateway health manually:

```bash
curl -H "Authorization: Bearer $TOOL_GATEWAY_TOKEN" "http://$TOOL_GATEWAY_HOST:$TOOL_GATEWAY_PORT/health"
```

Then open Freja client, go to Voice view, click **Start Live Session**, and verify:

- connected/streaming status changes to active
- audio level updates while speaking
- fps updates around configured value
- tool activity displays call/result when model triggers tools
