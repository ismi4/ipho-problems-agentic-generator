# How Humans Generate These Problems — and Creative Seeding

## First-principles: the olympiad author's loop

1. **Get seized by a phenomenon** — a device, demo, paper, or curiosity.
2. **Identify the core principle(s)** the problem should test.
3. **Idealize** — strip to a tractable model with clean assumptions.
4. **Design the arc** — pick givens/unknowns; order sub-parts by rising difficulty so
   each part scaffolds the next.
5. **Fully solve it** — confirm solvability, uniqueness, clean answers.
6. **Calibrate** — difficulty vs. time budget; must discriminate strong students.
7. **Check novelty** against existing problem banks.
8. **Polish** — narrative, realistic numbers, figures, marking scheme.
9. **Peer review / test-solve** by a committee.

**Key observation:** creativity lives in steps 1 & 3; correctness lives in step 5;
quality-control lives in steps 6–9. These map cleanly onto separate agents/nodes.

## The creative engine is the *seeding layer*

The engine (LLM) matters less than what you feed it. The "found a topic on YouTube"
trick generalizes to: **maximize seed diversity from the real world.** A catalogue of
seed strategies, each a pluggable "ideation source":

| Seed strategy | Example | Tooling needed |
|---|---|---|
| Media mining | slow-mo/demo YouTube channels → extract phenomenon | video search + transcript |
| Paper mining | lift a mechanism from arXiv, simplify to scope | arXiv API + summarizer |
| Everyday objects | spinning coin, dripping tap, Slinky drop, coffee cooling | LLM brainstorm |
| News/events | rocket launch, eclipse, new gadget | web search |
| Cross-domain analogy | map electrostatics structure onto gravitation | isomorphism prompt |
| Perturb a classic | add friction / relativity / finite size to a canonical problem | classic-problem corpus |
| Principle collision | thermo + circuits → thermally driven RC | concept-pair sampler |
| Real data fitting | fit a model to a real dataset/measurement | dataset source |
| Reverse a beautiful result | pick a constant/result, build a path to it | LLM + verifier |
| Image → physics | infer a problem from a photo (bridge, rainbow) | vision model |
| Simulation-first | run a sim, ask students to derive the analytic approx it confirms | numeric sim |
| Historical redux | Millikan/Cavendish re-imagined with a modern twist | history corpus |

**Design implication:** treat the seeder as a **strategy interface** with many
interchangeable implementations. Diversity of *sources* → novelty of *output*. This is
also where a human can inject a spark ("make one about a maglev train").

## Two ideation stances

- **Divergent** — generate many raw seeds cheaply, cast a wide net.
- **Convergent** — score/select seeds on richness, olympiad-fit, novelty before the
  (expensive) construction + verification stage.

A divergent→convergent funnel keeps cost down: verify only the promising seeds.
