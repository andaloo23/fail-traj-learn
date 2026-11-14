"""Regression-check every episode/repeat and persistent label visibility on a real reviewer.

Uses isolated browser storage; does not save notes or change native annotations.
Requires Playwright and an installed Chromium browser. No API calls or model loads.
"""
import argparse
import json
from pathlib import Path
import re


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url',default='http://127.0.0.1:8797/review.html')
    parser.add_argument('--browser')
    parser.add_argument('--out',type=Path,default=Path('outputs/binary_review_browser_checks'))
    args=parser.parse_args()
    from playwright.sync_api import sync_playwright

    args.out.mkdir(parents=True,exist_ok=True)
    errors=[]; label_checks=0; positions=0; rich_checks=0; rich_action_clicks=0; enrichment_checks=0
    action_overlay_checks=0; simultaneous_grasp_nonfailure_checks=0; visible_annotation_checks=0; action_jump_clicks=0
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(executable_path=args.browser,headless=True)
        page=browser.new_page(viewport=dict(width=1500,height=1100))
        page.on('pageerror',lambda error:errors.append(str(error)))
        response=page.goto(args.url,wait_until='domcontentloaded')
        assert response.status==200
        assert 'no-store' in response.headers.get('cache-control',''),'Review HTML must not be cached'
        episodes=page.evaluate('data.episodes')
        panel_count=len(episodes[0]['teachers'])
        planned=page.evaluate('data.planned_responses')
        total=sum(len(t) for e in episodes for t in e['teachers'].values())
        assert f'{total}/{planned} labels ready' in page.locator('#runStatus').inner_text()

        def choose(episode):
            page.select_option('#episode',episode['id'])
            page.wait_for_function("Array.from(document.querySelectorAll('video')).every(v=>v.readyState>=2&&!v.error)")
            assert page.locator('#split').inner_text()==episode['split']

        def at_frame(episode,frame):
            page.evaluate("f=>{const s=document.getElementById('scrub');s.value=f;s.dispatchEvent(new Event('input'))}",frame)
            page.wait_for_function('''p=>Array.from(document.querySelectorAll('video')).every(
                v=>v.readyState>=2&&!v.seeking&&!v.error&&Math.abs(v.currentTime-p.time)<p.tolerance)''',
                arg=dict(time=frame/episode['fps'],tolerance=max(.02,.2/episode['fps'])))
            assert page.locator('#scrub').input_value()==str(frame)

        # Plain URL, fresh browser: all splits show every available teacher/repeat.
        for episode in episodes:
            choose(episode)
            assert page.locator('.teacher').count()==panel_count,f"Labels hidden on {episode['id']}"
            assert page.locator('#reveal').get_attribute('aria-pressed')=='true'
            assert page.locator('video').count()==len(episode['videos'])
            frames={0,episode['n_frames']//2,episode['n_frames']-1}
            for action in episode.get('action_segments',[]):
                frames.update((action['start_frame'],action['end_frame']-1))
            for traces in episode['teachers'].values():
                for trace in traces:
                    for segment in trace['segments']:
                        frames.update((segment['start_frame'],segment['end_frame']-1))
                    for segment in trace.get('rich_segments', []):
                        frames.update((segment['start_frame'],segment['end_frame']-1))
            for frame in sorted(frames):
                at_frame(episode,frame);positions+=1
                for teacher,traces in episode['teachers'].items():
                    assert page.locator('#'+teacher+'Repeat option').count()==len(traces)
                    for trace in traces:
                        page.select_option('#'+teacher+'Repeat',str(trace['repeat']))
                        panel=page.locator('.teacher.'+teacher)
                        segment=next(s for s in trace['segments'] if s['start_frame']<=frame<s['end_frame'])
                        assert panel.get_attribute('data-frame')==str(frame)
                        expected_label=('Unknown' if segment['failure'] is None else
                                        'Failure' if segment['failure'] else 'Non-failure')
                        assert panel.locator('.current-label').inner_text()==expected_label
                        label_checks+=1
                        actions=(episode.get('action_segments') if teacher!='v9' else None) or trace.get('rich_segments')
                        if teacher=='v9':
                            assert panel.locator('.action-overlay').count()==0
                            assert panel.locator('.current-action').count()==0
                        if actions:
                            action=next(s for s in actions if s['start_frame']<=frame<s['end_frame'])
                            assert panel.locator('.current-action').inner_text()=='Action: '+action['action']
                            assert panel.locator('.action-overlay .action-box').count()==len(actions)
                            box=panel.locator('.action-overlay .action-box.active')
                            assert box.count()==1
                            assert box.get_attribute('data-action')==action['action']
                            assert box.get_attribute('data-start')==str(action['start_frame'])
                            assert box.get_attribute('data-end')==str(action['end_frame'])
                            assert panel.locator('.timeline.with-actions').count()==1
                            if episode.get('action_source'):
                                assert 'saved V8 Sol repeat 1' in panel.locator('.action-source').inner_text()
                            if action['action']=='grasp' and not segment['failure']:
                                assert panel.locator('.current-label').inner_text()=='Non-failure'
                                simultaneous_grasp_nonfailure_checks+=1
                            action_overlay_checks+=1
                        if 'failure_annotations' in trace:
                            detail=panel.locator('.failure-detail')
                            assert detail.get_attribute('data-start')==str(segment['start_frame'])
                            assert detail.get_attribute('data-end')==str(segment['end_frame'])
                            if segment['failure']:
                                annotation=next(s for s in trace['failure_annotations'] if s['start_frame']==segment['start_frame'])
                                assert detail.locator('.categories').inner_text()=='Categories: '+', '.join(annotation['categories'])
                                assert detail.locator('.explanation').inner_text()==annotation['explanation']
                            else:
                                assert detail.locator('.explanation').count()==0
                            assert trace['native_markdown']==panel.locator('.native-markdown').text_content()
                            cards=panel.locator('.failure-annotations .annotation-card')
                            assert cards.count()==len(trace['failure_annotations'])
                            for annotation in trace['failure_annotations']:
                                card=panel.locator('.annotation-card[data-start="'+str(annotation['start_frame'])+'"]')
                                assert card.is_visible()
                                assert card.locator('.annotation-categories').inner_text()=='Categories: '+', '.join(annotation['categories'])
                                assert card.locator('.annotation-explanation').inner_text()==annotation['explanation']
                                visible_annotation_checks+=1
                            consensus=panel.locator('.repeat-consensus')
                            if episode.get('repeatability',{}).get('complete'):
                                assert consensus.get_attribute('data-episode-exact')==str(episode['repeatability']['binary_exact_3_of_3']).lower()
                            enrichment_checks+=1
                        if trace.get('rich_segments'):
                            rich=next(s for s in trace['rich_segments'] if s['start_frame']<=frame<s['end_frame'])
                            detail=panel.locator('.rich-current')
                            assert detail.get_attribute('data-start')==str(rich['start_frame'])
                            assert detail.get_attribute('data-end')==str(rich['end_frame'])
                            assert detail.locator('h3').inner_text()=='Current V8 action: '+rich['action']
                            assert rich['observed_result'] in detail.inner_text()
                            assert trace['native_markdown']==panel.locator('.native-markdown').text_content()
                            rich_checks+=1
            for teacher,traces in episode['teachers'].items():
                if episode.get('action_segments') and traces and teacher!='v9':
                    panel=page.locator('.teacher.'+teacher)
                    assert panel.locator('.action-jumps button').count()==len(episode['action_segments'])
                    for action in episode['action_segments']:
                        panel.locator('.action-jumps button[data-start="'+str(action['start_frame'])+'"]').click()
                        assert page.locator('#scrub').input_value()==str(action['start_frame'])
                        assert panel.locator('.current-action').get_attribute('data-action')==action['action']
                        action_jump_clicks+=1
                for trace in traces:
                    if not trace.get('rich_segments'):
                        continue
                    page.select_option('#'+teacher+'Repeat',str(trace['repeat']))
                    panel=page.locator('.teacher.'+teacher)
                    assert panel.locator('.action-list button').count()==len(trace['rich_segments'])
                    for rich in trace['rich_segments']:
                        panel.locator('.action-list button[data-start="'+str(rich['start_frame'])+'"]').click()
                        assert page.locator('#scrub').input_value()==str(rich['start_frame'])
                        assert panel.locator('.rich-current').get_attribute('data-start')==str(rich['start_frame'])
                        rich_action_clicks+=1
            page.locator('#restart').click();page.locator('#forward').click()
            assert page.locator('#scrub').input_value()=='1'

        # Hide/show is a single user-selected mode across every split and reload.
        page.locator('#reveal').click()
        assert page.locator('#reveal').get_attribute('aria-pressed')=='false'
        for episode in episodes:
            choose(episode)
            assert page.locator('.teacher').count()==0
        page.reload(wait_until='domcontentloaded')
        assert page.locator('.teacher').count()==0
        assert page.locator('#episode').input_value()==episodes[-1]['id']
        page.locator('#reveal').click()
        for episode in episodes:
            choose(episode)
            assert page.locator('.teacher').count()==panel_count
        page.reload(wait_until='domcontentloaded')
        assert page.locator('.teacher').count()==panel_count
        assert page.locator('#episode').input_value()==episodes[-1]['id']

        # Exercise actual stale-snapshot refresh without writing model outputs.
        episode=next(e for e in episodes if all(e['teachers'].values()))
        choose(episode)
        frame=min(episode['n_frames']-1,episode['n_frames']//2)
        at_frame(episode,frame)
        selected={t:str(v[-1]['repeat']) for t,v in episode['teachers'].items()}
        for teacher,value in selected.items():page.select_option('#'+teacher+'Repeat',value)
        note='Isolated browser regression; never saved as a human annotation.'
        page.locator('#notes').fill(note)
        page.evaluate("()=>{const t=data.episodes.at(-1).teachers;t[Object.keys(t)[0]]=[];paintRunStatus()}")
        page.evaluate('refreshLabels()')
        assert f'{total}/{planned} labels ready' in page.locator('#runStatus').inner_text()

        def check_state():
            page.wait_for_function("Array.from(document.querySelectorAll('video')).every(v=>v.readyState>=2&&!v.error)")
            assert page.locator('#episode').input_value()==episode['id']
            assert page.locator('#scrub').input_value()==str(frame)
            assert page.locator('#notes').input_value()==note
            assert page.locator('.teacher').count()==panel_count
            for teacher,value in selected.items():
                assert page.locator('#'+teacher+'Repeat').input_value()==value
                assert page.locator('.teacher.'+teacher).get_attribute('data-frame')==str(frame)
        check_state()
        # Newly completed labels must appear on the episode already being viewed.
        page.evaluate("()=>{for(const t of Object.keys(current.teachers))current.teachers[t]=[];render();position(frame);paintRunStatus()}")
        assert page.locator('.teacher').count()==panel_count
        assert page.locator('.current-label').count()==0
        page.evaluate('refreshLabels()')
        check_state()
        page.reload(wait_until='domcontentloaded')
        check_state()

        # A newly published UI reloads automatically and restores the same state.
        with page.expect_navigation(wait_until='domcontentloaded'):
            page.evaluate("()=>{data.review_ui_version='simulated-previous-ui';refreshLabels()}")
        check_state()
        assert 'simulated-previous-ui'!=page.evaluate('data.review_ui_version')

        # Older bookmarks still honor explicit visibility, globally after navigation.
        base=re.sub(r'[?#].*','',args.url)
        page.goto(base+'?episode='+episodes[0]['id']+'&labels=show',wait_until='domcontentloaded')
        for episode in episodes:
            choose(episode)
            assert page.locator('.teacher').count()==panel_count
        assert not errors,errors
        page.screenshot(path=str(args.out/'review.png'),full_page=True)
        # Even a conditional request with a future timestamp must return new HTML.
        conditional=page.request.get(base,headers={'If-Modified-Since':'Wed, 01 Jan 2031 00:00:00 GMT'})
        assert conditional.status==200
        assert 'no-store' in conditional.headers.get('cache-control','')
        ui_version=page.evaluate('data.review_ui_version')
        browser.close()

    report=dict(review_url=args.url,review_ui_version=ui_version,
                episodes=len(episodes),splits=sorted({e['split'] for e in episodes}),
                validated_teacher_responses=total,video_positions=positions,label_checks=label_checks,
                rich_segment_checks=rich_checks,
                rich_action_clicks=rich_action_clicks,
                enrichment_checks=enrichment_checks,
                action_overlay_checks=action_overlay_checks,
                simultaneous_grasp_nonfailure_checks=simultaneous_grasp_nonfailure_checks,
                visible_annotation_checks=visible_annotation_checks,
                action_jump_clicks=action_jump_clicks,
                default_labels_visible_for_all_episodes=True,visibility_mode_persists=True,
                reload_and_live_refresh_preserve_state=True,ui_version_reload_verified=True,
                html_cache_disabled=True,next_frame_updates=True,javascript_errors=errors,
                native_model_output_correctness_assessed=False)
    (args.out/'browser_check.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
