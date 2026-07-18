# Key Challenges (the hard sub-problems)

Ranked roughly by how much they threaten the project.

## 1. Correctness & solvability verification  ← existential

- LLMs produce confident, subtly-wrong physics. Self-check is not enough.
- **Approach:** external verifier core.
  - **SymPy** — symbolic solve, simplify, check the answer satisfies the governing
    equations; dimensional analysis (every quantity carries units).
  - **Numerical simulation** — integrate ODEs/PDEs, Monte Carlo; cross-check symbolic
    results against numbers at sampled parameter values.
  - **Independent re-solve** — a second agent solves the *statement alone* and must
    match; catches under-/over-specification and hidden assumptions.
- **Hard cases:** problems whose "answer" is an approximation/limit, order-of-magnitude
  estimates (Fermi problems), or reasoning with no closed form.

## 2. Difficulty calibration

- IPhO problems must be hard-but-doable in a fixed time and *discriminate* students.
- No ground-truth difficulty signal for a novel problem. Proxies:
  - # of independent steps, # of concepts combined, math machinery required,
    closed-form vs. numeric, "trickiness" of the key insight.
  - **Student-simulator agents** at graded skill levels attempt the problem; the
    spread of who-solves-what estimates difficulty and discrimination.
- Risk: proxies are noisy; needs human-in-the-loop calibration data over time.

## 3. Novelty / anti-plagiarism

- Must not reproduce existing bank problems.
- Needs a **corpus** (past IPhO/national olympiads, textbooks) + similarity search
  (embeddings) to reject near-duplicates. Corpus sourcing/licensing is its own task.

## 4. The rising-difficulty arc

- Multi-part structure where each part scaffolds the next is what makes it *olympiad*
  style, not just "a physics question." Hard to get from a single generation; favors
  explicit arc-design as its own step.

## 5. Figures & diagrams

- Many problems are unintelligible without a correct figure.
- Generating *correct* diagrams (TikZ / matplotlib / SVG) that match the text is a
  separate verification problem (the figure can contradict the prose).

## 6. Marking scheme / official solution

- IPhO problems ship with step-by-step solutions and point-allocated rubrics.
- The verified solution trace from the verifier core can seed this — a real advantage
  of backward design (you already have every step).

## 7. Cost, latency, reproducibility

- Multi-agent + tools = many calls. Need caching, seed→artifact provenance, and the
  ability to replay a generation deterministically for debugging/regression.

## 8. Evaluation — "is this actually good?"

- Need an eval harness *before* scaling: a rubric-scored test set, human expert
  spot-checks, and metrics (yield, verified-correct rate, novelty rate, difficulty fit).
- Without this you can't tell if a fancier architecture is actually better.
