"""Ingestion ladder: I1 (text) and I2/I4 (vision → Markdown+LaTeX / typed IR)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .client import TrackedClient, image_message_parts
from .pdf_util import pdf_to_png_pages, pdf_to_text

I4_SCHEMA_HINT = """
Return ONLY a JSON object with this shape:
{
  "markdown": "<full Markdown+LaTeX transcription of the PDF>",
  "sub_parts": [
    {
      "id": "A.1",
      "title": "...",
      "givens": [{"symbol":"a","unit":"m","value":null,"note":"..."}],
      "equations": [{"latex":"...","label":"S3.2"}],
      "asked_quantity": "...",
      "answer_type": "numeric_with_units|symbolic|dimensionless_exponent|show_that|other",
      "boxed_answer": "...",
      "boundary_conditions": ["..."],
      "figure_refs": ["..."],
      "provenance_span": "short quote or page cue"
    }
  ],
  "notes": "any transcription uncertainty"
}
""".strip()


def ingest_i1(pdf_path: Path) -> dict[str, Any]:
    text = pdf_to_text(pdf_path)
    return {
        "rung": "I1",
        "pdf": str(pdf_path),
        "text": text,
        "n_chars": len(text),
        "cost_usd": 0.0,
        "retries": 0,
    }


def _parse_json_content(content: str) -> dict[str, Any]:
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", content, re.DOTALL)
        if m:
            return json.loads(m.group(0))
        raise


def ingest_vision(
    client: TrackedClient,
    pdf_path: Path,
    *,
    model: str,
    rung: str,
    work_dir: Path,
    purpose: str,
    typed_ir: bool,
    max_retries: int = 1,
    reasoning_effort: str = "low",
) -> dict[str, Any]:
    """I2 (markdown) or I4 (typed semantic IR). Optional one retry on parse failure."""
    pages_dir = work_dir / pdf_path.stem
    pages = pdf_to_png_pages(pdf_path, pages_dir, dpi=140)
    instruction = (
        "You are ingesting an IPhO theory PDF into a structured artifact for a solution verifier.\n"
        "Transcribe ALL math carefully as LaTeX. Preserve boxed answers and equation numbers.\n"
    )
    if typed_ir:
        instruction += "Produce a typed semantic IR.\n" + I4_SCHEMA_HINT
    else:
        instruction += (
            "Return ONLY JSON: {\"markdown\": \"...full transcription...\", \"notes\": \"...\"}"
        )

    last_err = None
    retries = 0
    total_cost = 0.0
    calls = []
    for attempt in range(max_retries + 1):
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": instruction + f"\nPDF: {pdf_path.name}; pages={len(pages)}"},
                    *image_message_parts(pages, detail="high"),
                ],
            }
        ]
        resp = client.chat(
            model=model,
            messages=messages,
            purpose=purpose,
            max_completion_tokens=12000,
            reasoning_effort=reasoning_effort,
            meta={"pdf": pdf_path.name, "rung": rung, "attempt": attempt, "n_pages": len(pages)},
        )
        total_cost += resp["cost_usd"]
        calls.append(resp["call_id"])
        try:
            parsed = _parse_json_content(resp["content"])
            return {
                "rung": rung,
                "pdf": str(pdf_path),
                "model": model,
                "n_pages": len(pages),
                "retries": retries,
                "cost_usd": total_cost,
                "call_ids": calls,
                "ir": parsed,
                "markdown": parsed.get("markdown", ""),
                "sub_parts": parsed.get("sub_parts", []),
                "raw_content": resp["content"],
            }
        except Exception as e:
            last_err = e
            retries += 1
    return {
        "rung": rung,
        "pdf": str(pdf_path),
        "model": model,
        "n_pages": len(pages),
        "retries": retries,
        "cost_usd": total_cost,
        "call_ids": calls,
        "error": str(last_err),
        "ir": None,
        "markdown": "",
        "sub_parts": [],
        "raw_content": "",
    }
