"""Prompt for the zero-shot VLM segmenter. PROMPT_VERSION is stored in every annotation record; bump it on any edit."""

PROMPT_VERSION = "p8"

# Appearance of LIBERO assets, keyed by object-slot / fixture name (sidecar object_slots, fixtures, target_objects).
# Written from outputs/annot_preview/_gallery_objects.png (object_gallery.py), NOT from memory: e.g. the alphabet
# soup is a dark-blue can, the butter box is red. A human annotator knows what the named objects look like; on real
# data (OOPSIE) the objects are recognisable household items and this glossary is simply empty.
LIBERO_GLOSSARY = {
    "alphabet_soup": "alphabet soup = a short DARK BLUE can with an orange/yellow label",
    "tomato_sauce": "tomato sauce = a short can with a RED and GREEN label",
    "bbq_sauce": "bbq sauce = a dark brown bottle with a red/orange cap",
    "ketchup": "ketchup = a red bottle",
    "salad_dressing": "salad dressing = a dark green bottle, medium height",
    "butter": "butter = a small RED and yellow box with the word BUTTER",
    "cream_cheese": "cream cheese = a small LIGHT BLUE and white box (Philadelphia style)",
    "milk": "milk = a red and white carton with the word MILK",
    "chocolate_pudding": "chocolate pudding = a brown and red box with the words CHOCOLATE PUDDING",
    "orange_juice": "orange juice = an orange and yellow carton with the word JUICE",
    "basket": "basket = a woven wicker basket with a white cloth lining, open on top",
    "akita_black_bowl": "bowl = a black bowl with a white pattern",
    "plate": "plate = a white plate with a red rim",
    "moka_pot": "moka pot = a silver octagonal stovetop coffee pot with a black handle",
    "wine_bottle": "wine bottle = a tall dark bottle with a long neck",
    "porcelain_mug": "white mug = a plain white porcelain mug",
    "red_coffee_mug": "red mug = a red mug",
    "white_yellow_mug": "yellow and white mug = a white mug with a yellow interior and handle",
    "black_book": "book = a black hardcover book",
    "yellow_book": "book = a yellow hardcover book",
    "chefmate_8_frypan": "frypan = a black frying pan",
    "flat_stove": "stove = a flat black stovetop with a knob; 'turn on' means rotating the knob",
    "wooden_cabinet": "cabinet = a wooden cabinet with three pull-out drawers (top, middle, bottom) with handles",
    "white_cabinet": "cabinet = a white cabinet with drawers",
    "microwave": "microwave = a microwave oven with a hinged door",
    "desk_caddy": "caddy = a wooden desk organizer with several vertical compartments",
    "wine_rack": "rack = a wooden wine rack",
    "wooden_two_layer_shelf": "shelf = a wooden two-layer shelf; 'under the shelf' means the lower level",
}


def scene_glossary(names):
    """Glossary lines for the named scene objects (slot names like 'alphabet_soup_1' -> key 'alphabet_soup')."""
    seen, lines = set(), []
    for n in names:
        key = n.rsplit("_", 1)[0] if n[-1].isdigit() else n
        key = key.replace("_cook_region", "").replace("_top_region", "").replace("_middle_region", "").replace("_top_side", "")
        if key in LIBERO_GLOSSARY and key not in seen:
            seen.add(key)
            lines.append("- " + LIBERO_GLOSSARY[key])
    return "\n".join(lines)

