# Human trajectory annotator

`human_annotator.py` is a local browser tool for reviewing a folder of trajectories.
It works with the observable packs produced by the preprocessing experiments:

```bash
/home/aliu/projects/fail-traj-learn/lerobot/.venv/bin/python \
  scripts/annotate/human_annotator.py \
  outputs/preprocessing_ablation_v3/holdout_source \
  --privileged-contacts
```

The argument may be the parent collection folder or an individual episode such as
`H001`. When given an episode, the server discovers its sibling episode folders;
pass `--single` to keep the old one-episode behavior. Each episode folder must
contain `cameras.npz` with `agent` and `wrist` frame arrays. An
`observable.json` file is optional but supplies the task and trajectory ID when it
exists. The tool renders JPEGs into a hidden `.human_annotator/` directory, opens a
browser page, and saves `human_annotation.json` beside the source files.

The navigation bar shows the current position, marks complete episodes with `✓`, and
provides **Previous episode**, an episode picker, and **Save & next episode**. Moving
between episodes saves the current annotation first. Unfinished segment text is
stored as a draft and restored when the episode is opened again. Starting from a
collection folder opens the first incomplete episode. On the final episode, the
navigation button becomes **Save annotation** and saves without trying to move past
the collection. Partial saves remain available, but receive a checkmark only after
segments cover the episode and the required outcome and failure-type choices are set.

To verify an annotation, open its episode and press **Replay annotations from
start**. The demonstration plays at the selected speed while a live card shows the
segment covering the current frame, including its classification, description,
failure type, and note. Colored bands show all labeled ranges on the timeline and
the current range is outlined; click a band or a row in the segment list to jump to
that segment. Use **Edit** beside a saved segment to load its description,
classification, failure type, and note into the editor. **Update segment** changes
those fields and can change its inclusive ending frame; then save the annotation
normally. An edited ending must remain contiguous with the next segment, when one
exists, and stay within the episode.
Progress is green, failure is red, recovery is blue, and neutral is gray.

For this holdout collection, `--privileged-contacts` adds a live, prominently
marked **PRIVILEGED SIMULATOR STATE** panel. It names the task target and updates
the following raw simulator signals at every frame:

- **Any gripper contact**: at least one gripper geom contacts the named object.
- **Bilateral grasp**: both fingers contact the named object.
- **External support**: the object contacts a support surface or another object.

The status line explicitly distinguishes correct-target grasp, correct-target
contact without a bilateral grasp, and non-target contact/grasp. "Unsupported"
means no logged external support at that frame; it is useful evidence of lifting,
but the panel deliberately reports the underlying state rather than inventing a
human label. This information is private annotation ground truth and must not be
treated as visual evidence or passed to a model intended to operate from cameras.
Annotations saved while the overlay is enabled record
`"annotation_aids": ["privileged_simulator_contacts"]` so their provenance remains
distinguishable from vision-only human labels.
The tool infers the adjacent `holdout_private_manifest.json` and original data root
from provenance. Use `--privileged-manifest PATH` or `--data-root PATH` to override
those locations for another collection.

The main workflow is semantic segment labeling. The first segment starts at frame 0.
Seek to the last frame of a segment, write a short description of what happens, and
press **Finish segment at current frame**. Describe observable facts in the text box,
then choose one general classification:
`progress`, `failure`, `recovery`, or `neutral`. When the classification is
`failure`, choose a failure type from the second dropdown. Put task-specific details
such as grasping or approaching a basket in the description. The classification is
the segment's task-level effect, so a failure segment can still include a good fact
such as “the gripper remains closed around the object.” The next segment starts
automatically at the following frame. Saved segment
ranges use an exclusive end frame, so a segment finished on frame 19 is saved as
`[start, 20)`. The episode outcome is recorded separately from the segment text.
Add a note only when a segment is visually uncertain or needs supporting detail.
The event and per-frame state controls are optional under **Detailed mode**.

Press **Save annotation** whenever you want a durable copy; saving writes only to the
selected trajectory folder.

## Reviewing a model candidate

Keep the model output immutable and save the assisted human decision under a different
name:

```bash
/home/aliu/projects/fail-traj-learn/lerobot/.venv/bin/python \
  scripts/annotate/human_annotator.py \
  outputs/gpt6_human_review_v1/episodes \
  --seed-name gpt6_annotation.json \
  --annotation-name human_review.json
```

When `human_review.json` does not exist, the editor starts from the GPT candidate and
records its filename and SHA-256 hash in `review_of`. Saving never changes
`gpt6_annotation.json`. This workflow measures candidate-assisted human review; it is
not an independent human-label condition. Run the tool without `--seed-name` for an
independent annotation. Before an assisted review is marked complete, explicitly choose
**accept candidate as-is** or **candidate corrected**. A corrected candidate requires a
short reviewer note describing the important changes.

For the human-demonstration GPT-6 condition, keep its review separate as well:

```bash
python scripts/annotate/human_annotator.py \
  outputs/gpt6_human_review_v1/episodes \
  --seed-name gpt6_fewshot_annotation.json \
  --annotation-name human_fewshot_review.json
```

Use `--no-browser` on a remote machine, then open the printed localhost URL through
your local port forwarding. Stop the server with Ctrl-C.

## Windows PowerShell

The annotator uses the Linux environment where the trajectory dependencies are
installed. From PowerShell, run it through WSL as one command:

```powershell
wsl bash -lc 'cd /mnt/c/Users/LocalPC/dev/fail-traj-learn && /home/aliu/projects/fail-traj-learn/lerobot/.venv/bin/python scripts/annotate/human_annotator.py outputs/preprocessing_ablation_v3/holdout_source/H001'
```

Remove `/H001` to start at the first unfinished episode in the collection. The tool prints a
`http://127.0.0.1:8765/` URL; open that URL in your Windows browser. PowerShell
uses a backtick for line continuation, not `\`.
