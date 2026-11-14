"""Readable Markdown annotations with explicit parsing and Unicode loss spans."""
import re

IDENTITY_FIELDS = {"Requested object": "requested_object", "Manipulated object": "manipulated_object",
                   "Match status": "match_status", "Uncertainty": "uncertainty"}
SEGMENT_FIELDS = {"Frames": "frames", "Action ID": "action_id", "Action": "action", "Object": "object_id",
                  "Destination": "destination_id", "Failure": "failure", "Categories": "categories",
                  "Recovery": "recovery", "Severity": "severity", "Resetability": "resetability",
                  "Review required": "review_required", "Uncertainty": "uncertainty"}
SECTIONS = {"Observed result": "observed_result", "Boundary reason": "boundary_reason", "What happened": "what_happened"}
NULLABLE = {"object_id", "destination_id", "recovery", "severity", "resetability"}
UNCERTAIN_FIELDS = {"timing", "action", "identity", "failure", "categories", "outcome",
                    "mechanism", "recovery", "severity", "resetability"}


def field_lines(name, value):
    lines = str(value).split("\n")
    return f"- {name}: {lines[0]}\n" + "".join("  " + line + "\n" for line in lines[1:])


def evidence_text(items):
    return "".join(field_lines(f"Frame {item['frame']}, camera {item['camera']}", item["observation"]) for item in items)


def render(value):
    identity = value["identity_check"]
    text = f"# Episode: {value['episode_id']}\n\n## Identity\n\n"
    for label, key in IDENTITY_FIELDS.items():
        text += field_lines(label, identity[key] or "None")
    text += "\n### Evidence\n\n" + evidence_text(identity["evidence"])
    for index, segment in enumerate(value["segments"], 1):
        text += f"\n## Segment {index}\n\n"
        for label, key in SEGMENT_FIELDS.items():
            if key == "frames":
                item = f"{segment['start_frame']}–{segment['end_frame']}"
            elif key in ("failure", "review_required"):
                item = "Yes" if segment[key] else "No"
            elif key == "categories":
                item = ", ".join(segment[key]) or "None"
            else:
                item = segment[key] if segment[key] is not None and segment[key] != "" else "None"
            text += field_lines(label, item)
        if "uncertain_fields" in segment:
            text += field_lines("Uncertain fields", ", ".join(segment["uncertain_fields"]) or "None")
        for heading, key in SECTIONS.items():
            text += f"\n### {heading}\n\n{segment[key]}\n"
        text += "\n### Evidence\n\n" + evidence_text(segment["evidence"])
    return text


def bullet_values(text):
    values, key = {}, None
    for line in text.splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(r"- ([^:]+): (.*)", line)
        if match:
            key, value = match.groups()
            if key in values:
                raise ValueError(f"Duplicate Markdown field: {key}")
            values[key] = value
        elif line.startswith("  ") and key is not None:
            values[key] += "\n" + line[2:]
        else:
            raise ValueError("Expected named Markdown bullets with indented continuation lines")
    return values


def parse_evidence(text):
    values = bullet_values(text)
    result = []
    for key, observation in values.items():
        match = re.fullmatch(r"Frame (\d+), camera (.+)", key)
        if not match:
            raise ValueError("Evidence needs a source frame and native camera name")
        result.append(dict(frame=int(match[1]), camera=match[2], observation=observation))
    return result


def parse_block(text, identity=False):
    headings = list(re.finditer(r"^### (.+?)\s*$", text, re.MULTILINE))
    if not headings:
        raise ValueError("Markdown annotation is missing evidence/description sections")
    values = bullet_values(text[:headings[0].start()])
    mapping = IDENTITY_FIELDS if identity else SEGMENT_FIELDS
    if not identity and "Uncertain fields" in values:
        mapping = dict(mapping, **{"Uncertain fields": "uncertain_fields"})
    if set(values) != set(mapping):
        raise ValueError("Markdown fields differ from the annotation contract")
    result = {mapping[key]: value for key, value in values.items()}
    sections = {}
    for i, heading in enumerate(headings):
        name = heading[1]
        if name in sections:
            raise ValueError("Duplicate Markdown subsection")
        end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        sections[name] = text[heading.end():end].strip("\r\n")
    expected = {"Evidence"} if identity else set(SECTIONS) | {"Evidence"}
    if set(sections) != expected:
        raise ValueError("Markdown subsections differ from the annotation contract")
    result["evidence"] = parse_evidence(sections.pop("Evidence"))
    if identity:
        result["uncertainty"] = "" if result["uncertainty"] == "None" else result["uncertainty"]
        return result
    for key in ("failure", "review_required"):
        if result[key].lower() not in ("yes", "no"):
            raise ValueError(f"{key} must be Yes or No")
        result[key] = result[key].lower() == "yes"
    frames = re.fullmatch(r"(\d+)\s*(?:–|-|to)\s*(\d+)", result.pop("frames"))
    if not frames:
        raise ValueError("Frames must be start–end, with end exclusive")
    result.update(start_frame=int(frames[1]), end_frame=int(frames[2]))
    result["categories"] = [] if result["categories"] == "None" else [s.strip() for s in result["categories"].split(",")]
    if "uncertain_fields" in result:
        fields = result["uncertain_fields"]
        result["uncertain_fields"] = [] if fields == "None" else [s.strip() for s in fields.split(",")]
        if len(set(result["uncertain_fields"])) != len(result["uncertain_fields"]) or not set(result["uncertain_fields"]) <= UNCERTAIN_FIELDS:
            raise ValueError("Unknown or duplicate uncertain fields")
        if bool(result["uncertain_fields"]) != result["review_required"]:
            raise ValueError("Uncertain fields must agree with the review flag")
    for key in NULLABLE:
        if result[key] == "None":
            result[key] = None
    result["uncertainty"] = "" if result["uncertainty"] == "None" else result["uncertainty"]
    result.update({SECTIONS[key]: value for key, value in sections.items()})
    return result


