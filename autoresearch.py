#!/usr/bin/env python3
"""
Generic Autoresearch — Self-improving prompt optimization for any skill.

Karpathy autoresearch pattern applied to any generative task:
1. Generate batch_size outputs with current prompt (configurable backend)
2. Evaluate each against N criteria via Claude vision/text → score
3. Compare against best score — keep winner
4. Mutate the winner prompt for next cycle
5. Repeat every cycle_seconds

Usage:
    python3 autoresearch.py                          # Continuous loop (default config.yaml)
    python3 autoresearch.py --config my_skill.yaml   # Use custom config
    python3 autoresearch.py --once                   # Single cycle
    python3 autoresearch.py --cycles 5               # Run N cycles
"""

import argparse
import base64
import json
import os
import random
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()


# ─── Config Loading ──────────────────────────────────────────────────────────


def load_config(config_path: str) -> dict:
    """Load and validate the YAML config file."""
    path = Path(config_path)
    if not path.exists():
        print(f"ERROR: Config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)
    with open(path) as f:
        cfg = yaml.safe_load(f)

    # Validate required fields
    required = ["generation", "evaluation", "topics"]
    for key in required:
        if key not in cfg:
            print(f"ERROR: Config missing required key: {key}", file=sys.stderr)
            sys.exit(1)

    if not cfg["evaluation"].get("criteria"):
        print("ERROR: Config must define at least one evaluation criterion", file=sys.stderr)
        sys.exit(1)

    return cfg


# ─── Data Paths ──────────────────────────────────────────────────────────────


def get_paths(config_path: str) -> dict:
    """Derive data paths from config file location."""
    base = Path(config_path).resolve().parent / "data"
    return {
        "base": base,
        "prompt": base / "prompt.txt",
        "best_prompt": base / "best_prompt.txt",
        "state": base / "state.json",
        "results": base / "results.jsonl",
        "outputs": base / "outputs",
    }


# ─── State ───────────────────────────────────────────────────────────────────


def load_state(paths: dict) -> dict:
    if paths["state"].exists():
        return json.loads(paths["state"].read_text())
    return {"best_score": -1, "run_number": 0}


def save_state(state: dict, paths: dict):
    paths["state"].write_text(json.dumps(state, indent=2))


def load_prompt(paths: dict) -> str:
    return paths["prompt"].read_text().strip()


def save_prompt(prompt: str, paths: dict):
    paths["prompt"].write_text(prompt)


# ─── Build Eval Prompt from Criteria ─────────────────────────────────────────


def build_eval_prompt(criteria: list[dict], output_type: str) -> str:
    """Auto-generate the evaluation prompt from config criteria."""
    media = "image" if output_type == "image" else "text output"
    lines = [
        f"You are evaluating a generated {media} against {len(criteria)} strict criteria. "
        f"Examine the {media} carefully.",
        "",
        "Criteria:",
    ]
    for i, c in enumerate(criteria, 1):
        lines.append(f"{i}. {c['name'].upper()}: {c['description'].strip()}")

    lines.append("")
    lines.append("Rate each criterion as PASS (true) or FAIL (false). Be strict.")
    lines.append("")
    lines.append("Respond in this exact JSON format:")

    # Build example JSON
    example = {c["name"]: True for c in criteria}
    example["failures"] = []
    lines.append(json.dumps(example))

    lines.append("")
    lines.append(
        'If any criterion fails, set it to false and add a brief description to the failures array.'
    )

    return "\n".join(lines)


# ─── Build Mutation Prompt ───────────────────────────────────────────────────


def build_mutation_prompt(
    cfg: dict,
    current_prompt: str,
    eval_results: list[dict],
    best_score: int,
    batch_size: int,
) -> str:
    """Build the mutation prompt from config and results."""
    criteria = cfg["evaluation"]["criteria"]
    max_score = batch_size * len(criteria)

    # Compute per-criterion pass rates
    rates = {}
    for c in criteria:
        rates[c["name"]] = sum(1 for r in eval_results if r.get(c["name"]))

    score = sum(rates.values())

    # Collect failures
    all_failures = []
    for r in eval_results:
        for f in r.get("failures", []):
            all_failures.append(f)
    unique_failures = list(dict.fromkeys(all_failures))[:20]
    failures_text = "\n".join(f"- {f}" for f in unique_failures) if unique_failures else "- None"

    # Build rates display
    rates_display = "\n".join(
        f"- {c.get('label', c['name'])}: {rates[c['name']]}/{batch_size}"
        for c in criteria
    )

    # Build rules
    rules = cfg.get("mutation", {}).get("rules", [])
    rules_text = "\n".join(f"- {r}" for r in rules) if rules else "- Make targeted improvements based on failure analysis"

    return f"""You are optimizing a prompt for a generative AI task. Your goal: modify it so generated outputs consistently pass ALL evaluation criteria.

CURRENT PROMPT:
---
{current_prompt}
---

LAST BATCH RESULTS ({score}/{max_score}):
{rates_display}

COMMON FAILURES:
{failures_text}

BEST SCORE SO FAR: {best_score}/{max_score}

RULES FOR YOUR MODIFICATION:
{rules_text}

Return ONLY the new prompt text — no explanation, no markdown fences."""


# ─── Generation Backends ─────────────────────────────────────────────────────


def generate_gemini_image(client, model: str, full_prompt: str, output_path: Path, backend_config: dict) -> bool:
    """Generate an image via Gemini image generation."""
    from google.genai import types

    modalities = backend_config.get("response_modalities", ["IMAGE", "TEXT"])
    try:
        response = client.models.generate_content(
            model=model,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                response_modalities=modalities,
            ),
        )
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_bytes(part.inline_data.data)
                return True
        return False
    except Exception as e:
        print(f"    GEN ERROR: {e}")
        return False


