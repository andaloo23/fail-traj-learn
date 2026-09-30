# GPT-6 v3 review instructions

This review uses a local browser viewer. It works on Windows, macOS, and Linux;
the only difference is how the Python virtual environment is activated.

## Get the review pack

Download [gpt6_v3_12_episode_review_pack.zip](https://drive.google.com/file/d/1-VDFWZSHHNnA2VW2IijQZrRHaJAhjFzE/view), then put it in the repository root.

Manual download is the recommended path. Google Drive can require a signed-in
account or an interstitial confirmation, which makes an unattended download
unreliable. The viewer accepts either the downloaded ZIP or its extracted
`gpt6_v3_12_episode_review_pack/` directory.

## Start the viewer on Windows PowerShell

```powershell
py -3.12 -m venv .venv-review
.\.venv-review\Scripts\Activate.ps1
python -m pip install -r scripts\annotate\review_requirements.txt
python scripts\annotate\launch_gpt6_v3_review.py .\gpt6_v3_12_episode_review_pack.zip
```

If PowerShell says that scripts are disabled, activate it for the current
session before the second command:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
```

## Start the viewer on macOS or Linux

```bash
python3 -m venv .venv-review
source .venv-review/bin/activate
python -m pip install -r scripts/annotate/review_requirements.txt
python scripts/annotate/launch_gpt6_v3_review.py ./gpt6_v3_12_episode_review_pack.zip
```

The final command opens a browser tab, or prints a `http://127.0.0.1:8765/`
URL to open locally. Stop the viewer with Ctrl-C.

For later runs, activate the existing `.venv-review` and rerun only the final
command.

## Review and save

For each episode R001 through R012, inspect both camera streams and compare the
candidate segments, outcome, failure type, event timing, evidence frames, and
uncertainty notes with what is visible. Use `unknown` if the camera evidence
cannot establish a claim. Select `accepted` when the candidate is supported, or
`corrected` and leave a brief reason when you make a material change.

Click **Save** before moving to another episode. Without `--reviewer`, the
viewer saves your work as `review_preview.json` beside each episode, and never
modifies the frozen `gpt6_fewshot_v3_annotation.json` candidate.
