# Transcript: Diagram Prompt Optimization Setup

## Task
User wants to systematically improve a prompt that generates technical diagrams using Gemini's image generation. Problems reported: garbled text, wrong colors. User has a Gemini API key and about 30 example topics.

## Step 1: Codebase Exploration

### Files examined:
- `/home/user/test-improver/autoresearch.py` — The core optimization loop (847 lines)
- `/home/user/test-improver/config.yaml` — Already configured for diagram generation
- `/home/user/test-improver/dashboard.py` — Live visualization of optimization progress
- `/home/user/test-improver/data/prompt.txt` — Current prompt (evolved over 8 runs)
- `/home/user/test-improver/data/best_prompt.txt` — Best prompt found so far
- `/home/user/test-improver/data/state.json` — Current state: run 8, best score 40/40
- `/home/user/test-improver/data/results.jsonl` — History of 8 optimization runs
- `/home/user/test-improver/examples/code_review_config.yaml` — Example config for text-based skill

### Key findings:
The system is already set up and has been run. The `autoresearch.py` script implements the Karpathy "autoresearch" pattern:
1. Generate a batch of outputs with the current prompt (via a configurable backend)
2. Evaluate each output against boolean criteria using Claude vision
3. Compare batch score against best score; keep the winning prompt
4. Mutate the prompt using Claude to address specific failures
5. Repeat

The config already targets the user's exact problem — it uses `gemini_image` backend with `gemini-2.5-flash-image` model and evaluates against 4 criteria: legible text, pastel colors, linear layout, and no numbers.

### Existing run history (from results.jsonl):
| Run | Score | Legible | Pastel | Linear | No Numbers |
|-----|-------|---------|--------|--------|------------|
| 1   | 32/40 | 8/10    | 10/10  | 5/10   | 9/10       |
| 2   | 37/40 | 7/10    | 10/10  | 10/10  | 10/10      |
| 3   | 34/40 | 4/10    | 10/10  | 10/10  | 10/10      |
| 4   | 35/40 | 5/10    | 10/10  | 10/10  | 10/10      |
| 5   | 36/40 | 6/10    | 10/10  | 10/10  | 10/10      |
| 6   | 40/40 | 10/10   | 10/10  | 10/10  | 10/10      |
| 7   | 37/40 | 7/10    | 10/10  | 10/10  | 10/10      |
| 8   | 37/40 | 8/10    | 10/10  | 10/10  | 9/10       |

The system already achieved a perfect 40/40 on run 6, but subsequent runs show variance (legibility remains the hardest criterion). The best prompt has been saved.

## Step 2: Decision — What I Would Recommend

Since the system is already configured and has prior run data, the user does not need to start from scratch. There are two paths:

### Option A: Continue from current state (recommended)
The config, criteria, prompt, and state are already in place. Simply run more cycles to further stabilize the prompt. The "legible" criterion is the volatile one — runs 7 and 8 regressed from the perfect run 6 score.

### Option B: Reset and re-run from scratch
Only needed if the user wants to change criteria, topics, or backend model.

## Step 3: Exact Commands I Would Run

### 3.1 Prerequisites — Environment Setup

```bash
# Ensure the Gemini API key is set (the config expects NANO_BANANA_API_KEY)
export NANO_BANANA_API_KEY="<user's Gemini API key>"

# Ensure Anthropic API key is set (needed for evaluation + mutation via Claude)
export ANTHROPIC_API_KEY="<user's Anthropic API key>"

# Install dependencies if not already present
pip install google-genai anthropic pyyaml python-dotenv
```

**Important note:** The config uses `api_key_env: "NANO_BANANA_API_KEY"` — the user should either set this env var to their Gemini API key, or edit config.yaml line 17 to use `"GEMINI_API_KEY"` (or whatever env var they prefer).

### 3.2 Option A: Continue Optimization (run 5 more cycles)

```bash
cd /home/user/test-improver
python3 autoresearch.py --config config.yaml --cycles 5
```

This will:
- Load the existing state (run 8, best score 40/40)
- For each cycle: sample 10 topics from the 30 available, generate 10 diagrams via Gemini, evaluate each with Claude vision, score, mutate the prompt if not perfect
- Take approximately 10-15 minutes (5 cycles x ~2 min each)

### 3.3 Option B: Run a single test cycle first

```bash
cd /home/user/test-improver
python3 autoresearch.py --config config.yaml --once
```

This runs one cycle to verify everything works before committing to a longer run.

