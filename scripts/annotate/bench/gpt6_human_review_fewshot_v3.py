#!/usr/bin/env python3
"""All-twelve-human-demonstration GPT-6 annotation condition without added rules.

This condition keeps the all-H001--H012 in-context examples but intentionally does
not encode review-derived, hand-written behavioral rules. The model must infer the
label boundary conventions from the supplied human examples.
"""
from __future__ import annotations

import gpt6_human_review_fewshot_v1 as protocol


protocol.OUT = protocol.BASE_OUT / "fewshot_v3"
protocol.EXAMPLE_IDS = tuple(f"H{i:03d}" for i in range(1, 13))
protocol.VERSION = "gpt6_human_review_fewshot_v3"
protocol.OBSERVATION_NAME = "gpt6_fewshot_v3_observation.json"
protocol.AUDIT_NAME = "gpt6_fewshot_v3_audit.json"
protocol.CANDIDATE_NAME = "gpt6_fewshot_v3_annotation.json"
protocol.REVIEW_NAME = "human_fewshot_v3_review.json"
protocol.SCHEMA = protocol.base.SCHEMA.replace(
    '"gpt6_human_review_v1"', f'"{protocol.VERSION}"'
)


if __name__ == "__main__":
    protocol.main()