def generate_anthropic_text(client, model: str, full_prompt: str, output_path: Path, backend_config: dict) -> bool:
    """Generate text output via Anthropic."""
    try:
        response = client.messages.create(
            model=model,
            max_tokens=backend_config.get("max_tokens", 4096),
            messages=[{"role": "user", "content": full_prompt}],
        )
        text = response.content[0].text
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text)
        return True
    except Exception as e:
        print(f"    GEN ERROR: {e}")
        return False


def generate_openai_text(client, model: str, full_prompt: str, output_path: Path, backend_config: dict) -> bool:
    """Generate text output via OpenAI."""
    try:
        response = client.chat.completions.create(
            model=model,
            max_tokens=backend_config.get("max_tokens", 4096),
            messages=[{"role": "user", "content": full_prompt}],
        )
        text = response.choices[0].message.content
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text)
        return True
    except Exception as e:
        print(f"    GEN ERROR: {e}")
        return False


def generate_shell(client, model: str, full_prompt: str, output_path: Path, backend_config: dict) -> bool:
    """Generate output by running a shell command. The prompt is passed via stdin."""
    import subprocess

    cmd = backend_config.get("command")
    if not cmd:
        print("    GEN ERROR: shell backend requires 'command' in backend_config")
        return False
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            cmd,
            shell=True,
            input=full_prompt,
            capture_output=True,
            text=True,
            timeout=backend_config.get("timeout", 60),
        )
        if result.returncode != 0:
            print(f"    GEN ERROR: {result.stderr[:200]}")
            return False
        output_path.write_text(result.stdout)
        return True
    except Exception as e:
        print(f"    GEN ERROR: {e}")
        return False


BACKENDS = {
    "gemini_image": generate_gemini_image,
    "anthropic_text": generate_anthropic_text,
    "openai_text": generate_openai_text,
    "shell": generate_shell,
}


# ─── Generation (generic) ───────────────────────────────────────────────────


