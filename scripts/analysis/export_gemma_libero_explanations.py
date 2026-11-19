"""Normal-speed Sol/Gemma MP4 with native categories and explanations."""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from fractions import Fraction
import html
import json
from pathlib import Path

import av
import numpy as np
from PIL import Image, ImageDraw

import export_gemma_libero_4x as prior

REPO,RUN=prior.REPO,prior.RUN
font,sha,at=prior.font,prior.sha,prior.at
SIZE=(1920,1080)
FPS=Fraction(20)
COLORS=prior.COLORS
NAME='sol_gemma_libero_categories_explanations_1x.mp4'


def metadata():
    return dict(title='Sol / Partner Gemma | LIBERO 50 | Categories and explanations | Normal speed 1x',
        comment='Normal-speed derived presentation. Preserved gpt-6.1-sol references versus partner Gemma-4-E4B-it adapter. '
        'Native categories and what_happened explanations displayed verbatim at native segment boundaries. '
        'All 50 original validation episodes; every source frame at 20 FPS. Invalid strict timelines remain Unknown; '
        'their nonempty native segments are shown as unvalidated text. No new inference or teacher calls.')


def wrap(text,face,width):
    """Wrap without dropping or rewriting any source text."""
    result=[]
    for paragraph in str(text).split('\n'):
        line=''
        for word in paragraph.split():
            if line and face.getlength(line+' '+word)>width:result.append(line);line=''
            while face.getlength(word)>width:
                end=1
                while end<len(word) and face.getlength(word[:end+1])<=width:end+=1
                if line:result.append(line);line=''
                result.append(word[:end]);word=word[end:]
            line=(line+' '+word).strip()
        result.append(line)
    return result


def text_layout(s):
    categories=', '.join(s['categories']) or 'None'
    cats=wrap(categories,font(27,True),876)
    explanation=wrap(s['what_happened'],font(28),876)
    # Two category lines and five explanation lines fit at a readable 28px.
    bottom=620+len(cats)*32+14+32+len(explanation)*33
    assert bottom<=925,('Text would be clipped',s['what_happened'],bottom)
    return cats,explanation


def base_canvas(e,position):
    canvas=Image.new('RGB',SIZE,'#101722');d=ImageDraw.Draw(canvas)
    d.text((30,14),f"Episode {position+1} / 50  |  {e['id']}",font=font(34,True),fill='#eef4fc')
    task='Task: '+e['task'];size=29 if d.textlength(task,font=font(29))<1850 else 25
    d.text((30,64),task,font=font(size),fill='#d4e1f1')
    for x,title,key in [(24,'Sol reference','sol'),(972,'Partner Gemma','partner')]:
        d.rounded_rectangle((x,134,x+924,1014),radius=14,fill='#192433',outline='#3a4c64',width=2)
        d.text((x+24,152),title,font=font(40,True),fill='#eef3fc')
        for px,camera in [(110,'Agent camera'),(558,'Wrist camera')]:
            d.text((x+px,304),camera,font=font(21,True),fill='#c8d8ea')
        for s in e['teachers'][key][0]['segments']:
            a=x+24+round(876*s['start_frame']/e['n_frames']);b=x+24+round(876*s['end_frame']/e['n_frames'])
            d.rectangle((a,948,max(a,b-1),972),fill=COLORS[s['failure']])
        d.text((x+24,980),'0.00 s',font=font(20),fill='#bacbdd')
        end=f"{e['n_frames']/e['fps']:.2f} s"
        d.text((x+900-d.textlength(end,font=font(20)),980),end,font=font(20),fill='#bacbdd')
    label='Normal speed (1\u00d7)';width=d.textlength(label,font=font(34,True))
    d.rounded_rectangle((1890-width-40,10,1890,81),radius=10,fill='#34435f')
    d.text((1870-width,23),label,font=font(34,True),fill='white')
    d.text((1020,1030),'Native categories and explanations | Gray: invalid timeline',font=font(23),fill='#cfdeef')
    return canvas


def signature(e,f):
    return tuple(at(e['native_segments'][k],f)['start_frame'] for k in ['sol','partner'])


