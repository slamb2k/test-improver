---
name: autoresearch
description: Generic self-improving prompt optimization using the Karpathy autoresearch pattern. Point it at any generative skill — diagrams, code, text — define eval criteria in YAML, and let it optimize. Includes a live web dashboard.
allowed-tools: Read, Bash, Glob, Grep, Edit, Write, AskUserQuestion
---

# Autoresearch — Generic Self-Improving Prompt Optimization

## Skill Behavior

When this skill is invoked, follow this procedure:

### Step 1: Load and Validate Config

Read the config file (default `config.yaml`) and check if `evaluation.criteria` is defined.

```bash
python3 autoresearch.py --config config.yaml  # dry-run to validate
```

### Step 2: Criteria Setup (Interactive)

If the config has **no evaluation criteria** defined (empty or missing `evaluation.criteria`), run the interactive criteria setup:

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
python3 autoresearch.py generate-criteria --config config.yaml
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
1. Run: `python3 autoresearch.py optimize-criterion --config config.yaml --criterion-json '<json>'`
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
python3 autoresearch.py save-criteria --config config.yaml \
  --criteria-json '<finalized_criteria_json>' \
  --rules-json '<mutation_rules_json>'
```

### Step 3: Run the Optimization Loop

Once criteria are set up, run the autoresearch loop:

```bash
# Single cycle (test)
python3 autoresearch.py --config config.yaml --once

# Run N cycles
python3 autoresearch.py --config config.yaml --cycles 10

# Continuous loop
python3 autoresearch.py --config config.yaml
```

Ask the user how they want to run it if not specified.

### Step 4: Dashboard (optional)

Offer to start the live dashboard:
```bash
python3 dashboard.py --config config.yaml --port 8501
```

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

The script provides subcommands for criteria management:

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
# NANO_BANANA_API_KEY=your_gemini_key
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

## Models
- **Evaluation**: Claude (vision for images, text for text outputs)
- **Mutation**: Claude (prompt rewriting based on failure analysis)
- **Generation**: Configurable (Gemini, Claude, OpenAI, or shell command)
