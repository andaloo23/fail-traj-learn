"""Exercise the real video reviewer with Playwright, without saving review notes.

Requires the optional Playwright Python package and a Chromium installation.
Run against the rebuilt combined reviewer served by serve_oopsie_review.py.
"""
import argparse
import hashlib
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:8792/review.html')
    parser.add_argument('--browser', help='Optional Chromium/Chrome executable')
    parser.add_argument('--out', type=Path, default=Path('outputs/oopsie_viewer_comparison_checks'))
    args = parser.parse_args()
    from playwright.sync_api import sync_playwright

    args.out.mkdir(parents=True, exist_ok=True)
    errors = []
    checked = 0
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=args.browser, headless=True)
        page = browser.new_page(viewport=dict(width=1440, height=1080))
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(args.url, wait_until='networkidle')
        episodes = page.evaluate("data.episodes.filter(e=>Object.values(e.teachers).every(t=>t.status==='ready'))")
        assert episodes, 'No complete teacher pairs to check'

        def at_frame(episode, frame):
            page.wait_for_function('''f => Array.from(document.querySelectorAll('video')).every(
                v => v.readyState >= 2 && !v.seeking && !v.error && Math.abs(v.currentTime-f.time)<0.015)''',
                arg=dict(time=frame / episode['fps']))
            assert int(page.locator('#scrub').input_value()) == frame
            assert page.locator('#comparisonClock').inner_text().endswith('Frame ' + str(frame))
            for teacher, item in episode['teachers'].items():
                panel = page.locator('.teacher.' + teacher)
                assert panel.get_attribute('data-frame') == str(frame)
                segment = next(s for s in item['annotation']['segments']
                               if s['start_frame'] <= frame < s['end_frame'])
                assert segment['what_happened'] in panel.inner_text()
                assert segment['observed_result'] in panel.inner_text()
                evidence = panel.locator('.frame-evidence').inner_text()
                citations = [e for e in segment['evidence'] if e['frame'] == frame]
                if citations:
                    assert all(e['observation'] in evidence for e in citations)
                else:
                    assert 'No citation at this exact frame.' in evidence

        for episode in episodes:
            page.select_option('#episode', episode['id'])
            page.wait_for_function("Array.from(document.querySelectorAll('video')).every(v=>v.readyState>=2&&!v.error)")
            if episode['split'] != 'train':
                assert page.locator('.teacher').count() == 0
                page.locator('#nextSample').click()
                assert page.locator('.teacher').count() == 0
                page.locator('#reveal').click()
            page.locator('#restart').click()
            at_frame(episode, episode.get('window_start_frame', 0))
            assert page.locator('#previousSample').is_disabled()
            # Exercise every next/previous button step, including consecutive
            # frames within a segment and segment transitions in both teachers.
            for frame in episode['sampled_frames'][1:]:
                page.locator('#nextSample').evaluate('(button)=>button.click()')
                at_frame(episode, frame)
                checked += 1
            assert page.locator('#nextSample').is_disabled()
            for frame in reversed(episode['sampled_frames'][:-1]):
                page.locator('#previousSample').evaluate('(button)=>button.click()')
                at_frame(episode, frame)
                checked += 1
            # The same named fields line up across both columns.
            for label in ['What happened', 'Physical result']:
                ys = [page.locator('.teacher.' + teacher + ' .section-title')
                      .filter(has_text=label).bounding_box()['y'] for teacher in ('sol', 'astra')]
                assert abs(ys[0] - ys[1]) < 1, (episode['id'], label, ys)
            print(episode['id'] + ': sampled-frame navigation, media, evidence and alignment passed', flush=True)

        page.select_option('#episode', episodes[0]['id'])
        page.locator('#restart').click()
        page.wait_for_function("Array.from(document.querySelectorAll('video')).every(v=>!v.seeking)")
        before = hashlib.sha256(page.locator('video').first.screenshot()).hexdigest()
        details = page.locator('.teacher.sol details').first
        details.evaluate('(node)=>node.open=true')
        page.locator('#nextSample').evaluate('(button)=>button.click()')
        page.wait_for_function("Array.from(document.querySelectorAll('video')).every(v=>!v.seeking)")
        after = hashlib.sha256(page.locator('video').first.screenshot()).hexdigest()
        assert before != after, 'Decoded video image did not change after next teacher frame'
        assert details.get_attribute('open') is not None, 'Stepping within a segment collapsed details'
        details.evaluate('(node)=>node.open=false')
        for width, height, name in [(1440, 1080, 'desktop'), (1024, 900, 'tablet'), (390, 844, 'mobile')]:
            page.set_viewport_size(dict(width=width, height=height))
            page.evaluate('window.scrollTo(0,0)')
            assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth'), name
            left, right = [page.locator('.teacher.' + t).bounding_box() for t in ('sol', 'astra')]
            if width > 520:
                assert abs(left['y'] - right['y']) < 1 and left['x'] + left['width'] <= right['x']
            else:
                assert left['y'] + left['height'] <= right['y']
            page.screenshot(path=str(args.out / (name + '.png')), full_page=True)
        assert not errors, errors
        browser.close()
    report = ('# Video comparison browser checks\n\n'
              '- Automated interaction checks; no human review decisions were created.\n'
              f'- Checked {checked} next/previous teacher-frame steps across {len(episodes)} real OopsieData review units.\n'
              '- Every camera seek, active segment, current-frame citation and frame readout matched.\n'
              '- Decoded video pixels changed when advancing; open interval details remained open within a segment.\n'
              '- Sol/Astra fields aligned on desktop and tablet; mobile stacked without horizontal overflow.\n'
              '- Held-out annotations stayed hidden until explicitly revealed.\n'
              '- No browser JavaScript errors.\n')
    (args.out / 'browser_checks.md').write_text(report, encoding='utf-8')
    print(report)


if __name__ == '__main__':
    main()
