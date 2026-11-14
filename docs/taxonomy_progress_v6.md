# V6: observable progress definition

The user-approved progress definition replaces V5's short progress paragraph.
Progress means observable improvement toward the instructed task, including useful
prerequisites and recovery. Examples cover alignment, contact/control, repositioning,
opening, turning, insertion, cleaning, and resolving problems. Wrong-object grasping
and backing away to realign clarify the boundaries. Progress is judged over a
meaningful action segment, with independently supported failure boundaries retained.

These examples are not progress categories. Progress and failure remain independent
booleans, with complete timeline coverage and a free-text explanation of task effect.
The nine-category failure taxonomy and all other prompt sections remain unchanged.

- [Exact prompt](../scripts/annotate/prompts/failure_taxonomy_progress_v6.txt)
- Runner: `scripts/annotate/api_taxonomy_progress_v6.py`
- Frozen evidence and raw responses: `outputs/taxonomy_progress_v6/`
- Same R001–R004 episodes, GPT-6.1 Sol and Gemini Robotics ER 2 Preview, low reasoning,
  4 Hz image samples and 8192 output tokens as V5.
- Verified identical model settings, schema validator, episode metadata, telemetry,
  and every supplied image byte against V5. Only the progress prompt block changes.
- Eight planned calls, no automatic retries, $4 total reservation. Status and cost
  accounting are in `outputs/taxonomy_progress_v6/summary.json`.

All eight calls completed and passed strict schema, evidence-reference, and full
coverage validation, without display aliases. Generation estimate: $0.3990155;
conservative preflight allowance: $0.265561; combined: $0.6645765. Headless Edge
checks passed for all eight timelines and segment selection, with no browser errors.

Refresh [the viewer](http://127.0.0.1:8767/) and select V6. Annotations appear below
each model's timeline, with V5 and earlier runs retained for comparison. Raw responses
and the exact prompt remain available. Any recognized display-only schema aliases
are flagged without changing strict validation status or raw output.

This remains a development-set experiment. Successful schema/coverage validation
does not establish object recognition or progress/failure accuracy. Although the
definition includes examples beyond pick-and-place, these four episodes do not
evaluate performance across that broader task range.
