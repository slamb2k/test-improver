# Transcript: Running 5 Autoresearch Cycles with Existing Config

## Task
User requested: "I already have a config.yaml with criteria defined for my code review prompt optimizer. Just run 5 cycles for me and show me the dashboard when done."

## Step 1: Understand the Existing Config

I examined `/home/user/test-improver/config.yaml`. However, this config is NOT for code review -- it is for **diagram generation** using the Gemini image backend. Its name is `"diagram-generation"` and it optimizes prompts for generating clean technical diagrams. It has 4 criteria: Legible, Pastel, Linear, and No Numbers.

There IS a code review config at `/home/user/test-improver/examples/code_review_config.yaml` which uses the `anthropic_text` backend and has criteria: Actionable, Correct, Prioritized, and Tone.

**Decision point:** The user said "my code review prompt optimizer" but the root `config.yaml` is for diagram generation, not code review. This is a mismatch I would need to clarify with the user before proceeding. See `user_notes.md` for details.

## Step 2: Determine the Command to Run 5 Cycles

The `autoresearch.py` script accepts a `--cycles N` flag. The command would be:

### Option A: If the user meant the root config.yaml (diagram generation)
```bash
cd /home/user/test-improver && python3 autoresearch.py --config config.yaml --cycles 5
```

### Option B: If the user meant the code review example config
```bash
cd /home/user/test-improver && python3 autoresearch.py --config examples/code_review_config.yaml --cycles 5
```

## Step 3: Prerequisites / Environment Check

Before running, the following environment variables must be set:

- **For Option A (diagram generation):**
  - `NANO_BANANA_API_KEY` -- required for the Gemini image generation backend
  - `ANTHROPIC_API_KEY` -- required for evaluation (Claude) and mutation (Claude)

- **For Option B (code review):**
  - `ANTHROPIC_API_KEY` -- required for generation (Anthropic text), evaluation, and mutation

I would verify these are set:
```bash
echo "ANTHROPIC_API_KEY set: $([ -n \"$ANTHROPIC_API_KEY\" ] && echo yes || echo no)"
echo "NANO_BANANA_API_KEY set: $([ -n \"$NANO_BANANA_API_KEY\" ] && echo yes || echo no)"
```

## Step 4: Check Existing State

The `data/` directory already exists with prior run data:
- `data/state.json` -- tracks run number and best score
- `data/results.jsonl` -- historical run results
- `data/prompt.txt` -- current prompt being optimized
- `data/best_prompt.txt` -- best prompt found so far
- `data/diagrams/` -- generated output files (named `outputs/` in code, aliased here)

Running 5 more cycles would continue from the existing state (incrementing the run number).

## Step 5: Run 5 Cycles

I would execute:
```bash
cd /home/user/test-improver && python3 autoresearch.py --cycles 5
```

This would:
1. Load `config.yaml` and validate it (criteria already exist, so no auto-generation needed)
2. Load existing state from `data/state.json`
3. For each of the 5 cycles:
   - Sample 10 topics (batch_size) from the 30 defined topics
   - Generate 10 outputs in parallel (max 3 workers) using the configured backend
   - Evaluate each output against 4 criteria using Claude (max 5 workers)
   - Compute total score (max possible: 10 batches x 4 criteria = 40)
   - If score > best_score: keep as new best, save prompt
   - If score < max: mutate the prompt using Claude
   - Wait up to cycle_seconds (120s) before next cycle
4. Print final best score

Expected runtime: ~10-15 minutes (5 cycles x ~2 min each, dominated by generation + evaluation API calls).

## Step 6: Launch the Dashboard

After the 5 cycles complete, I would launch the dashboard:

```bash
cd /home/user/test-improver && python3 dashboard.py --config config.yaml --port 8501 &
```

Then tell the user:
> "Dashboard is running at http://localhost:8501. It shows:
> - Current best score vs baseline
> - Score progression chart across all runs
> - Per-criterion charts (Legible, Pastel, Linear, No Numbers)
> - Run history table with per-criterion breakdowns
> - The current best prompt text
>
> The dashboard auto-refreshes every 15 seconds."

## Step 7: What I Would Tell the User

> **Important clarification needed:** Your `config.yaml` is configured for **diagram generation** (Gemini image backend), not code review. There is a code review config at `examples/code_review_config.yaml`. Which one did you want me to run?
>
> Assuming you meant the root config.yaml, I would run:
> ```
> python3 autoresearch.py --cycles 5
> ```
> followed by:
> ```
> python3 dashboard.py --port 8501
> ```
>
> Prerequisites: `NANO_BANANA_API_KEY` and `ANTHROPIC_API_KEY` must be set in your environment.

## Summary of Commands

| Step | Command | Purpose |
|------|---------|---------|
| 1 | `python3 autoresearch.py --cycles 5` | Run 5 optimization cycles |
| 2 | `python3 dashboard.py --config config.yaml --port 8501` | Launch live dashboard |
| Alt | `python3 autoresearch.py --config examples/code_review_config.yaml --cycles 5` | If user meant the code review config |
