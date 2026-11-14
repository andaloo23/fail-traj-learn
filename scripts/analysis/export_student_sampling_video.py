"""Export a student observation schedule at original episode speed as MP4."""
import argparse
from fractions import Fraction
import json
import math
from pathlib import Path

import av
from PIL import Image,ImageDraw,ImageFont

REPO=Path(__file__).resolve().parents[2]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--episode',default='O0006')
    p.add_argument('--source',type=Path,default=REPO/'outputs/oopsie_rich_failure_v8_1_500_batch_v1')
    p.add_argument('--sample-fps',type=Fraction,help='Explicit video-time sample rate, e.g. 4/3; otherwise use the fork default rule')
    p.add_argument('--start-seconds',type=Fraction,default=Fraction(0))
    p.add_argument('--duration-seconds',type=Fraction,help='Export a source-time excerpt rather than the full episode')
    p.add_argument('--out',type=Path,default=REPO/'outputs/teacher_sampling_visualization_v1/O0006_student_1.33fps.mp4')
    a=p.parse_args();source=a.source
    m=json.loads((source/'manifest.json').read_text(encoding='utf-8'))
    e=next(e for e in m['episodes'] if e['id']==a.episode)
    rate=Fraction(str(e['fps'])).limit_denominator(1000)
    start=round(a.start_seconds*rate)
    end=min(e['n_frames'],start+round(a.duration_seconds*rate)) if a.duration_seconds is not None else e['n_frames']
    if not 0<=start<end<=e['n_frames']:raise ValueError('Invalid source-time excerpt')
    if len(e['images'])!=e['n_frames'] or [x['frame'] for x in e['images']]!=list(range(e['n_frames'])):
        raise ValueError('Export requires every native source timestamp, with cameras packed in image strips')
    if a.sample_fps is None:
        teacher=sorted(set(range(0,e['n_frames'],5))|{e['n_frames']-1})
        student=[f for i,f in enumerate(teacher) if i%3==0 or i==len(teacher)-1]
        sample_fps=rate/15;policy='fork default sampling rule'
    else:
        sample_fps=a.sample_fps
        if not 0<sample_fps<=rate:raise ValueError('Sample FPS must be positive and no higher than native FPS')
        count=math.ceil(Fraction(e['n_frames']-1)*sample_fps/rate)+1
        student=sorted({round(k*rate/sample_fps) for k in range(count) if round(k*rate/sample_fps)<e['n_frames']}|{0,e['n_frames']-1})
        policy='fixed-rate sampling illustration'
    # Start the excerpt with its own observation and preserve its final frame.
    student=sorted({f for f in student if start<=f<end}|{start,end-1})
    font_path=Path('C:/Windows/Fonts/segoeui.ttf')
    bold_path=Path('C:/Windows/Fonts/seguisb.ttf')
    def font(size,bold=False):
        path=bold_path if bold else font_path
        return ImageFont.truetype(str(path),size) if path.exists() else ImageFont.load_default(size=size)
    images={f:Image.open(source/e['images'][f]['path']).convert('RGB') for f in student}
    width=1120;first=images[student[0]];image_height=round(first.height*width/first.width)
    image_height+=image_height%2;height=image_height+152
    a.out.parent.mkdir(parents=True,exist_ok=True)
    if a.out.exists():raise ValueError('Video already exists; choose another output path')
    with av.open(str(a.out),'w',options={'movflags':'+faststart'}) as output:
        stream=output.add_stream('libx264',rate=rate)
        stream.width=width;stream.height=height;stream.pix_fmt='yuv420p'
        stream.options={'crf':'18','preset':'medium'}
        index=0
        for f in range(start,end):
            while index+1<len(student) and student[index+1]<=f:index+=1
            shown=student[index]
            canvas=Image.new('RGB',(width,height),'#0c111b')
            canvas.paste(images[shown].resize((width,image_height),Image.Resampling.LANCZOS),(0,90))
            draw=ImageDraw.Draw(canvas)
            draw.text((22,10),f"Student view: {float(sample_fps):.2f} observations/sec | original speed",font=font(29,True),fill='#c4afff')
            draw.text((22,51),f"Real OopsieData {e['id']} | {policy}",font=font(21),fill='#a5b4ca')
            draw.text((22,image_height+101),f"Source time {f/e['fps']:.2f}s  |  image from {shown/e['fps']:.2f}s  |  observation {index+1}/{len(student)}",font=font(25),fill='#e8eef8')
            frame=av.VideoFrame.from_image(canvas);frame.pts=f-start;frame.time_base=1/rate
            for packet in stream.encode(frame):output.mux(packet)
        for packet in stream.encode():output.mux(packet)
    with av.open(str(a.out)) as video:
        decoded_count=sum(1 for _ in video.decode(video=0))
        duration=float(video.duration/av.time_base)
        if decoded_count!=end-start or abs(duration-(end-start)/e['fps'])>.01:
            raise ValueError('Export timing differs from source episode')
    report=dict(episode=e['id'],file=str(a.out),source_run=str(source),native_fps=e['fps'],student_regular_fps=float(sample_fps),sampling_policy=policy,
        student_source_frames=student,encoded_frames=decoded_count,duration_seconds=duration,
        source_start_frame=start,source_end_frame=end,source_start_seconds=start/e['fps'],source_end_seconds=end/e['fps'],
        original_speed=True,audio=False,comparison_is_illustrative=True)
    a.out.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report),flush=True)


if __name__=='__main__':main()