SYSTEM = """You are an expert reviewer of robot manipulation rollouts. You analyse a tabletop episode recorded by a Franka
robot in simulation and produce a temporal diagnosis as strict JSON.

You will receive:
1. the language instruction the policy was given;
2. the episode outcome (success or failure) and its length;
3. start/end observations for every action CHUNK (10 steps, 0.5 seconds), grouped into image grids.
   Read grids in row order; each cell labels its exact chunk and step and contains agentview left, wrist right.
   These are sampled observations, not continuous video; events between frames may be invisible;
4. a table of robot signals per chunk (positions/aperture measured at the final observation of the chunk; end-effector position in cm, height change, speed, gripper aperture and
   gripper command). Aperture ~4 cm means open, ~0 cm means closed; command CLOSE means the policy is squeezing.

Label every chunk with exactly one of:
- progress: the action advances task completion (approaching the correct object, a stable grasp, lifting,
  transporting toward the goal, a correct placement, opening the right drawer, ...).
- failure_inducing: the action introduces or worsens an error (approaching the wrong object, closing the gripper
  off-centre, an unstable grasp that will slip, pushing the object away, colliding, setting the object on the rim,
  releasing in the wrong place, moving away from the goal, ...).
- recovery: the action tries to restore feasibility after an error (re-opening and re-grasping, re-approaching the
  correct object, lifting the object again after a drop, correcting a placement).
- neutral: little meaningful effect (hovering, idle, tiny oscillations, waiting) while the task is still feasible.
- aftermath: the episode is already unrecoverable and the remaining motion no longer matters (object out of reach,
  with clear evidence of lost feasibility). Repetition or holding still alone is insufficient; use neutral
  when irrecoverability is uncertain.

Temporal landmarks (chunk indices, null when not applicable):
- failure_onset: first chunk with an observable sign of degradation.
- decisive_error: the chunk whose action most determined the failure. It is often EARLIER than the visible
  failure (an off-centre grasp precedes the slip; approaching the wrong object precedes grasping it).
- visible_failure: chunk where the failure becomes obvious to a viewer.
- recoverable_until: last chunk at which a competent policy could still have completed the task in the remaining time.
For a successful episode set all four to null unless a real error happened and was recovered from, in which case
fill supported failure_onset, decisive_error and visible_failure landmarks; recoverable_until may remain null.

Cause of failure, one of: reaching (never reached / mis-positioned approach), grasp (unstable, off-centre, missed
grasp, slip), manipulation (wrong placement, rim placement, drop during transport, wrong drawer motion),
sequencing_semantic (wrong object, wrong order, wrong target region, task misunderstood), collision (arm or gripper
hits scene or objects with consequences), hardware (never in simulation), other, unclear. Use "unclear" when the
evidence does not support a single cause. For successful episodes use "unclear" unless a recovered error is visible.

How to read the signal table (check the images against it):
- command CLOSE with finger position 1-3 cm suggests a possible grasp, but does not establish object contact or holding.
- command CLOSE with finger position near 0 cm suggests closure; check images for a missed grasp or release.
  Finger position alone cannot establish a drop or prove nothing was held. The reported aperture is one finger
  joint coordinate, not total fingertip separation.
- command switching to open after holding = a release; where the object lands decides success (inside the goal
  container, on its rim, or on the table).
- large speed with an object held = transport; dz strongly positive after a grasp = lift; dz negative near the
  goal = lowering to place.
- speed near 0 for many chunks = idle / stalled. Whether that is neutral or aftermath depends on whether the task
  is still feasible in the remaining time.

Rules:
- Base your judgement on what is visible in the images and consistent with the signal table. Do not infer an error merely from the episode outcome.
- The instruction names objects by their dataset names; a glossary of what each object looks like is provided.
  FIRST identify the object the gripper touches, grasps and carries from the WRIST camera (right half of each
  image), where it appears large and close, and compare its colours with the glossary. Only diagnose a wrong-object
  error when the wrist view clearly shows an object whose appearance does not match the target's description.
- The decisive error is the best-supported harmful action contributing to the final failure; it need not make
  failure inevitable. Use null when its timing or responsibility cannot be established from the observations. A missed grasp that is later corrected by a successful re-grasp is failure_inducing then
  recovery, and is not the decisive error if the object was later dropped or misplaced.
- The episode ends at success or at a fixed timeout. A long tail of repetitive motion before the timeout is
  aftermath if the task was already lost, neutral if it was still feasible.
- Segments must cover every chunk from 0 to the last chunk, be in order, and not overlap.
- Confidence is your probability that the label of that segment is right.
- Output ONLY one JSON object with this exact structure and no other text. Every <chunk> is an integer chunk
  index that YOU determine from this episode's images and signals (or null); do not reuse numbers from these
  instructions:
{
  "outcome": "failure" | "success",
  "failure_symptom": "<one sentence, what went wrong as seen>",
  "root_cause": "<one sentence, why>",
  "cause": "<one of the cause labels>",
  "failure_onset": <chunk or null>,
  "decisive_error": <chunk or null>,
  "visible_failure": <chunk or null>,
  "recoverable_until": <chunk or null>,
  "segments": [
    {"start": <chunk>, "end": <chunk>, "label": "<label>", "confidence": <0-1>},
    {"start": <chunk>, "end": <chunk>, "label": "failure_inducing", "cause": "<cause>", "confidence": <0-1>},
    ...
  ]
}
Segments cover chunk 0 through the last chunk in order, typically 2 to 6 segments."""

