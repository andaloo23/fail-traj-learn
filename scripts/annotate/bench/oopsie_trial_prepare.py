"""Prepare outcome-blind inputs for two isolated direct annotation conditions."""
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from common import Episode, open_dataset
from review_oracle import decode_episode, ffmpeg_pipe

OUT = HERE.parents[2] / 'outputs/oopsie_transfer_v1'
SAMPLE = [('full_shift16__t1', 1), ('full_goals8__t2', 1),
          ('full_l90__t74', 1), ('full_shift8__t6', 1)]

def sheet(agent, wrist, frames, path):
    im = Image.new('RGB', (1152, 218 * ((len(frames)+2)//3)), 'white')
    draw = ImageDraw.Draw(im)
    for j, f in enumerate(frames):
        x,y = j%3*384,j//3*218
        pair = Image.fromarray(np.concatenate([agent[f],wrist[f]],axis=1)).resize((384,192))
        im.paste(pair,(x,y+24)); draw.text((x+5,y+5),f'frame {f}',fill='black')
    im.save(path,quality=94)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    entries=[]
    for i,(dsname,idx) in enumerate(SAMPLE):
        ident=f'E{i+1:02d}'
        visual=OUT/'visual'/ident; visual.mkdir(parents=True,exist_ok=True)
        tele=OUT/'telemetry'/ident;tele.mkdir(parents=True,exist_ok=True)
        ds=open_dataset(dsname);ep=Episode(ds,dsname,idx)
        a,w,_=decode_episode(ds,ep)
        meta=dict(id=ident,task=ep.task,n_frames=ep.n,fps=ep.fps,
                  cameras=['external','wrist'],frame_bounds='zero-based, end exclusive')
        (visual/'metadata.json').write_text(json.dumps(meta,indent=2))
        np.savez_compressed(visual/'cameras.npz',agent=a,wrist=w)
        frames=list(range(0,ep.n,5))
        if frames[-1]!=ep.n-1:frames.append(ep.n-1)
        for j in range(0,len(frames),24):sheet(a,w,frames[j:j+24],visual/f'sheet_{j//24:02d}.jpg')
        proc=ffmpeg_pipe(visual/'raw.mp4',512,280,ep.fps)
        for f in range(ep.n):
            im=Image.new('RGB',(512,280),'white');im.paste(Image.fromarray(np.concatenate([a[f],w[f]],axis=1)),(0,24))
            ImageDraw.Draw(im).text((5,5),f'frame {f}',fill='black');proc.stdin.write(im.tobytes())
        proc.stdin.close();assert proc.wait()==0
        # Strict input allowlist: never read priv.*, outcome, chunk labels, or reference files.
        state=ep.col('observation.state');action=ep.col('action')
        rows=[dict(frame=f,eef_xyz_m=state[f,:3].round(5).tolist(),
                   eef_axis_angle_rad=state[f,3:6].round(5).tolist(),
                   finger_qpos_m=state[f,6:8].round(5).tolist(),
                   gripper_command='close' if action[f,6]>0 else 'open') for f in range(ep.n)]
        (tele/'robot.json').write_text(json.dumps(dict(
            notes='Measured end-effector position/orientation and finger joint positions; finger qpos is not total aperture. Gripper command decoded from action[6], positive close. Arm controller deltas omitted because physical conversion unverified.',
            rows=rows),indent=2))
        entries.append(dict(id=ident,dataset=dsname,episode_index=idx,n_frames=ep.n,fps=ep.fps))
        print(ident,ep.n,'prepared',flush=True)
    (OUT/'private_manifest.json').write_text(json.dumps(entries,indent=2))

if __name__=='__main__':main()
