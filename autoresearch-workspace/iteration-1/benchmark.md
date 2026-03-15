# Skill Benchmark: autoresearch

**Model**: claude-opus-4-6
**Date**: 2026-03-15
**Evals**: diagram-optimization, existing-config, email-from-scratch (1 run each per configuration)

## Summary

| Metric | With Skill | Without Skill | Delta |
|--------|------------|---------------|-------|
| Pass Rate | 92% ± 14% | 85% ± 13% | +0.07 |
| Time | 122.9s ± 27.0s | 114.9s ± 29.6s | +8.0s |
| Tokens | 25811 ± 10479 | 33765 ± 2645 | -7954 |

## Per-Eval Breakdown

| Eval | With Skill | Without Skill |
|------|-----------|--------------|
| 1. Diagram Optimization | 5/5 (100%) | 4/5 (80%) |
| 2. Existing Config | 3/4 (75%) | 3/4 (75%) |
| 3. Email From Scratch | 5/5 (100%) | 5/5 (100%) |

## Notes

- Eval 1 "Reads SKILL.md" assertion passes 100% with_skill but 0% without — expected by design, not discriminating
- Eval 2 config identification fails equally in both configurations — the skill doesn't help resolve ambiguous config references
- Eval 3 shows no pass_rate difference — both achieve 5/5. With-skill used 37% fewer tokens
- With-skill runs used 24% fewer tokens on average — the skill provides structure that reduces exploration
- The skill's main value-add is in procedural structure and interactive features (criteria generation flow), not task accuracy
