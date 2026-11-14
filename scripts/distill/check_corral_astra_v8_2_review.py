"""Check new judgment fields against a served V8.2 reviewer; no label writes."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True)
    parser.add_argument('--browser')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    from playwright.sync_api import sync_playwright
    checks = 0; errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=args.browser, headless=True)
        page = browser.new_page(viewport=dict(width=1500, height=1100))
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(args.url, wait_until='domcontentloaded')
        data = page.evaluate('data')
        for episode in data['episodes']:
            page.select_option('#episode', episode['id'])
            page.wait_for_function("Array.from(document.querySelectorAll('video')).every(v=>v.readyState>=2&&!v.error)")
            for trace in episode['teachers']['v8']:
                page.select_option('#v8Repeat', str(trace['repeat']))
                assert page.locator('.language-task').inner_text() == 'Language task: ' + trace['language_task']
                assert page.locator('.episode-outcome').inner_text() == 'Episode outcome: ' + trace['success_label']
                assert page.locator('.outcome-evidence').inner_text() == trace['outcome_evidence']
                for annotation in trace['failure_annotations']:
                    card = page.locator(f".annotation-card[data-start='{annotation['start_frame']}']")
                    card.locator('button').click()
                    assert page.locator('#scrub').input_value() == str(annotation['start_frame'])
                    for host in [card, page.locator('.failure-detail')]:
                        for key, label in [('recovery', 'Recovery'), ('severity', 'Severity'),
                                ('severity_evidence', 'Severity evidence'), ('resetability', 'Resetability'),
                                ('resetability_evidence', 'Resetability evidence')]:
                            field = host.locator('.' + key.replace('_', '-'))
                            assert field.is_visible()
                            assert field.inner_text() == label + ': ' + annotation[key]
                            checks += 1
        assert not errors, errors
        for width, height in [(1500, 1100), (390, 844)]:
            page.set_viewport_size(dict(width=width, height=height))
            assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth')
        args.out.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(args.out / 'severity_resetability_review.png'), full_page=True)
        browser.close()
    report = dict(url=args.url, episodes=len(data['episodes']), judgment_field_checks=checks,
        javascript_errors=errors, model_output_correctness_assessed=False)
    (args.out / 'severity_resetability_check.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
