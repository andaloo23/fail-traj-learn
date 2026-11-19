"""Derived MP4s showing native cameras, reconciled labels and exact carried tails.

The full MP4 retains source chronology and duration. Individual part MP4s contain
exactly their two context frames followed by their disjoint new-frame interval.
Every encoded frame's timestamp, label color, part ID and context role is checked.
Native source media, prompts, requests and responses are never modified.
"""
import argparse
from fractions import Fraction
import html
import json
from pathlib import Path

import av
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

import corral_astra_window_pilot as pilot

SIZE=(1920,1080)
TIME_BASE=Fraction(1,90000)
BG='#101720'; PANEL='#1a2735'; WHITE='#eff5ff'; MUTED='#bbcadb'
LABEL_COLORS={False:'#276b56',True:'#9b3849'}
ROLE_COLORS={'new':'#23485e','tail':'#b88622','context':'#a45b22'}
PART_COLORS=['#387ab4','#755aab','#347e72','#a16e35','#835d8a','#527fa1']
FONT_ROOT=Path('C:/Windows/Fonts')


def font(size,bold=False):
    return ImageFont.truetype(str(FONT_ROOT/('segoeuib.ttf' if bold else 'segoeui.ttf')),size)


def wrap(text,f,width):
    lines=[]
    for paragraph in text.split('\n'):
        line=''
        for word in paragraph.split():
            candidate=(line+' '+word).strip()
            if line and f.getlength(candidate)>width:
                lines.append(line);line=word
            else:line=candidate
        lines.append(line)
    return lines


def fit_text(draw,text,box,size=22,minimum=16,fill=WHITE,bold=False):
    x,y,right,bottom=box
    for pts in range(size,minimum-1,-1):
        f=font(pts,bold);lines=wrap(text,f,right-x);step=pts+5
        if len(lines)*step<=bottom-y:
            for i,line in enumerate(lines):draw.text((x,y+i*step),line,font=f,fill=fill)
            return
    raise ValueError('Annotation text does not fit; never silently truncate: '+text[:100])


def role(w,index,last=False):
    if index<w['start']:return 'context'
    if not last and index>=w['end']-2:return 'tail'
    return 'new'


def expected_rgb(color):
    return np.array([int(color[i:i+2],16) for i in (1,3,5)],dtype=int)


class Encoder:
    def __init__(self,path,fps):
        self.path=path;path.parent.mkdir(parents=True,exist_ok=True)
        self.partial=path.with_suffix('.partial.mp4')
        self.container=av.open(str(self.partial),'w',options={'movflags':'+faststart'})
        self.stream=self.container.add_stream('libx264',rate=fps)
        self.stream.width,self.stream.height=SIZE;self.stream.pix_fmt='yuv420p'
        self.stream.time_base=TIME_BASE;self.stream.codec_context.time_base=TIME_BASE
        self.stream.codec_context.thread_count=4
        self.stream.options={'crf':'20','preset':'veryfast'}
        self.frames=0

    def add(self,image,seconds):
        frame=av.VideoFrame.from_image(image);frame.pts=round(seconds/TIME_BASE);frame.time_base=TIME_BASE
        for packet in self.stream.encode(frame):self.container.mux(packet)
        self.frames+=1

    def close(self):
        for packet in self.stream.encode():self.container.mux(packet)
        self.container.close()


