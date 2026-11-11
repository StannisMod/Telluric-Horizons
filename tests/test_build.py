import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))

spec=importlib.util.spec_from_file_location("compiler",Path(__file__).resolve().parents[1]/"tools/build.py")
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)

class ModelTests(unittest.TestCase):
    def setUp(self): self.m=b.load()
    def reject(self, mutate):
        mutate(self.m)
        with self.assertRaises((ValueError,KeyError)): b.validate(self.m)
    def test_baseline(self): self.assertEqual(len(self.m["routes"]),42)
    def test_unique_directions(self): self.assertEqual(len({(r["source"],r["target"]) for r in self.m["routes"]}),40)
    def test_duplicate_route(self): self.reject(lambda m:m["routes"].append(copy.deepcopy(m["routes"][0])))
    def test_unknown_schema(self): self.reject(lambda m:m.update(schema_version=99))
    def test_unknown_field(self): self.reject(lambda m:m["routes"][0].update(enrgy=1))
    def test_zero_cost(self): self.reject(lambda m:m["routes"][0].update(energy=0))
    def test_negative_duration(self): self.reject(lambda m:m["routes"][0].update(days=-1))
    def test_boolean_cost(self): self.reject(lambda m:m["routes"][0].update(energy=True))
    def test_forbidden_source(self): self.reject(lambda m:m["routes"][0].update(source="pc_gas_giant"))
    def test_unknown_destination(self): self.reject(lambda m:m["routes"][0].update(target="pc_fake"))
    def test_ai_weight_is_bounded(self): self.reject(lambda m:m["routes"][0].update(ai_weight=6))
    def test_localization_parity(self): self.reject(lambda m:m["localization"]["th_title"].pop("russian"))
    def test_technology_required(self): self.reject(lambda m:m["routes"][0].update(technologies=[]))
    def test_determinism(self): self.assertEqual(b.render(self.m),b.render(copy.deepcopy(self.m)))
    def test_all_engineered_worlds_reach_all_climates(self):
        targets=b.engineering_targets(self.m)
        for k,c in self.m["classes"].items():
            if c["policy"]=="engineer": self.assertEqual({t["target"] for t in self.m["routes"] if t["source"]==k},targets)
    def test_candidate_not_required(self):
        output=b.render(self.m)
        # Candidates are handed to vanilla, never required for our branch.
        text=output["telluric_horizons/common/terraform/zz_th_engineering.txt"].decode()
        self.assertIn('NOT = { AND = { from = { has_modifier = terraforming_candidate }',text)
        self.assertNotIn('has_archaeological_site',output['telluric_horizons/common/scripted_triggers/th_eligibility.txt'].decode())
    def test_localization_bom(self):
        for k,v in b.render(self.m).items():
            if k.endswith(".yml"): self.assertTrue(v.startswith(b"\xef\xbb\xbf"))
    def test_generated_drift_and_unexpected_files(self):
        original=b.OUT
        with tempfile.TemporaryDirectory() as tmp:
            b.OUT=Path(tmp)
            try:
                b.build();b.build(check=True)
                (b.OUT/"unexpected").write_text("manual")
                with self.assertRaises(ValueError): b.build(check=True)
                with self.assertRaises(ValueError): b.build()
            finally:b.OUT=original
    def test_size_bounds(self): self.reject(lambda m:m["defaults"].update(min_size_proxy=99))
    def test_engineering_no_cycles(self):
        # Expansion links terminate in climates, never point back into engineering sources.
        sources={t["source"] for t in self.m["routes"]}
        self.assertFalse(sources & {t["target"] for t in self.m["routes"]})

if __name__=="__main__": unittest.main()
