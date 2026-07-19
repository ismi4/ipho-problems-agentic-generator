"""Fast unit tests (no OpenAI calls) for the deterministic core + accounting."""
import json
import os

from verifier.common.deterministic import check_subpart, symbolic_equivalent, FAIL, ESCALATE
from verifier.common.pricing import Usage, cost_of, load_prices
from bench.problems_data import PROBLEMS

HERE = os.path.dirname(__file__)
DATASET = os.path.join(HERE, "..", "dataset", "instances.jsonl")


def test_symbolic_equivalence_true_and_false():
    assert symbolic_equivalent("(m + rho*S*h)*g", "g*(m + rho*S*h)", ["m", "rho", "S", "h", "g"])
    assert not symbolic_equivalent("(m + rho*S*h)*g", "(m - rho*S*h)*g", ["m", "rho", "S", "h", "g"])


def test_pricing_matches_hand_calc():
    prices = load_prices()
    u = Usage(model="gpt-5", prompt_tokens=1000, cached_tokens=200,
              completion_tokens=500, reasoning_tokens=300)
    # (800 uncached * 1.25 + 200 cached * 0.125 + 500 out * 10) / 1e6
    expected = (800 * 1.25 + 200 * 0.125 + 500 * 10.0) / 1_000_000
    assert abs(cost_of(u, prices) - expected) < 1e-12


def test_deterministic_falsifies_unit_dropped():
    cox = PROBLEMS["cox_timepiece_2025"]
    sp = next(s for s in cox["subparts"] if s["id"] == "A.2b")
    cand = {"type": "numeric", "value": 14.7, "unit": "", "requires_unit": True}
    assert check_subpart(sp, cand).outcome == FAIL


def test_qualitative_escalates():
    cox = PROBLEMS["cox_timepiece_2025"]
    sp = next(s for s in cox["subparts"] if s["id"] == "A.2")
    assert check_subpart(sp, sp["answer"]).outcome == ESCALATE


def test_dataset_labels_consistent_with_deterministic_stack():
    insts = [json.loads(line) for line in open(DATASET)]
    assert len(insts) == 30
    for inst in insts:
        prob = PROBLEMS[inst["problem"]]
        outcomes = {sp["id"]: check_subpart(sp, inst["subpart_answers"][sp["id"]]).outcome
                    for sp in prob["subparts"]}
        if inst["label"] == "ACCEPT":
            assert FAIL not in outcomes.values(), inst["id"]
        else:
            fs = inst["failing_subpart"]
            assert outcomes[fs] in (FAIL, ESCALATE), (inst["id"], outcomes)
