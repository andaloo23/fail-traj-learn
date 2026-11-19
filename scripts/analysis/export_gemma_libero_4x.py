"""Render preserved LIBERO results in the established 1080p, 4x MP4 style."""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from fractions import Fraction
import html
import json
from pathlib import Path

import av
import numpy as np
from PIL import Image, ImageDraw

import export_teacher_joint_side_by_side as style

REPO=Path(__file__).resolve().parents[2]
RUN=REPO/'outputs/partner_gemma4_libero_native_20261113_v1'
SIZE=(1920,1080)
FPS=Fraction(30)
COLORS={True:'#a33542',False:'#226b51',None:'#606c7e'}
font,sha,at=style.font,style.sha,style.at
NAME='sol_gemma_libero_all_50_4x.mp4'


def metadata():
    return dict(title='Sol / Partner Gemma | LIBERO validation 50 | Sped up 4x',
        comment='Derived presentation of preserved gpt-6.1-sol references and partner Gemma-4-E4B-it adapter outputs. '
        'Exactly 50 original LIBERO validation episodes. Strictly invalid episode timelines remain Unknown. '
        'Playback speed 4x; native outputs unchanged; no new inference or teacher calls.')


def base_canvas(e,position):
    image=Image.new('RGB',SIZE,'#101722');d=ImageDraw.Draw(image)
    d.text((30,14),f"Episode {position+1} / 50  |  {e['id']}",font=font(34,True),fill='#eef4fc')
    task='Task: '+e['task'];size=29 if d.textlength(task,font=font(29))<1850 else 25
    d.text((30,64),task,font=font(size),fill='#d4e1f1')
    for x,title,key in [(24,'Sol reference','sol'),(972,'Partner Gemma','partner')]:
        d.rounded_rectangle((x,134,x+924,1014),radius=14,fill='#192433',outline='#3a4c64',width=2)
        d.text((x+24,152),title,font=font(40,True),fill='#eef3fc')
        d.text((x+24,198),'Failure / non-failure',font=font(20),fill='#bacbdd')
        for s in e['teachers'][key][0]['segments']:
            a=x+24+round(876*s['start_frame']/e['n_frames']);b=x+24+round(876*s['end_frame']/e['n_frames'])
            d.rectangle((a,918,max(a,b-1),944),fill=COLORS[s['failure']])
        for px,camera in [(24,'Agent camera'),(472,'Wrist camera')]:
            d.text((x+px,348),camera,font=font(22,True),fill='#c8d8ea')
        invalid=any(s['failure'] is None for s in e['teachers'][key][0]['segments'])
        note='UNKNOWN: invalid timeline (extra zero-length segment)' if invalid else 'Original LIBERO validation episode'
        d.text((x+24,842),note,font=font(24),fill='#d4e1f1')
        d.text((x+24,955),'0.00 s',font=font(21),fill='#bacbdd')
        end=f"{e['n_frames']/e['fps']:.2f} s"
        d.text((x+900-d.textlength(end,font=font(21)),955),end,font=font(21),fill='#bacbdd')
    banner='Sped up 4\u00d7';width=d.textlength(banner,font=font(40,True))
    d.rounded_rectangle((1920-width-70,10,1890,81),radius=10,fill='#34435f')
    d.text((1920-width-50,20),banner,font=font(40,True),fill='white')
    d.text((1030,1030),'Red: failure | Green: non-failure | Gray: unknown',font=font(23),fill='#cfdeef')
    return image


def status(base,e,f):
    canvas=base.copy();d=ImageDraw.Draw(canvas)
    for x,key in [(24,'sol'),(972,'partner')]:
        s=at(e['teachers'][key][0]['segments'],f);label=s['failure']
        d.rounded_rectangle((x+24,229,x+900,283),radius=9,fill=COLORS[label])
        text='UNKNOWN' if label is None else 'FAILURE' if label else 'NON-FAILURE'
        d.text((x+44,234),text,font=font(31,True),fill='white')
        d.text((x+24,294),f"{s['start_frame']/e['fps']:.2f}-{s['end_frame']/e['fps']:.2f} s  |  frames [{s['start_frame']}, {s['end_frame']})",font=font(23),fill='#d4e1f0')
    return canvas


