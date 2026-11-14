"""Speed the completed presentation up four times and burn in the speed label."""
import hashlib
import json
from pathlib import Path
import subprocess

import av
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'outputs/astra_joint_presentation_50_20261109_v1'


def wsl(path):
    return '/mnt/c/' + path.resolve().relative_to(Path('C:/')).as_posix()


def main():
    source = OUT / 'astra_joint_all_50.mp4'
    target = OUT / 'astra_joint_all_50_4x.mp4'
    if target.exists():
        raise ValueError('The 4x export already exists; no overwrite')
    manifest = json.loads((OUT / 'manifest.json').read_text())
    text = OUT / 'speed_label_4x.txt'
    text.write_text('Sped up 4×', encoding='utf-8')
    with av.open(str(source)) as original:
        metadata = dict(original.metadata)
        source_frames = original.streams.video[0].frames
        original_duration = original.duration / av.time_base
    # Select exact source frames 0,4,8,..., then retime them to 30 FPS.
    # Existing frame-aligned overlays remain attached to their source pictures.
    vf = ("select='not(mod(n,4))',setpts=N/(30*TB),"
          'drawtext=fontfile=/mnt/c/Windows/Fonts/seguisb.ttf:textfile=' + wsl(text) +
          ':fontcolor=white:fontsize=40:x=w-tw-48:y=24:box=1:boxcolor=0x34435f@0.95:boxborderw=14')
    command = ['wsl.exe', '-d', 'Ubuntu-22.04', '--exec', 'ffmpeg', '-hide_banner', '-n',
               '-i', wsl(source), '-map', '0:v:0', '-vf', vf, '-r', '30', '-an',
               '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-threads', '8',
               '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-map_metadata', '0',
               '-metadata', 'title=Astra / Joint-trained Qwen | all 50 episodes | Sped up 4x',
               '-metadata', 'comment=' + metadata.get('comment', '') + ' Playback speed: 4x, visibly labeled.',
               wsl(target)]
    with (OUT / 'speed_4x_encode.log').open('w', encoding='utf-8') as log:
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=log, check=True,
                       creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    count = 0
    with av.open(str(target)) as container:
        stream = container.streams.video[0]
        if (stream.width, stream.height) != (1920, 1080):
            raise ValueError('Presentation dimensions changed')
        for index, frame in enumerate(container.decode(video=0)):
            if abs(float(frame.pts * frame.time_base) - index / 30) > 1e-5:
                raise ValueError('Sped-up presentation frame timing changed')
            if index == 0:
                image = frame.to_image()
                image.save(OUT / 'speed_4x_preview.jpg', quality=95)
                banner = np.asarray(image)[12:92, 1490:1900]
                if np.count_nonzero(np.all(banner > 220, axis=2)) < 250:
                    raise ValueError('Visible speed label was not rendered')
            count += 1
        duration = container.duration / av.time_base
    if count != (source_frames + 3) // 4 or abs(duration * 4 - original_duration) > .04:
        raise ValueError('Export does not run at exactly four times the source speed')
    with target.open('rb') as f:
        digest = hashlib.file_digest(f, 'sha256').hexdigest()
    result = dict(file=target.name, speed_multiplier=4, visible_label='Sped up 4×',
        episodes=50, source_frames=source_frames, encoded_frames=count, fps=30,
        source_duration_seconds=original_duration, duration_seconds=duration,
        dimensions=[1920, 1080], sha256=digest, original_preserved=True,
        source_frame_selection='Every fourth presentation frame, beginning at frame 0',
        chapters=[dict(episode=c['episode'], start_seconds=c['start_seconds'] / 4,
                       duration_seconds=c['duration_seconds'] / 4) for c in manifest['chapters']])
    (OUT / 'speed_4x_manifest.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)


if __name__ == '__main__':
    main()
