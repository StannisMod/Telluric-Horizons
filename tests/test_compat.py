from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import build
from check_compat import inspect


class CompatibilityTests(unittest.TestCase):
    def test_conflicts_and_planet_mutations_require_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'descriptor.mod').write_text('name="Synthetic conflict"')
            path=root/'common/scripted_triggers';path.mkdir(parents=True)
            (path/'th_eligibility.txt').write_text('th_eligible_world = { always = yes }\nexample = { change_pc = pc_gas_giant }')
            (root/'test.yml').write_text('l_english:\n th_size:0 "conflict"\n')
            result=inspect(root,build.load())
        self.assertEqual(result['status'],'REVIEW_REQUIRED')
        self.assertIn('th_eligible_world',result['trigger_collisions'])
        self.assertIn('th_size',result['localization_collisions'])
        self.assertIn('change_pc',result['sensitive_script_keys'])

    def test_disjoint_script_is_only_a_static_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'descriptor.mod').write_text('name="Synthetic widget"')
            (root/'widget.txt').write_text('widget = { effect = { } }')
            result=inspect(root,build.load())
        self.assertEqual(result['status'],'NO_STATIC_CONFLICT_FOUND')
        self.assertEqual(result['gameplay'],'NOT TESTED')


if __name__=='__main__':unittest.main()