def verify(path,expected,chapters):
    count=0;chapter_index=0
    with av.open(str(path)) as container:
        stream=container.streams.video[0]
        assert (stream.width,stream.height)==SIZE and stream.average_rate==FPS
        for i,frame in enumerate(container.decode(video=0)):
            assert abs(float(frame.pts*frame.time_base)-i/30)<1e-5
            while i>=chapters[chapter_index]['end_output_frame']:chapter_index+=1
            c=chapters[chapter_index];f=c['selected_source_frames'][i-c['start_output_frame']]
            pixels=frame.reformat(width=192,height=108,format='rgb24').to_ndarray()
            for x,key in [(88,'sol'),(183,'partner')]:
                color=COLORS[at(c['tracks'][key],f)['failure']]
                target=np.array([int(color[j:j+2],16) for j in (1,3,5)])
                assert np.max(np.abs(pixels[25,x].astype(int)-target))<=30,(i,f,color)
            assert np.count_nonzero(np.all(pixels[1:9,159:189]>120,axis=2))>10,'Missing speed banner'
            count+=1
        duration=container.duration/av.time_base
    assert count==expected and abs(duration-count/30)<.02
    return dict(encoded_frames=count,fps=30,dimensions=list(SIZE),duration_seconds=duration,
        every_encoded_label_and_timestamp_checked=True,every_encoded_speed_banner_checked=True,sha256=sha(path))


def render(job):
    out,e,position,selected,reuse=job;out=Path(out);path=out/'episodes'/f"{e['id']}_4x.mp4"
    c=dict(episode=e['id'],position=position+1,task=e['task'],source_frames=e['n_frames'],source_fps=e['fps'],
        selected_source_frames=selected,tracks={k:e['teachers'][k][0]['segments'] for k in ['sol','partner']},
        start_output_frame=0,end_output_frame=len(selected),file=path.relative_to(out).as_posix())
    if path.exists():
        assert reuse,'Existing episode export; choose a new version'
        try:return dict(c,**verify(path,len(selected),[c]))
        except (AssertionError,OSError,ValueError,IndexError):
            # Keep interrupted encodes for provenance; verified clips are reused.
            index=1
            previous=path.with_name(path.stem+f'.interrupted_{index}.mp4')
            while previous.exists():
                index+=1;previous=path.with_name(path.stem+f'.interrupted_{index}.mp4')
            path.rename(previous)
    base=base_canvas(e,position);source=REPO/'outputs/sol_v8_distillation_500/source'/e['id']/'cameras.npz'
    cached=None;signature=None
    with np.load(source) as cameras, av.open(str(path),'w',options={'movflags':'+faststart'}) as dest:
        dest.metadata.update(metadata());stream=dest.add_stream('libx264',rate=FPS)
        stream.width,stream.height=SIZE;stream.pix_fmt='yuv420p';stream.options={'crf':'18','preset':'veryfast'}
        stream.codec_context.thread_count=4
        arrays={k:cameras[k] for k in ['agent','wrist']}
        assert all(a.shape==(e['n_frames'],256,256,3) for a in arrays.values())
        for index,f in enumerate(selected):
            key=tuple(at(c['tracks'][k],f)['start_frame'] for k in ['sol','partner'])
            if key!=signature:cached=status(base,e,f);signature=key
            canvas=cached.copy()
            for camera,px in [('agent',24),('wrist',472)]:
                picture=Image.fromarray(arrays[camera][f]).resize((428,428),Image.Resampling.LANCZOS)
                for offset in (24,972):canvas.paste(picture,(offset+px,380))
            d=ImageDraw.Draw(canvas)
            for x in (24,972):
                cursor=x+24+round(876*f/e['n_frames']);d.rectangle((cursor,912,cursor+2,950),fill='white')
            d.text((30,1030),f"Source {f/e['fps']:.2f} / {e['n_frames']/e['fps']:.2f} s  |  Frame {f} / {e['n_frames']-1}",font=font(23),fill='#cfdeef')
            if index==len(selected)//2:canvas.save(path.with_suffix('.jpg'),quality=95)
            frame=av.VideoFrame.from_image(canvas);frame.pts=index;frame.time_base=Fraction(1,30)
            for packet in stream.encode(frame):dest.mux(packet)
        for packet in stream.encode():dest.mux(packet)
    c.update(verify(path,len(selected),[c]));return c


