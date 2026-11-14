"""Add fresh Sol/Astra atomic annotations to the existing comparison viewer."""
import shutil

import api_atomic_actions as run


def extend(target, episodes, choices):
    if not (run.OUT / "manifest.json").exists():
        return None
    manifest = run.verify()
    inputs = {ep["id"]: ep for ep in manifest["episodes"]}
    shutil.copyfile(run.OUT / "prompt.txt", target / "atomic_actions_prompt.txt")
    for displayed in episodes:
        eid = displayed["id"]
        if eid not in inputs:
            continue
        ep = inputs[eid]
        if any(displayed[k] != ep[k] for k in ("task", "n_frames", "fps")):
            raise ValueError("Atomic viewer episode metadata differs")
        for name, digest in ep["source_sha256"].items():
            if run.common.digest(run.SOURCE / eid / name) != digest:
                raise ValueError("Atomic source evidence changed")
        folder = target / "atomic_sampled" / eid
        folder.mkdir(parents=True, exist_ok=True)
        for frame in ep["sampled_frames"]:
            for camera in ("agent", "wrist"):
                name = f"{frame:04d}_{camera}.jpg"
                shutil.copyfile(run.OUT / eid / name, folder / name)
        annotations, statuses, evidence = {}, {}, {}
        for column, model in (("openai", "sol"), ("gemini", "astra")):
            name = eid + "_" + model
            path = run.OUT / (name + "_annotation.json")
            value = run.common.load(path) if path.exists() else None
            if value is not None:
                run.validate(value, ep)
            annotations[column] = value
            slot = run.OUT / "attempts" / (name + ".json")
            record = run.common.load(slot) if slot.exists() else {}
            answer = run.OUT / (name + "_answer.txt")
            link = "atomic_" + name + "_answer.txt" if answer.exists() else None
            if link:
                shutil.copyfile(answer, target / link)
            statuses[column] = dict(status=record.get("status", "pending"),
                                    error=record.get("error", ""), raw_link=link, display_note="")
            evidence[column] = dict(
                frames=ep["sampled_frames"], initial_frames=ep["sampled_frames"],
                prefix="atomic_sampled", calls=int(record.get("generation_sent", False)),
                cost=record.get("generation_estimate_usd"),
                allowance=record.get("preflight_allowance_usd", 0), requests=[],
            )
        displayed["versions"]["atomic_actions"] = annotations
        displayed["statuses"]["atomic_actions"] = statuses
        displayed.setdefault("evidence_versions", {})["atomic_actions"] = evidence
    choices.append(dict(
        id="atomic_actions", label="Atomic actions - Sol / Astra",
        columns={"openai": "GPT-6.1 Sol", "gemini": "GPT-6 Astra"},
        heading="Sol vs Astra - shared atomic action prompt",
        prompt_file="atomic_actions_prompt.txt",
    ))
    import evaluate_atomic_descriptions as judge
    judge.export_viewer(target)
    return "atomic_actions"