def status(base,e,f):
    canvas=base.copy();d=ImageDraw.Draw(canvas)
    for x,key in [(24,'sol'),(972,'partner')]:
        s=at(e['native_segments'][key],f);label=at(e['teachers'][key][0]['segments'],f)['failure']
        text='UNKNOWN (invalid timeline)' if label is None else 'FAILURE' if label else 'NON-FAILURE'
        if label is not None and s['review_required']:text+=' | REVIEW REQUIRED'
        d.rounded_rectangle((x+24,208,x+900,259),radius=9,fill=COLORS[label])
        d.text((x+40,213),text,font=font(29,True),fill='white')
        native=('Native '+('failure' if s['failure'] else 'non-failure')+' | ') if label is None else ''
        detail=f"{native}{s['action']} | {s['start_frame']/20:.2f}-{s['end_frame']/20:.2f} s | frames [{s['start_frame']}, {s['end_frame']})"
        assert font(22).getlength(detail)<876,'Action detail too wide'
        d.text((x+24,270),detail,font=font(22),fill='#d4e1f0')
        cats,explanation=text_layout(s)
        d.text((x+24,602),'Categories:',font=font(24,True),fill='#b6c9e1')
        y=632
        for line in cats:d.text((x+24,y),line,font=font(27,True),fill='#f2d69e');y+=32
        y+=10;d.text((x+24,y),'Explanation:',font=font(24,True),fill='#b6c9e1');y+=32
        for line in explanation:d.text((x+24,y),line,font=font(28),fill='#eef3fc');y+=33
        assert y<=937,'Explanation extends into timeline'
    return canvas


def text_masks(canvas):
    # Use the same swscale resize as decoded frames to compare encoded text.
    pixels=av.VideoFrame.from_image(canvas).reformat(width=960,height=540,format='rgb24').to_ndarray()
    return [np.min(pixels[300:469,x:x+438],axis=2)>120 for x in (24,498)]


def verify(path,e,position,expected_frames,offset=0,decoded=None):
    base=base_canvas(e,position);cached={};count=0;text_min_f1=1.0
    if decoded is None:
        container=av.open(str(path));frames=container.decode(video=0)
        stream=container.streams.video[0]
        assert (stream.width,stream.height)==SIZE and stream.average_rate==FPS
    else:container=None;frames=decoded
    try:
        for f in range(expected_frames):
            frame=next(frames);assert abs(float(frame.pts*frame.time_base)-(offset+f)/20)<1e-5
            pixels=frame.reformat(width=960,height=540,format='rgb24').to_ndarray()
            for x,key in [(440,'sol'),(915,'partner')]:
                color=COLORS[at(e['teachers'][key][0]['segments'],f)['failure']]
                target=np.array([int(color[j:j+2],16) for j in (1,3,5)])
                assert np.max(np.abs(pixels[117,x].astype(int)-target))<=30,(e['id'],f,color)
            sig=signature(e,f)
            if sig not in cached:cached[sig]=text_masks(status(base,e,f))
            for x,target in zip((24,498),cached[sig]):
                actual=np.min(pixels[300:469,x:x+438],axis=2)>120
                overlap=np.count_nonzero(actual&target);denom=np.count_nonzero(actual)+np.count_nonzero(target)
                fidelity=2*overlap/denom if denom else 1
                assert fidelity>.90,('Encoded categories/explanation mismatch',e['id'],f,fidelity)
                text_min_f1=min(text_min_f1,fidelity)
            assert np.count_nonzero(np.all(pixels[5:41,730:945]>120,axis=2))>80,'Missing normal-speed banner'
            count+=1
        if container:
            assert next(frames,None) is None
            assert abs(container.duration/av.time_base-count/20)<.02
    finally:
        if container:container.close()
    return dict(encoded_frames=count,minimum_encoded_text_pixel_f1=text_min_f1,
        every_encoded_label_timestamp_category_and_explanation_checked=True)


