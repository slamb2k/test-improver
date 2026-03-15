# User Notes: Uncertainties and Clarifications Needed

## Critical: Config Mismatch

The user said "my code review prompt optimizer" but the root `config.yaml` at `/home/user/test-improver/config.yaml` is configured for **diagram generation**, not code review:
- Name: `diagram-generation`
- Backend: `gemini_image` (Gemini 2.5 Flash)
- Criteria: Legible, Pastel colors, Linear layout, No Numbers

A code review config exists at `/home/user/test-improver/examples/code_review_config.yaml`:
- Name: `code-review`
- Backend: `anthropic_text` (Claude Sonnet)
- Criteria: Actionable, Correct, Prioritized, Tone

**Action needed:** Clarify which config the user wants. If they want code review, they should either:
1. Copy `examples/code_review_config.yaml` to `config.yaml`, or
2. Use `--config examples/code_review_config.yaml`

## API Keys Required

- For the diagram config: Both `NANO_BANANA_API_KEY` (Gemini) and `ANTHROPIC_API_KEY` (Claude for eval/mutation) must be set.
- For the code review config: Only `ANTHROPIC_API_KEY` is needed (used for generation, evaluation, and mutation).

I did not check whether these environment variables are currently set.

## Existing State

There is already run data in `/home/user/test-improver/data/`. Running 5 more cycles will append to this existing history, not start fresh. If the user wants a clean run, they would need to delete or move the `data/` directory first.

## Dashboard Behavior

The dashboard is a simple HTTP server that reads from `data/results.jsonl`. It must be pointed at the same config used for the run (so paths resolve correctly). It auto-refreshes every 15 seconds, so it can be launched before, during, or after the cycles. It defaults to port 8501.

## No Prompt Seed for Code Review Config

If using the code review config for the first time, the script will auto-create a generic seed prompt: "Generate a high-quality output for the given topic." This is quite generic. For better results, the user might want to create `examples/data/prompt.txt` with a more targeted initial prompt for code review.