### 3.4 Monitor progress with the dashboard

```bash
cd /home/user/test-improver
python3 dashboard.py --config config.yaml --port 8501
```

Then open `http://localhost:8501` in a browser to see live score charts.

### 3.5 If starting fresh (reset state)

If the user wants a clean slate:

```bash
cd /home/user/test-improver

# Back up current data
cp -r data data_backup_$(date +%Y%m%d)

# Reset state
echo '{"best_score": -1, "run_number": 0}' > data/state.json

# Optionally write a new seed prompt
cat > data/prompt.txt << 'EOF'
Create a clean, hand-drawn style diagram on a white background. Use soft pastel colored rounded rectangles for each concept. Use thin black arrows to show flow direction. All text must be real, correctly spelled English words. Flow must be strictly left-to-right in a single horizontal line. No numbers anywhere.
EOF

# Clear results history
> data/results.jsonl

# Run 10 cycles
python3 autoresearch.py --config config.yaml --cycles 10
```

### 3.6 If user wants to customize criteria or topics

Edit `/home/user/test-improver/config.yaml` directly. The relevant sections:

- **criteria** (lines 39-66): Add/remove/modify evaluation criteria. Each needs a `name`, `label`, and `description`.
- **mutation.rules** (lines 74-83): Domain-specific guidance for how the mutator should improve the prompt.
- **topics** (lines 87-117): The 30 diagram topics. Add more for better coverage.
- **batch_size** (line 120): Currently 10. Reduce to 5 for faster/cheaper cycles, or increase for more reliable scoring.

### 3.7 Auto-generate new criteria (if user wants different ones)

```bash
cd /home/user/test-improver
python3 autoresearch.py generate-criteria --config config.yaml
```

This uses Claude to auto-generate criteria based on the skill description and topics. Review the JSON output and save with:

```bash
python3 autoresearch.py save-criteria --config config.yaml \
  --criteria-json '<paste JSON array here>' \
  --rules-json '<paste rules JSON array here>'
```

## Step 4: What I Would Tell the User

"Your system is already set up and has completed 8 optimization runs. Here is the situation:

1. **Your config.yaml is ready.** It targets Gemini image generation (`gemini-2.5-flash-image`) with 4 evaluation criteria: legible text, pastel colors, linear layout, and no numbers. You have 30 diagram topics — that is solid coverage.

2. **The system already achieved a perfect 40/40 on run 6**, but subsequent runs show the prompt does not consistently produce perfect results — legibility (garbled text) remains the hardest criterion to nail. This is expected with image generation models.

3. **To continue optimizing**, ensure `NANO_BANANA_API_KEY` (your Gemini key) and `ANTHROPIC_API_KEY` are set, then run:
   ```
   python3 autoresearch.py --config config.yaml --cycles 10
   ```

4. **Key bottleneck is text legibility.** The prompt has evolved detailed spelling rules, but image models are inherently unreliable with text rendering. Consider whether this criterion should be relaxed or whether a post-processing step (e.g., OCR validation) might be more effective than prompt engineering alone.

5. **Cost estimate:** Each cycle generates 10 images via Gemini and runs 10 Claude vision evaluations plus 1 mutation call. At roughly $0.01-0.03 per Gemini image and $0.01-0.05 per Claude vision call, expect roughly $0.30-0.80 per cycle, or $3-8 for 10 cycles.

6. **Monitor with the dashboard:** Run `python3 dashboard.py` and open localhost:8501."

## Step 5: Architecture Summary

```
config.yaml          -- Defines skill, backend, criteria, topics, settings
     |
autoresearch.py      -- Main optimization loop
     |
     +-- generate_one()   -- Calls Gemini to create diagram image
     +-- evaluate_one()   -- Calls Claude vision to score against criteria
     +-- mutate_prompt()  -- Calls Claude to improve prompt based on failures
     +-- run_cycle()      -- Orchestrates one generate->evaluate->score->mutate cycle
     |
data/
  prompt.txt         -- Current working prompt (mutated each cycle)
  best_prompt.txt    -- Best-scoring prompt snapshot
  state.json         -- Run counter + best score
  results.jsonl      -- Append-only log of per-run scores
  outputs/run_NNN/   -- Generated images per run
     |
dashboard.py         -- Web UI to visualize progress over time
```

The loop is: **Generate batch -> Evaluate with Claude Vision -> Score -> Keep if better -> Mutate prompt -> Repeat**
