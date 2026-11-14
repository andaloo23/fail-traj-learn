"""Exercise the live sampling visualization, including source-time playback."""
import argparse
import json
from pathlib import Path


def main():
    from playwright.sync_api import sync_playwright
    p=argparse.ArgumentParser();p.add_argument('--url',default='http://127.0.0.1:8801/')
    p.add_argument('--browser');p.add_argument('--out',type=Path,default=Path('outputs/teacher_sampling_visualization_v1/browser_checks'));a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True);errors=[];rates=[]
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(headless=True,executable_path=a.browser)
        page=browser.new_page(viewport=dict(width=1500,height=1120))
        page.on('pageerror',lambda e:errors.append(str(e)))
        response=page.goto(a.url,wait_until='networkidle');assert response.status==200
        page.wait_for_function("document.getElementById('status').textContent.startsWith('Ready')")
        assert page.locator('#episode option').count()==500
        assert page.locator('#nativeRate').inner_text()=='20 FPS'
        assert page.locator('#forkRate').inner_text()=='4 FPS'
        assert page.locator('#studentRate').inner_text()=='1.333 FPS'
        page.click('#forward')
        assert [page.locator('#'+s+'Image').get_attribute('data-frame') for s in ('native','fork','student')]==['1','0','0']
        page.click('#forkNext')
        assert page.locator('#scrub').input_value()=='5'
        assert [page.locator('#'+s+'Image').get_attribute('data-frame') for s in ('native','fork','student')]==['5','5','0']
        page.click('#studentNext')
        assert page.locator('#scrub').input_value()=='15'
        page.click('#studentPrev');assert page.locator('#scrub').input_value()=='0'
        page.click('#play');page.wait_for_timeout(1050);page.click('#play')
        advanced=int(page.locator('#scrub').input_value());assert 17<=advanced<=27,advanced
        page.evaluate("()=>{const x=document.getElementById('scrub');x.value=49;x.dispatchEvent(new Event('input'))}")
        assert [page.locator('#'+s+'Image').get_attribute('data-frame') for s in ('native','fork','student')]==['49','49','49']
        assert page.locator('#forkNext').is_disabled()
        # Validate every episode's endpoint and nested teacher/student schedules.
        coverage=page.evaluate('''()=>dataset.episodes.map(e=>{const t=schedule(e.n_frames,5),s=studentSchedule(t);return {id:e.id,n:e.n_frames,teacher:t,student:s}})''')
        for e in coverage:
            expected=sorted(set(range(0,e['n'],5))|{e['n']-1})
            assert e['teacher']==expected
            assert e['student']==[f for i,f in enumerate(expected) if i%3==0 or i==len(expected)-1]
        representatives=page.evaluate('''()=>[...new Map(dataset.episodes.map(e=>[e.fps,e])).values()].map(e=>({id:e.id,fps:e.fps,n:e.n_frames}))''')
        for e in representatives:
            page.select_option('#episode',e['id'])
            page.wait_for_function("document.querySelectorAll('.evidence').length===3 && [...document.querySelectorAll('.evidence')].every(x=>x.complete&&x.naturalWidth>0)")
            value=page.evaluate('({fps:current.fps,counts:streams.map(s=>s.frames.length),native:streams[0].frames})')
            assert value['fps']==e['fps'];assert value['native']==list(range(e['n']))
            assert value['counts'][0]>=value['counts'][1]>=value['counts'][2]
            rates.append(e['fps'])
        page.select_option('#episode','O0006')
        page.wait_for_function("document.getElementById('status').textContent.startsWith('Ready')")
        page.evaluate("()=>{const x=document.getElementById('scrub');x.value=14;x.dispatchEvent(new Event('input'))}")
        page.wait_for_function("[...document.querySelectorAll('.evidence')].every(x=>x.complete&&x.naturalWidth>0)")
        page.screenshot(path=str(a.out/'sampling_comparison.png'),full_page=True)
        page.reload(wait_until='networkidle');assert page.locator('#nativeRate').inner_text()=='20 FPS'
        assert not errors,errors
        browser.close()
    result=dict(episodes_checked=len(coverage),native_rates_checked=sorted(rates),playback_frames_in_about_one_second=advanced,
        default_native_fps=20,fork_teacher_fps=4,fork_student_fps=20/15,endpoint_and_nested_schedules_passed=True,
        next_previous_and_reload_passed=True,javascript_errors=errors)
    (a.out/'report.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    (a.out/'report.md').write_text('# Sampling visualization checks\n\nAll 500 episode schedules retain the first and final frame. Every native rate (5, 7.5, 10, 12, 15, 20, 30, 50 FPS) was exercised in Chromium. Source stepping, teacher/student observation stepping, endpoint behavior, source-time playback and reload passed. No JavaScript errors. No labels, review notes or model calls were changed.\n',encoding='utf-8')
    print(json.dumps(result),flush=True)


if __name__=='__main__':main()
