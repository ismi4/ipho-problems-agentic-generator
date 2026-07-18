"""Registry mapping config name -> verifier instance factory."""
from __future__ import annotations

import json
import os
from typing import Any, Callable

from verifier.solution_a.configs import AV0, AV1, AV2
from verifier.solution_b.configs import BV0, BV1, BV2
from verifier.solution_c.configs import CV0, CV1, CV2
from verifier.composed.system import Composed

_TUNING_PATH = os.path.join(os.path.dirname(__file__), "..", "results", "tuning.json")


def _tuning() -> dict[str, Any]:
    if os.path.exists(_TUNING_PATH):
        with open(_TUNING_PATH) as f:
            return json.load(f)
    return {}


def build_registry() -> dict[str, Callable[[], Any]]:
    t = _tuning()
    # A.V1 is the naive cheap-first cascade with a fixed moderate threshold
    # (partial savings). A.V2 uses the dev-tuned threshold + accept-guard, which
    # is where the router calibration recovers quality at maximal savings.
    a_v1_thr = 0.7
    a_v2_thr = t.get("A.V2", {}).get("conf_threshold", 0.9)
    comp_thr = t.get("composed", {}).get("conf_threshold", 0.9)
    return {
        "A.V0": AV0,
        "A.V1": lambda: AV1(conf_threshold=a_v1_thr),
        "A.V2": lambda: AV2(conf_threshold=a_v2_thr),
        "B.V0": BV0,
        "B.V1": BV1,
        "B.V2": BV2,
        "C.V0": CV0,
        "C.V1": CV1,
        "C.V2": CV2,
        "composed": lambda: Composed(conf_threshold=comp_thr),
    }


ALL_CONFIGS = ["A.V0", "A.V1", "A.V2", "B.V0", "B.V1", "B.V2",
               "C.V0", "C.V1", "C.V2", "composed"]
