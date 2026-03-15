# Transcript: Setting Up Email Subject Line Optimization Loop

## Task
Create an optimization loop for an email subject line generator that uses OpenAI's API for generation and evaluates on click-worthiness, clarity, and length.

## Steps Taken

### Step 1: Explored the Codebase
Read and analyzed the following files to understand the autoresearch system:

- **`autoresearch.py`** — The main optimization loop script. It supports a generic pattern:
  1. Generate a batch of outputs using a configurable backend (OpenAI, Anthropic, Gemini, shell)
  2. Evaluate each output against boolean criteria using Claude
  3. Compare against best score, keep the winner prompt
  4. Mutate the winning prompt for the next cycle
  5. Repeat

- **`config.yaml`** — Example config for diagram generation using Gemini. Shows the full config structure: `name`, `description`, `generation`, `evaluation` (with criteria), `mutation` (with rules), `topics`, and loop settings.

- **`dashboard.py`** — A live dashboard that reads `results.jsonl` and shows progress charts. Works with any config.

- **`examples/code_review_config.yaml`** — A second example config using `anthropic_text` backend for text generation. Confirmed the pattern for text-based skills.

### Step 2: Designed the Config
Key decisions made:

1. **Backend**: `openai_text` — The user specified OpenAI's API. The codebase has built-in support for this via the `generate_openai_text` function.

2. **Model**: `gpt-4o` — A strong default. The user can change this to `gpt-4o-mini` for cost savings or `gpt-4-turbo` as needed.

3. **Output type**: `text` with `.txt` extension — Subject lines are plain text.

4. **Max tokens**: `256` — Subject lines are short; no need for large token budgets.

5. **Evaluation criteria** (3 criteria matching the user's request):
   - `click_worthiness` — Checks for curiosity/urgency hooks while banning spammy tactics
   - `clarity` — Checks that the subject line communicates the email's topic on first read
   - `appropriate_length` — Enforces the 30-60 character sweet spot for email clients

6. **Mutation rules**: Targeted guidance for each criterion failure, plus general anti-spam rules.

7. **Topics**: 20 diverse email campaign scenarios (SaaS launch, flash sale, newsletter, abandoned cart, cold outreach, etc.) to ensure the prompt generalizes well.

8. **Batch size**: 10 (samples 10 topics per cycle for evaluation).

9. **Cycle time**: 90 seconds — text generation is fast so cycles can be shorter than the 120s default.

### Step 3: Created the Initial Prompt
Wrote `initial_prompt.txt` as the seed prompt for the optimization loop. It contains basic instructions about length, clarity, and anti-spam requirements. The autoresearch loop will iteratively improve this prompt.

### Step 4: Created the Config File
Wrote `email_config.yaml` following the exact schema expected by `autoresearch.py`.

## Commands to Run

### Prerequisites
1. Ensure environment variables are set:
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   export ANTHROPIC_API_KEY="your-anthropic-api-key"
   ```
   - OpenAI key is needed for generation (subject line creation)
   - Anthropic key is needed for evaluation (Claude scores the outputs) and mutation (Claude rewrites the prompt)

2. Ensure Python dependencies are installed:
   ```bash
   pip install openai anthropic pyyaml python-dotenv
   ```
   Alternatively, place keys in a `.env` file in the working directory.

### Setup: Copy config and seed prompt into position
```bash
# Copy the config to the working directory
cp /home/user/test-improver/autoresearch-workspace/iteration-1/eval-3-email-from-scratch/without_skill/outputs/email_config.yaml /home/user/test-improver/email_config.yaml

# The autoresearch script stores data relative to the config file location.
# It will create a data/ directory next to email_config.yaml.
# Create the data directory and place the initial prompt:
mkdir -p /home/user/test-improver/data
cp /home/user/test-improver/autoresearch-workspace/iteration-1/eval-3-email-from-scratch/without_skill/outputs/initial_prompt.txt /home/user/test-improver/data/prompt.txt
```

Note: The `get_paths()` function in autoresearch.py derives data paths from the config file location (`Path(config_path).resolve().parent / "data"`). Since email_config.yaml would be placed at `/home/user/test-improver/email_config.yaml`, data goes to `/home/user/test-improver/data/`.

### Run a Single Test Cycle
```bash
cd /home/user/test-improver
python3 autoresearch.py --config email_config.yaml --once
```
This runs one cycle to verify everything works: generates 10 subject lines, evaluates them, and mutates the prompt.

### Run Multiple Optimization Cycles
```bash
cd /home/user/test-improver
python3 autoresearch.py --config email_config.yaml --cycles 10
```
This runs 10 optimization cycles. Each cycle generates a batch, evaluates, and mutates. Expect ~15 minutes total.

### Run Continuous Optimization
```bash
cd /home/user/test-improver
python3 autoresearch.py --config email_config.yaml
```
Runs indefinitely until interrupted with Ctrl+C.

### Monitor Progress with Dashboard
```bash
cd /home/user/test-improver
python3 dashboard.py --config email_config.yaml --port 8501
```
Then open `http://localhost:8501` in a browser to see live score charts.

## How the Loop Works (for this config)

1. **Generate**: OpenAI `gpt-4o` receives the current prompt + a random email campaign topic and produces a subject line. 10 subject lines per batch.

2. **Evaluate**: Claude `claude-sonnet-4-6` scores each subject line on 3 boolean criteria (click-worthiness, clarity, length). Max score per cycle = 10 x 3 = 30.

3. **Score & Compare**: If the batch score beats the best score so far, the current prompt is saved as `best_prompt.txt`. Otherwise, it reverts to the best prompt.

4. **Mutate**: Claude analyzes which criteria failed and rewrites the prompt to address failures, guided by the mutation rules.

5. **Repeat**: The mutated prompt is used for the next cycle. Over time, the prompt converges on instructions that consistently produce high-scoring subject lines.

## Expected Output Files (after running)
- `data/prompt.txt` — Current prompt (mutated each cycle)
- `data/best_prompt.txt` — Best-performing prompt found so far
- `data/state.json` — Run counter and best score
- `data/results.jsonl` — Log of all cycle results (used by dashboard)
- `data/outputs/run_NNN/output_NN.txt` — Individual generated subject lines
