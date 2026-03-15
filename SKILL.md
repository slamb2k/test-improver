---
name: autoresearch
description: >
  Automatically improve any AI prompt through iterative optimization. Use when
  the user wants to systematically make a prompt better — for image generation,
  text generation, code generation, or any other AI task. Works by running the
  prompt many times, scoring outputs against criteria, and using Claude to
  rewrite the prompt based on what failed. Supports Gemini, OpenAI, Claude, and
  shell backends. Make sure to use this skill whenever the user mentions prompt
  optimization, improving prompt quality, A/B testing prompts, the autoresearch
  pattern, or wants to iterate on a generative AI workflow, even if they don't
  use the word "optimize" explicitly.
allowed-tools: Read, Bash, Glob, Grep, Edit, Write, AskUserQuestion
---

# Autoresearch — Self-Improving Prompt Optimization

This skill runs an automated loop that makes any AI prompt better over time.
The idea (inspired by Karpathy's autoresearch pattern): generate a batch of
outputs, score them against pass/fail criteria, keep the prompt if it improves,
then use Claude to rewrite it based on what failed. Repeat until the prompt
consistently produces high-quality outputs.

## When to Use This

- User wants to **improve a prompt** for image generation, text generation, or any AI task
- User wants to **set up automated evaluation** of AI outputs
- User mentions **prompt optimization**, **prompt engineering at scale**, or **iterative improvement**
- User has a generative workflow that produces **inconsistent quality** and wants to fix it
- User wants to **A/B test** or **benchmark** different prompt versions

## Skill Behavior

Follow this procedure. The key principle: **always confirm with the user before running anything expensive** (API calls cost money).

### Step 0: Identify the Right Config

Before anything else, check what configs exist and match the user's intent:

1. Look for config files: `config.yaml`, `*_config.yaml`, `examples/*.yaml`
2. Read the `name` and `description` fields of each config found
3. **Compare against what the user asked for.** If the user says "code review" but the config says "diagram-generation", flag this mismatch and ask which config they meant. Don't silently use the wrong one.
4. If no config matches the user's intent, offer to create one from scratch (see "Creating a New Config" below).

This step matters because the repo may contain multiple configs for different use cases.

### Step 1: Load and Validate Config

Read the config file and verify it has the required sections (`generation`, `topics`).

```bash
python3 autoresearch.py --config <config_file>  # dry-run to validate
```

Also check:
- **API keys**: Does the required env var exist? (e.g., `ANTHROPIC_API_KEY`, the backend's key). If not, tell the user what to set before proceeding.
- **Dependencies**: Are required packages installed? (`pyyaml`, `anthropic`, `python-dotenv`, plus backend-specific ones like `google-genai` or `openai`)
- **Existing state**: Check `data/state.json` — if prior runs exist, tell the user their current best score and ask whether to continue or reset.

### Step 2: Criteria Setup (Interactive)

Evaluation criteria are the heart of the system — they define what "good" means for the user's outputs. Each criterion is a yes/no question applied to every generated output.

If the config has **no evaluation criteria** (empty or missing `evaluation.criteria`), run the interactive criteria setup:

#### 2a. Ask whether to generate criteria

Ask the user whether they want evaluation criteria auto-generated.

If `AskUserQuestion` is available, use it:
- Question: "No evaluation criteria found in config. Would you like me to generate them automatically?"
- Options: "Yes, generate criteria (Recommended)" / "No, I'll define them manually"

If `AskUserQuestion` is NOT available, ask via text output and wait for the user's response.

If the user declines, tell them to add criteria to their config manually and stop.

#### 2b. Generate criteria

Run the generation subcommand:
```bash
python3 autoresearch.py generate-criteria --config <config_file>
```

This outputs JSON with `criteria` and `mutation_rules`. Parse the output.

#### 2c. Offer to review criteria

Ask the user whether they want to review the generated criteria one-by-one, or accept them all.

If `AskUserQuestion` is available:
- Question: "I generated N criteria. Would you like to review them?"
- Options: "Review new criteria only (Recommended)" / "Accept all as-is"

If the user wants to accept all, skip to Step 2e.

If the config already has criteria, also offer: "Review all criteria (existing + new)"

#### 2d. Review each criterion

For each criterion, present it to the user and let them choose what to do.

If `AskUserQuestion` is available, use it with a **preview** showing the criterion description:
- Header: "Eval N/M"
- Question: "How would you like to handle the '[label]' criterion?"
- Options:
  - "Keep as-is" — use the current description unchanged
  - "Optimize" — generate an AI-improved version (calls `optimize-criterion` subcommand)
  - "Write my own" — user provides their own description via the "Other" free-text option
- Preview: show the criterion name, label, and full description

If the user picks **"Optimize"**:
1. Run: `python3 autoresearch.py optimize-criterion --config <config_file> --criterion-json '<json>'`
2. Parse the optimized criterion from stdout
3. Show the user both versions (original and optimized) and ask them to pick:
   - If `AskUserQuestion` is available, show both as previews:
     - "Use optimized version (Recommended)" with preview of new description
     - "Keep original" with preview of original description
     - "Write my own" — free-text via Other

If the user picks **"Write my own"** (via the "Other" option), use their text as the new description, keeping the same `name` and `label`.

If `AskUserQuestion` is NOT available:
- Display each criterion as formatted text
- Ask the user to reply with their choice (keep/optimize/custom) and wait for their response
- For "optimize", display both versions and ask them to pick

#### 2e. Save finalized criteria

After all criteria are reviewed, save them to the config:
```bash
python3 autoresearch.py save-criteria --config <config_file> \
  --criteria-json '<finalized_criteria_json>' \
  --rules-json '<mutation_rules_json>'
```

### Step 3: Run the Optimization Loop

Once criteria are set up, ask the user how they want to run it:

```bash
# Single cycle (test first to verify everything works)
python3 autoresearch.py --config <config_file> --once

# Run N cycles
python3 autoresearch.py --config <config_file> --cycles 10

# Continuous loop (runs until Ctrl+C)
python3 autoresearch.py --config <config_file>
```

**Always recommend `--once` first** for a new setup — it verifies API keys work, the backend generates outputs, and evaluation produces scores. Then scale up.

### Step 4: Dashboard (optional)

Offer to start the live dashboard:
```bash
python3 dashboard.py --config <config_file> --port 8501
```

The dashboard at `http://localhost:8501` shows real-time score progression, per-criterion breakdowns, and the current best prompt. It auto-refreshes every 15s.

---

## Creating a New Config

When the user wants to optimize a prompt for a new use case (not covered by existing configs):

1. **Pick the backend** based on what API the user has:
   - `openai_text` — for OpenAI (GPT-4o, etc.)
   - `anthropic_text` — for Claude
   - `gemini_image` — for Gemini image generation
   - `shell` — for any command-line tool

2. **Create the config YAML** (see Config File Format below). Key fields to get right:
   - `generation.backend` and `generation.model` — match the user's API
   - `generation.api_key_env` — the env var name for their API key
   - `generation.output_type` — "image" or "text"
   - `topics` — 15-30 diverse input variations for the task

3. **Leave `evaluation.criteria` empty** — the interactive criteria generation (Step 2) will handle this with the user, producing better-tailored criteria than guessing upfront.

4. **Write an initial seed prompt** and save it to `data/prompt.txt`. Keep it simple — the optimization loop will improve it.

5. **Set up the data directory**: `mkdir -p data`

## Config File Format

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

# evaluation.criteria can be omitted — the skill will offer to generate them
evaluation:
  model: "claude-sonnet-4-6"
  criteria:
    - name: "criterion_one"
      label: "Display Name"
      description: "What to check for — be specific"

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

## CLI Subcommands

| Command | Description | Output |
|---------|-------------|--------|
| `generate-criteria --config X` | Auto-generate 4-6 criteria from config context | JSON `{criteria, mutation_rules}` |
| `optimize-criterion --config X --criterion-json '{...}'` | Suggest improved version of one criterion | JSON criterion object |
| `save-criteria --config X --criteria-json '[...]' --rules-json '[...]'` | Write criteria/rules to config file | Confirmation message |

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
# GEMINI_API_KEY=your_gemini_key
# OPENAI_API_KEY=your_openai_key
```

Dependencies: `pyyaml`, `anthropic`, `python-dotenv`
Plus backend-specific: `google-genai` (Gemini), `openai` (OpenAI)

## File Structure

```
autoresearch.py       # Main generate -> eval -> mutate loop + criteria subcommands
dashboard.py          # Live web dashboard (Chart.js)
config.yaml           # Your skill config
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

## How the Optimization Loop Works

Understanding this helps diagnose issues:

1. **Generate**: Sample `batch_size` topics, combine each with the current prompt using `prompt_template`, send to the backend. Outputs saved to `data/outputs/run_NNN/`.
2. **Evaluate**: Send each output to Claude with an auto-generated eval prompt. Claude scores each criterion as PASS/FAIL. For images, uses vision; for text, inline.
3. **Score**: Sum all passes across criteria and batch. Compare to best score in `state.json`.
4. **Keep or revert**: If new score > best, save prompt as `best_prompt.txt`. Otherwise, revert to best prompt for next mutation.
5. **Mutate**: Claude analyzes per-criterion pass rates and failure descriptions, then rewrites the prompt. Mutation rules from config guide the rewrite.
6. **Repeat**: Wait `cycle_seconds`, then loop.

## Models

- **Evaluation**: Claude (vision for images, text for text outputs)
- **Mutation**: Claude (prompt rewriting based on failure analysis)
- **Generation**: Configurable (Gemini, Claude, OpenAI, or shell command)
