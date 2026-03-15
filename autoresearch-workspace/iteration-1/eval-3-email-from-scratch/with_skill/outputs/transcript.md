# Transcript: Email Subject Line Generator — Autoresearch Optimization Loop Setup

## Task
Set up a complete optimization loop from scratch for an email subject line generator that uses OpenAI's API, evaluating on click-worthiness, clarity, and length.

---

## Step 1: Load and Validate Config

**Action:** Read the SKILL.md to understand the full skill procedure and config format.

**Findings:**
- The skill follows a 4-step procedure: Load Config, Criteria Setup (Interactive), Run Optimization Loop, Dashboard.
- Config format requires: name, description, generation, evaluation, mutation, topics, and loop settings.
- The user wants OpenAI as the generation backend, which maps to the `openai_text` backend type.
- Output type is `text` (subject lines are plain text strings).

**Action:** Read the example `config.yaml` (diagram-generation) to use as a structural template.

**Action:** Created `email_config.yaml` with all fields populated for the email subject line use case:
- `backend: "openai_text"`, `model: "gpt-4o"`, `api_key_env: "OPENAI_API_KEY"`
- `output_type: "text"`, `output_extension: ".txt"`
- `prompt_template: "{prompt}\n\nEmail campaign context: {topic}"`
- Left `evaluation.criteria: []` intentionally empty so that Step 2 (interactive criteria generation) is triggered.
- Wrote 8 mutation rules specific to email subject line optimization.
- Wrote 20 diverse email campaign topics covering newsletters, abandoned carts, B2B outreach, re-engagement, product launches, seasonal sales, etc.

**Decision:** I chose `gpt-4o` as the generation model since the user said "OpenAI's API" without specifying a model. GPT-4o is a reasonable default; the user can change this to `gpt-4o-mini` for cost savings or `gpt-4` for different behavior.

**Action:** Created `initial_prompt.txt` — the seed prompt that the optimization loop will start from and iteratively improve. It instructs the model to produce a single subject line under 60 characters with guidelines for tone, clarity, and format.

**Validation command (WOULD run):**
```bash
python3 autoresearch.py --config email_config.yaml  # dry-run to validate config
```
This validates the config structure and checks that required fields are present. If OPENAI_API_KEY is not set in the environment or `.env`, the script would error at this point.

---

## Step 2: Criteria Setup (Interactive)

Since `evaluation.criteria` is intentionally left empty in the config, the skill procedure triggers the interactive criteria generation flow.

### Step 2a: Ask whether to generate criteria

**WOULD ask the user:**
> "No evaluation criteria found in config. Would you like me to generate them automatically?"
> Options: "Yes, generate criteria (Recommended)" / "No, I'll define them manually"

**Assumed answer:** Yes (since the user asked us to set everything up).

### Step 2b: Generate criteria

**WOULD run:**
```bash
python3 autoresearch.py generate-criteria --config email_config.yaml
```

**Expected output:** JSON with 4-6 criteria and mutation rules. Based on the user's stated evaluation dimensions (click-worthiness, clarity, and length), the generated criteria would likely include:

1. **click_worthiness** — "The subject line creates a compelling reason to open the email. It uses one or more proven techniques: curiosity gap, urgency, personalization, benefit-driven language, or emotional appeal. A reader seeing this in a crowded inbox would feel drawn to click."

2. **clarity** — "The subject line clearly and immediately communicates what the email is about. The reader can understand the topic and value proposition within 1-2 seconds of reading. No ambiguity, no vague phrasing, no jargon that would confuse a general audience."

3. **length_appropriateness** — "The subject line is between 30 and 60 characters (including spaces). It is long enough to convey meaning but short enough to display fully on mobile devices without truncation."

4. **tone_and_professionalism** — "The subject line strikes an appropriate professional tone for the given campaign context. It avoids spam-like patterns (excessive punctuation, ALL CAPS, clickbait phrases) while remaining engaging and human."

5. **relevance_to_context** — "The subject line accurately reflects the specific email campaign context provided. It addresses the right audience, product/service, and purpose — not a generic subject line that could apply to anything."

### Step 2c: Offer to review criteria

**WOULD ask the user:**
> "I generated 5 criteria. Would you like to review them?"
> Options: "Review new criteria only (Recommended)" / "Accept all as-is"