def render(job):
    out,e,position,reuse=job;out=Path(out);path=out/'episodes'/f"{e['id']}_explanations_1x.mp4"
    if path.exists():
        assert reuse,'Choose a new export version'
        checked=verify(path,e,position,e['n_frames'])
        return dict(episode=e['id'],position=position,task=e['task'],file=path.relative_to(out).as_posix(),sha256=sha(path),**checked)
    base=base_canvas(e,position);cached=None;sig=None
    source=REPO/'outputs/sol_v8_distillation_500/source'/e['id']/'cameras.npz'
    with np.load(source) as data:arrays={k:data[k] for k in ['agent','wrist']}
    assert all(a.shape==(e['n_frames'],256,256,3) for a in arrays.values())
    with av.open(str(path),'w',options={'movflags':'+faststart'}) as dest:
        dest.metadata.update(metadata());stream=dest.add_stream('libx264',rate=FPS)
        stream.width,stream.height=SIZE;stream.pix_fmt='yuv420p';stream.options={'crf':'18','preset':'veryfast'}
        stream.codec_context.thread_count=4
        # Save a failure example where possible; native text is never summarized.
        poster=next((s['start_frame'] for s in e['native_segments']['sol'] if s['failure']),e['n_frames']//2)
        for f in range(e['n_frames']):
            key=signature(e,f)
            if key!=sig:cached=status(base,e,f);sig=key
            canvas=cached.copy()
            for camera,px in [('agent',110),('wrist',558)]:
                picture=Image.fromarray(arrays[camera][f])
                for x in (24,972):canvas.paste(picture,(x+px,334))
            d=ImageDraw.Draw(canvas)
            for x in (24,972):
                cursor=x+24+round(876*f/e['n_frames']);d.rectangle((cursor,943,cursor+2,978),fill='white')
            d.text((30,1030),f"Source {f/20:.2f} / {e['n_frames']/20:.2f} s | Frame {f} / {e['n_frames']-1}",font=font(23),fill='#cfdeef')
            if f==poster:canvas.save(path.with_suffix('.jpg'),quality=95)
            frame=av.VideoFrame.from_image(canvas);frame.pts=f;frame.time_base=Fraction(1,20)
            for packet in stream.encode(frame):dest.mux(packet)
        for packet in stream.encode():dest.mux(packet)
    checked=verify(path,e,position,e['n_frames'])
    return dict(episode=e['id'],position=position,task=e['task'],file=path.relative_to(out).as_posix(),sha256=sha(path),**checked)


def concatenate(out,records,episodes):
    target=out/NAME;assert not target.exists();start=0
    with av.open(str(out/records[0]['file'])) as first, av.open(str(target),'w',options={'movflags':'+faststart'}) as dest:
        dest.metadata.update(metadata());output=dest.add_stream_from_template(first.streams.video[0])
        for r in records:
            with av.open(str(out/r['file'])) as source:
                stream=source.streams.video[0];offset=Fraction(start,20)/stream.time_base;assert offset.denominator==1
                for packet in source.demux(stream):
                    if packet.pts is None or packet.dts is None:continue
                    packet.pts+=int(offset);packet.dts+=int(offset);packet.stream=output;dest.mux(packet)
            r.update(start_output_frame=start,end_output_frame=start+r['encoded_frames'],start_seconds=start/20)
            start+=r['encoded_frames']
    checks=[]
    with av.open(str(target)) as container:
        stream=container.streams.video[0];assert (stream.width,stream.height)==SIZE and stream.average_rate==FPS
        decoded=container.decode(video=0)
        for e,r in zip(episodes,records):checks.append(verify(target,e,r['position'],e['n_frames'],r['start_output_frame'],decoded))
        assert next(decoded,None) is None
        duration=container.duration/av.time_base;assert abs(duration-start/20)<.02
    return dict(encoded_frames=start,fps=20,dimensions=list(SIZE),duration_seconds=duration,sha256=sha(target),
        every_source_frame_preserved=True,every_encoded_label_timestamp_category_and_explanation_checked=True,
        minimum_encoded_text_pixel_f1=min(c['minimum_encoded_text_pixel_f1'] for c in checks))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--reuse-rendered',action='store_true');args=p.parse_args();out=args.out.resolve()
    assert not out.exists() or args.reuse_rendered,'Choose a new export version'
    assert not (out/'manifest.json').exists() and not (out/NAME).exists(),'Completed export already exists'
    review=json.loads((RUN/'review_data.json').read_text(encoding='utf-8'));episodes=review['episodes']
    assert len(episodes)==50
    provenance=json.loads((RUN/'review_provenance.json').read_text());hashes={}
    for e in episodes:
        eid=e['id'];assert e['fps']==20
        path=RUN/'parsed'/f'{eid}.json'
        native=json.loads(path.read_text(encoding='utf-8'))
        assert sha(RUN/'predictions'/f'{eid}.json')==provenance['source_prediction_sha256'][eid]
        camera=REPO/'outputs/sol_v8_distillation_500/source'/eid/'cameras.npz'
        assert sha(camera)==provenance['media'][eid]['source_npz_sha256']
        e['native_segments']=dict(sol=e['teachers']['sol'][0]['rich_segments'],partner=[s for s in native['segments'] if s['start_frame']<s['end_frame']])
        for segments in e['native_segments'].values():
            cursor=0
            for s in segments:
                assert s['start_frame']==cursor and s['start_frame']<s['end_frame']<=e['n_frames'];cursor=s['end_frame'];text_layout(s)
            assert cursor==e['n_frames']
        hashes[eid]=dict(native_parsed_sha256=sha(path),native_prediction_sha256=sha(RUN/'predictions'/f'{eid}.json'))
    out.mkdir(parents=True,exist_ok=args.reuse_rendered);(out/'episodes').mkdir(exist_ok=args.reuse_rendered)
    records=[]
    with ProcessPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(render,(str(out),e,i,args.reuse_rendered)) for i,e in enumerate(episodes)]
        for future in as_completed(futures):
            records.append(future.result());print(f'Rendered and verified {len(records)}/50: {records[-1]["episode"]}',flush=True)
            (out/'progress.md').write_text(f'# Normal-speed categories and explanations\n\nRendered and verified {len(records)}/50 episodes.\n',encoding='utf-8')
    records.sort(key=lambda r:r['position']);checked=concatenate(out,records,episodes)
    assert checked['encoded_frames']==sum(e['n_frames'] for e in episodes)
    result=dict(episodes=50,speed_multiplier=1,visible_speed_label='Normal speed (1\u00d7)',teacher_source_model='gpt-6.1-sol',
        categories_and_explanations_verbatim=True,explanation_source_field='what_happened',native_outputs_modified=False,
        source_review_sha256=sha(RUN/'review_data.json'),source_outputs=hashes,new_inference_calls=0,new_teacher_calls=0,
        strict_invalid_timelines_remain_unknown=True,invalid_timeline_native_text_shown_with_notice=True,
        compilation=checked,chapters=records)
    (out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    lines=['# Sol / Gemma categories and explanations: normal speed','',
        'All 50 original LIBERO validation episodes. Sol on the left and Gemma on the right, with synchronized agent and wrist views. Every native source frame is shown once at 20 FPS; playback speed is 1x.','',
        'Categories and explanations are copied verbatim from each native atomic segment. Explanation is the what_happened field. The action, segment times, failure label and review flag are also shown. The underlying responses remain unchanged.','',
        'Three invalid Gemma timelines remain gray/Unknown. Their nonempty native segments supply the visible categories and explanations, marked with the native failure label below the invalid-timeline banner. Zero-duration segments have no display duration and remain in the original responses. This does not repair or rescore the outputs.','',
        f'Duration: {checked["duration_seconds"]:.2f} seconds. 1920x1080. Every encoded label, timestamp, category and explanation panel was checked after decoding. No new inference or labeling.','',
        '| Episode | Start | Episode MP4 |','| --- | --- | --- |']
    for r in records:lines.append(f'| {r["episode"]} | {prior.style.timestamp(r["start_seconds"])} | [{r["episode"]}]({r["file"]}) |')
    (out/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    links=''.join(f'<li><button onclick="v.currentTime={r["start_seconds"]};v.play()">{r["episode"]}</button> {html.escape(r["task"])}</li>' for r in records)
    (out/'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Sol / Gemma categories and explanations, normal speed</title><style>body{font:17px/1.5 system-ui;background:#101722;color:#edf3fb;max-width:1600px;margin:auto;padding:24px}a{color:#c8baff}video{width:100%;background:#000}li{margin:9px 0}button{cursor:pointer;padding:6px}</style>'
        '<h1>Sol / Gemma: categories and explanations, normal speed (1\u00d7)</h1>'
        f'<video id="v" controls playsinline preload="metadata" src="{NAME}"></video><p><a href="{NAME}" download>Download MP4</a> · <a href="README.md">Export notes</a> · <a href="../review.html">Full annotation reviewer</a></p><ol>'+links+'</ol></html>',encoding='utf-8')
    print(json.dumps(dict(complete=True,file=str(out/NAME),**checked)),flush=True)


if __name__=='__main__':main()