def generate_one(gen_client, cfg: dict, prompt: str, topic: str, output_path: Path) -> bool:
    """Generate a single output using the configured backend."""
    gen_cfg = cfg["generation"]
    template = gen_cfg.get("prompt_template", "{prompt}\n\n{topic}")
    full_prompt = template.format(prompt=prompt, topic=topic)

    backend_name = gen_cfg["backend"]
    backend_fn = BACKENDS.get(backend_name)
    if not backend_fn:
        print(f"    GEN ERROR: Unknown backend '{backend_name}'. Available: {list(BACKENDS.keys())}")
        return False

    return backend_fn(
        gen_client,
        gen_cfg["model"],
        full_prompt,
        output_path,
        gen_cfg.get("backend_config", {}),
    )


# ─── Evaluation (Claude) ─────────────────────────────────────────────────────


def evaluate_one(anthropic_client, output_path: Path, eval_prompt: str, eval_model: str, output_type: str) -> dict | None:
    """Evaluate a single output against criteria via Claude."""
    try:
        if output_type == "image":
            image_bytes = output_path.read_bytes()
            b64 = base64.b64encode(image_bytes).decode()
            # Detect media type from extension
            ext = output_path.suffix.lower()
            media_types = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp"}
            media_type = media_types.get(ext, "image/png")

            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {"type": "base64", "media_type": media_type, "data": b64},
                        },
                        {"type": "text", "text": eval_prompt},
                    ],
                }
            ]
        else:
            # Text output — read and include inline
            text_content = output_path.read_text()
            messages = [
                {
                    "role": "user",
                    "content": f"Here is the generated output to evaluate:\n\n---\n{text_content}\n---\n\n{eval_prompt}",
                }
            ]

        response = anthropic_client.messages.create(
            model=eval_model,
            max_tokens=512,
            messages=messages,
        )
        text = response.content[0].text.strip()
        # Extract JSON from response (handle markdown fences)
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()
        return json.loads(text)
    except Exception as e:
        print(f"    EVAL ERROR: {e}")
        return None


# ─── Mutation (Claude) ───────────────────────────────────────────────────────


def mutate_prompt(anthropic_client, cfg: dict, current_prompt: str, eval_results: list[dict], best_score: int, batch_size: int) -> str:
    """Use Claude to improve the prompt based on failure analysis."""
    mutate_model = cfg.get("mutation", {}).get("model", "claude-sonnet-4-6")
    mutation_prompt = build_mutation_prompt(cfg, current_prompt, eval_results, best_score, batch_size)

    response = anthropic_client.messages.create(
        model=mutate_model,
        max_tokens=1024,
        messages=[{"role": "user", "content": mutation_prompt}],
    )
    return response.content[0].text.strip()


# ─── Client Factory ──────────────────────────────────────────────────────────


def create_gen_client(cfg: dict):
    """Create the generation client based on backend config."""
    gen_cfg = cfg["generation"]
    backend = gen_cfg["backend"]
    api_key_env = gen_cfg.get("api_key_env", "")
    api_key = os.getenv(api_key_env) if api_key_env else None

    if backend == "gemini_image":
        if not api_key:
            print(f"ERROR: {api_key_env} not set", file=sys.stderr)
            sys.exit(1)
        from google import genai
        return genai.Client(api_key=api_key)

    elif backend == "anthropic_text":
        if not api_key:
            api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print(f"ERROR: {api_key_env or 'ANTHROPIC_API_KEY'} not set", file=sys.stderr)
            sys.exit(1)
        import anthropic
        return anthropic.Anthropic(api_key=api_key)

    elif backend == "openai_text":
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print(f"ERROR: {api_key_env or 'OPENAI_API_KEY'} not set", file=sys.stderr)
            sys.exit(1)
        from openai import OpenAI
        return OpenAI(api_key=api_key)

    elif backend == "shell":
        return None  # Shell backend doesn't need a client

    else:
        print(f"ERROR: Unknown backend '{backend}'", file=sys.stderr)
        sys.exit(1)


# ─── Main Cycle ──────────────────────────────────────────────────────────────


