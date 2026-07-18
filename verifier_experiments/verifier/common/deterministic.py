"""Deterministic (non-LLM, $0-token) checkers: SymPy symbolic equivalence and
Pint unit/dimension checks. Used by dataset curation and Solution B's Tier-0/1.

Per-sub-part outcome is one of:
  PASS      - deterministic certifier says candidate matches the reference
  FAIL      - deterministic falsifier says candidate is wrong (confident REJECT)
  ESCALATE  - no algebraic handle (qualitative deliverable / parse failure) ->
              must be sent to an LLM (Tier-2)
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import sympy as sp
from pint import UnitRegistry

_UREG = UnitRegistry()

PASS, FAIL, ESCALATE = "PASS", "FAIL", "ESCALATE"

# Local names allowed inside sympify (so Rational/sqrt/exp/tan/pi resolve).
_SYMPY_LOCALS = {
    "Rational": sp.Rational,
    "sqrt": sp.sqrt,
    "exp": sp.exp,
    "tan": sp.tan,
    "sin": sp.sin,
    "cos": sp.cos,
    "log": sp.log,
    "pi": sp.pi,
}


@dataclass
class CheckResult:
    subpart_id: str
    outcome: str  # PASS | FAIL | ESCALATE
    method: str
    detail: str
    cpu_s: float


def _sympify(expr: str, symbols: list[str]):
    locs = dict(_SYMPY_LOCALS)
    for s in symbols:
        locs[s] = sp.Symbol(s, positive=True)
    return sp.sympify(expr, locals=locs)


def symbolic_equivalent(ref_expr: str, cand_expr: str, symbols: list[str]) -> bool:
    """SymPy equivalence via symbolic simplification + numeric substitution."""
    r = _sympify(ref_expr, symbols)
    c = _sympify(cand_expr, symbols)
    diff = sp.simplify(r - c)
    if diff == 0:
        return True
    # Numeric-substitution fallback (robust for messy forms): random positive pts.
    syms = sorted(r.free_symbols | c.free_symbols, key=str)
    import random

    rng = random.Random(12345)
    for _ in range(6):
        subs = {s: sp.Float(rng.uniform(0.3, 2.5)) for s in syms}
        try:
            rv = complex(r.evalf(subs=subs))
            cv = complex(c.evalf(subs=subs))
        except (TypeError, ValueError):
            return False
        if abs(rv - cv) > 1e-6 * (1 + abs(rv)):
            return False
    return True


def _unit_dimensionality(unit: str):
    try:
        return _UREG.parse_expression(unit).dimensionality if unit else None
    except Exception:  # noqa: BLE001
        return "PARSE_ERROR"


def numeric_ok(ref: dict[str, Any], cand: dict[str, Any]) -> tuple[bool, str]:
    """Tier-0 numeric check: unit presence + unit dimension + tolerance."""
    requires_unit = cand.get("requires_unit", False) or bool(ref.get("unit"))
    if not ref.get("dimensionless", False) and requires_unit and not cand.get("unit"):
        return False, "unit missing (required)"
    ru, cu = ref.get("unit", ""), cand.get("unit", "")
    if ru and cu:
        rd, cd = _unit_dimensionality(ru), _unit_dimensionality(cu)
        if rd == "PARSE_ERROR" or cd == "PARSE_ERROR":
            return False, "unit parse error"
        if rd != cd:
            return False, f"unit dimension mismatch ({cu} vs {ru})"
    tol = ref.get("tol", abs(ref["value"]) * 0.02)
    if abs(cand["value"] - ref["value"]) > tol:
        return False, f"value {cand['value']} outside {ref['value']}±{tol}"
    return True, "numeric within tolerance, units consistent"


def check_subpart(
    subpart: dict[str, Any], cand_answer: dict[str, Any], tier0_only: bool = False
) -> CheckResult:
    """Run the deterministic stack on one sub-part.

    tier0_only=True restricts to Tier-0 falsifiers (Pint units/dimension +
    numeric tolerance); symbolic sub-parts then ESCALATE (Tier-1 SymPy skipped).
    """
    t0 = time.process_time()
    ref = subpart["answer"]
    sid = subpart["id"]
    kind = subpart["kind"]

    if kind == "qualitative" or ref["type"] == "qualitative":
        return CheckResult(sid, ESCALATE, "qualitative",
                           "no algebraic form -> Tier-2", time.process_time() - t0)

    if ref["type"] == "numeric":
        ok, detail = numeric_ok(ref, cand_answer)
        return CheckResult(sid, PASS if ok else FAIL, "pint+tolerance", detail,
                           time.process_time() - t0)

    if ref["type"] == "symbolic":
        if tier0_only:
            return CheckResult(sid, ESCALATE, "tier0",
                               "symbolic form deferred to Tier-1/LLM",
                               time.process_time() - t0)
        if cand_answer.get("type") != "symbolic":
            return CheckResult(sid, FAIL, "sympy", "candidate not symbolic",
                               time.process_time() - t0)
        try:
            eq = symbolic_equivalent(ref["expr"], cand_answer["expr"], ref["symbols"])
        except Exception as e:  # noqa: BLE001 - unparseable -> escalate
            return CheckResult(sid, ESCALATE, "sympy",
                               f"parse/simplify error: {e}", time.process_time() - t0)
        return CheckResult(sid, PASS if eq else FAIL, "sympy",
                           "symbolic-equivalent" if eq else "not equivalent to reference",
                           time.process_time() - t0)

    return CheckResult(sid, ESCALATE, "none", "unknown answer type",
                       time.process_time() - t0)
