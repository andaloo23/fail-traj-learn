"""Prepare a local, pixel-audited contact-sheet preview. No API calls or submission.

Original sources, prepared frames, frozen requests and labels remain unchanged.
The preview uses the existing model-input pixels, including prior JPEG95/resize
preprocessing. It does not establish equivalent model-label quality.
"""
import argparse
import hashlib
import html
import json
from pathlib import Path

from PIL import Image

import oopsie_common as common
import corral_astra_v8_2_batch as batch


def rgb_sha(image):
    return hashlib.sha256(image.convert('RGB').tobytes()).hexdigest()


def frame_layout(panels):
    """Choose ordered camera columns without resizing or cropping any panel."""
    options=[]
    for breaks in range(1 << (len(panels)-1)):
        columns=[[]]
        for index,panel in enumerate(panels):
            if index and breaks & (1 << (index-1)):columns.append([])
            columns[-1].append(panel)
        width=sum(max(p['width'] for p in col) for col in columns)
        height=max(sum(p['height'] for p in col) for col in columns)
        positions=[];x=0
        for column in columns:
            y=0
            for panel in column:
                positions.append(dict(camera=panel['camera'],source_x=panel['x'],source_y=panel['y'],
                    x=x,y=y,width=panel['width'],height=panel['height']))
                y+=panel['height']
            x+=max(p['width'] for p in column)
        options.append((width*height,width,height,positions))
    return min(options,key=lambda option:option[:3])


def rearrange(source, positions, size):
    """Drop only proven black padding; compare every actual camera pixel."""
    rebuilt=Image.new('RGB',source.size,'black')
    result=Image.new('RGB',size,'black')
    checks=[]
    for p in positions:
        old_box=(p['source_x'],p['source_y'],p['source_x']+p['width'],p['source_y']+p['height'])
        camera=source.crop(old_box)
        rebuilt.paste(camera,(p['source_x'],p['source_y']))
        result.paste(camera,(p['x'],p['y']))
        new_box=(p['x'],p['y'],p['x']+p['width'],p['y']+p['height'])
        if result.crop(new_box).tobytes()!=camera.tobytes():raise ValueError('Camera pixels changed')
        checks.append(dict(camera=p['camera'],rgb_sha256=rgb_sha(camera)))
    if rebuilt.tobytes()!=source.tobytes():raise ValueError('Nonblack pixels exist outside the recorded camera panels')
    return result,checks