def concatenate(out,chapters):
    target=out/NAME;assert not target.exists();start=0
    with av.open(str(out/chapters[0]['file'])) as first:
        with av.open(str(target),'w',options={'movflags':'+faststart'}) as dest:
            dest.metadata.update(metadata());output=dest.add_stream_from_template(first.streams.video[0])
            for c in chapters:
                with av.open(str(out/c['file'])) as source:
                    stream=source.streams.video[0];offset=Fraction(start,30)/stream.time_base;assert offset.denominator==1
                    for packet in source.demux(stream):
                        if packet.pts is None or packet.dts is None:continue
                        packet.pts+=int(offset);packet.dts+=int(offset);packet.stream=output;dest.mux(packet)
                c.update(start_output_frame=start,end_output_frame=start+c['encoded_frames'],start_seconds=start/30)
                start+=c['encoded_frames']
    return verify(target,start,chapters)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--reuse-rendered',action='store_true');args=p.parse_args();out=args.out.resolve()
    assert not out.exists() or args.reuse_rendered,'Choose a new output version'
    assert not (out/'manifest.json').exists() and not (out/NAME).exists(),'Completed export already exists'
    data=json.loads((RUN/'review_data.json').read_text(encoding='utf-8'));plan=json.loads((RUN/'plan.json').read_text())
    episodes=data['episodes'];assert len(episodes)==50 and [e['id'] for e in episodes]==plan['episode_ids']
    provenance=json.loads((RUN/'review_provenance.json').read_text())
    out.mkdir(parents=True,exist_ok=args.reuse_rendered);(out/'episodes').mkdir(exist_ok=args.reuse_rendered)
    jobs=[];source_offset=0
    for index,e in enumerate(episodes):
        assert e['fps']==20 and all(len(e['teachers'][k])==1 for k in ['sol','partner'])
        source=REPO/'outputs/sol_v8_distillation_500/source'/e['id']/'cameras.npz'
        assert sha(source)==provenance['media'][e['id']]['source_npz_sha256'],'Source cameras changed'
        assert sha(RUN/'predictions'/f"{e['id']}.json")==provenance['source_prediction_sha256'][e['id']],'Native output changed'
        first=(source_offset*3+7)//8;last=((source_offset+e['n_frames'])*3+7)//8
        selected=[k*8//3-source_offset for k in range(first,last)]
        assert selected and all(0<=f<e['n_frames'] for f in selected)
        jobs.append((str(out),e,index,selected,args.reuse_rendered));source_offset+=e['n_frames']
    records=[]
    with ProcessPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(render,j) for j in jobs]
        for future in as_completed(futures):
            records.append(future.result());print(f"Rendered and verified {len(records)}/50: {records[-1]['episode']}",flush=True)
            (out/'progress.md').write_text(f'# LIBERO 4x MP4 export\n\nRendered and verified {len(records)}/50 episodes.\n',encoding='utf-8')
    records.sort(key=lambda c:c['position']);checked=concatenate(out,records)
    assert checked['encoded_frames']==(source_offset*3+7)//8
    assert abs(checked['duration_seconds']-source_offset/20/4)<1/30
    result=dict(episodes=50,teacher_source_model='gpt-6.1-sol',student='Partner google/gemma-4-E4B-it adapter',
        speed_multiplier=4,visible_speed_label='Sped up 4\u00d7',source_review_sha256=sha(RUN/'review_data.json'),
        source_provenance_sha256=sha(RUN/'review_provenance.json'),source_frames=source_offset,
        frame_selection='Global 30 FPS output index k maps to floor(k*8/3) in the concatenated 20 FPS native source, exactly 4x.',
        invalid_timelines_shown_as_unknown=True,native_outputs_modified=False,new_inference_calls=0,new_teacher_calls=0,
        compilation=checked,chapters=records)
    (out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    lines=['# Sol / Gemma LIBERO: 50 episodes at 4x','',
        'The same side-by-side 1920x1080, 30 FPS style as the earlier comparison MP4s. Sol reference on the left, partner Gemma on the right; identical synchronized agent and wrist cameras on both sides.','',
        'Failure labels, intervals, timelines, source time and the 4x speed banner are burned in. Gray means an invalid strict timeline; all three zero-length-segment errors remain Unknown, matching the score and reviewer.','',
        'Derived presentation of preserved outputs. No new inference, labels, smoothing or output edits. The actual teacher is gpt-6.1-sol. Readable annotations and full-speed source frames remain in the original reviewer. At 4x/30 FPS, some short spans may fall between displayed frames.','',
        f'Duration: {checked["duration_seconds"]:.3f} seconds. Every encoded label, timestamp and speed banner was decoded and checked.','',
        '| Episode | Presentation start | Episode MP4 |','| --- | --- | --- |']
    for c in records:lines.append(f'| {c["episode"]} | {style.timestamp(c["start_seconds"])} | [{c["episode"]}]({c["file"]}) |')
    (out/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    links=''.join(f'<li><button onclick="v.currentTime={c["start_seconds"]};v.play()">{c["episode"]}</button> {html.escape(c["task"])}</li>' for c in records)
    (out/'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Sol / Gemma LIBERO 4x</title><style>body{font:17px/1.5 system-ui;background:#101722;color:#edf3fb;max-width:1500px;margin:auto;padding:24px}a{color:#c8baff}video{width:100%;background:#000}li{margin:9px 0}button{cursor:pointer;padding:6px}</style>'
        '<h1>Sol / Gemma: all 50 LIBERO validation episodes, 4\u00d7</h1>'
        f'<video id="v" controls playsinline preload="metadata" src="{NAME}"></video><p><a href="{NAME}" download>Download MP4</a> · <a href="README.md">Export notes</a> · <a href="../review.html">Full-speed annotation reviewer</a></p><ol>'+links+'</ol></html>',encoding='utf-8')
    print(json.dumps(dict(complete=True,file=str(out/NAME),**checked)),flush=True)


if __name__=='__main__':main()