### Step 2d: Review each criterion

**WOULD present each criterion one at a time** and for each ask:
> "How would you like to handle the '[label]' criterion?"
> Options: "Keep as-is" / "Optimize" / "Write my own"

If the user chose "Optimize" for any criterion, WOULD run:
```bash
python3 autoresearch.py optimize-criterion --config email_config.yaml --criterion-json '<json>'
```
Then present both versions and let the user pick.

### Step 2e: Save finalized criteria

After review, **WOULD run:**
```bash
python3 autoresearch.py save-criteria --config email_config.yaml \
  --criteria-json '[<finalized criteria array>]' \
  --rules-json '[<mutation rules array>]'
```

This writes the criteria and any updated mutation rules back into `email_config.yaml`.

---

## Step 3: Run the Optimization Loop

**WOULD ask the user:** "How would you like to run the optimization loop?"
- Single cycle (test): `python3 autoresearch.py --config email_config.yaml --once`
- Run N cycles: `python3 autoresearch.py --config email_config.yaml --cycles 10`
- Continuous loop: `python3 autoresearch.py --config email_config.yaml`

**Recommended starting command:**
```bash
python3 autoresearch.py --config email_config.yaml --once
```
This runs a single cycle first so the user can verify everything works before committing to a longer run.

**What a single cycle does:**
1. Samples 10 topics from the topics list (batch_size: 10).
2. Sends each topic + the current prompt to OpenAI's GPT-4o, getting back 10 subject lines.
3. Evaluates each subject line against all criteria using Claude (claude-sonnet-4-6).
4. Computes an average score across all criteria and topics.
5. If this is the first run, or the score beats the previous best, saves the prompt as `best_prompt.txt`.
6. Uses Claude to mutate the winning prompt based on failure analysis for the next cycle.
7. Logs everything to `data/results.jsonl`.

**After verifying the single cycle works, WOULD run:**
```bash
python3 autoresearch.py --config email_config.yaml --cycles 10
```

---

## Step 4: Dashboard (Optional)

**WOULD offer to the user:**
> "Would you like to start the live dashboard to monitor optimization progress?"

**WOULD run:**
```bash
python3 dashboard.py --config email_config.yaml --port 8501
```

The dashboard at `http://localhost:8501` would show:
- Best score, baseline score, improvement %, and runs kept/total
- Score-over-time chart
- Per-criterion breakdown (click_worthiness, clarity, length, etc.)
- Run history table
- Current best prompt display

---

## Environment Prerequisites

Before any of the above commands can run, the user needs:

1. **API Keys in `.env` file:**
   ```
   ANTHROPIC_API_KEY=sk-ant-...   # Required for evaluation and mutation (Claude)
   OPENAI_API_KEY=sk-...          # Required for generation (GPT-4o)
   ```

2. **Python dependencies:**
   ```bash
   pip install pyyaml anthropic python-dotenv openai
   ```

3. **Initial prompt file:** The `initial_prompt.txt` must be placed at `data/prompt.txt` (the default location the script reads from):
   ```bash
   mkdir -p data
   cp initial_prompt.txt data/prompt.txt
   ```

---

## Files Created

| File | Purpose |
|------|---------|
| `email_config.yaml` | Full config file for the email subject line optimization loop |
| `initial_prompt.txt` | Seed prompt that the optimization loop starts from |
| `transcript.md` | This file — documents all steps and decisions |
| `user_notes.md` | Uncertainties and questions for the user |

---

## Summary of Decisions Made

1. **Model choice:** Selected `gpt-4o` as the OpenAI generation model. This is a reasonable default but can be changed.
2. **Criteria left empty in config:** Intentionally left `evaluation.criteria: []` so the skill's interactive criteria generation flow (Step 2) is triggered, which produces better-tailored criteria.
3. **20 diverse topics:** Created a wide range of email campaign scenarios to ensure the optimizer generalizes well across different email types.
4. **Subject line length target:** Set 30-60 characters as the ideal range, based on industry best practices for mobile email display.
5. **8 mutation rules:** Wrote domain-specific rules that guide the mutation model to make effective prompt improvements for email subject lines specifically.
6. **Seed prompt design:** The initial prompt is intentionally simple and rule-based, giving the optimizer room to improve via creative techniques (curiosity gaps, personalization, etc.).
