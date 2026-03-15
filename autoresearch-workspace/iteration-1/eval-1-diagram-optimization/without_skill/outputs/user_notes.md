# User Notes: Uncertainties and Open Questions

## Environment Uncertainties

1. **API key env var name.** The config expects `NANO_BANANA_API_KEY` for the Gemini API key. This appears to be a custom name. The user should confirm this matches their environment, or change `config.yaml` line 17 (`api_key_env`) to whatever env var holds their Gemini key (e.g., `GEMINI_API_KEY`).

2. **Anthropic API key required.** The system uses Claude for evaluation (vision) and prompt mutation, even though generation uses Gemini. The user needs both `NANO_BANANA_API_KEY` and `ANTHROPIC_API_KEY` set. This dual-key requirement is not obvious from the user's description ("I have a Gemini API key").

3. **Python dependencies.** The script requires `google-genai`, `anthropic`, `pyyaml`, and `python-dotenv`. I did not check whether these are installed. Run `pip install google-genai anthropic pyyaml python-dotenv` if needed.

## Optimization Uncertainties

4. **Text legibility is inherently hard for image models.** The run history shows legibility is the most volatile criterion (ranging from 4/10 to 10/10 across runs). Prompt engineering alone may hit a ceiling — the Gemini model's text rendering capability is the fundamental constraint. The user should decide whether:
   - A legibility score of 7-8/10 is acceptable
   - They want to switch to a different model (e.g., a newer Gemini version) that handles text better
   - They want to add a post-generation OCR validation step

5. **Score variance is high.** Run 6 scored 40/40 (perfect), but runs 7 and 8 regressed to 37/40 with the same or very similar prompt. This suggests the generation model itself has high variance. More cycles will help find a robust prompt, but perfection on every batch may not be achievable.

6. **Batch size of 10 with 30 topics.** Each cycle samples 10 of 30 topics. This means each topic is tested roughly once every 3 cycles. Some topics may be inherently harder (e.g., topics with more technical terms are more likely to produce garbled text). The user could increase batch_size to 15-20 for more representative scoring, at the cost of higher per-cycle API spend.

7. **Prompt length is growing.** The prompt started at 560 chars (run 1) and grew to 2307 chars (run 8). The mutation rules say "keep prompt under 400 words" but the current prompt is already quite long. There is a risk of prompt bloat where added constraints start conflicting. The user may want to periodically manually prune the prompt.

## Scope Uncertainties

8. **"About 30 example topics"** — The config already has exactly 30 topics. It is unclear whether the user wants to add different topics or is referring to these existing ones.

9. **User's current prompt vs. the evolved one.** The system has already evolved the prompt through 8 runs. If the user has a different starting prompt in mind, they should overwrite `data/prompt.txt` and reset the state.

10. **Cost awareness.** Running 10 cycles will cost approximately $3-8 in combined Gemini and Anthropic API charges. The user should be aware of this before starting a long run.
