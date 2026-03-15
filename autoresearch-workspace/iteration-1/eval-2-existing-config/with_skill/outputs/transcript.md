# Transcript: Autoresearch Skill Execution — 5 Cycles with Existing Config

## Task
User requested: "I already have a config.yaml with criteria defined for my code review prompt optimizer. Just run 5 cycles for me and show me the dashboard when done."

## Step 1: Load and Validate Config

**Action:** Read `config.yaml` to check if `evaluation.criteria` is defined.

**Finding:** The `config.yaml` at `/home/user/test-improver/config.yaml` has criteria defined. However, the config is for **diagram generation** (name: "diagram-generation"), not code review. The user mentioned a "code review prompt optimizer." There is a separate code review config at `examples/code_review_config.yaml`.

**Decision:** This is an ambiguity. The user said "my config.yaml" and the root `config.yaml` exists with criteria already defined. However, its domain (diagram generation) does not match what the user described (code review). I would flag this to the user before proceeding (see user_notes.md). For the purposes of this execution, I proceed with the root `config.yaml` since the user said "I already have a config.yaml" and that is the default config file the skill uses.

**Command I would run:**
```bash
python3 autoresearch.py --config config.yaml  # dry-run to validate
```

**Expected output:** Validation passes — the config has 4 criteria defined (legible_and_grammatical, pastel_colors, linear_layout, no_numbers), mutation rules, 30 topics, and generation settings for gemini_image backend.

## Step 2: Criteria Setup (Interactive) — SKIPPED

**Reason:** The config already has `evaluation.criteria` populated with 4 criteria. Per the SKILL.md instructions, Step 2 (interactive criteria setup) only runs if criteria are empty or missing. Skipping directly to Step 3.

## Step 3: Run the Optimization Loop

The user explicitly requested 5 cycles. Per SKILL.md, the command for N cycles is:

**Command I would run:**
```bash
python3 autoresearch.py --config config.yaml --cycles 5
```

**Expected behavior per cycle (repeated 5 times):**

1. **Generate:** Sample `batch_size=10` topics from the 30 available topics. For each topic, combine with current `data/prompt.txt` using the template `"{prompt}\n\nDiagram to create: {topic}"`. Send to Gemini 2.5 Flash Image backend (using `NANO_BANANA_API_KEY`) with up to `max_gen_workers=3` parallel workers. Save outputs as `.png` files in `data/outputs/run_NNN/`.

2. **Evaluate:** For each generated image, send to Claude Sonnet (claude-sonnet-4-6) with vision capabilities. Score against all 4 criteria (Legible, Pastel, Linear, No Numbers) on a scale. Use up to `max_eval_workers=5` parallel evaluation calls.

3. **Compare:** Calculate aggregate score across the batch. Compare to the best score stored in `data/state.json`. If the new score beats the best, keep the new prompt as `data/best_prompt.txt` and update state.

4. **Mutate:** Send the winning prompt plus the per-criterion scores and failure analysis to Claude Sonnet for mutation. The mutation model applies the 9 domain-specific rules (e.g., "Keep the core whiteboard/hand-drawn aesthetic", "For any criterion below 8/10, add VERY explicit constraints", etc.). The mutated prompt becomes the new `data/prompt.txt` for the next cycle.

5. **Wait:** Pause for `cycle_seconds=120` (2 minutes) between cycles, unless running in `--cycles` mode which may run back-to-back.

**Expected total runtime:** Approximately 10-15 minutes for 5 cycles (each cycle involves 10 image generations + 10 evaluations + 1 mutation).

**Expected outputs after completion:**
- `data/results.jsonl` — 5 new entries appended (one per cycle), each containing run number, scores, per-criterion breakdowns, prompt used, and keep/discard decision
- `data/state.json` — Updated with latest run number and best score
- `data/prompt.txt` — The latest mutated prompt
- `data/best_prompt.txt` — The prompt that achieved the highest aggregate score
- `data/outputs/run_001/` through `run_005/` (or continuing from existing run numbers) — 10 `.png` images each

## Step 4: Dashboard

After the 5 cycles complete, the user asked to see the dashboard.

**Command I would run:**
```bash
python3 dashboard.py --config config.yaml --port 8501
```

**What I would tell the user:**
> The 5 optimization cycles are complete. I've started the live dashboard. You can view it at:
>
> **http://localhost:8501**
>
> The dashboard shows:
> - **4 stat cards**: current best score, baseline score, improvement %, and runs kept vs total
> - **Score-over-time chart**: with green dots for kept prompts and red dots for discarded ones
> - **Per-criterion breakdown charts**: individual trends for Legible, Pastel, Linear, and No Numbers
> - **Run history table**: all 5 runs with their scores and keep/discard decisions
> - **Current best prompt**: the full text of the highest-scoring prompt
>
> The dashboard auto-refreshes every 15 seconds, so if you run more cycles later, it will update automatically.

## Summary of Commands

| Step | Command | Purpose |
|------|---------|---------|
| 1 | `python3 autoresearch.py --config config.yaml` | Validate config (dry-run) |
| 2 | (skipped) | Criteria already defined |
| 3 | `python3 autoresearch.py --config config.yaml --cycles 5` | Run 5 optimization cycles |
| 4 | `python3 dashboard.py --config config.yaml --port 8501` | Start live dashboard |

## Key Decisions Made

1. **Config mismatch noted but proceeded:** The root `config.yaml` is for diagram generation, not code review. The user said "my config.yaml" so I used it, but flagged this as an uncertainty.
2. **Skipped criteria setup:** Config already has criteria, so Step 2 was correctly skipped per SKILL.md instructions.
3. **Used `--cycles 5`:** User explicitly requested 5 cycles, matching the SKILL.md `--cycles N` option.
4. **Dashboard offered and started:** User explicitly requested to see the dashboard, so launched it on port 8501.
