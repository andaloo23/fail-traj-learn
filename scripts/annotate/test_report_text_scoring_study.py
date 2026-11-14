import contextlib
import io as stream
from pathlib import Path
import tempfile
import unittest

import annotation_runtime as io
from report_text_scoring_study import report,normalize_relation_whitespace


class StudyReportTests(unittest.TestCase):
    def test_whitespace_normalization_is_logged_without_changing_the_judgment(self):
        raw={'overall_relation':' unrelated','dimensions':{}}
        normalized,changes=normalize_relation_whitespace(raw,'slots')
        self.assertEqual(normalized['overall_relation'],'unrelated')
        self.assertEqual(raw['overall_relation'],' unrelated')
        self.assertEqual(changes,[dict(field='overall_relation',before=' unrelated',after='unrelated')])

    def test_invalid_fact_pair_does_not_discard_valid_neighbors(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp); folder=out/'judges';folder.mkdir()
            pairs=[dict(pair_id=k,kind='control',name=k,left='held',right='held',context={},expected_relation='equivalent') for k in ('good','bad')]
            io.write_json(out/'corpus.json',dict(pairs=pairs,controls=2,real_pairs=0))
            job=dict(name='test',model='flash',mode='facts',order='ab',ids=['good','bad'])
            io.write_json(folder/'manifest.json',dict(corpus_sha256=io.digest(out/'corpus.json'),files={},jobs=[job]))
            io.write_json(folder/'test_attempt.json',dict(status='error',generation_estimate_usd=.01))
            good=dict(pair_id='good',facts_a=[dict(id='a',claim='held')],facts_b=[dict(id='b',claim='held')],alignments=[dict(a_id='a',b_id='b',relation='equivalent')],rationale='same')
            bad=dict(good,pair_id='bad',alignments=good['alignments']*2)
            import json
            answer=json.dumps({'pairs':[good,bad]})
            (folder/'test_answer.txt').write_text(answer,encoding='utf-8')
            io.write_json(folder/'test_raw.json',dict(candidates=[dict(finishReason='STOP',content=dict(parts=[dict(text=answer)]))]))
            with contextlib.redirect_stdout(stream.StringIO()):report(out)
            result=io.load(out/'report_data.json')
            self.assertEqual(result['judges']['flash_facts']['good']['ab']['computed']['score'],1)
            self.assertNotIn('bad',result['judges']['flash_facts'])
            self.assertEqual(result['summary']['invalid_calls_or_pairs'][0]['pairs'],['bad'])
            self.assertEqual(result['summary']['generation_estimate_usd'],.01)


if __name__=='__main__':unittest.main()