def parse(text):
    if not isinstance(text, str) or "```" in text:
        raise ValueError("Return an unfenced Markdown annotation")
    title = re.match(r"\A# Episode: ([^\r\n]+)\r?\n", text)
    if not title:
        raise ValueError("Markdown must start with # Episode: followed by its ID")
    headings = list(re.finditer(r"^## (Identity|Segment (\d+))[ \t]*\r?$", text, re.MULTILINE))
    if len(headings) < 2 or headings[0][1] != "Identity":
        raise ValueError("One identity section and at least one segment are required")
    if text[title.end():headings[0].start()].strip():
        raise ValueError("Unexpected prose before the identity section")
    identity, segments, spans = None, [], []
    for i, heading in enumerate(headings):
        end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        block = text[heading.end():end]
        if i == 0:
            identity = parse_block(block, identity=True)
        else:
            if heading[1] == "Identity" or int(heading[2]) != i:
                raise ValueError("Markdown segment numbers must be chronological and contiguous")
            segments.append(parse_block(block))
        spans.append((heading.start(), end))
    return dict(episode_id=title[1], identity_check=identity, segments=segments), spans


def target_with_masks(value, text=None):
    text = render(value) if text is None else text
    parsed, spans = parse(text)
    if parsed != value:
        raise ValueError("Markdown target changed annotation values")
    if any("uncertain_fields" in s for s in value["segments"]):
        return field_target_with_masks(value, text, spans)
    identity = value["identity_check"]
    identity_mask = identity["match_status"] != "unresolved" and not identity["uncertainty"].strip()
    excluded, masks = [], []
    if not identity_mask:
        excluded.append(dict(start=spans[0][0], end=spans[0][1], reason="uncertain_identity"))
    for index, segment in enumerate(value["segments"]):
        eligible = not segment["review_required"]
        masks.append(dict(segment_index=index, start_frame=segment["start_frame"], end_frame=segment["end_frame"],
                          teacher_loss_mask=int(eligible), review_required=segment["review_required"]))
        if not eligible:
            start, end = spans[index + 1]
            excluded.append(dict(start=start, end=end, reason="review_required_segment", segment_index=index))
    return text, dict(identity_teacher_loss_mask=int(identity_mask), segments=masks,
                      assistant_excluded_char_ranges=excluded,
                      offset_unit="Unicode characters in the assistant text; start inclusive, end exclusive",
                      has_unflagged_segment_targets=any(m["teacher_loss_mask"] for m in masks), human_verified=False)


def field_masks(segment):
    """Conservative v3 whitelist; prose in a flagged segment remains excluded."""
    unknown = set(segment["uncertain_fields"])
    if bool(unknown) != segment["review_required"] or not unknown <= UNCERTAIN_FIELDS:
        raise ValueError("Uncertain fields must agree with the review flag")
    return {"Frames": "timing" not in unknown,
            "Action": not unknown.intersection({"action", "mechanism"}) and segment["action"] != "unknown",
            "Object": "identity" not in unknown,
            "Destination": "identity" not in unknown,
            "Failure": "failure" not in unknown,
            "Categories": not unknown.intersection({"failure", "categories"}),
            "Recovery": not unknown.intersection({"failure", "categories", "recovery"}),
            "Severity": not unknown.intersection({"failure", "severity"}),
            "Resetability": not unknown.intersection({"failure", "resetability"})}


def field_target_with_masks(value, text, spans):
    identity = value["identity_check"]
    identity_mask = identity["match_status"] != "unresolved" and not identity["uncertainty"].strip()
    excluded, masks = [], []
    if not identity_mask:
        excluded.append(dict(start=spans[0][0], end=spans[0][1], reason="uncertain_identity"))
    for index, segment in enumerate(value["segments"]):
        if "uncertain_fields" not in segment:
            raise ValueError("Do not mix v2 and v3 uncertainty contracts")
        fields = field_masks(segment)
        # Usable failure supervision is counted independently of whole-segment review.
        eligible = fields["Failure"]
        masks.append(dict(segment_index=index, start_frame=segment["start_frame"], end_frame=segment["end_frame"],
                          teacher_loss_mask=int(eligible), failure_teacher_loss_mask=int(fields["Failure"]),
                          field_teacher_loss_masks={k: int(v) for k, v in fields.items()},
                          review_required=segment["review_required"]))
        if not segment["review_required"]:
            continue
        start, end = spans[index + 1]
        block = text[start:end]
        # Only explicitly supported scalar labels survive; all flagged narrative,
        # evidence, boundary explanations and uncertainty metadata stay masked.
        allowed = []
        for match in re.finditer(r"^- ([^:\r\n]+): [^\r\n]*(?:\r?\n|$)", block, re.MULTILINE):
            if fields.get(match[1], False):
                allowed.append((start + match.start(), start + match.end()))
        cursor = start
        for a, b in allowed:
            if cursor < a:
                excluded.append(dict(start=cursor, end=a, reason="uncertain_segment_fields", segment_index=index))
            cursor = b
        if cursor < end:
            excluded.append(dict(start=cursor, end=end, reason="uncertain_segment_fields", segment_index=index))
    return text, dict(supervision_contract="field_review_v3", identity_teacher_loss_mask=int(identity_mask),
                      segments=masks, assistant_excluded_char_ranges=excluded,
                      offset_unit="Unicode characters in the assistant text; start inclusive, end exclusive",
                      has_unflagged_segment_targets=any(not s["review_required"] for s in value["segments"]),
                      has_eligible_segment_targets=any(s["teacher_loss_mask"] for s in masks), human_verified=False)
