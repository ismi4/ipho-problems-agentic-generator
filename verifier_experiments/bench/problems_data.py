"""Faithful, machine-checkable transcriptions of 3 IPhO mechanics problems and
the single-fault variants injected to build the labeled gold set.

Each sub-part carries a canonical `answer` object so that BOTH deterministic
checkers (Pint/SymPy) and LLM verifiers can operate against a reference rubric,
while the per-instance ACCEPT/REJECT label stays hidden from the verifier.

Answer object types
-------------------
  symbolic : {"type":"symbolic","expr":"<sympy>","symbols":[...]}
  numeric  : {"type":"numeric","value":float,"unit":"<str>","tol":float,
              "dimensionless":bool}
  qualitative : {"type":"qualitative","desc":"<str>"}   # no algebraic form

Provenance: pdftotext -layout dumps in dataset/problems/ (official IPhO
problem + solution PDFs, https://ipho.olimpicos.net/).
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

# --------------------------------------------------------------------------
# Problem 1 — Cox's Timepiece (IPhO 2025, Q2/S2)
# --------------------------------------------------------------------------
COX = {
    "key": "cox_timepiece_2025",
    "title": "Cox's Timepiece",
    "year": 2025,
    "qs": "Q2/S2",
    "statement": (
        "Cox's clock is driven by atmospheric-pressure fluctuations moving mercury "
        "between vessels. Gravity g is uniform (g = 9.8 m/s^2, downward -u_z); liquids "
        "are incompressible with density rho; surface tension is neglected; transformations "
        "are isothermal at ambient T_a.\n"
        "Part A: A vertical cylindrical tube (length H = 1 m, cross-section S = 10 cm^2, "
        "mass m = 0.5 kg, top closed, bottom open) is dipped in a bath (surface z=0). h is the "
        "altitude of the tube top; z_l the water level inside. P_0 = 1.000e5 Pa external.\n"
        "A.1 In configuration (b) express water pressure P_w at the tube top and the force F "
        "needed to hold the tube, in terms of P_0, rho, m, S, h, g, u_z.\n"
        "A.2 For experiments 1,2,3 (water at 20/80/99 C; P_sat = 2.34e3 / 47.4e3 / 99.8e3 Pa; "
        "rho = 1.00e3/0.97e3/0.96e3) classify behaviour A vs B and give F_max (and h* if B). "
        "Behaviour B occurs when h* = (P_0 - P_sat)/(rho g) < H.\n"
        "A.3 With mercury (rho=13.5e3, P_sat=0.163 Pa), express and evaluate the relative error "
        "epsilon from neglecting P_sat vs P_0 in F_max."
    ),
    "subparts": [
        {
            "id": "A.1",
            "points": 0.2,
            "statement": "Force F to hold the tube (case b).",
            "kind": "symbolic",
            "answer": {"type": "symbolic", "expr": "(m + rho*S*h)*g",
                       "symbols": ["m", "rho", "S", "h", "g"]},
            "dimension": "[M L T^-2]",
        },
        {
            "id": "A.2",
            "points": 0.8,
            "statement": "Behaviour classification A/A/B for the three experiments.",
            "kind": "qualitative",
            "answer": {"type": "qualitative",
                       "desc": "Experiments 1,2 -> behaviour A; experiment 3 -> behaviour B "
                               "(regime classification, all-or-nothing)."},
        },
        {
            "id": "A.2b",
            "points": 0.4,
            "statement": "Numerical F_max for experiment 1.",
            "kind": "numeric",
            "answer": {"type": "numeric", "value": 14.7, "unit": "N", "tol": 0.4,
                       "dimensionless": False},
        },
        {
            "id": "A.3",
            "points": 0.3,
            "statement": "Relative error epsilon = P_sat/(P_0 + m g / S) for mercury.",
            "kind": "dimensionless_numeric",
            "answer": {"type": "numeric", "value": 1.6e-6, "unit": "", "tol": 0.6e-6,
                       "dimensionless": True},
        },
    ],
}

# --------------------------------------------------------------------------
# Problem 2 — Black Widow Pulsar (IPhO 2024, Q3/S3)
# --------------------------------------------------------------------------
PULSAR = {
    "key": "black_widow_pulsar_2024",
    "title": "Black Widow Pulsar",
    "year": 2024,
    "qs": "Q3/S3",
    "statement": (
        "A binary system: masses M1, M2 separated by a, center of mass at origin, "
        "a1 = M2 a/M, a2 = M1 a/M, M = M1+M2, angular velocity omega = sqrt(G M / a^3).\n"
        "A.3 With M1:M2 = 3:1, the middle Lagrange point (between xbar=0 and 0.75) is x0/a "
        "(dimensionless), found numerically.\n"
        "A.4 Mass transfer at rate beta gives orbit decay a_dot and period change P_dot, "
        "with J = mu a^2 omega conserved-quantity analysis (angular momentum).\n"
        "A.5 A thin accretion ring in equilibrium radiates; find its temperature T(r).\n"
        "Part B: stellar hydrostatic stability. B.3 dimensional analysis for a length scale r0 "
        "from G, p_c, rho_c. B.9 radial-oscillation stability -> gamma_min and angular "
        "frequency omega of oscillations for polytrope index gamma."
    ),
    "subparts": [
        {
            "id": "A.3",
            "points": 0.5,
            "statement": "Middle Lagrange point x0/a (dimensionless numeric).",
            "kind": "dimensionless_numeric",
            "answer": {"type": "numeric", "value": 0.36, "unit": "", "tol": 0.02,
                       "dimensionless": True},
        },
        {
            "id": "A.4",
            "points": 0.6,
            "statement": "Orbit decay a_dot from angular-momentum conservation.",
            "kind": "symbolic",
            "answer": {"type": "symbolic", "expr": "-2*beta*a*(1/M1 - 1/M2)",
                       "symbols": ["beta", "a", "M1", "M2"]},
        },
        {
            "id": "A.5",
            "points": 1.0,
            "statement": "Equilibrium ring temperature T(r).",
            "kind": "symbolic",
            "answer": {"type": "symbolic", "expr": "(G*M1*beta/(8*pi*sigma*r**3))**(Rational(1,4))",
                       "symbols": ["G", "M1", "beta", "sigma", "r"]},
            "dimension": "[Theta]",
        },
        {
            "id": "B.3",
            "points": 0.4,
            "statement": "Length scale r0 by dimensional analysis of G, p_c, rho_c.",
            "kind": "symbolic",
            "answer": {"type": "symbolic",
                       "expr": "G**(Rational(-1,2))*pc**(Rational(1,2))*rhoc**(-1)",
                       "symbols": ["G", "pc", "rhoc"]},
            "dimension": "[L]",
        },
        {
            "id": "B.9",
            "points": 0.6,
            "statement": "Radial-oscillation stability threshold gamma_min.",
            "kind": "dimensionless_numeric",
            "answer": {"type": "numeric", "value": 1.3333333, "unit": "", "tol": 0.01,
                       "dimensionless": True},
        },
    ],
}

# --------------------------------------------------------------------------
# Problem 3 — Water and Objects (IPhO 2023, Q3/S3)
# --------------------------------------------------------------------------
WATER = {
    "key": "water_and_objects_2023",
    "title": "Water and Objects",
    "year": 2023,
    "qs": "Q3/S3",
    "statement": (
        "Surface-tension statics with gravity. gamma is surface tension, rho density, g gravity.\n"
        "A.1 Two drops of radius a merge; fraction k=0.06 of released surface energy becomes "
        "kinetic energy; find the jump speed v (M = 8 pi a^3 rho/3).\n"
        "Part B: a vertical board partially wets water. B.2 horizontal pressure force f_x on a "
        "water column between depths z1<z2. B.4 the conserved combination gives capillary length "
        "ell and exponent a in (1/2)(z/ell)^a + cos theta = const. B.5 surface profile z(x) with "
        "boundary conditions z(inf)=0, z'(0)=tan theta0.\n"
        "Part C: two rods on water attract; C.2 horizontal force F_x on a rod in terms of the "
        "midpoint displacement z0 (symmetry-breaking parameter)."
    ),
    "subparts": [
        {
            "id": "A.1",
            "points": 2.0,
            "statement": "Jump speed v after drop merger (numeric).",
            "kind": "numeric",
            "answer": {"type": "numeric", "value": 0.232, "unit": "m/s", "tol": 0.02,
                       "dimensionless": False},
        },
        {
            "id": "B.2",
            "points": 0.8,
            "statement": "Horizontal pressure force f_x on the water column.",
            "kind": "symbolic",
            "answer": {"type": "symbolic", "expr": "Rational(1,2)*rho*g*(z2**2 - z1**2)",
                       "symbols": ["rho", "g", "z1", "z2"]},
            "dimension": "[M T^-2]",
        },
        {
            "id": "B.4",
            "points": 0.8,
            "statement": "Capillary length ell (conservation-law combination).",
            "kind": "symbolic",
            "answer": {"type": "symbolic", "expr": "sqrt(gamma/(rho*g))",
                       "symbols": ["gamma", "rho", "g"]},
            "dimension": "[L]",
        },
        {
            "id": "B.5",
            "points": 1.5,
            "statement": "Surface profile z(x) from boundary conditions.",
            "kind": "symbolic",
            "answer": {"type": "symbolic", "expr": "-ell*tan(theta0)*exp(-x/ell)",
                       "symbols": ["ell", "theta0", "x"]},
        },
        {
            "id": "C.2",
            "points": 1.5,
            "statement": "Horizontal force F_x on a rod (symmetry-breaking z0).",
            "kind": "symbolic",
            "answer": {"type": "symbolic", "expr": "-Rational(1,2)*rho*g*z0**2",
                       "symbols": ["rho", "g", "z0"]},
            "dimension": "[M T^-2]",
        },
    ],
}

PROBLEMS = {p["key"]: p for p in (COX, PULSAR, WATER)}


# --------------------------------------------------------------------------
# Fault catalogue: (fault_type, target_subpart, faulted_answer).
# Each entry injects exactly ONE documented fault into the correct solution,
# yielding a REJECT instance whose failing sub-part is known by construction.
# --------------------------------------------------------------------------
FAULTS: dict[str, list[dict[str, Any]]] = {
    "cox_timepiece_2025": [
        {"fault": "sign_flip", "subpart": "A.1",
         "answer": {"type": "symbolic", "expr": "(m - rho*S*h)*g",
                    "symbols": ["m", "rho", "S", "h", "g"]}},
        {"fault": "dropped_term", "subpart": "A.1",
         "answer": {"type": "symbolic", "expr": "rho*S*h*g",
                    "symbols": ["m", "rho", "S", "h", "g"]}},
        {"fault": "wrong_constant", "subpart": "A.2b",
         "answer": {"type": "numeric", "value": 20.0, "unit": "N", "tol": 0.4,
                    "dimensionless": False}},
        {"fault": "unit_dropped", "subpart": "A.2b",
         "answer": {"type": "numeric", "value": 14.7, "unit": "", "tol": 0.4,
                    "dimensionless": False, "requires_unit": True}},
        {"fault": "regime_misclassification", "subpart": "A.2",
         "answer": {"type": "qualitative",
                    "desc": "Experiments 1,2,3 all -> behaviour A (WRONG: exp 3 is B)."}},
        {"fault": "dimensionless_factor", "subpart": "A.3",
         "answer": {"type": "numeric", "value": 3.2e-6, "unit": "", "tol": 0.6e-6,
                    "dimensionless": True}},
        {"fault": "geometric_factor", "subpart": "A.1",
         "answer": {"type": "symbolic", "expr": "(m + 2*rho*S*h)*g",
                    "symbols": ["m", "rho", "S", "h", "g"]}},
        {"fault": "wrong_law", "subpart": "A.1",
         "answer": {"type": "symbolic", "expr": "(m + rho*S*h**2)*g",
                    "symbols": ["m", "rho", "S", "h", "g"]}},
        {"fault": "wrong_constant_numeric", "subpart": "A.2b",
         "answer": {"type": "numeric", "value": 11.0, "unit": "N", "tol": 0.4,
                    "dimensionless": False}},
    ],
    "black_widow_pulsar_2024": [
        {"fault": "sign_flip", "subpart": "A.4",
         "answer": {"type": "symbolic", "expr": "2*beta*a*(1/M1 - 1/M2)",
                    "symbols": ["beta", "a", "M1", "M2"]}},
        {"fault": "geometric_factor", "subpart": "A.4",
         "answer": {"type": "symbolic", "expr": "-beta*a*(1/M1 - 1/M2)",
                    "symbols": ["beta", "a", "M1", "M2"]}},
        {"fault": "wrong_exponent", "subpart": "A.5",
         "answer": {"type": "symbolic", "expr": "(G*M1*beta/(8*pi*sigma*r**3))**(Rational(1,2))",
                    "symbols": ["G", "M1", "beta", "sigma", "r"]}},
        {"fault": "dimensional_error", "subpart": "B.3",
         "answer": {"type": "symbolic",
                    "expr": "G**(Rational(-1,2))*pc**(Rational(1,2))*rhoc**(-2)",
                    "symbols": ["G", "pc", "rhoc"]}},
        {"fault": "dimensionless_factor", "subpart": "A.3",
         "answer": {"type": "numeric", "value": 0.30, "unit": "", "tol": 0.02,
                    "dimensionless": True}},
        {"fault": "wrong_constant", "subpart": "B.9",
         "answer": {"type": "numeric", "value": 0.75, "unit": "", "tol": 0.01,
                    "dimensionless": True}},
        {"fault": "dropped_term", "subpart": "A.4",
         "answer": {"type": "symbolic", "expr": "-2*beta*a*(1/M1)",
                    "symbols": ["beta", "a", "M1", "M2"]}},
        {"fault": "wrong_law", "subpart": "A.5",
         "answer": {"type": "symbolic", "expr": "G*M1*beta/(8*pi*sigma*r**3)",
                    "symbols": ["G", "M1", "beta", "sigma", "r"]}},
        {"fault": "dimensionless_factor_2", "subpart": "B.9",
         "answer": {"type": "numeric", "value": 1.6666667, "unit": "", "tol": 0.01,
                    "dimensionless": True}},
    ],
    "water_and_objects_2023": [
        {"fault": "wrong_constant", "subpart": "A.1",
         "answer": {"type": "numeric", "value": 0.33, "unit": "m/s", "tol": 0.02,
                    "dimensionless": False}},
        {"fault": "unit_dropped", "subpart": "A.1",
         "answer": {"type": "numeric", "value": 0.232, "unit": "", "tol": 0.02,
                    "dimensionless": False, "requires_unit": True}},
        {"fault": "geometric_factor", "subpart": "B.2",
         "answer": {"type": "symbolic", "expr": "rho*g*(z2**2 - z1**2)",
                    "symbols": ["rho", "g", "z1", "z2"]}},
        {"fault": "sign_flip", "subpart": "C.2",
         "answer": {"type": "symbolic", "expr": "Rational(1,2)*rho*g*z0**2",
                    "symbols": ["rho", "g", "z0"]}},
        {"fault": "wrong_bc_constant", "subpart": "B.5",
         "answer": {"type": "symbolic", "expr": "ell*tan(theta0)*exp(-x/ell)",
                    "symbols": ["ell", "theta0", "x"]}},
        {"fault": "dropped_term", "subpart": "B.2",
         "answer": {"type": "symbolic", "expr": "Rational(1,2)*rho*g*z2**2",
                    "symbols": ["rho", "g", "z1", "z2"]}},
        {"fault": "dimensional_error", "subpart": "B.4",
         "answer": {"type": "symbolic", "expr": "gamma/(rho*g)",
                    "symbols": ["gamma", "rho", "g"]}},
        {"fault": "wrong_law", "subpart": "B.5",
         "answer": {"type": "symbolic", "expr": "-ell*tan(theta0)*exp(x/ell)",
                    "symbols": ["ell", "theta0", "x"]}},
        {"fault": "conservation_violation", "subpart": "C.2",
         "answer": {"type": "symbolic", "expr": "-rho*g*z0**2",
                    "symbols": ["rho", "g", "z0"]}},
    ],
}


def _answer_to_text(ans: dict[str, Any]) -> str:
    t = ans["type"]
    if t == "symbolic":
        return f"Answer (symbolic): {ans['expr']}"
    if t == "numeric":
        if ans.get("unit"):
            return f"Answer (numeric): {ans['value']} {ans['unit']}"
        return f"Answer (numeric): {ans['value']}"
    if t == "qualitative":
        return f"Answer (qualitative): {ans['desc']}"
    return "Answer: (unknown)"


def render_candidate(problem: dict[str, Any], subpart_answers: dict[str, dict]) -> str:
    """Render a full candidate solution text from per-sub-part answer objects."""
    lines = [f"Candidate solution for '{problem['title']}' (IPhO {problem['year']}):"]
    for sp in problem["subparts"]:
        ans = subpart_answers[sp["id"]]
        lines.append(f"\n[{sp['id']}] {sp['statement']}")
        lines.append(f"  Working: derived per the governing physics for {sp['id']}.")
        lines.append(f"  {_answer_to_text(ans)}")
    return "\n".join(lines)


def reference_rubric(problem: dict[str, Any]) -> str:
    """Reference answer key handed to the verifier (rubric); NOT the gold label."""
    lines = [f"Reference answer key for '{problem['title']}' (full marks):"]
    for sp in problem["subparts"]:
        lines.append(f"[{sp['id']}] ({sp['points']} pt) {_answer_to_text(sp['answer'])}")
    return "\n".join(lines)


def correct_subpart_answers(problem: dict[str, Any]) -> dict[str, dict]:
    return {sp["id"]: deepcopy(sp["answer"]) for sp in problem["subparts"]}