class Renderer:
    def __init__(self,root,plan,e,final):
        self.root,self.plan,self.e,self.final=root,plan,e,final;self.cache={}
        self.parts=plan['windows'];self.segments=final['segments']
        self.part_predictions={w['id']:pilot.common.read(root/'traces'/w['id']/'parsed.json') for w in self.parts}
        self.tails={}
        for i,w in enumerate(self.parts):
            if i:
                self.tails[i]=[]
                for index in range(w['context_start'],w['start']):
                    im=e['images'][index];path=root/im['path']
                    assert pilot.common.sha(path)==im['sha256']
                    with Image.open(path) as source:
                        self.tails[i].append((index,ImageOps.contain(source.convert('RGB'),(596,119))))
        count=len(e['videos']);width=(1196-12*(count-1))//count
        self.slots=[(24+i*(width+12),228,width,355) for i in range(count)]

    def background(self,part_index,segment_index,phase):
        key=(part_index,segment_index,phase)
        if key in self.cache:return self.cache[key].copy()
        e=self.e;w=self.parts[part_index];s=self.segments[segment_index]
        image=Image.new('RGB',SIZE,BG);d=ImageDraw.Draw(image)
        d.text((24,16),f'{e["id"]}  |  Astra annotation  |  Episode outcome: {self.final["success_label"].upper()}',font=font(28,True),fill=WHITE)
        d.rectangle((1180,25,1212,57),fill=PART_COLORS[part_index%len(PART_COLORS)])
        d.rounded_rectangle((1248,17,1896,60),radius=7,fill=ROLE_COLORS[phase])
        headline={'new':'NEW FRAMES: label this part only','tail':'LAST 2 FRAMES: reused in the next call','context':'CARRIED CONTEXT ONLY: do not relabel'}[phase]
        d.text((1268,25),headline,font=font(22,True),fill=WHITE)
        fit_text(d,'Task: '+e['task'],(24,65,1896,112),size=22,minimum=18)
        for i,p in enumerate(self.parts):
            x=24+round(1872*p['start']/e['n_frames']);right=24+round(1872*p['end']/e['n_frames'])
            d.rectangle((x,116,right-2,151),fill=PART_COLORS[i%len(PART_COLORS)] if i==part_index else '#283648')
            label=f'PART {i+1}' if right-x>85 else str(i+1)
            d.text((x+8,120),label,font=font(19,True),fill=WHITE)
            if i<len(self.parts)-1:
                tx=24+round(1872*(p['end']-2)/e['n_frames'])
                d.rectangle((tx,116,max(tx+2,right-2),151),fill=ROLE_COLORS['tail'])
        d.text((24,164),f'Part {part_index+1}/{len(self.parts)}: NEW annotation interval [{w["start"]}, {w["end"]})',font=font(24,True),fill=WHITE)
        for video,(x,y,width,height) in zip(e['videos'],self.slots):
            d.text((x,201),video['camera'],font=font(21,True),fill=MUTED)
            d.rectangle((x,y,x+width,y+height),fill='#03070c')
        d.rounded_rectangle((1240,161,1896,1038),radius=12,fill=PANEL)
        d.text((1256,174),f'Context supplied to part {part_index+1}',font=font(26,True),fill=WHITE)
        if part_index:
            for j,(index,thumb) in enumerate(self.tails[part_index]):
                y=216+j*157
                d.text((1256,y),f'Tail frame {index}  |  {e["images"][index]["seconds"]:.3f} s',font=font(21,True),fill='#ffd78c')
                image.paste(thumb,(1256,y+31));d.rectangle((1254,y+29,1258+thumb.width,y+33+thumb.height),outline='#e0ac4e',width=2)
            previous=self.part_predictions[w['previous_window']];tail=previous['segments'][-1]
            d.text((1256,541),'PREVIOUS PART: TAIL PREDICTION',font=font(22,True),fill='#ffd78c')
            label='FAILURE' if tail['failure'] else 'NO LOCAL FAILURE'
            d.text((1256,576),f'{label}  [{tail["start_frame"]}, {tail["end_frame"]})',font=font(22,True),fill=WHITE)
            if tail['failure']:
                annotation=next(a for a in previous['failure_annotations'] if a['start_frame']==tail['start_frame'])
                text=annotation['explanation']+'\nSeverity: '+annotation['severity']+'\nResetability: '+annotation['resetability']
            else:text='The previous part ends without an annotated local failure. This provisional prediction does not establish episode success.'
            fit_text(d,text,(1256,619,1880,927),size=21,minimum=17)
            fit_text(d,'These TWO images are context only. The API also received the complete previous part annotation; its tail is shown above.',(1256,947,1880,1027),size=19,minimum=17,fill=MUTED)
        else:
            fit_text(d,'No preceding part.\n\nAll frames in part 1 are new.\n\nLater calls receive exactly TWO preceding source frames plus the previous part annotation.\n\nGold ticks on the top strip mark those two-frame tails.\n\nNew annotation intervals remain disjoint.',(1260,245,1870,900),size=26,minimum=23,fill=MUTED)
        d.rounded_rectangle((24,625,1220,1038),radius=12,fill=PANEL)
        d.rounded_rectangle((40,641,268,686),radius=6,fill=LABEL_COLORS[s['failure']])
        d.text((62,647),'FAILURE' if s['failure'] else 'NO FAILURE',font=font(27,True),fill=WHITE)
        d.text((290,646),f'FINAL reconciled label  |  [{s["start_frame"]}, {s["end_frame"]})',font=font(23,True),fill=WHITE)
        if s['failure']:
            a=next(a for a in self.final['failure_annotations'] if a['start_frame']==s['start_frame'])
            text=('Categories: '+', '.join(a['categories'])+'\nExplanation: '+a['explanation']+
                '\nRecovery: '+a['recovery']+'\nSeverity: '+a['severity']+'. '+a['severity_evidence']+
                '\nResetability: '+a['resetability']+'. '+a['resetability_evidence'])
        else:text='No local failure is annotated in this interval. This does not certify overall task success.\n\n'+self.final['outcome_evidence']
        fit_text(d,text,(42,702,1200,1020),size=22,minimum=16)
        self.cache[key]=image
        return image.copy()

    def render(self,index,part_index,segment_index,phase,cameras):
        image=self.background(part_index,segment_index,phase);d=ImageDraw.Draw(image)
        for camera,(x,y,width,height) in zip(cameras,self.slots):
            fitted=ImageOps.contain(camera,(width,height),Image.Resampling.LANCZOS)
            image.paste(fitted,(x+(width-fitted.width)//2,y+(height-fitted.height)//2))
        seconds=self.e['images'][index]['seconds']
        d.text((24,591),f'SOURCE FRAME {index}/{self.e["n_frames"]-1}  |  {seconds:.3f} / {self.e["duration_seconds"]:.3f} s',font=font(20,True),fill=WHITE)
        d.text((24,1048),'Derived review video | Original source timing | Part labels are provisional; final labels are reconciled | Human review pending',font=font(18),fill=MUTED)
        cursor=24+round(1872*index/self.e['n_frames']);d.line((cursor,113,cursor,154),fill='white',width=3)
        return image


def check_encoded(encoder,indices,parts,segments,e,fixed_part=None):
    part_index=segment_index=0;origin=e['images'][indices[0]]['seconds'];checked=0
    with av.open(str(encoder.partial)) as container:
        stream=container.streams.video[0]
        assert stream.width==SIZE[0] and stream.height==SIZE[1]
        for count,frame in enumerate(container.decode(stream)):
            assert count<len(indices),'Extra encoded frames'
            index=indices[count]
            while index>=parts[part_index]['end']:part_index+=1
            while index>=segments[segment_index]['end_frame']:segment_index+=1
            shown=part_index if fixed_part is None else fixed_part
            phase=role(parts[shown],index,shown==len(parts)-1)
            actual=float(frame.pts*frame.time_base);expected=e['images'][index]['seconds']-origin
            assert abs(actual-expected)<.0001,(index,actual,expected)
            pixels=frame.to_ndarray(format='rgb24')
            for y,x,color in [(650,48,LABEL_COLORS[segments[segment_index]['failure']]),
                               (44,1196,PART_COLORS[shown%len(PART_COLORS)]),
                               (30,1260,ROLE_COLORS[phase])]:
                observed=pixels[y-1:y+2,x-1:x+2].mean(axis=(0,1))
                assert np.max(np.abs(observed-expected_rgb(color)))<35,(index,observed,color)
            checked+=1
        assert checked==len(indices),(checked,len(indices))
    encoder.partial.replace(encoder.path)
    return dict(path=encoder.path.name,frames=checked,source_first=indices[0],source_last=indices[-1],
        all_timestamps_verified=True,all_label_part_role_colors_verified=True,
        sha256=pilot.common.sha(encoder.path),bytes=encoder.path.stat().st_size)


def export(root,out):
    plan,e=pilot.verify(root);eid=e['id'];parts=plan['windows']
    final=pilot.common.read(root/'traces'/f'{eid}_final'/'parsed.json')
    if out.exists():raise ValueError('Export version already exists; preserve it and choose a new version')
    out.mkdir(parents=True)
    for video in e['videos']:assert pilot.common.sha(root/video['url'])==video['sha256']
    render=Renderer(root,plan,e,final);fps=Fraction(str(e['fps'])).limit_denominator(10000)
    main=Encoder(out/f'{eid}_annotated_parts.mp4',fps)
    clips={};finished={};containers=[av.open(str(root/v['url'])) for v in e['videos']]
    decoders=[iter(c.decode(video=0)) for c in containers];part_index=segment_index=0
    checkpoints={0,parts[1]['start']-2,parts[1]['start']-1,parts[1]['start'],e['n_frames']-1}
    try:
        for index in range(e['n_frames']):
            cameras=[];seconds=e['images'][index]['seconds']
            for decoder in decoders:
                frame=next(decoder);assert abs(float(frame.pts*frame.time_base)-seconds)<.001
                cameras.append(frame.to_image().convert('RGB'))
            while index>=parts[part_index]['end']:part_index+=1
            while index>=final['segments'][segment_index]['end_frame']:segment_index+=1
            phase=role(parts[part_index],index,part_index==len(parts)-1)
            image=render.render(index,part_index,segment_index,phase,cameras)
            main.add(image,seconds)
            if index in checkpoints:image.save(out/f'preview_frame_{index:06d}.jpg',quality=94)
            for i,w in enumerate(parts):
                if w['context_start']<=index<w['end']:
                    if i not in clips:clips[i]=Encoder(out/'parts'/f'{eid}_part_{i+1:02d}_api_input.mp4',fps)
                    clip_image=image if i==part_index else render.render(index,i,segment_index,'context',cameras)
                    clips[i].add(clip_image,seconds-e['images'][w['context_start']]['seconds'])
                    if index==w['end']-1:clips[i].close();finished[i]=clips[i]
            if index%150==0:print(eid,'rendered',index,'/',e['n_frames'],flush=True)
        assert all(next(d,None) is None for d in decoders)
        main.close()
    finally:
        for c in containers:c.close()
    print(eid,'validating every encoded frame',flush=True)
    checks=[check_encoded(main,list(range(e['n_frames'])),parts,final['segments'],e)]
    for i,w in enumerate(parts):
        checks.append(check_encoded(finished[i],list(range(w['context_start'],w['end'])),parts,final['segments'],e,i))
    for video in e['videos']:assert pilot.common.sha(root/video['url'])==video['sha256']
    manifest=dict(episode=eid,derived_artifact=True,teacher_model='gpt-6-astra',source_episode_sha256=plan['episode_sha256'],
        final_response_sha256=pilot.common.sha(root/'traces'/f'{eid}_final'/'response.json'),source_frames=e['n_frames'],
        source_duration_seconds=e['duration_seconds'],source_camera_count=len(e['videos']),
        main_video_has_no_repeated_frames_or_review_holds=True,source_frame_pts_verified_all_cameras=True,
        new_label_intervals_disjoint=True,part_clips_have_exact_two_context_frames=True,
        windows=parts,encoded_checks=checks,human_label_correctness_verified=False)
    pilot.transport.atomic_json(out/'manifest.json',manifest)
    rows=['# Disjoint parts and the exact two carried frames','',
        'Full MP4: original source timeline, one rendered frame per source frame. Part MP4s: '
        'two preceding context frames followed by new frames, at original playback speed. No artificial holds. '
        'Context thumbnails persist so the two brief frames remain inspectable. All intervals below are start-inclusive, end-exclusive.','',
        '| Part | New annotation interval | Tail frames supplied as context | Previous annotation | MP4 |','|---|---|---|---|---|']
    links=[]
    for i,w in enumerate(parts):
        tail=', '.join(str(x) for x in range(w['context_start'],w['start'])) or 'None'
        previous=w['previous_window'] or 'None'
        name=f'parts/{eid}_part_{i+1:02d}_api_input.mp4'
        rows.append(f'| {i+1} | [{w["start"]}, {w["end"]}) | {tail} | {previous} | [Part {i+1}]({name}) |')
        links.append(f'<li><a href="{name}">Part {i+1} MP4</a>: new frames [{w["start"]}, {w["end"]}); carried frames {tail}. '
                     f'<a href="../traces/{w["id"]}/annotation.md">Native part annotation</a></li>')
    (out/'parts.md').write_text('\n'.join(rows)+'\n',encoding='utf-8')
    page=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{eid} annotated MP4 review</title><style>body{{max-width:1600px;margin:24px auto;padding:0 20px;background:#101720;color:#eff5ff;font:17px/1.5 system-ui}}a{{color:#a9d0ff}}video{{width:100%;background:black}}li{{margin:10px 0}}</style>
<h1>{eid}: annotated parts and carried tail frames</h1><p>{html.escape(e['task'])}</p>
<p>{e['n_frames']:,} original frames · {e['duration_seconds']:.2f} seconds · {len(e['videos'])} camera views · {len(parts)} disjoint parts.</p>
<video controls playsinline preload="metadata" poster="preview_frame_000000.jpg" src="{eid}_annotated_parts.mp4"></video>
<p><a href="{eid}_annotated_parts.mp4" download>Download full annotated MP4</a> · <a href="../review.html">Interactive labels and review notes</a> · <a href="parts.md">Exact part/frame table</a></p>
<p>Gold ticks mark the two frames reused by the next call. The right panel keeps those exact two frames visible throughout each subsequent part, with the previous part's tail prediction. The API received the complete previous annotation. Main video labels show the final reconciliation.</p>
<p>The full MP4 preserves source timing. Each part MP4 begins with its two context frames, followed by its new disjoint interval; context is clearly marked and is not labeled again. The two frames play briefly at source rate; pause or inspect the persistent thumbnails.</p>
<h2>Individual part review clips</h2><ol>{''.join(links)}</ol><p>These MP4s visualize the source frames supplied to each call. Burned-in review labels and graphics were added afterward and were not model image inputs. Source videos and native teacher outputs are preserved. Human label review remains pending.</p></html>'''
    (out/'index.html').write_text(page,encoding='utf-8')
    print(json.dumps(dict(episode=eid,mp4=str(main.path),all_encoded_checks_passed=True,files=len(checks))),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--out',type=Path)
    args=parser.parse_args();root=args.run.resolve()
    export(root,args.out.resolve() if args.out else root/'exports_v1')
