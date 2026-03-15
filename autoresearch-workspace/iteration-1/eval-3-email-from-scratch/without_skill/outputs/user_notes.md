# User Notes: Uncertainties and Considerations

## API Keys Required
- **OPENAI_API_KEY**: Must be set for subject line generation. The config references this via `api_key_env: "OPENAI_API_KEY"`.
- **ANTHROPIC_API_KEY**: Must be set for evaluation and mutation (Claude is used for both). This is checked directly in `autoresearch.py`'s `main()` function.

## Model Choice Uncertainty
- I chose `gpt-4o` as the generation model. If cost is a concern, `gpt-4o-mini` would be significantly cheaper and may be sufficient for subject line generation. The user should adjust based on their budget and quality needs.
- The evaluation model is set to `claude-sonnet-4-6` which is the default in the codebase. `claude-sonnet-4-6` could also work if available.

## Character Count Evaluation
- The `appropriate_length` criterion asks Claude to judge whether the subject line is 30-60 characters. LLMs are not perfectly reliable at counting characters. In practice, this should work reasonably well since Claude can estimate length, but it may occasionally misjudge edge cases (e.g., 29 or 61 characters). If precise length enforcement is critical, consider adding a `shell` backend post-processing step or a custom evaluation script.

## Data Directory Overlap
- The existing `config.yaml` (for diagram generation) already uses `/home/user/test-improver/data/` for its outputs. If both configs are used from the same directory, they will share the same `data/` folder and conflict. To avoid this, either:
  1. Place `email_config.yaml` in its own subdirectory (e.g., `/home/user/test-improver/email/email_config.yaml`)
  2. Or clear the existing `data/` directory before starting the email optimization

## Topic Coverage
- I created 20 email campaign topics. The batch size is 10, so each cycle samples 10 of these. For better generalization, the user may want to add more topics specific to their actual use case (their industry, audience, product type, etc.).

## Batch Size and Cycle Time
- Batch size of 10 with 90-second cycles is a reasonable default. If OpenAI rate limits are hit, reduce `max_gen_workers` from 3 to 1-2. If costs are a concern, reduce `batch_size` to 5.

## Prompt Template
- The template is `"{prompt}\n\nEmail campaign context: {topic}"`. This means OpenAI receives the optimized prompt instructions followed by the specific campaign context. This structure matches how the other example configs work.

## What I Did NOT Do
- I did not run `autoresearch.py` or make any API calls, as instructed.
- I did not read SKILL.md.
- I did not modify any existing files in the repository.
