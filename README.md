### pydantic-ai + pydantic-ai-litellm + puter.js 

> **Proof-of-Work · Developer Tutorial**
>
> How to use **[Puter.js](https://puter.com)** as a **FREE inference provider** for the **[Pydantic-AI](https://ai.pydantic.dev/)** agentic framework via the **[pydantic-ai-litellm](https://pypi.org/project/pydantic-ai-litellm/)** bridge library.

This project is structured as a proper Python package — it has a `pyproject.toml`, can be built with `uv`, and could be published to PyPI — but **it doesn't do anything meaningful on its own**. Its sole purpose is to demonstrate the integration pattern as a working proof-of-work that you can clone, read, and adapt into your own projects.

---

## Why Puter.js?

[Puter.com](https://puter.com) exposes an **OpenAI-compatible REST API** as part of there Puter.js family of endpoints giving developers access to 400+ frontier models (GPT-5, Claude, Gemini, Llama, and more) at **zero developer cost** through a *user-pays* model — end-users cover their own inference costs through their Puter account, so you never touch an API key or an inference bill.

```
https://api.puter.com/puterai/openai/v1/
```

Because it is OpenAI-compatible, any library that accepts a custom `api_base` — including **LiteLLM** — can use it as a drop-in provider.

---

## How the stack fits together

```
Your Pydantic-AI Agent
        │  uses
        ▼
LiteLLMModel          ← from pydantic-ai-litellm  (the critical bridge)
        │  calls
        ▼
LiteLLM               ← routes to any OpenAI-compatible endpoint
        │
        ▼
Puter.js API         ← free inference, user-pays model
```

| Layer | Package | Role |
|---|---|---|
| Agent framework | `pydantic-ai-slim` | Agents, tools, fasta2a server |
| LLM bridge | `pydantic-ai-litellm` | Exposes `LiteLLMModel` to Pydantic-AI |
| Inference router | `litellm` (auto-dep) | Drives any OpenAI-compatible endpoint |
| Free inference | Puter.js API | 400+ models at zero dev cost |

> **Critical:** You **must** use [`pydantic-ai-litellm`](https://github.com/mochow13/pydantic-ai-litellm) and its `LiteLLMModel` class — *not* Pydantic-AI's built-in OpenAI model. This separate library bridges Pydantic-AI to LiteLLM's routing layer, enabling custom `api_base` endpoints and access to 100+ providers through a unified interface.

---

## Prerequisites

- Python ≥ 3.13
- A free **[Puter.com](https://puter.com)** account + your auth token

### Getting your Puter auth token

1. Go to **[puter.com/dashboard#account](https://puter.com/dashboard#account)**
2. Scroll to the bottom — click **Reveal auth token**
3. Copy it — this is your `PUTER_AUTH_TOKEN`

> **Alternative:** Open browser DevTools (`F12` → *Console*) and run `puter.authToken`

---

## Step 1 — Install the dependencies

In your own project, install:

```bash
pip install pydantic-ai-slim[a2a] pydantic-ai-litellm python-dotenv uvicorn
```

Or with `uv`:

```bash
uv add pydantic-ai-slim[a2a] pydantic-ai-litellm python-dotenv uvicorn
```

---

## Step 2 — Configure your environment

Create a `.env` file:

```env
PUTER_API_BASE=https://api.puter.com/puterai/openai/v1/
PUTER_MODEL=openai/gpt-4o        # see https://developer.puter.com/ai/models/ for all model IDs
PUTER_AUTH_TOKEN=your_puter_token_here
```

---

## Step 3 — Wire it up (the complete pattern)

This is the entire proof-of-work. The source lives in [`src/pydantic_ai_litellm_puterjs/main.py`](src/pydantic_ai_litellm_puterjs/main.py).

```python
from pydantic_ai import Agent
from pydantic_ai_litellm import LiteLLMModel   # ← must use this, not the built-in OpenAI class
from dotenv import load_dotenv
import os

load_dotenv()

# 1. Point LiteLLMModel at the Puter OpenAI-compatible endpoint
model = LiteLLMModel(
    model_name=os.getenv("PUTER_MODEL"),        # e.g. "openai/gpt-4o" — see model naming note below
    api_key=os.getenv("PUTER_AUTH_TOKEN"),       # Puter token acts as the API key
    api_base=os.getenv("PUTER_API_BASE"),        # https://api.puter.com/puterai/openai/v1/
    custom_llm_provider="openai"                 # tells LiteLLM to use OpenAI-compatible request/response format
)

# 2. Create a Pydantic-AI Agent with that model
agent = Agent(model=model, instructions="Be helpful!")

# 3. Add tools with a simple decorator
@agent.tool_plain
def get_weather(city: str) -> str:
    """Get weather for a city."""
    return f"Weather in {city}: Sunny, 72°F"

@agent.tool_plain
def calculator(expression: str) -> str:
    """Evaluate a math expression."""
    return str(eval(expression))

# 4. Expose the agent as a fasta2a server — Pydantic-AI's own agent-to-agent protocol (required)
app = agent.to_a2a()
```

### What each piece does

| Line | Purpose |
|---|---|
| `LiteLLMModel(...)` | Routes calls through LiteLLM |
| `api_base` | Sends traffic to Puter's free endpoint |
| `api_key` | Your Puter token — no paid API key needed |
| `custom_llm_provider="openai"` | Required by `LiteLLMModel` to format requests/responses as OpenAI-compatible when using a custom `api_base` |
| `agent.to_a2a()` | Wraps the agent in a [fasta2a](https://ai.pydantic.dev/a2a/) ASGI server — Pydantic-AI's own agent-to-agent protocol |

---

## Step 4 — Run it

```bash
uvicorn your_module:app --host 0.0.0.0 --port 9999
```

The fasta2a server is available at `http://localhost:9999`.

---

## Swapping models

Change one line in `.env` — no code changes:

> **Model naming for OpenAI-compatible endpoints:** When `custom_llm_provider="openai"` is set on `LiteLLMModel`, the `model_name` is passed directly to your custom endpoint. For Puter's endpoint, every model is identified as **`openai/provider-model-version`** — the `openai/` prefix followed by the provider and model slug joined with hyphens. This is a `pydantic-ai-litellm` requirement when pointing `LiteLLMModel` at any OpenAI-compatible custom endpoint.

```env
# Native OpenAI models
PUTER_MODEL=openai/gpt-4o

# Non-OpenAI models accessed via Puter's OpenAI-compatible endpoint
# follow the same openai/provider-model-version format
PUTER_MODEL=openai/anthropic-claude-sonnet-4-6
PUTER_MODEL=openai/meta-llama-3-1-8b
```

See all available model slugs at **[developer.puter.com/ai/models](https://developer.puter.com/ai/models/)**.

---

## Going further

**Structured outputs** — pass a Pydantic model as `output_type`:

```python
from pydantic_ai import Agent
from pydantic_ai_litellm import LiteLLMModel
from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

model = LiteLLMModel(
    model_name=os.getenv("PUTER_MODEL"),
    api_key=os.getenv("PUTER_AUTH_TOKEN"),
    api_base=os.getenv("PUTER_API_BASE"),
    custom_llm_provider="openai"
)

class Answer(BaseModel):
    text: str
    confidence: float

agent = Agent(model=model, output_type=Answer)
```

**More tools** — use `@agent.tool` when the function needs the agent run context:

```python
@agent.tool
async def fetch_data(ctx, url: str) -> str:
    ...
```

---

## Credits & Acknowledgements

This project is simply a proof-of-work demonstrating that these pieces fit together. All the hard work was done by the teams behind these projects:

| Project | Who | What they built |
|---|---|---|
| [Puter.js](https://github.com/HeyPuter/puter) | puter.js | The open-source Puter.js project and its OpenAI-compatible inference API that makes zero-cost LLM access possible |
| [pydantic-ai-litellm](https://github.com/mochow13/pydantic-ai-litellm) | [@mochow13](https://github.com/mochow13) | The critical bridge library exposing `LiteLLMModel` to Pydantic-AI |
| [Pydantic-AI](https://github.com/pydantic/pydantic-ai) | Pydantic team | The agent framework, `fasta2a` server protocol, and structured output support |
| [LiteLLM](https://github.com/BerriAI/litellm) | BerriAI | The unified LLM routing layer that handles 100+ providers through one interface |

---

## Further Reading

- [Puter.com AI docs](https://docs.puter.com/ai/) — Puter platform overview
- [Puter AI Models](https://developer.puter.com/ai/models/) — all available model slugs
- [pydantic-ai-litellm on GitHub](https://github.com/mochow13/pydantic-ai-litellm) — the bridge library this project uses
- [pydantic-ai-litellm on PyPI](https://pypi.org/project/pydantic-ai-litellm/)
- [Pydantic-AI documentation](https://ai.pydantic.dev/)
- [LiteLLM Providers](https://docs.litellm.ai/docs/providers) — full provider/model naming reference
- [Pydantic-AI fasta2a docs](https://ai.pydantic.dev/a2a/) — Pydantic-AI's agent-to-agent protocol