def run_cycle(gen_client, anthropic_client, cfg: dict, state: dict, paths: dict) -> dict:
    """Run one autoresearch optimization cycle."""
    criteria = cfg["evaluation"]["criteria"]
    batch_size = cfg.get("batch_size", 10)
    max_gen_workers = cfg.get("max_gen_workers", 3)
    max_eval_workers = cfg.get("max_eval_workers", 5)
    output_type = cfg["generation"].get("output_type", "image")
    output_ext = cfg["generation"].get("output_extension", ".png")
    eval_model = cfg["evaluation"]["model"]
    max_score = batch_size * len(criteria)

    run_num = state["run_number"] + 1
    state["run_number"] = run_num
    run_dir = paths["outputs"] / f"run_{run_num:03d}"
    run_dir.mkdir(parents=True, exist_ok=True)

    prompt = load_prompt(paths)
    topics = random.sample(cfg["topics"], min(batch_size, len(cfg["topics"])))

    print(f"\n{'='*60}")
    print(f"RUN {run_num} | {datetime.now().strftime('%H:%M:%S')} | Best: {state['best_score']}/{max_score}")
    print(f"{'='*60}")

    # ── Generate ──────────────────────────────────────────────────
    print(f"\n  Generating {batch_size} outputs...")
    generated: list[tuple[int, str, Path]] = []

    with ThreadPoolExecutor(max_workers=max_gen_workers) as pool:
        futures = {}
        for i, topic in enumerate(topics):
            out = run_dir / f"output_{i:02d}{output_ext}"
            f = pool.submit(generate_one, gen_client, cfg, prompt, topic, out)
            futures[f] = (i, topic, out)

        for f in as_completed(futures):
            i, topic, out = futures[f]
            try:
                ok = f.result()
            except Exception as e:
                ok = False
                print(f"    [{i+1}/{batch_size}] ERROR: {e}")
            if ok:
                generated.append((i, topic, out))
                print(f"    [{i+1}/{batch_size}] generated: {topic[:50]}")
            else:
                print(f"    [{i+1}/{batch_size}] FAILED: {topic[:50]}")

    if not generated:
        print("  ERROR: No outputs generated. Skipping cycle.")
        save_state(state, paths)
        return state

    # ── Evaluate ──────────────────────────────────────────────────
    eval_prompt = build_eval_prompt(criteria, output_type)
    print(f"\n  Evaluating {len(generated)} outputs via Claude...")
    eval_results: list[dict] = []
    fail_default = {c["name"]: False for c in criteria}
    fail_default["failures"] = ["eval_error"]

    with ThreadPoolExecutor(max_workers=max_eval_workers) as pool:
        futures = {}
        for i, topic, path in generated:
            f = pool.submit(evaluate_one, anthropic_client, path, eval_prompt, eval_model, output_type)
            futures[f] = (i, topic, path)

        for f in as_completed(futures):
            i, topic, path = futures[f]
            try:
                result = f.result()
            except Exception as e:
                result = None
                print(f"    [{i+1}] EVAL ERROR: {e}")

            if result:
                eval_results.append(result)
                criteria_pass = sum(1 for c in criteria if result.get(c["name"], False))
                fails = result.get("failures", [])
                print(f"    [{i+1}] {criteria_pass}/{len(criteria)} | {'; '.join(fails) if fails else 'all pass'}")
            else:
                eval_results.append(dict(fail_default))
                print(f"    [{i+1}] 0/{len(criteria)} | eval failed")

    # ── Score ─────────────────────────────────────────────────────
    rates = {}
    for c in criteria:
        rates[c["name"]] = sum(1 for r in eval_results if r.get(c["name"]))
    score = sum(rates.values())

    print(f"\n  SCORE: {score}/{max_score}")
    for c in criteria:
        label = c.get("label", c["name"])
        print(f"    {label:20s} {rates[c['name']]}/{batch_size}")

    # ── Log ───────────────────────────────────────────────────────
    log_entry = {
        "run": run_num,
        "timestamp": datetime.now().isoformat(),
        "score": score,
        "max": max_score,
        "criteria": {c["name"]: rates[c["name"]] for c in criteria},
        "prompt_len": len(prompt),
        "generated": len(generated),
    }
    with open(paths["results"], "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    # ── Keep or discard ───────────────────────────────────────────
    if score > state["best_score"]:
        old_best = state["best_score"]
        state["best_score"] = score
        paths["best_prompt"].write_text(prompt)
        print(f"\n  NEW BEST! {score}/{max_score} (was {old_best})")
    else:
        print(f"\n  No improvement ({score} vs best {state['best_score']})")
        if paths["best_prompt"].exists():
            print("  Reverting to best prompt for next mutation")

    # ── Mutate ────────────────────────────────────────────────────
    if score < max_score:
        print("\n  Mutating prompt...")
        base_prompt = paths["best_prompt"].read_text().strip() if paths["best_prompt"].exists() else prompt
        new_prompt = mutate_prompt(anthropic_client, cfg, base_prompt, eval_results, state["best_score"], batch_size)
        save_prompt(new_prompt, paths)
        preview = new_prompt[:200].replace("\n", " ")
        print(f"  New prompt ({len(new_prompt)} chars):")
        print(f"    {preview}...")
    else:
        print(f"\n  PERFECT {max_score}/{max_score}! Prompt fully optimized.")

    save_state(state, paths)
    return state


# ─── Entry Point ──────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Generic autoresearch prompt optimization loop")
    parser.add_argument("--config", default="config.yaml", help="Path to YAML config file (default: config.yaml)")
    parser.add_argument("--once", action="store_true", help="Run a single cycle")
    parser.add_argument("--cycles", type=int, default=0, help="Run N cycles (0=infinite)")
    args = parser.parse_args()

    cfg = load_config(args.config)
    paths = get_paths(args.config)

    # Ensure ANTHROPIC_API_KEY is set (needed for eval/mutation)
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_key:
        print("ERROR: ANTHROPIC_API_KEY not set (required for evaluation/mutation)", file=sys.stderr)
        sys.exit(1)

    import anthropic

    # Setup directories
    paths["base"].mkdir(parents=True, exist_ok=True)
    paths["outputs"].mkdir(parents=True, exist_ok=True)

    # Create initial prompt file if missing
    if not paths["prompt"].exists():
        paths["prompt"].write_text("Generate a high-quality output for the given topic.")

    gen_client = create_gen_client(cfg)
    anthropic_client = anthropic.Anthropic(api_key=anthropic_key)
    state = load_state(paths)

    criteria = cfg["evaluation"]["criteria"]
    batch_size = cfg.get("batch_size", 10)
    max_score = batch_size * len(criteria)
    cycle_seconds = cfg.get("cycle_seconds", 120)

    print(f"Autoresearch: {cfg.get('name', 'unnamed')}")
    print(f"  Description:  {cfg.get('description', '')}")
    print(f"  Backend:      {cfg['generation']['backend']}")
    print(f"  Gen model:    {cfg['generation']['model']}")
    print(f"  Eval model:   {cfg['evaluation']['model']}")
    print(f"  Criteria:     {len(criteria)} ({', '.join(c.get('label', c['name']) for c in criteria)})")
    print(f"  Batch size:   {batch_size}")
    print(f"  Max score:    {max_score}")
    print(f"  Cycle:        {cycle_seconds}s")
    print(f"  State:        run {state['run_number']}, best {state['best_score']}/{max_score}")

    if args.once:
        run_cycle(gen_client, anthropic_client, cfg, state, paths)
        return

    max_cycles = args.cycles or float("inf")
    i = 0
    while i < max_cycles:
        start = time.time()
        try:
            state = run_cycle(gen_client, anthropic_client, cfg, state, paths)
        except Exception as e:
            print(f"\n  CYCLE ERROR: {e}")
            traceback.print_exc()
        elapsed = time.time() - start
        i += 1

        if i < max_cycles:
            wait = max(0, cycle_seconds - elapsed)
            if wait > 0:
                print(f"\n  Waiting {wait:.0f}s until next cycle...")
                time.sleep(wait)
            else:
                print(f"\n  Cycle took {elapsed:.0f}s (>{cycle_seconds}s budget)")

    print(f"\nDone. Best score: {state['best_score']}/{max_score}")
    if paths["best_prompt"].exists():
        print(f"Best prompt: {paths['best_prompt']}")


if __name__ == "__main__":
    main()
