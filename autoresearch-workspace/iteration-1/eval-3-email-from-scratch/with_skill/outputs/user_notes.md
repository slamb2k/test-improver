# User Notes — Uncertainties and Questions

## Must Resolve Before Running

1. **OpenAI model choice:** I defaulted to `gpt-4o` in `email_config.yaml`. If you prefer a different model (e.g., `gpt-4o-mini` for lower cost, or `gpt-3.5-turbo` for speed), update the `generation.model` field.

2. **API keys:** Both `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` must be set in a `.env` file in the project root. The OpenAI key is for generation; the Anthropic key is for evaluation and mutation (Claude). Without both, the loop will fail.

3. **Initial prompt placement:** The seed prompt was saved as `initial_prompt.txt` in the outputs directory. Before running the loop, it needs to be copied to `data/prompt.txt` (the default location `autoresearch.py` reads from):
   ```bash
   mkdir -p data
   cp initial_prompt.txt data/prompt.txt
   ```

## Design Uncertainties

4. **Evaluation criteria were left empty on purpose.** The config has `criteria: []` so the skill's interactive criteria-generation step (Step 2) fires automatically. This lets the autoresearch tool generate and refine criteria with your input. If you would rather skip the interactive flow, you can paste criteria directly into the config — see the example criteria in the transcript.

5. **Subject line length range (30-60 characters):** This is based on common email marketing guidance for mobile-friendly subject lines. If your audience primarily reads on desktop, you could extend the upper limit to 70-80 characters. Adjust both the evaluation criterion description and the seed prompt accordingly.

6. **Number of topics (20):** I included 20 diverse email campaign scenarios. If your use case is narrower (e.g., only e-commerce emails), you may want to remove irrelevant topics and add more in your specific domain. More topic diversity = more generalizable prompts, but slower convergence.

7. **Batch size (10):** Each cycle generates 10 subject lines (one per sampled topic). This is a reasonable default for balancing cost vs. signal quality. Lower it to 5 if you want cheaper test runs; raise it to 15-20 for more robust scoring.

8. **Mutation rules are opinionated.** The 8 rules I wrote reflect standard email marketing best practices. If your brand voice or strategy differs (e.g., you intentionally use ALL CAPS for a specific brand), adjust the rules in `email_config.yaml`.

9. **Single subject line per topic vs. multiple options.** The current setup generates one subject line per topic per cycle. If you want the model to produce multiple variants (e.g., "Generate 3 subject line options"), you would need to modify the seed prompt and potentially adjust the evaluation to score each variant separately. The current autoresearch framework evaluates one output per topic.

## Cost Estimates

10. **Per cycle cost (approximate):**
    - Generation: 10 calls to GPT-4o (~$0.02-0.05 per call) = ~$0.20-0.50
    - Evaluation: 10 calls to Claude Sonnet for scoring = ~$0.10-0.30
    - Mutation: 1 call to Claude Sonnet = ~$0.02-0.05
    - **Total per cycle: roughly $0.30-0.85**
    - **10 cycles: roughly $3-8.50**

    These are rough estimates. Actual costs depend on prompt length, response length, and current API pricing. Use `--once` first to verify a single cycle before committing to longer runs.