def preview(root,eid='C0094'):
    episode=common.read(root/'prepared'/(eid+'.json'))
    output=root/'packaging_preview'/'verification_v1';output.mkdir(parents=True,exist_ok=True)
    _,width,height,positions=frame_layout(episode['images'][0]['panels'])
    starts=sorted({0,max(0,episode['n_frames']//2-8),max(0,episode['n_frames']-16)})
    checks=[];sections=[]
    for start in starts:
        images=episode['images'][start:start+16]
        sheet=Image.new('RGB',(width*4,height*4),'black')
        original_sheet_size=None;original_sheet=None
        for index,record in enumerate(images):
            path=common.inside(root,record['path'])
            if common.sha(path)!=record['sha256']:raise ValueError('Prepared source hash changed')
            with Image.open(path) as inp:source=inp.convert('RGB')
            if rgb_sha(source)!=record['rgb_sha256']:raise ValueError('Prepared source pixels differ')
            cell,camera_checks=rearrange(source,positions,(width,height))
            if original_sheet is None:
                original_sheet_size=source.size
                original_sheet=Image.new('RGB',(source.width*4,source.height*4),'black')
            original_sheet.paste(source,((index%4)*source.width,(index//4)*source.height))
            x=(index%4)*width;y=(index//4)*height;sheet.paste(cell,(x,y))
            for panel in positions:
                expected=source.crop((panel['source_x'],panel['source_y'],panel['source_x']+panel['width'],panel['source_y']+panel['height']))
                actual=sheet.crop((x+panel['x'],y+panel['y'],x+panel['x']+panel['width'],y+panel['y']+panel['height']))
                if actual.tobytes()!=expected.tobytes():raise ValueError('Contact-sheet camera pixels differ')
            checks.append(dict(frame=record['frame'],source_sha256=record['sha256'],cameras=camera_checks))
            if start==0 and index==0:
                source.save(output/'original_frame.png')
                cell.save(output/'proposed_frame.png')
        name=f'proposed_frames_{start:06d}.png';sheet.save(output/name,compress_level=3)
        original_name=f'original_layout_frames_{start:06d}.png';original_sheet.save(output/original_name,compress_level=3)
        with Image.open(output/name) as decoded:
            if decoded.convert('RGB').tobytes()!=sheet.tobytes():raise ValueError('PNG round-trip pixels differ')
        sections.append(f'<section><h2>Frames {start}–{start+len(images)-1}</h2><p>Read each grid left to right, then top to bottom. Each cell is one source frame.</p><div class="pair"><figure><figcaption>Existing camera layout, grouped for comparison</figcaption><a href="{original_name}"><img src="{original_name}" alt="Original camera layout"></a></figure><figure><figcaption>Proposed camera layout and contact sheet</figcaption><a href="{name}"><img src="{name}" alt="Proposed lossless contact sheet"></a></figure></div></section>')
    panels_checked=sum(len(c['cameras']) for c in checks)
    summary=dict(episode=eid,preview_only=True,generation_submitted=False,frames_checked=len(checks),
        camera_panels_checked=panels_checked,pixel_differences=0,source_frame_size=original_sheet_size,
        proposed_frame_size=[width,height],camera_layout=positions,source_preprocessing='Existing reviewed 280-pixel/JPEG95 model inputs',
        changes='Black padding removal and camera/frame rearrangement only; native sources and frozen artifacts untouched.',checks=checks)
    (output/'pixel_audit.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    camera_rows=''.join(f"<tr><td>{html.escape(p['camera'])}</td><td>{p['width']} × {p['height']}</td><td>{p['x']}, {p['y']}</td></tr>" for p in positions)
    video_links=' · '.join(f'<a href="../../{html.escape(v["url"],quote=True)}">{html.escape(v["camera"])}</a>' for v in episode['videos'])
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Proposed input packaging — review only</title><style>body{font:16px/1.5 system-ui;margin:24px auto;padding:0 20px;max-width:1500px;color:#20242b}h1{font-size:28px}.notice{padding:16px;border:2px solid #b47913;background:#fff5db}.pair{display:grid;grid-template-columns:1fr 1fr;gap:20px}figure{margin:0;min-width:0}img{max-width:100%;height:auto;border:1px solid #aaa}figcaption{font-weight:600}section{margin:36px 0}td,th{text-align:left;padding:8px;border-bottom:1px solid #ddd}a{color:#175da8}@media(max-width:800px){.pair{grid-template-columns:1fr}}</style>'''
    page+=f'<h1>Proposed packaging for {eid}: verify before submission</h1><div class="notice"><strong>Preview only. None of the 63 held episodes has been submitted.</strong><p>Original videos, HDF5 files, prepared input frames, requests and labels are unchanged. The originals and proposed layouts below use existing model-input pixels, which already underwent the reviewed 280-pixel/JPEG95 preprocessing.</p></div><p>The proposal removes proven black padding and changes camera/frame arrangement. It adds no further image scaling and removes no camera pixels or source frames. Equal pixels do not establish equal label quality.</p><p><strong>Audit: {len(checks)} source frames, {panels_checked} camera-panel comparisons, zero pixel differences.</strong> Beginning, middle and end samples are shown. Click any image to inspect its full resolution.</p><p>Original videos: {video_links}. <a href="../../review.html?episode={eid}">Open the original-video reviewer</a>.</p><h2>Within each proposed frame cell</h2><table><tr><th>Native camera</th><th>Unchanged pixel dimensions</th><th>New x, y position</th></tr>{camera_rows}</table><div class="pair"><figure><figcaption>Existing single-frame model input</figcaption><a href="original_frame.png"><img src="original_frame.png" alt="Existing source frame"></a></figure><figure><figcaption>Proposed single-frame camera layout</figcaption><a href="proposed_frame.png"><img src="proposed_frame.png" alt="Proposed frame layout"></a></figure></div>'
    page+=''.join(sections)+'</html>'
    (output/'review.html').write_text(page,encoding='utf-8')
    (output/'README.md').write_text(f'# Proposed contact-sheet packaging — preview only\n\nEpisode: {eid}. All 63 long episodes remain held for user verification before submission.\n\nThe proposal changes derived model-input arrangement. Original media and frozen artifacts remain unchanged. Existing 280-pixel/JPEG95 input preprocessing is retained. Black padding is removed only after proving every non-panel source pixel is black. Every camera panel retains its full existing pixel dimensions.\n\nVerified {len(checks)} frames and {panels_checked} camera panels with zero pixel differences. Label quality equivalence has not been established.\n\nOpen review.html for side-by-side beginning/middle/end examples and original video links.\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('checks','camera_layout')},indent=2))
    print('Preview: http://127.0.0.1:8809/packaging_preview/verification_v1/review.html')


def camera_block_preview(root,eid='C0094'):
    """Show the more compact proposal needed for the largest episode.

    Camera images remain whole at their current resolution. Their arrangement
    changes to one chronological block per camera, making the change explicit.
    """
    episode=common.read(root/'prepared'/(eid+'.json'))
    output=root/'packaging_preview'/'verification_v2';output.mkdir(parents=True,exist_ok=True)
    panels=episode['images'][0]['panels'];count=15;width=1120;blocks=[];y=0
    for p in panels:
        columns=width//p['width'];rows=(count+columns-1)//columns
        blocks.append(dict(camera=p['camera'],x=0,y=y,width=p['width'],height=p['height'],columns=columns,rows=rows,
            source_x=p['x'],source_y=p['y']))
        y+=rows*p['height']
    sheet_size=(width,y);starts=sorted({0,max(0,episode['n_frames']//2-7),max(0,episode['n_frames']-count)})
    sections=[];audit=[];camera_count=0
    for start in starts:
        records=episode['images'][start:start+count]
        original=None;proposed=Image.new('RGB',sheet_size,'black');expected=[]
        for index,record in enumerate(records):
            source_path=common.inside(root,record['path'])
            if common.sha(source_path)!=record['sha256']:raise ValueError('Prepared frame hash changed')
            with Image.open(source_path) as image:source=image.convert('RGB')
            if rgb_sha(source)!=record['rgb_sha256']:raise ValueError('Prepared RGB pixels changed')
            if original is None:original=Image.new('RGB',(source.width*3,source.height*5),'black')
            original.paste(source,((index%3)*source.width,(index//3)*source.height))
            rebuilt=Image.new('RGB',source.size,'black')
            for p in blocks:
                camera=source.crop((p['source_x'],p['source_y'],p['source_x']+p['width'],p['source_y']+p['height']))
                rebuilt.paste(camera,(p['source_x'],p['source_y']))
                x=(index%p['columns'])*p['width'];y=p['y']+(index//p['columns'])*p['height']
                proposed.paste(camera,(x,y));expected.append((camera,(x,y,x+p['width'],y+p['height'])))
                audit.append(dict(frame=record['frame'],camera=p['camera'],source_frame_sha256=record['sha256'],
                    camera_rgb_sha256=rgb_sha(camera),proposed_x=x,proposed_y=y,width=p['width'],height=p['height']))
                camera_count+=1
            if rebuilt.tobytes()!=source.tobytes():raise ValueError('Source contains nonblack pixels outside camera panels')
            if start==0 and index==0:source.save(output/'original_single_frame.png')
        before=f'original_frames_{start:06d}.png';after=f'proposed_camera_blocks_{start:06d}.png'
        original.save(output/before,compress_level=3);proposed.save(output/after,compress_level=3)
        with Image.open(output/after) as image:
            decoded=image.convert('RGB')
            for camera,box in expected:
                if decoded.crop(box).tobytes()!=camera.tobytes():raise ValueError('Encoded contact-sheet camera pixels differ')
        sections.append(f'<section><h2>Source frames {start}–{start+len(records)-1}</h2><div class="pair"><figure><figcaption>Existing input frames, grouped here only for comparison</figcaption><a href="{before}"><img src="{before}" alt="Existing frames and camera arrangement"></a></figure><figure><figcaption>Proposed: one chronological block per native camera</figcaption><a href="{after}"><img src="{after}" alt="Proposed camera blocks"></a></figure></div></section>')
    block_rows=''.join(f"<tr><td>{html.escape(p['camera'])}</td><td>{p['width']} × {p['height']}</td><td>{p['columns']}</td><td>y={p['y']}</td></tr>" for p in blocks)
    video_links=' · '.join(f'<a href="../../{html.escape(v["url"],quote=True)}">{html.escape(v["camera"])}</a>' for v in episode['videos'])
    summary=dict(episode=eid,preview_only=True,generation_submitted=False,frames_checked=sum(len(episode['images'][s:s+count]) for s in starts),
        camera_panels_checked=camera_count,pixel_differences=0,source_frames_per_proposed_sheet=count,
        sheet_size=list(sheet_size),camera_layout=blocks,source_preprocessing='Existing reviewed 280-pixel/JPEG95 model inputs',
        label_quality_equivalence_established=False,token_limit_fit_verified=False,
        source_padding_percent=100*(1-sum(p['width']*p['height'] for p in panels)/
            (max(p['x']+p['width'] for p in panels)*max(p['y']+p['height'] for p in panels))),checks=audit)
    (output/'pixel_audit.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Verify proposed camera/frame packaging</title><style>body{font:16px/1.5 system-ui;margin:24px auto;padding:0 20px;max-width:1500px;color:#20242b}h1{font-size:28px}.notice{padding:16px;border:2px solid #b47913;background:#fff5db}.pair{display:grid;grid-template-columns:1fr 1fr;gap:20px}figure{margin:0;min-width:0}img{max-width:100%;height:auto;border:1px solid #aaa}figcaption{font-weight:600}section{margin:36px 0}td,th{text-align:left;padding:8px;border-bottom:1px solid #ddd}a{color:#175da8}@media(max-width:800px){.pair{grid-template-columns:1fr}}</style>'''
    page+=f'<h1>{eid}: proposed model-input packaging</h1><div class="notice"><strong>Preview only. The 63 long episodes remain held for your verification before submission.</strong><p>Original videos, HDF5 files, prepared frame images, frozen requests and labels are unchanged.</p></div><h2>What would change</h2><p>The current requests send one image per source frame, with cameras side by side. This proposal groups 15 consecutive frames into one image, arranged as a separate chronological block for each camera. Within each camera block, read left to right, then top to bottom. All blocks show the same 15 source frames. The model would receive explicit camera positions and source-frame mappings.</p><p>This removes black padding and rearranges the model input. Each camera retains its full current pixel dimensions. No additional scaling or scene cropping is applied. These pixels already include the reviewed 280-pixel/JPEG95 preprocessing; they are not raw-resolution originals.</p><p><strong>Verified {summary["frames_checked"]} frames and {camera_count} camera panels from the beginning, middle and end: zero pixel differences.</strong> Identical camera pixels do not establish equivalent model-label quality.</p><table><tr><th>Native camera</th><th>Unchanged camera dimensions</th><th>Columns within block</th><th>Block starts</th></tr>{block_rows}</table><p>Original videos: {video_links}. <a href="../../review.html?episode={eid}">Original-video reviewer</a>.</p><p>Click any image to inspect its full resolution.</p>'
    page+=f'<p><strong>Token-limit fit has not been established.</strong> The source frame contains only {summary["source_padding_percent"]:.1f}% black padding. This layout changes where padding and empty cells occur; removing padding alone does not solve this episode’s token limit. This is a format/fidelity preview, not a ready-to-submit request.</p>'
    page+=''.join(sections)+'</html>'
    (output/'review.html').write_text(page,encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('checks','camera_layout')},indent=2))
    print('Preview: http://127.0.0.1:8809/packaging_preview/verification_v2/review.html')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,default=batch.DEFAULT)
    parser.add_argument('--episode',default='C0094')
    parser.add_argument('--layout',choices=['camera-blocks','frame-grid'],default='camera-blocks')
    args=parser.parse_args()
    if args.layout=='camera-blocks':camera_block_preview(args.run.resolve(),args.episode)
    else:preview(args.run.resolve(),args.episode)