REFINE_SYSTEM = """You are an expert reviewer of robot manipulation rollouts. You previously localised the decisive error of a failed
episode to a coarse window. You now see denser frames from that window only (every image is labelled with its chunk
index and step within the episode; the third-person camera is on the left, the wrist camera on the right).
Re-estimate the landmarks as chunk indices, using only the chunks shown: failure_onset, decisive_error,
visible_failure, recoverable_until (null when outside the window or not applicable). Determine each value from the
frames; do not reuse numbers from the coarse diagnosis unless the frames confirm them. Output ONLY a JSON object:
{"decisive_error": <chunk or null>, "failure_onset": <chunk or null>, "visible_failure": <chunk or null>, "recoverable_until": <chunk or null>, "reason": "<one sentence>"}"""


def episode_header(task, outcome, n_chunks, n_frames, fps):
    return (f"Instruction given to the policy: \"{task}\"\n"
            f"Episode outcome: {outcome.upper()}. Length: {n_frames} steps = {n_chunks} chunks of 10 steps "
            f"({n_frames / fps:.1f} s at {fps} fps). Chunk indices run from 0 to {n_chunks - 1}.\n")


def build_user_content(task, outcome, n_chunks, n_frames, fps, tiles, table_text, glossary_text="", facts_text=""):
    """Interleaved content: header (+ scene glossary, + verified facts), then 'chunk k' text + image per tile, then the
    signal table and the ask. `tiles` is a list of (caption, PIL.Image, (chunk_a, chunk_b))."""
    head = episode_header(task, outcome, n_chunks, n_frames, fps)
    if glossary_text:
        head += "Objects in this scene:\n" + glossary_text + "\n"
    if facts_text:
        head += facts_text + " These are tentative visual observations; verify against the episode frames.\n"
    content = [{"type": "text", "text": head + "\nStart/end observations, read each grid in row order:"}]
    for caption, img, _ in tiles:
        content.append({"type": "text", "text": caption + ":"})
        content.append({"type": "image", "image": img})
    content.append({"type": "text", "text": "\nRobot signals per chunk (non-privileged, from proprioception and the commanded action):\n"
                    + table_text
                    + f"\n\nProduce the JSON diagnosis for this {outcome} episode covering chunks 0 to {n_chunks - 1}."})
    return content


def build_refine_content(task, coarse, window_tiles, table_text):
    txt = (f"Instruction: \"{task}\"\nCoarse diagnosis: cause={coarse.get('cause')}, decisive_error={coarse.get('decisive_error')}, "
           f"failure_onset={coarse.get('failure_onset')}, visible_failure={coarse.get('visible_failure')}, "
           f"symptom: {coarse.get('failure_symptom')}\nDense frames from the window:")
    content = [{"type": "text", "text": txt}]
    for caption, img, _ in window_tiles:
        content.append({"type": "text", "text": caption + ":"})
        content.append({"type": "image", "image": img})
    content.append({"type": "text", "text": "\nSignals for the window chunks:\n" + table_text + "\n\nReturn the refined landmark JSON."})
    return content


IDENTIFY_SYSTEM = """You are a careful visual inspector of robot wrist-camera images. Each image is a close-up from the camera mounted on
the gripper at a candidate interaction moment; an object may or may not be held. Decide which object is between the fingers.
Compare colours and shapes with the object list. Output ONLY a JSON object:
{"held_object": "<one name from the list, or null if nothing is clearly held>", "appearance": "colours and shape you see", "confidence": 0.0-1.0}"""


def build_identify_content(task, glossary_text, tiles):
    content = [{"type": "text", "text": f"Instruction given to the robot: \"{task}\"\nObjects in this scene:\n{glossary_text}\n\nWrist close-ups:"}]
    for caption, img, _ in tiles:
        content.append({"type": "text", "text": caption + ":"})
        content.append({"type": "image", "image": img})
    content.append({"type": "text", "text": "Which object from the list is held between the fingers? Return the JSON."})
    return content


def held_object_fact(held, target_names, chunks):
    """Sentence stating the identified object, injected into the diagnosis prompt as a verified fact."""
    span = f"chunks {chunks[0]}-{chunks[-1]}" if len(chunks) > 1 else f"chunk {chunks[0]}"
    if held is None:
        return f"Tentative identification from wrist close-ups: the gripper closes around NOTHING clearly identifiable in {span}."
    role = "the TARGET object" if held in target_names else "NOT the target: a distractor"
    return f"Tentative identification from wrist close-ups ({span}): the object held by the gripper is the {held.replace('_', ' ')} ({role})."
