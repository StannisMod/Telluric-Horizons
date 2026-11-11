"""Collect only our fixture markers; never copies a save or a full game log."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re

from build import load


def collect(text, model):
    records=re.findall(r'\[TH TEST\] (PASS|FAIL) ([^\r\n]+)',text)
    expected={r['id']+' '+case for r in model['routes']
              for case in ('eligible','protected','small','special_deposit','restored')}
    passed=Counter(label.strip() for status,label in records if status=='PASS' and label.strip() in expected)
    failed=sorted(label.strip() for status,label in records if status=='FAIL')
    missing=sorted(expected-passed.keys())
    duplicate=sorted(label for label,count in passed.items() if count>1)
    complete=text.count('[TH TEST] SETUP COMPLETE;')==1
    status='FAIL' if failed else 'PASS' if complete and not missing and not duplicate else 'INCOMPLETE'
    return dict(eligibility_fixture=status,expected_assertions=len(expected),
                passed_assertions=sum(passed.values()),failures=failed,missing=missing,duplicates=duplicate,
                gameplay_payment='NOT TESTED',save_reload='NOT TESTED',ai_observation='NOT TESTED',
                completion_markers=[dict(status=s,label=l.strip()) for s,l in records if l.strip().startswith('completed ')])


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('game_log',type=Path);args=parser.parse_args()
    result=collect(args.game_log.read_text(errors='replace'),load())
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return {'PASS':0,'FAIL':1,'INCOMPLETE':2}[result['eligibility_fixture']]


if __name__=='__main__':raise SystemExit(main())
