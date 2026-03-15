# User Notes: Uncertainties and Open Questions

## Uncertainties

### 1. API Key Configuration
- The config references `NANO_BANANA_API_KEY` as the Gemini API key environment variable name. The user said they "have a Gemini API key" but it is unclear whether they have already set this environment variable or if the variable name matches what they expect. They may need to rename it or update `config.yaml` to match their actual env var name.
- An `ANTHROPIC_API_KEY` is also required for the evaluation and mutation steps (Claude Sonnet is used for both). The user did not mention having an Anthropic key. This is a hard requirement -- without it, the eval/mutation loop cannot run even if Gemini generation works.

### 2. Current State -- Already Optimized?
- The system shows a best_score of 40/40 after 8 runs, meaning the current prompt has already achieved a perfect score against all 4 criteria. It is unclear whether:
  - The user is aware of these prior runs
  - The user wants to continue from this state or start fresh
  - The 40/40 score is genuinely stable or was a one-time lucky result
- Recommendation: Run at least 3 verification cycles (`--cycles 3`) to confirm the score holds before declaring the prompt optimized.

### 3. "About 30 Example Topics"
- The config already contains exactly 30 topics. It is unclear whether the user wrote these themselves or if they were pre-populated. If the user has a different set of 30 topics in mind, the `topics` section of `config.yaml` would need to be updated.

### 4. Criteria Coverage
- The 4 existing criteria address the user's stated problems (garbled text, wrong colors) but may not capture all quality dimensions they care about. For example:
  - **Semantic accuracy**: Does the diagram correctly represent the described system?
  - **Completeness**: Does it include all the components mentioned in the topic?
  - **Consistency**: Are the style/size of elements uniform?
- The user should consider whether additional criteria are needed after seeing initial results.

### 5. Gemini Model Availability
- The config uses `gemini-2.5-flash-image` which is a specific model variant that supports native image generation. If this model is not available in the user's Gemini API plan or region, generation will fail. They may need to switch to a different model.

### 6. Batch Size vs. Topic Count
- `batch_size` is 10 and there are 30 topics. Each cycle randomly samples 10 of the 30. This means any given cycle only tests 1/3 of the topics. It would take approximately 3 cycles minimum to cover all topics at least once (probabilistically more like 5-7 cycles for full coverage due to random sampling with replacement).

### 7. Cost Estimation
- Each cycle makes approximately 10 Gemini image generation calls + 10 Claude vision evaluation calls + 1 Claude text mutation call. At ~$0.003-0.01 per Gemini image and ~$0.01-0.03 per Claude vision call, a 10-cycle run could cost $3-7. The user should be aware of this before starting continuous mode.

### 8. Dashboard Port Availability
- The dashboard defaults to port 8501. If the user is running other services (e.g., Streamlit also uses 8501), there may be a port conflict. They can change it with `--port <number>`.

### 9. No AskUserQuestion Tool Available
- The SKILL.md specifies using `AskUserQuestion` for interactive criteria review. This tool was not available in the current environment, so the criteria review step was handled via documented text output rather than interactive prompts. In a live session, the user would need to respond to these questions directly.

### 10. Image Quality Evaluation Reliability
- Claude's vision capability is used to evaluate generated diagrams. Vision-based evaluation of image quality properties (legibility, color accuracy, layout structure) has inherent subjectivity and may not always agree with human judgment. The user should manually spot-check a sample of evaluations, especially for the "legible_and_grammatical" criterion which requires reading generated text in images.
