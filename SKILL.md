---
name: autoresearch
description: Generic self-improving prompt optimization using the Karpathy autoresearch pattern. Point it at any generative skill — diagrams, code, text — define eval criteria in YAML, and let it optimize. Includes a live web dashboard.
allowed-tools: Read, Bash, Glob, Grep
---

# Autoresearch — Generic Self-Improving Prompt Optimization

## What It Does
Applies the Karpathy autoresearch pattern to **any generative skill**. Every cycle:
1. Generates a batch of outputs with the current prompt (configurable backend)
2. Evaluates each against your custom criteria via Claude (score out of batch × criteria)
3. Keeps the prompt if it beats the best score, discards otherwise
4. Mutates the best prompt to try to improve further
5. Logs everything to JSONL for tracking

## Quick Start

```bash
# 1. Create a config.yaml defining your skill (see config.yaml for the diagram example)
# 2. Create data/prompt.txt with your initial prompt

# Run continuous loop
python3 autoresearch.py --config config.yaml

# Single cycle (test)
python3 autoresearch.py --config config.yaml --once

# Run N cycles
python3 autoresearch.py --config config.yaml --cycles 10

# Start the live dashboard
python3 dashboard.py --config config.yaml --port 8501
```

## Config File

All domain-specific settings live in a YAML config:

```yaml
name: "my-skill"
description: "What this skill does"

generation:
  backend: "gemini_image"    # or: anthropic_text, openai_text, shell
  model: "gemini-2.5-flash-image"
  api_key_env: "MY_API_KEY"
  output_type: "image"       # or: text
  output_extension: ".png"
  prompt_template: "{prompt}\n\nTopic: {topic}"
  backend_config: {}

evaluation:
  model: "claude-sonnet-4-6"
  criteria:
    - name: "criterion_one"
      label: "Display Name"
      description: "What to check for — be specific"
    - name: "criterion_two"
      label: "Another Check"
      description: "Another thing to evaluate"

mutation:
  model: "claude-sonnet-4-6"
  rules:
    - "Domain-specific guidance for prompt improvement"

topics:
  - "Input variation 1"
  - "Input variation 2"

batch_size: 10
cycle_seconds: 120
```

## Generation Backends

| Backend | Description | API Key Env |
|---------|-------------|-------------|
| `gemini_image` | Gemini native image generation | Custom (set `api_key_env`) |
| `anthropic_text` | Claude text generation | `ANTHROPIC_API_KEY` |
| `openai_text` | OpenAI text generation | `OPENAI_API_KEY` |
| `shell` | Run a shell command (prompt via stdin) | None |

## Environment
Requires in `.env`:
```
ANTHROPIC_API_KEY=your_anthropic_api_key   # Always required (eval/mutation)
# Plus whatever your generation backend needs:
# NANO_BANANA_API_KEY=your_gemini_key
# OPENAI_API_KEY=your_openai_key
```

Dependencies: `pyyaml`, `anthropic`, `python-dotenv`
Plus backend-specific: `google-genai` (Gemini), `openai` (OpenAI)

## File Structure

```
autoresearch.py       # Main generate → eval → mutate loop
dashboard.py          # Live web dashboard (Chart.js)
config.yaml           # Your skill config (diagram example included)
data/
  prompt.txt          # Current prompt being optimized
  best_prompt.txt     # Best prompt found so far
  state.json          # Loop state (run number, best score)
  results.jsonl       # Append-only experiment log
  outputs/
    run_001/          # Batch outputs per run
    run_002/
```

## Dashboard
Serves at `http://localhost:8501` with:
- 4 stat cards (current best, baseline, improvement %, runs/kept)
- Score-over-time chart with keep/discard dot coloring
- Per-criterion breakdown charts (auto-generated from your criteria)
- Run history table
- Current best prompt display
- Auto-refreshes every 15s

## Models
- **Evaluation**: Claude (vision for images, text for text outputs)
- **Mutation**: Claude (prompt rewriting based on failure analysis)
- **Generation**: Configurable (Gemini, Claude, OpenAI, or shell command)
