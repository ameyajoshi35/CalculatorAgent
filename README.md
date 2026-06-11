# CalculatorAgent

A FastAPI server that exposes a conversational calculator powered by a [LlamaIndex](https://www.llamaindex.ai/) ReAct agent and [Groq](https://groq.com/) LLM. The agent reasons step-by-step, calls arithmetic tools, and streams responses back via Server-Sent Events (SSE).

## How it works

The agent uses the **ReAct** (Reasoning + Acting) loop:

1. **Thought** — the LLM reasons about which tool to use
2. **Action** — calls one of the calculator tools (`add`, `subtract`, `multiply`, `divide`)
3. **Observation** — the tool result is fed back to the LLM
4. **Answer** — the LLM returns the final answer

## Requirements

- Python 3.12+
- [uv](https://github.com/astral-sh/uv)
- A [Groq API key](https://console.groq.com)

## Setup

```bash
uv sync
```

## Running

```bash
export GROQ_API_KEY=gsk_your_key_here
uv run python main.py
```

Server starts at `http://localhost:8000`.

## API

### `POST /messages`

Send a message to the agent. Streams the response as SSE.

| Query param | Type | Description |
|-------------|------|-------------|
| `session_id` | int | Identifies the conversation session |
| `message` | string | The user's message |

```bash
curl -N -H "Accept: text/event-stream" \
  -X POST "http://localhost:8000/messages?session_id=1&message=what+is+5+plus+3"
```

### `GET /messages`

Retrieve chat history for a session.

```bash
curl "http://localhost:8000/messages?session_id=1"
```

### `GET /ping`

Health check.

```bash
curl http://localhost:8000/ping
# {"ok": true}
```

## Interactive docs

Visit `http://localhost:8000/docs` for the Swagger UI.