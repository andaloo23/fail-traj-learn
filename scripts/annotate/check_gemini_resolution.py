"""Bounded token-count diagnostics; never sends generation requests."""
import copy
import json
import api_frame_selection as old

OUT = old.ROOT / 'outputs/gemini_resolution_check_v1'


def main():
    old.verify()
    OUT.mkdir()  # Exclusive: no accidental repeat probes.
    keys = old.common.credentials()
    body, _, _ = old.build_payload(old.jobs()[1])
    probes = [('pair_default', False, False), ('pair_low', True, False), ('full_low', True, True)]
    for name, low, full in probes:
        request = copy.deepcopy(body)
        if not full:
            request['contents'][0]['parts'] = request['contents'][0]['parts'][:4]
        if low:
            request['generationConfig']['mediaResolution'] = 'MEDIA_RESOLUTION_LOW'
        count_body = {'generateContentRequest': {'model': 'models/' + old.MODELS['gemini'], **request}}
        path = OUT / (name + '.json')
        record = {'name': name, 'reserved_usd': .05, 'generation_sent': False,
                  'payload_sha256': old.sha_bytes(json.dumps(count_body, sort_keys=True).encode()), 'status': 'in_flight'}
        old.common.write_json(path, record)
        try:
            raw = old.post('https://generativelanguage.googleapis.com/v1beta/models/' + old.MODELS['gemini'] + ':countTokens', 'gemini', count_body, keys)
            record.update(status='completed', response=raw, input_rate_allowance_usd=raw['totalTokens'] / 1e6)
        except Exception as e:
            record.update(status='stopped', error=old.redact(str(e), keys))
            raise
        finally:
            old.atomic_json(path, record)
            print(json.dumps(record), flush=True)
        if record['input_rate_allowance_usd'] > .05:
            raise ValueError('Diagnostic allowance exceeded; stop')


if __name__ == '__main__':
    main()
