"""Synthetic fixtures only; no original game files are stored with tests."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import build
from paradox import parse, one, values
from balance import shortest, check_routes
from game_data import terraform_links


class DataReaderTests(unittest.TestCase):
    def test_comments_quotes_repeated_keys_and_lists(self):
        tree=parse('\ufeff# ignored\n thing = { label = "a # b { c" tag = one tag = two list = { "x" y } size >= 10 }')
        item=one(tree,'thing')
        self.assertEqual(one(item,'label'),'a # b { c')
        self.assertEqual(values(item,'tag'),['one','two'])
        self.assertEqual(one(item,'list'),[(None,'=','x'),(None,'=','y')])
        self.assertIn(('size','>=','10'),item)

    def test_malformed_blocks_fail(self):
        for text in ['a = { b = c', 'a =', '}', 'a = "unfinished']:
            with self.subTest(text=text),self.assertRaises(ValueError):parse(text)

    def test_adjacent_braces(self):
        self.assertEqual(one(one(parse('a={b={}}'),'a'),'b'),[])

    def test_only_top_level_is_a_definition(self):
        tree=parse('tech_outer = { prerequisites = { tech_inner = { } } }')
        self.assertEqual([k for k,_,v in tree],['tech_outer'])

    def test_link_variables_and_inline_cost_are_resolved(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'common/terraform';path.mkdir(parents=True)
            (path/'test.txt').write_text('@cost = 17\n@days = 42\nterraform_link = { from = pc_test_a to = pc_test_b duration = @days resources = { inline_script = { script = terraform/triggered_costs ENERGY_COST = @cost } } potential = { from = { has_modifier = test_candidate } } }')
            links=terraform_links(tmp)
        self.assertEqual((links[0]['energy'],links[0]['days']),(17,42))
        self.assertEqual(links[0]['modifiers'],{'test_candidate'})


class BalanceTests(unittest.TestCase):
    def test_indirect_path_beats_expensive_direct_edge(self):
        edges=[dict(source='a',target='b',energy=5),dict(source='b',target='c',energy=3),dict(source='a',target='c',energy=12)]
        self.assertEqual(shortest(edges,'a','energy')['c'],8)

    def test_engineering_shortcut_is_rejected(self):
        model=build.load()
        route=next(r for r in model['routes'] if r['source']=='pc_barren' and r['target']=='pc_continental')
        route['energy']+=1
        with self.assertRaisesRegex(ValueError,'Cheaper indirect path'):check_routes(model)

    def test_duration_shortcut_is_rejected_separately(self):
        model=build.load()
        route=next(r for r in model['routes'] if r['source']=='pc_barren' and r['target']=='pc_continental')
        route['days']+=1
        with self.assertRaisesRegex(ValueError,'days'):check_routes(model)

    def test_missing_route_and_injected_flag_are_rejected(self):
        model=build.load();model['routes'].pop()
        with self.assertRaisesRegex(ValueError,'coverage'):build.validate(model)
        model=build.load();model['defaults']['protected_planet_flags'].append('bad } always = yes {')
        with self.assertRaisesRegex(ValueError,'protected_planet_flags'):build.validate(model)

    def test_vanilla_handoffs_cover_only_audited_pairs(self):
        links=parse(build.render(build.load())['telluric_horizons/common/terraform/zz_th_engineering.txt'].decode())
        branches=[v for k,_,v in links if k=='terraform_link']
        self.assertEqual(len(branches),42)
        gated=[v for v in branches if values(one(v,'potential'),'NOT')]
        self.assertEqual(len(gated),32)
        frozen=[v for v in branches if one(v,'from')=='pc_frozen' and one(v,'to')=='pc_ocean'][0]
        gate=one(one(one(frozen,'potential'),'NOT'),'AND')
        self.assertEqual(len(values(one(gate,'OR'),'has_aquatic_trait')),1)

    def test_release_has_no_resource_or_deposit_grant_effect(self):
        scripts=build.render(build.load())
        links=parse(scripts['telluric_horizons/common/terraform/zz_th_engineering.txt'].decode())
        from paradox import walk
        for k,_,v in links:
            if k=='terraform_link':
                keys={key for key,_,value in walk(one(v,'effect'))}
                self.assertTrue({'from','if','limit','has_modifier','remove_modifier'} <= keys)
                self.assertTrue(keys <= {'from','if','limit','has_modifier','remove_modifier','detox_hangover'})


if __name__=='__main__':unittest.main()
