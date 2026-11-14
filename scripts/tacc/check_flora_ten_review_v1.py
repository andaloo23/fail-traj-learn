"""Exercise every episode and native segment in the FLORA dense video reviewer."""
import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--url', default='http://127.0.0.1:8802/')
    p.add_argument('--browser', help='Path to an installed browser')
    p.add_argument('--out', type=Path, default=Path('outputs/flora_oopsie_ten_review_3533752_v1/browser_checks'))
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    errors = []
    checked = 0
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, executable_path=a.browser)
        page = browser.new_page(viewport=dict(width=1536, height=1100))
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(a.url)
        data = page.evaluate('data')
        assert len(data) == 10

        def wait_ready():
            page.wait_for_function('ready && videos.every(v=>v.readyState>=2&&!v.error)', timeout=30000)

        def at_frame(e, f):
            page.wait_for_function('''x=>frame===x.frame && videos.every(v=>
                !v.seeking && v.readyState>=2 && !v.error && Math.abs(v.currentTime-x.time)<.001)''',
                arg=dict(frame=f, time=(f+.5)/e['fps']), timeout=15000)
            s = next(s for s in e['segments'] if s['start_frame'] <= f < s['end_frame'])
            assert page.locator('#liveLabel').inner_text() == s['label']
            assert page.locator('#liveRationale').inner_text() == (s['rationale'] or 'No rationale supplied for this segment.')
            assert int(page.locator('#scrub').input_value()) == f
            assert page.locator('#spans tr.active').count() == 1

        for e in data:
            page.select_option('#episode', e['id'])
            wait_ready()
            assert page.locator('video').count() == len(e['cameras'])
            assert page.locator('#spans tr').count() == len(e['segments'])
            assert page.locator('#liveLabel').inner_text() == e['segments'][0]['label']
            for s in e['segments']:
                for f in sorted({s['start_frame'], s['end_frame']-1}):
                    page.evaluate('f=>seekFrame(f)', f)
                    at_frame(e, f)
                    checked += 1
            page.evaluate('seekFrame(0)')
            at_frame(e, 0)
            page.locator('#forward').click()
            at_frame(e, 1)
            page.locator('#back').click()
            at_frame(e, 0)
            if len(e['segments']) > 1:
                page.locator('#nextSegment').click()
                at_frame(e, e['segments'][1]['start_frame'])
                page.locator('#prevSegment').click()
                at_frame(e, 0)
            page.locator('#spans tr').last.locator('button').click()
            at_frame(e, e['segments'][-1]['start_frame'])
            page.evaluate('seekFrame(0)')
            at_frame(e, 0)
            page.locator('#speed').select_option('2')
            assert page.evaluate('videos.every(v=>v.playbackRate===2)')
            page.locator('#speed').select_option('1')
            page.locator('#play').click()
            page.wait_for_function('videos.every(v=>!v.paused) && videos[0].currentTime>.25')
            page.wait_for_timeout(350)
            assert page.evaluate('videos.every(v=>Math.abs(v.currentTime-videos[0].currentTime)<.12)')
            page.locator('#play').click()
            assert page.evaluate('videos.every(v=>v.paused)')
            if e['id'] in ('O003', 'O004'):
                page.evaluate('seekFrame(0)')
                at_frame(e, 0)
                page.screenshot(path=str(a.out / (e['id']+'.png')), full_page=True)
            print(e['id']+' checked', flush=True)
        page.reload()
        wait_ready()
        assert page.locator('#episode').input_value() == 'O010'
        page.locator('#prevEpisode').click()
        wait_ready()
        assert page.locator('#episode').input_value() == 'O009'
        page.locator('#nextEpisode').click()
        wait_ready()
        assert page.locator('#episode').input_value() == 'O010'
        page.locator('#episodes button').nth(3).click()
        wait_ready()
        assert page.locator('#episode').input_value() == 'O004'
        page.screenshot(path=str(a.out / 'overview.png'), full_page=True)
        browser.close()
    assert not errors, errors
    report = dict(episodes=len(data), segments=sum(len(e['segments']) for e in data),
                  boundary_frames_checked=checked, errors=errors, passed=True)
    (a.out / 'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
