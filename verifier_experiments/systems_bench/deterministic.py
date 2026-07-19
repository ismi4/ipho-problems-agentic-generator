"""Tier-0 / Tier-1 deterministic falsifiers over extracted solution text.

These are pattern+physics checks for the known 2023 Water-and-Objects structure.
They cost $0 at inference time. They can only refute, never certify.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass
from typing import Any


SUBPARTS = ["A.1", "B.1", "B.2", "B.3", "B.4", "B.5", "C.1", "C.2", "C.3"]


@dataclass
class CheckResult:
    check_id: str
    subpart: str
    status: str  # pass | fail | skip
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _norm(s: str) -> str:
    """Flatten unicode math italics / whitespace for stabler matching."""
    # NFKD splits 𝑒 → e + combining; drop combining marks
    out = []
    for ch in unicodedata.normalize("NFKD", s):
        if unicodedata.category(ch) == "Mn":
            continue
        out.append(ch)
    s2 = "".join(out)
    s2 = s2.replace("−", "-").replace("–", "-").replace("—", "-")
    s2 = s2.replace("𝑥", "x").replace("ℓ", "l").replace("𝛾", "gamma").replace("𝜌", "rho")
    s2 = s2.replace("θ", "theta").replace("𝜃", "theta").replace("γ", "gamma").replace("ρ", "rho")
    s2 = s2.replace("𝑓", "f").replace("𝑥", "x").replace("𝑣", "v").replace("𝑧", "z")
    s2 = s2.replace("𝐹", "F").replace("ₐ", "a").replace("₀", "0").replace("₁", "1").replace("₂", "2")
    s2 = re.sub(r"\s+", " ", s2)
    return s2


def _slice_subpart(text: str, sp: str) -> str:
    pat = re.compile(rf"(?:^|\n)\s*{re.escape(sp)}\b", re.MULTILINE)
    m = pat.search(text)
    if not m:
        return ""
    start = m.start()
    next_positions = []
    for o in SUBPARTS:
        if o == sp:
            continue
        mo = re.search(rf"(?:^|\n)\s*{re.escape(o)}\b", text[m.end() :], re.MULTILINE)
        if mo:
            next_positions.append(m.end() + mo.start())
    # Also cut at next Part header
    mo = re.search(r"(?:^|\n)\s*Part\s+[A-Z]\b", text[m.end() :], re.MULTILINE)
    if mo:
        next_positions.append(m.end() + mo.start())
    end = min(next_positions) if next_positions else len(text)
    return text[start:end]


def check_err1_numeric_A1(text: str) -> CheckResult:
    a1 = _slice_subpart(text, "A.1") or text
    n = _norm(a1)
    # Prefer boxed-style "v = 0.23 m/s" / "v = 0.31 m/s"
    ms = list(re.finditer(r"v\s*=\s*(0\.\d+)\s*m/s", n, flags=re.I))
    if not ms:
        return CheckResult("2_dimless_factor_A1", "A.1", "skip", "no numeric v found")
    val = float(ms[-1].group(1))
    # Exponent fingerprint: 2^{2/3} vs 2^{1/3}
    has_23 = bool(re.search(r"2\s*2/3|2\^\{?2/3\}?|22/3", n))
    has_13 = bool(re.search(r"2\s*1/3|2\^\{?1/3\}?|21/3", n))
    return CheckResult(
        "2_dimless_factor_A1",
        "A.1",
        "skip",
        f"observed v={val} m/s; exponent_fingerprint 2/3={has_23} 1/3={has_13}; "
        "dimensionless geometric factor not decidable by Tier-0/1",
    )


def check_err2_sign_B3(text: str) -> CheckResult:
    b3 = _slice_subpart(text, "B.3") or text
    n = _norm(b3).replace(" ", "")
    # Correct: fx = gammacostheta1 - gammacostheta2
    correct = bool(re.search(r"fx=gammacostheta1-gammacostheta2", n, re.I))
    faulty = bool(re.search(r"fx=gammacostheta2-gammacostheta1", n, re.I))
    # Also tolerate missing "gamma" duplication: fx=gammacostheta1-gammacostheta2
    if not correct:
        correct = bool(re.search(r"fx=.*costheta1.*-.*costheta2", n, re.I)) and not faulty
    if faulty and not re.search(r"fx=gammacostheta1-gammacostheta2", n, re.I):
        return CheckResult(
            "0.3_sign_direction",
            "B.3",
            "fail",
            "sign of f_x flipped vs force balance / B.2 leftward",
        )
    if re.search(r"fx=gammacostheta1-gammacostheta2", n, re.I):
        return CheckResult("0.3_sign_direction", "B.3", "pass", "f_x = γ cos θ1 − γ cos θ2")
    return CheckResult("0.3_sign_direction", "B.3", "skip", "could not parse B.3 boxed form")


def check_err3_dimensional_B4(text: str) -> CheckResult:
    b4 = _slice_subpart(text, "B.4") or text
    # Multi-line boxed forms in pdftotext:
    #   l = √
    #      ρg     (good)   or just ρ (bad)
    # Look at the boxed region after "B.4" points header
    m = re.search(r"B\.4[^\n]*\n(.*)$", b4, re.DOTALL)
    region = m.group(1) if m else b4[-400:]
    n = _norm(region)
    # Compact whitespace already done; check for sqrt(gamma/rhog) vs sqrt(gamma/rho)
    # Raw multiline: after ell = sqrt, next nonspace tokens
    raw = region
    # Find capillary length assignment near end
    if re.search(r"ℓ\s*=\s*√", raw) or re.search(r"l\s*=\s*√", n, re.I):
        # Take text after last ell = √
        idx = max(raw.rfind("ℓ = √"), raw.rfind("ℓ=√"), raw.lower().rfind("l = √"))
        after = raw[idx : idx + 80] if idx >= 0 else raw[-80:]
        after_n = _norm(after).replace(" ", "")
        if re.search(r"sqrt?\(?gamma/rho\)?$", after_n, re.I) or (
            "gamma" in after_n and "rho" in after_n and "g" not in after_n.replace("gamma", "")
        ):
            # more precise: denominator has rho but not g after rho
            if re.search(r"gamma/rho(?!g)", after_n, re.I) or (
                "rho" in after_n and not re.search(r"rhog|rho\*g|rho g", after_n, re.I)
            ):
                # Confirm it's the boxed answer (faulty doc has only rho under radical)
                if "rhog" not in after_n and not re.search(r"rho\s*g", _norm(after)):
                    return CheckResult(
                        "0.1_dimensional",
                        "B.4",
                        "fail",
                        "ℓ=√(γ/ρ) is dimensionally inconsistent (missing g)",
                    )
        if re.search(r"rhog|rho\*g|rho g|gamma/\(rhog\)|gamma/rhog", after_n, re.I) or re.search(
            r"rho\s*g", _norm(after)
        ):
            return CheckResult("0.1_dimensional", "B.4", "pass", "ℓ=√(γ/(ρg)) dimensionally OK")

    # Fallback line-based: last 6 lines
    lines = [ln.strip() for ln in region.splitlines() if ln.strip()]
    tail = " ".join(lines[-6:])
    tn = _norm(tail)
    if re.search(r"l\s*=\s*√", tn) and re.search(r"rho\s*g", tn):
        return CheckResult("0.1_dimensional", "B.4", "pass", "ℓ=√(γ/(ρg)) dimensionally OK")
    if re.search(r"l\s*=\s*√", tn) and re.search(r"\brho\b", tn) and not re.search(r"rho\s*g", tn):
        return CheckResult(
            "0.1_dimensional",
            "B.4",
            "fail",
            "ℓ=√(γ/ρ) is dimensionally inconsistent (missing g)",
        )
    return CheckResult("0.1_dimensional", "B.4", "skip", "could not locate capillary-length expression")


def check_err4_root_branch_B5(text: str) -> CheckResult:
    b5 = _slice_subpart(text, "B.5") or text
    n = _norm(b5).replace(" ", "")
    # Boxed forms:
    # clean: z(x)=-ltantheta0 e-x/l
    # faulty: z(x)=ltantheta0 ex/l
    decaying = bool(re.search(r"e-x/l", n, re.I)) or bool(re.search(r"e\^-x", n))
    growing = bool(re.search(r"ex/l", n, re.I)) or bool(re.search(r"e\^\+?x/l", n, re.I))
    # BC assignment fingerprint
    b_zero = bool(re.search(r"leads?toB=0|B=0", n))
    a_zero = bool(re.search(r"leads?toA=0|A=0", n))
    if (growing and not decaying) or (b_zero and not a_zero and "ex/l" in n.lower()):
        return CheckResult(
            "1.2_plugback_root_branch",
            "B.5",
            "fail",
            "retained growing branch e^{+x/ℓ}; diverges as x→∞, contradicting z(∞)=0",
        )
    if decaying and a_zero:
        return CheckResult("1.2_plugback_root_branch", "B.5", "pass", "decaying branch e^{-x/ℓ} retained")
    if decaying:
        return CheckResult("1.2_plugback_root_branch", "B.5", "pass", "decaying branch e^{-x/ℓ} retained")
    return CheckResult("1.2_plugback_root_branch", "B.5", "skip", "could not parse B.5 boxed z(x)")


def check_err5_symbol_whitelist_C2(text: str) -> CheckResult:
    c2 = _slice_subpart(text, "C.2") or text
    # Only the score-box region (points header), not the derivation (which mentions za/xa).
    m = re.search(r"(?:^|\n)\s*C\.2\s+\d", c2)
    region = c2[m.start() :] if m else c2[-400:]
    n = _norm(region)
    # Faulty: Fx = −2ρg za² / (e^(xa/ℓ) + e^(−xa/ℓ))²
    if re.search(r"\bza\b", n, re.I) or re.search(r"\bxa\b", n, re.I):
        return CheckResult(
            "0.5_symbol_whitelist",
            "C.2",
            "fail",
            "boxed F_x reintroduces za/xa (violates demanded symbol set; algebraically equivalent trap)",
        )
    # Clean: F_x = -1/2 ρ g z0^2
    if re.search(r"z0|z_0|z02", n, re.I) and re.search(r"F.?x|Fx", n):
        return CheckResult("0.5_symbol_whitelist", "C.2", "pass", "F_x uses z0 only")
    if re.search(r"1/2|½", n) and re.search(r"rho\s*g", n):
        return CheckResult("0.5_symbol_whitelist", "C.2", "pass", "F_x ≈ −½ρg z0² form present")
    return CheckResult("0.5_symbol_whitelist", "C.2", "skip", "could not locate C.2 boxed symbols")


def run_deterministic(solution_text: str) -> dict[str, Any]:
    checks = [
        check_err1_numeric_A1(solution_text),
        check_err2_sign_B3(solution_text),
        check_err3_dimensional_B4(solution_text),
        check_err4_root_branch_B5(solution_text),
        check_err5_symbol_whitelist_C2(solution_text),
    ]
    fails = [c for c in checks if c.status == "fail"]
    return {
        "checks": [c.to_dict() for c in checks],
        "n_fail": len(fails),
        "failed_subparts": sorted({c.subpart for c in fails}),
        "verdict_hint": "REJECT" if fails else "NO_DETERMINISTIC_REJECT",
    }
