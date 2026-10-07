from __future__ import annotations

import hashlib
import json
import os
import re
import time
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from llm.config import estimate_cost, get_run_budget_usd, resolve_model
from schemas.run_record import RunRecord

DEFAULT_PROMPTS_DIR = Path(__file__).parent / "prompts"

T = TypeVar("T", bound=BaseModel)

MAX_RETRIES = 2  # per specs/00-foundations.md: "Retries on validation error (max 2)"


class BudgetExceededError(Exception):
    pass


class LLMValidationError(Exception):
    def __init__(self, message: str, attempts: int):
        super().__init__(message)
        self.attempts = attempts


def _load_prompt(prompt_id: str, prompts_dir: Path) -> str:
    path = prompts_dir / f"{prompt_id}.md"
    if not path.exists():
        raise FileNotFoundError(f"no prompt file for '{prompt_id}' at {path}")
    return path.read_text()


def _prompt_version(prompt_id: str, prompts_dir: Path) -> str:
    """Content hash stands in for a version string until prompts carry explicit
    frontmatter versions (not needed by any Foundations prompt yet)."""
    return hashlib.sha256(_load_prompt(prompt_id, prompts_dir).encode()).hexdigest()[:12]


def _render(template: str, variables: dict[str, Any]) -> str:
    return template.format(**variables)


def _extract_json(text: str) -> dict:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    raise ValueError(f"could not find JSON object in LLM response: {text[:200]!r}")


def _call_anthropic(model: str, system: str, user_content: str) -> tuple[str, int, int]:
    """Isolated so tests can monkeypatch this one function instead of the SDK."""
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    response = client.messages.create(
        model=model,
        max_tokens=16000,
        system=system,
        messages=[{"role": "user", "content": user_content}],
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    return text, response.usage.input_tokens, response.usage.output_tokens


def call(
    prompt_id: str,
    variables: dict[str, Any],
    output_model: type[T],
    model_tier: str = "standard",
    *,
    module: str = "unknown",
    run_record_repo=None,
    validation_context: dict[str, Any] | None = None,
    prompts_dir: Path | None = None,
) -> T:
    """Render prompt_id with variables, call the LLM, validate into output_model.

    Retries up to MAX_RETRIES times on a Pydantic ValidationError, appending the
    error to the prompt each time. Always writes a RunRecord (via run_record_repo,
    if given) — on success or on final failure. Enforces NUDGE_RUN_BUDGET_USD.

    `validation_context` is passed through to `output_model.model_validate(...,
    context=...)`, so a model_validator can reject things Pydantic's type system
    alone can't catch — e.g. M1's synthesiser checks every cited evidence_id
    actually exists, turning a hallucinated ID into a validation error that
    triggers the same retry-with-error-appended path as any other bad output.

    `prompts_dir` defaults to llm/prompts/ but per CLAUDE.md's convention
    ("All agent prompts in agents/<mod>/prompts/*.md"), a module agent passes
    its own `Path(__file__).parent / "prompts"`.
    """
    prompts_dir = prompts_dir or DEFAULT_PROMPTS_DIR
    template = _load_prompt(prompt_id, prompts_dir)
    base_prompt = _render(template, variables)
    model = resolve_model(model_tier)
    schema_instruction = (
        "\n\nRespond with ONLY a JSON object matching this JSON Schema, no prose:\n"
        f"{json.dumps(output_model.model_json_schema())}"
    )
    system = "You are a precise assistant that only outputs valid JSON matching the given schema."

    budget = get_run_budget_usd()
    total_tokens_in = 0
    total_tokens_out = 0
    total_cost = 0.0
    start = time.monotonic()
    last_error: Exception | None = None
    prompt = base_prompt + schema_instruction

    for attempt in range(MAX_RETRIES + 1):
        text, tokens_in, tokens_out = _call_anthropic(model, system, prompt)
        total_tokens_in += tokens_in
        total_tokens_out += tokens_out
        total_cost += estimate_cost(model_tier, tokens_in, tokens_out)

        if total_cost > budget:
            _log_run_record(
                run_record_repo, module, prompt_id, variables, model,
                total_tokens_in, total_tokens_out, total_cost, start, prompts_dir,
                error=f"budget exceeded: ${total_cost:.4f} > ${budget:.4f}",
            )
            raise BudgetExceededError(
                f"run cost ${total_cost:.4f} exceeded NUDGE_RUN_BUDGET_USD=${budget:.4f}"
            )

        try:
            data = _extract_json(text)
            result = output_model.model_validate(data, context=validation_context)
            _log_run_record(
                run_record_repo, module, prompt_id, variables, model,
                total_tokens_in, total_tokens_out, total_cost, start, prompts_dir,
                output_ids=[result.id] if hasattr(result, "id") else [],
            )
            return result
        except (ValidationError, ValueError, json.JSONDecodeError) as e:
            last_error = e
            prompt = (
                f"{base_prompt}\n\nYour previous response was invalid: {e}\n"
                f"Previous response:\n{text}\n{schema_instruction}"
            )

    _log_run_record(
        run_record_repo, module, prompt_id, variables, model,
        total_tokens_in, total_tokens_out, total_cost, start, prompts_dir,
        error=str(last_error),
    )
    raise LLMValidationError(
        f"failed to get valid {output_model.__name__} after {MAX_RETRIES + 1} attempts: {last_error}",
        attempts=MAX_RETRIES + 1,
    )


def _log_run_record(
    run_record_repo,
    module: str,
    prompt_id: str,
    variables: dict[str, Any],
    model: str,
    tokens_in: int,
    tokens_out: int,
    cost: float,
    start: float,
    prompts_dir: Path,
    output_ids: list | None = None,
    error: str | None = None,
) -> RunRecord:
    inputs_hash = hashlib.sha256(
        json.dumps(variables, sort_keys=True, default=str).encode()
    ).hexdigest()[:16]
    record = RunRecord(
        module=module,
        inputs_hash=inputs_hash,
        prompt_versions={prompt_id: _prompt_version(prompt_id, prompts_dir)},
        model=model,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost=cost,
        duration_ms=int((time.monotonic() - start) * 1000),
        output_ids=output_ids or [],
        error=error,
    )
    if run_record_repo is not None:
        return run_record_repo.add(record)
    return record
