# Injected-Error Test Set for the Solution Verifier

A labelled fault set for validating the verifier described in [`DEFINITION.MD`](DEFINITION.MD).
Two genuine IPhO reference solutions were edited to contain **ten faults of ten
distinct types**, five per document. Everything not listed below is unchanged
from the official PDF.

This is the "injected faults" half of open decision **§8.2** of `DEFINITION.MD`
("measure ... the false-accept rate on injected faults, esp. faithfulness drifts
and dimensionless-factor errors").

---

## 1. Corpus

`pdfs/` holds the pristine downloads from <https://ipho.olimpicos.net/> (`pdf/IPhO_YYYY_{Q,S}n.pdf`) —
both the problem statement `Q` and the solution `S` for each anchor problem, since
faithfulness (condition **IV**) can only be judged against `P`:

| Year | Problem | Files |
|---|---|---|
| 2025 | Cox's Timepiece | `IPhO_2025_Q2.pdf`, `IPhO_2025_S2.pdf` |
| 2024 | Black Widow Pulsar | `IPhO_2024_Q3.pdf`, `IPhO_2024_S3.pdf` |
| 2023 | Water and Objects | `IPhO_2023_Q3.pdf`, `IPhO_2023_S3.pdf` |
| 2022 | Scaling Laws | `IPhO_2022_Q3.pdf`, `IPhO_2022_S3.pdf` |
| 2021 | Planetary Physics | `IPhO_2021_Q1.pdf`, `IPhO_2021_S1.pdf` |
| 2020 | Anisotropic Friction | `IPhO_2020_Q2.pdf`, `IPhO_2020_S2.pdf` |

`pdfs/faulty/` holds the two edited solutions:

- `IPhO_2023_S3_FAULTY.pdf` — errors 1–5
- `IPhO_2021_S1_FAULTY.pdf` — errors 6–10

**Why these two.** Both are official LaTeX-set PDFs with clean, reliable text
extraction (the 2020 solution is an HTML-print with MathJax fragments scattered
out of reading order, and the 2024 one is Word-set). Between them they cover
capillary/surface-tension statics, energy conservation, hydrostatic equilibrium/
isostasy, dimensional analysis and ray propagation — a wide enough physics span
that the ten faults are not all of one flavour.

### Scope note: why no ILL-POSED case

`DEFINITION.MD` §0 treats **(I) well-posedness** as a property of the *problem*
`P`, emitted as a distinct `ILL-POSED` verdict for which "correctness of `S` is
undefined". Only solution PDFs were edited here, so condition (I) is
deliberately unrepresented. A well-posedness fault set would require editing the
`Q` PDFs and is a separate exercise.

---

## 2. The ten errors

| # | Doc | Part | Error type | Condition | Cheapest check that fires |
|---|---|---|---|---|---|
| 1 | 2023 S3 | A.1 | Dimensionless geometric factor | III | **Tier 2 only** |
| 2 | 2023 S3 | B.3 | Sign / direction flip | III | Tier 0.3 |
| 3 | 2023 S3 | B.4 | Dimensional inconsistency | III | Tier 0.1 |
| 4 | 2023 S3 | B.5 | Wrong BC / root branch | III | Tier 1.2 |
| 5 | 2023 S3 | C.2 | Symbol-whitelist violation | V | Tier 0.5 |
| 6 | 2021 S1 | A.1 | Faithfulness drift `P→S` | **IV** | **Tier 2.5 only** |
| 7 | 2021 S1 | A.4 | Wrong retained order | II | **Tier 2.4 only** |
| 8 | 2021 S1 | A.5 | Right-answer-wrong-reasoning | III | **Tier 2.1 only** |
| 9 | 2021 S1 | B.2 | Conservation / energy-budget violation | II | Tier 1.3 |
| 10 | 2021 S1 | B.3 | Completeness — answer never delivered | V | checklist |

Condition coverage: **II** ×2, **III** ×5, **IV** ×1, **V** ×2.
Five faults are cheap-detectable (Tier 0/1); **five defeat the cheap core
entirely** and exist specifically to exercise the caveats in `DEFINITION.MD` §7.

---

## 3. Error detail

### ERR-1 — Dimensionless geometric factor · 2023 S3, A.1 · condition III

| | |
|---|---|
| Original | `ΔE = 4π(2 − 2^(2/3)) a²γ` → `v = 0.232 m/s`, boxed `0.23 m/s` |
| Injected | `ΔE = 4π(2 − 2^(1/3)) a²γ` → `v = 0.311 m/s`, boxed `0.31 m/s` |

Volume conservation on merging two radius-`a` drops gives `R = 2^(1/3) a`, so the
merged **area** is `4πR² = 4π·2^(2/3)a²` and the surface-energy deficit carries
`2 − 2^(2/3)`. The exponent was changed on the surviving `2`, and the numeric
answer recomputed consistently, so the sub-part is internally coherent.

This is the residual flagged as **highest** in `DEFINITION.MD` §6: a pure
dimensionless factor. Dimensional analysis (0.1), units (0.2), and plug-back all
pass; the value is wrong by 34 % but nothing cheap knows the right value.

### ERR-2 — Sign / direction flip · 2023 S3, B.3 · condition III

| | |
|---|---|
| Original | `f_x + γcos θ2 − γcos θ1 = 0` → boxed `f_x = γcos θ1 − γcos θ2` |
| Injected | `f_x + γcos θ1 − γcos θ2 = 0` → boxed `f_x = γcos θ2 − γcos θ1` |

All three lines of B.3 (prose, equation S3.6, boxed answer) flip together, so the
sub-part is self-consistent. Caught by Tier 0.3, and independently by cross-part
chaining: it contradicts B.2's leftward `f_x` and equation (S3.7) in B.4, which
was left correct.

### ERR-3 — Dimensional inconsistency · 2023 S3, B.4 · condition III

| | |
|---|---|
| Original | `ℓ = √(γ/ρg)` (both the inline statement and the boxed answer) |
| Injected | `ℓ = √(γ/ρ)` |

`γ/ρ = m³/s²`, so the root has dimension `m^1.5·s⁻¹` and cannot be the capillary
length. The single cheapest possible falsifier (Tier 0.1).

### ERR-4 — Wrong boundary condition / root branch · 2023 S3, B.5 · condition III

| | |
|---|---|
| Original | `z(∞)=0 ⟹ A=0`; `z′(0)=tan θ0 ⟹ B=−ℓ tan θ0`; boxed `z(x) = −ℓ tan θ0 e^(−x/ℓ)` |
| Injected | `z(∞)=0 ⟹ B=0`; `z′(0)=tan θ0 ⟹ A=+ℓ tan θ0`; boxed `z(x) = ℓ tan θ0 e^(+x/ℓ)` |

The general solution `z = Ae^(x/ℓ) + Be^(−x/ℓ)` is kept, but the *growing* branch
is retained. The algebra is then internally correct (`A = ℓ tan θ0` really does
follow from `z′(0) = tan θ0` once `B=0`), yet the surface height diverges as
`x→∞`, contradicting the boundary condition the same line invokes. This is the
"wrong root branch / wrong integration constant from BCs" mode of §1 fact 7;
caught by plug-back (1.2) or a limiting-case check (1.1).

### ERR-5 — Symbol-whitelist / demanded-form violation · 2023 S3, C.2 · condition V

| | |
|---|---|
| Original | boxed `F_x = −½ρg z0²` |
| Injected | boxed `F_x = −2ρg z_a² / (e^(x_a/ℓ) + e^(−x_a/ℓ))²` |

**The injected expression is algebraically correct** — it is exactly `−½ρg z0²`
with `z0` substituted from C.3. But C.2 demands `F_x` *"without using θa, θb, za,
zb"*, and the answer re-introduces `z_a` and `x_a`.

This is the deliberate false-negative trap: dimensions, units, sign, limiting
cases, conservation, plug-back and **CAS symbolic equivalence to the reference
value all pass**. Only the per-type answer-form check with the symbol whitelist
(Tier 0.5) rejects it. A verifier that grades value-equivalence alone will score
this correct — the failure mode named in §7.6 ("answer mis-typing silently drops
requirements").

### ERR-6 — Faithfulness drift `P→S` · 2021 S1, A.1 · condition IV

| | |
|---|---|
| Original | oil poured until its **lower** level reaches the lower plate edges ⟹ `ρ0gh = ρ_oil g h′` ⟹ `h′ = (ρ0/ρ_oil)h`; `F_x = (ρ0/ρ_oil − 1)·ρ0gh²w/2`, acting **to the right** |
| Injected | "The oil is poured until its free surface is level with the water surface, so that `h′ = h`"; `F_x = (ρ_oil − ρ0)·gh²w/2`, acting **to the left** |

The rewritten solution is internally consistent, dimensionally sound, uses the
correct method, and would be fully correct — **for a different problem**. The
fill condition it assumes contradicts the one Q1 actually states.

This is the dominant generated-content failure mode of `DEFINITION.MD` §0 and
§7.5: an unfaithful `S` passes every intrinsic check. Nothing in Tier 0 or Tier 1
can fire, because nothing in Tier 0 or Tier 1 reads `P`. Only the Layer-0 gate or
Tier 2.5 (`P↔S` datum reconciliation) catches it. Requires `IPhO_2021_Q1.pdf`.

### ERR-7 — Wrong retained order in a sanctioned approximation · 2021 S1, A.4 · condition II

| | |
|---|---|
| Original | "the term with `D² ∝ k⁻²` is of the leading order" ⟹ `F ≈ 2gLh²(ρ1−ρ0)²/(k²ρ1)` |
| Injected | "the term with `hD ∝ k⁻¹` is of the leading order" ⟹ `F ≈ 2gLh²(ρ1−ρ0)/k` |

Since `D ∝ k⁻¹`, expanding `(h+D)²` makes `D² ∝ k⁻²` dominant; the cross term
`2hD ∝ k⁻¹` is strictly sub-leading. The injected answer keeps the wrong one.
Both expressions are dimensionally identical (`(ρ1−ρ0)²/ρ1` and `(ρ1−ρ0)` are both
a density, `k` is dimensionless), so Tier 0.1 is blind. Requires Tier 2.4,
approximation-application legitimacy.

### ERR-8 — Right-answer-wrong-reasoning (provenance) · 2021 S1, A.5 · condition III

| | |
|---|---|
| Original | "This gives `α = β = 1, γ = −1, δ = 2`" ⟹ `τ = A c ρ1 D²/κ` |
| Injected | "This gives `α = β = 1, γ = −1, δ = 3`" ⟹ `τ = A c ρ1 D²/κ` (unchanged) |

The delivered answer stays **correct**, but the exponent the dimensional-analysis
step claims to have derived is not the one the answer uses, and does not satisfy
the linear system printed directly above it (`δ = 3` would give `D³`).

Per §6 and §7.1, "a right number obtained from a wrong formula earns nothing" and
right-answer-wrong-reasoning **survives the entire cheap core** — every endpoint
check passes by construction. Only Tier 2.1 step-logic re-derivation localizes it.
Note the solution also offers a correct Method 2, so a verifier that accepts on
"cross-method agreement" (1.4) without auditing Method 1 will also miss it.

### ERR-9 — Conservation / energy-budget violation · 2021 S1, B.2 · condition II

| | |
|---|---|
| Original | `(E/π) dθ0` is the energy in `[θ0, θ0+dθ0)`; `ε = (E/π)|dθ0/dx|`; `ε(x) = EA/(πb(A²+x²)) = 2Ez0/(π(4z0²+x²))` |
| Injected | `(E/2π) dθ0`; `ε = (E/2π)|dθ0/dx|`; `ε(x) = EA/(2πb(A²+x²)) = Ez0/(π(4z0²+x²))` |

The source emits into a half-plane only — all directions with positive `z`
component — so the angular measure is `π`, not `2π`. Normalising over `2π`
accounts for only half the released energy: integrating the injected `ε(x)` over
both sides of the surface yields `E/2`, not `E`.

Dimensionally invisible and a plausible-looking normalisation. Caught by the
Tier 1.3 conservation residual — and this one is a genuine test of §7.2, since
the check only works if the verifier first establishes that the energy budget
*is* applicable (waves fully absorbed at the surface, per the problem text).

### ERR-10 — Completeness, answer never delivered · 2021 S1, B.3 · condition V

| | |
|---|---|
| Original | `x_max = A cos²(bθ0)/(b δθ0) = 2z0 cos²θ0 / δθ0` |
| Injected | "…gives `x_max`, which can then be evaluated numerically for given `θ0` and `δθ0`." |

B.3 demands `x_max` "in terms of `θ0`, `δθ0` and other constants given above". The
derivation runs to completion and then stops short of producing the closed form,
so the requested quantity is never delivered in the demanded form. Condition (V):
"every part answered ... each quantity delivered in the *demanded form*".

---

## 4. Reproduction

`inject_errors/` regenerates both faulty PDFs from the pristine originals:

```bash
cd verifier_experiments/pdfs
python ../inject_errors/inject_s3.py     # -> faulty/IPhO_2023_S3_FAULTY.pdf
python ../inject_errors/inject_s1.py     # -> faulty/IPhO_2021_S1_FAULTY.pdf
```

Requires `pymupdf` and the Cambria font (`C:/Windows/Fonts/cambria.ttc`).
`injlib.py` holds the edit engine, `discover.py` dumps line/block coordinates for
locating new targets.

**Method.** Characters are located via `rawdict`, their exact bounding boxes are
redacted, and replacement text is redrawn at the same origin with `TextWriter`.
Two constraints are baked into the scripts and worth knowing before adding edits:

- a match must be **contiguous** — matched glyph boxes are unioned into one
  redaction rect, so a split match erases whatever lies between the halves;
- replacement text must stay in the **Basic Multilingual Plane**. PyMuPDF emits a
  broken `ToUnicode` CMap for U+1D400-block math italics, so replacements use
  `x`/`ρ` where the surrounding document has U+1D465/U+1D70C. Semantics are
  unaffected; the codepoints differ from their neighbours.

Consecutive lines' bounding boxes overlap vertically in both documents, so
region blanking uses explicitly clamped rects rather than full line boxes.

## 5. Fidelity caveats

- **Extract with geometric sorting** — `page.get_text(sort=True)` in PyMuPDF, or
  `pdftotext`. Replacement glyphs are appended to the content stream, so raw
  stream-order extraction places edited fragments out of sequence. Sorted
  extraction and visual rendering are both correct; this was verified page by
  page for every edit.
- Edited fragments are set in **Cambria**; the originals use Latin Modern Math
  (2023) and Linux Libertine (2021). Edited text is legible and correctly
  positioned but visibly a different face on close inspection.
- Stacked fractions that had to be rewritten wholesale are **linearised**
  (`a/b`, `^` for exponents), and sub/superscripts in replacement text render
  inline (`z0`, `θ1`, `h²`) rather than as true typeset math.
- No figure, table, answer box or unedited line was altered; fraction rules
  belonging to removed expressions were cleared along with them.
