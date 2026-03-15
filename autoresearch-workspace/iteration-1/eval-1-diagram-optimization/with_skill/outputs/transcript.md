# Transcript: Diagram Prompt Optimization via Autoresearch Skill

## Task Summary

The user wants to systematically improve a prompt that generates technical diagrams using Gemini's image generation. Problems reported: garbled text, wrong colors, inconsistent quality. They have a Gemini API key and approximately 30 example topics. The goal is to set up an automated optimization loop using the autoresearch pattern.

---

## Step 1: Load and Validate Config

**Action:** Read `config.yaml` to understand current state.

**Command I would run:**
```bash
cd /home/user/test-improver
python3 autoresearch.py --config config.yaml
```

**Findings:**
- The config is already well-structured for the diagram generation use case.
- `name`: "diagram-generation"
- `generation.backend`: "gemini_image" using model "gemini-2.5-flash-image"
- `generation.api_key_env`: "NANO_BANANA_API_KEY" (the user's Gemini API key environment variable)
- `generation.output_type`: "image" with `.png` extension
- `generation.prompt_template`: `"{prompt}\n\nDiagram to create: {topic}"`
- 30 topics are already defined covering CI/CD pipelines, ML workflows, auth flows, microservices, ETL, and many more.
- `batch_size`: 10, `cycle_seconds`: 120, `max_gen_workers`: 3, `max_eval_workers`: 5

**Decision:** Config structure is valid and complete. No modifications needed to the base config layout. Proceed to criteria check.

---

## Step 2: Criteria Setup (Interactive)

**Action:** Check if `evaluation.criteria` is defined in the config.

**Findings:** Criteria ARE already defined. The config contains 4 evaluation criteria:

1. **legible_and_grammatical** ("Legible"): All text must be clearly readable with no garbled, overlapping, blurry, or cut-off text. Correct spelling and grammar required.
2. **pastel_colors** ("Pastel"): Only soft pastel colors for fills. No bright, saturated, neon, or dark-colored fills.
3. **linear_layout** ("Linear"): Diagram must flow in one clear linear direction (left-to-right or top-to-bottom). No circular, radial, scattered, or hub-and-spoke layouts.
4. **no_numbers** ("No Numbers"): Zero numbers, step numbers, ordinals, sequence indicators, or numerical ordering anywhere in the diagram.

**Decision:** Since criteria already exist, skip the generation sub-step (2a-2b). However, per the SKILL.md instructions, I would ask the user if they want to review or optimize these criteria.

**What I would ask the user:**
> "Your config already has 4 evaluation criteria defined (Legible, Pastel, Linear, No Numbers). Would you like to review them, or accept all as-is?"
>
> Options:
> - "Review all criteria" -- walk through each one and optionally optimize
> - "Accept all as-is" -- proceed directly to the optimization loop

**Assumed user response (for simulation):** "Accept all as-is" -- the criteria directly address the reported problems (garbled text, wrong colors) and add two additional quality dimensions.

The mutation rules are also already defined with 9 domain-specific rules that give targeted guidance for each criterion failure mode. These are well-crafted and specific to image generation constraints.

---

## Step 3: Verify Environment and Data Directory

**Action:** Check the existing state of the optimization loop.

**Findings from `data/` directory:**
- `prompt.txt` exists with a well-developed prompt (already iterated). It includes detailed sections on layout rules, spelling rules, and numbers rules.
- `state.json` shows: run_number=8, best_score=40 (out of max 40, i.e., 10 batch_size * 4 criteria).
- `results.jsonl` exists with historical run data.
- `best_prompt.txt` exists.

**Decision:** The system has already been run for 8 cycles and has reached a perfect score of 40/40. This is critical context. I would inform the user of this.

**What I would tell the user:**
> "Good news -- it looks like this optimization loop has already been run (8 cycles completed) and has achieved a perfect score of 40/40 (all 4 criteria passing across all 10 batch samples). The current prompt in `data/prompt.txt` has been iteratively refined to include explicit rules for layout, spelling, and number avoidance.
>
> You have a few options:
> 1. **Run more cycles** to verify the score holds (scores can fluctuate due to generation randomness)
> 2. **Add new/stricter criteria** and continue optimizing
> 3. **Reset and start fresh** with a simpler seed prompt to observe the full optimization trajectory
> 4. **Run a validation batch** with `--once` to confirm the 40/40 holds on new random topic samples"

---

## Step 4: Commands I Would Run

### Option A: Verify current performance (recommended first step)

```bash
# Ensure API keys are in .env
# NANO_BANANA_API_KEY=<user's Gemini API key>
# ANTHROPIC_API_KEY=<user's Anthropic API key for eval/mutation>

# Run a single verification cycle
cd /home/user/test-improver
python3 autoresearch.py --config config.yaml --once
```

This would:
1. Sample 10 random topics from the 30 available
2. Generate 10 diagrams using Gemini 2.5 Flash (image mode) with the current optimized prompt
3. Evaluate each diagram against all 4 criteria using Claude Sonnet vision
4. Report the score and per-criterion breakdown
5. If score < 40, mutate the prompt and save the new version

### Option B: Run a full optimization session (if starting fresh or adding criteria)

```bash
# Run 10 optimization cycles
python3 autoresearch.py --config config.yaml --cycles 10
```

### Option C: Start the live dashboard to monitor progress

```bash
# In a separate terminal
python3 dashboard.py --config config.yaml --port 8501
# Dashboard accessible at http://localhost:8501
```

The dashboard provides:
- 4 stat cards (current best, baseline, improvement %, runs/kept)
- Score-over-time chart with keep/discard dot coloring
- Per-criterion breakdown charts (Legible, Pastel, Linear, No Numbers)
- Run history table
- Current best prompt display
- Auto-refreshes every 15 seconds

---

## Step 5: Setup Prerequisites

**What the user needs before running:**

1. **Install Python dependencies:**
   ```bash
   pip install pyyaml anthropic python-dotenv google-genai
   ```

2. **Create `.env` file** (or export environment variables):
   ```
   ANTHROPIC_API_KEY=<their Anthropic API key for eval + mutation>
   NANO_BANANA_API_KEY=<their Gemini API key for image generation>
   ```

3. **Verify the Gemini API key** supports image generation (the `gemini-2.5-flash-image` model with `response_modalities: ["IMAGE", "TEXT"]`).

---

## Step 6: Interpretation of Existing Results

The current optimized prompt (`data/prompt.txt`) is 1,754 characters and has evolved through 8 iterations to include:

- **Visual style directives:** Hand-drawn/whiteboard aesthetic, pastel rounded rectangles with specific color names, thin black arrows, simple line-art icons
- **Layout constraint (MANDATORY):** Extremely explicit rules for single horizontal left-to-right flow, no branching, no fan-out, no vertical elements
- **Spelling constraint (MANDATORY):** Lists common technical terms with correct spellings, forbids garbled/truncated/invented words
- **Numbers constraint (MANDATORY):** Absolute ban on all digits, counters, step numbers, ordinals, version numbers, sequence indicators

The prompt has become very directive and imperative in tone, which aligns with the mutation rule "Be specific and imperative -- image models respond to direct commands."

---

## Step 7: Recommendations for Further Improvement

If the user wants to push quality further beyond the current 40/40:

1. **Add more criteria** to capture additional quality dimensions:
   - `correct_topology`: Does the diagram accurately represent the described system architecture?
   - `visual_balance`: Are boxes evenly sized and spaced?
   - `icon_relevance`: Do the icons inside boxes relate to the labeled concept?
   - `arrow_clarity`: Are arrows clean with no overlapping or crossing?

2. **Increase batch_size** to 15-20 for more statistically significant scoring (at the cost of more API calls per cycle).

3. **Run continuous mode** with the dashboard for long-duration overnight optimization:
   ```bash
   python3 autoresearch.py --config config.yaml --cycles 50 &
   python3 dashboard.py --config config.yaml --port 8501 &
   ```

4. **Test with edge-case topics** that are harder to render (complex branching systems described linearly, topics with many technical terms prone to misspelling).

---

## Summary of Decisions Made

| Decision | Rationale |
|----------|-----------|
| Did not modify config.yaml | Already well-configured for the use case with appropriate backend, criteria, and topics |
| Did not regenerate criteria | 4 existing criteria directly address the user's reported issues (garbled text = legible criterion, wrong colors = pastel criterion) plus two bonus quality dimensions |
| Did not reset state | 8 runs with 40/40 best score represents valuable optimization progress |
| Recommended verification run first | Even with 40/40, image generation has inherent randomness; confirming consistency is important |
| Recommended dashboard | Provides real-time visibility into optimization progress, essential for a 30-topic, multi-cycle workflow |

## Estimated API Cost Per Cycle

- **Gemini generation:** 10 images per cycle (cost depends on Gemini pricing)
- **Claude evaluation:** 10 vision API calls per cycle (each sending a PNG + eval prompt to Claude Sonnet)
- **Claude mutation:** 1 text API call per cycle (if score < max)
- **Approximate:** ~12 API calls per cycle, with 10 being vision calls (most expensive)
- **For 10 cycles:** ~120 API calls total
