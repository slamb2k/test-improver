# User Notes — Uncertainties and Observations

## Uncertainty 1: Config Domain Mismatch

**Issue:** The user said they have a config for a "code review prompt optimizer," but the root `config.yaml` is configured for **diagram generation** (name: "diagram-generation", backend: "gemini_image", output_type: "image"). There is a separate code review example at `examples/code_review_config.yaml` that matches the user's description (name: "code-review", backend: "anthropic_text", output_type: "text").

**What I would ask the user (if this were a real execution):**
> Your `config.yaml` is set up for diagram generation, not code review. Did you mean to use `examples/code_review_config.yaml` instead? I can either:
> 1. Run with the current `config.yaml` (diagram generation)
> 2. Copy `examples/code_review_config.yaml` to `config.yaml` and run that
> 3. Point autoresearch at the example config directly: `--config examples/code_review_config.yaml`

**Decision made:** Proceeded with root `config.yaml` since the user said "I already have a config.yaml" and the skill instructions say to use the default config file. But this is likely not what the user intended.

## Uncertainty 2: API Keys

**Issue:** Running 5 cycles requires:
- `NANO_BANANA_API_KEY` — for Gemini image generation (the diagram config's backend)
- `ANTHROPIC_API_KEY` — for Claude evaluation and mutation

If the user actually meant the code review config, only `ANTHROPIC_API_KEY` would be needed (since both generation and evaluation use Anthropic).

**Note:** No `.env` file was checked for these keys. In a real execution, the first cycle would fail if keys are missing.

## Uncertainty 3: Existing State

**Observation:** The `data/` directory already contains `prompt.txt`, `best_prompt.txt`, `state.json`, and `results.jsonl`. This means previous runs have occurred. The 5 new cycles would continue from the existing state (appending to results.jsonl, incrementing run numbers). If the user wanted a fresh start, they would need to clear or rename the `data/` directory first.

**What I would mention to the user:**
> I see you have existing run data in `data/`. The 5 cycles will continue from where you left off. Would you like to start fresh instead?

## Uncertainty 4: Dashboard Blocking

**Observation:** `python3 dashboard.py` starts an HTTP server that blocks the terminal. In a real execution, I would either:
- Run it in the background: `python3 dashboard.py --config config.yaml --port 8501 &`
- Or run it after the optimization completes, noting it will block further commands

The SKILL.md does not specify whether to run it in the background. For the user's convenience, running it in the background after the cycles complete would be the practical choice.
