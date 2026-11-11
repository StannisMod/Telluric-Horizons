"""Boundary, migration and independent scenario expectations for authored rules."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import build
from economy import price_table, ai_reserves, ai_decision, check_scenarios
from migrate_model import upgrade_v1
from paradox import parse,one,values,walk
from runtime_tests import fixture_files
from collect_runtime import collect


class ScenarioTests(unittest.TestCase):
    def setUp(self):self.m=build.load()

    def test_hydrocentric_indirect_discount_is_offered_directly(self):
        table=price_table(self.m,True)
        self.assertEqual(table['toxic_to_arctic']['energy'],31250)
        self.assertEqual(table['toxic_to_ocean']['energy'],26250)
        self.assertEqual(table['barren_to_tropical']['energy'],16250)
        self.assertEqual(table['toxic_to_arctic']['biomass'],15625)

    def test_gaia_base_prices_preserve_native_biomass_ratio(self):
        table=price_table(self.m)
        expected={'barren_to_gaia':(21500,10500),'barren_cold_to_gaia':(23500,11500),
                  'frozen_to_gaia':(17500,8500),'toxic_to_gaia':(37500,18500),
                  'frozen_candidate_to_gaia':(12500,6000),'toxic_candidate_to_gaia':(17500,8500)}
        for route,pair in expected.items():self.assertEqual((table[route]['energy'],table[route]['biomass']),pair)
        hydro=price_table(self.m,True)
        self.assertEqual(hydro['barren_cold_to_gaia']['energy'],23250)
        self.assertEqual(hydro['toxic_to_gaia']['energy'],33750)
        self.assertEqual(hydro['frozen_candidate_to_gaia'],{'energy':11250,'biomass':5375})
        self.assertEqual(hydro['toxic_candidate_to_gaia'],{'energy':15000,'biomass':7250})

    def test_gaia_is_gated_and_candidate_variants_are_complements(self):
        text=build.render(self.m)['telluric_horizons/common/terraform/zz_th_engineering.txt'].decode()
        links=[v for k,_,v in parse(text) if k=='terraform_link' and one(v,'to')=='pc_gaia']
        self.assertEqual(len(links),6)
        for link in links:self.assertIn('ap_world_shaper',values(one(link,'potential'),'has_ascension_perk'))
        for source in ('pc_frozen','pc_toxic'):
            branches=[one(v,'potential') for v in links if one(v,'from')==source]
            regular=next(v for v in branches if values(v,'NOT'))
            ready=next(v for v in branches if values(v,'AND'))
            self.assertEqual(one(one(regular,'NOT'),'AND'),one(ready,'AND'))

    def test_gaia_without_perk_or_missing_candidate_variant_fails(self):
        model=copy.deepcopy(self.m)
        next(r for r in model['routes'] if r['id']=='barren_to_gaia').pop('required_perks')
        with self.assertRaisesRegex(ValueError,'World Shaper'):build.validate(model)
        model=copy.deepcopy(self.m);model['routes']=[r for r in model['routes'] if r['id']!='toxic_candidate_to_gaia']
        with self.assertRaisesRegex(ValueError,'coverage'):build.validate(model)

    def test_toxic_ready_gaia_keeps_native_cleanup(self):
        text=build.render(self.m)['telluric_horizons/common/terraform/zz_th_engineering.txt'].decode()
        self.assertEqual(text.count('detox_hangover = yes'),1)
        self.assertNotIn('add_modifier = terraforming_candidate',text)

    def test_no_discount_changes_baseline(self):
        table=price_table(self.m)
        for route in self.m['routes']:
            self.assertEqual(table[route['id']]['energy'],route['energy'])
            if route['target']!='pc_gaia':self.assertEqual(table[route['id']]['biomass']*2,route['energy'])
        check_scenarios(self.m)

    def test_cost_triggers_select_exactly_one_resource(self):
        def matches(nodes,w,h):
            result=[]
            for k,_,v in nodes:
                if k=='is_wilderness_empire':result.append(w==(v=='yes'))
                elif k=='has_ascension_perk':result.append(h)
                elif k=='NOT':result.append(not matches(v,w,h))
                else:self.fail('Unexpected cost trigger '+str(k))
            return all(result)
        rendered=build.render(self.m)['telluric_horizons/common/terraform/zz_th_engineering.txt'].decode()
        links=[v for k,_,v in parse(rendered) if k=='terraform_link']
        for link in links:
            for w in (False,True):
                for h in (False,True):
                    costs=[v for v in values(one(link,'resources'),'cost') if matches(one(v,'trigger'),w,h)]
                    self.assertEqual(len(costs),1)
                    self.assertIsNotNone(one(costs[0],'biomass' if w else 'energy'))
                    self.assertEqual(one(one(link,'resources'),'category'),'terraforming')

    def test_candidates_without_perk_retain_expensive_fallback(self):
        text=build.render(self.m)['telluric_horizons/common/terraform/zz_th_engineering.txt'].decode()
        links={(one(v,'from'),one(v,'to')):v for k,_,v in parse(text) if k=='terraform_link'}
        def visible(nodes,marker=True,aquatic=False,hydro=False,detox=False,knights=False):
            out=[]
            for key,_,v in nodes:
                if key in ('AND','from'):out.append(visible(v,marker,aquatic,hydro,detox,knights))
                elif key=='OR':out.append(any(visible([x],marker,aquatic,hydro,detox,knights) for x in v))
                elif key=='NOT':out.append(not visible(v,marker,aquatic,hydro,detox,knights))
                elif key=='has_modifier':out.append(marker)
                elif key in ('has_aquatic_trait','has_trait'):out.append(aquatic)
                elif key=='has_ascension_perk':out.append(hydro if v=='ap_hydrocentric' else detox)
                elif key=='has_country_flag':out.append(knights)
                elif key=='exists':out.append(True)
                else:self.fail('Unexpected potential: '+str(key))
            return all(out)
        toxic=one(links['pc_toxic','pc_arctic'],'potential')
        self.assertTrue(visible(toxic))
        self.assertFalse(visible(toxic,detox=True))
        self.assertFalse(visible(toxic,knights=True))
        self.assertTrue(visible(toxic,marker=False,detox=True))
        frozen=one(links['pc_frozen','pc_ocean'],'potential')
        self.assertTrue(visible(frozen,aquatic=True))
        self.assertFalse(visible(frozen,aquatic=True,hydro=True))
        self.assertTrue(visible(frozen,hydro=True))

    def test_ai_boundaries_and_rejection_cases(self):
        route=next(r for r in self.m['routes'] if r['id']=='barren_to_desert')
        reserve=ai_reserves(self.m,route)
        self.assertEqual(reserve,{'energy':38000,'biomass':19000})
        policy=self.m['defaults']['ai_policy']
        state=dict(ideal=True,peaceful=True,colonies=3,active_projects=0,available_colony=False,
                   stockpile=38000,income=100,required_stockpile=38000,deficits=False)
        self.assertTrue(ai_decision(policy,**state))
        for patch in [dict(ideal=False),dict(peaceful=False),dict(colonies=2),dict(active_projects=1),
                      dict(available_colony=True),dict(stockpile=37999),dict(income=99),dict(deficits=True)]:
            with self.subTest(patch=patch):self.assertFalse(ai_decision(policy,**dict(state,**patch)))
        self.assertTrue(ai_decision(policy,**dict(state,stockpile=19000,required_stockpile=19000,income=50,resource='biomass')))

    def test_ai_configuration_can_be_disabled(self):
        self.m['defaults']['ai_enabled']=False
        text=build.render(build.validate(self.m))['telluric_horizons/common/terraform/zz_th_engineering.txt'].decode()
        self.assertEqual(text.count('ai_weight = { weight = 0 }'),42)
        self.assertIn('potential = {\n        is_ai = no',text)

    def test_unknown_and_special_deposits_are_not_whitelisted(self):
        supported=self.m['defaults']['supported_deposits']
        self.assertEqual(len(supported),51)
        self.assertIn('d_minerals_2',supported)
        self.assertNotIn('d_living_metal_deposit',supported)
        self.assertNotIn('d_modded_story_reward',supported)

    def test_megastructure_filter_is_body_specific(self):
        scripts=build.render(self.m)
        tree=parse(scripts['telluric_horizons/common/scripted_triggers/th_eligibility.txt'].decode())
        nodes=list(walk(one(tree,'th_eligible_world')))
        self.assertIn(('built_on_planet','=','yes'),nodes)
        self.assertIn(('is_same_value','=','prevprevprev'),nodes)

    def test_nested_unknown_fields_and_wrong_types_fail(self):
        for mutate in [lambda m:m['defaults'].update(ai_enabld=True),
                       lambda m:m['defaults']['ai_policy'].update(cost_multiple=True),
                       lambda m:m['classes']['pc_barren'].update(fake='yes'),
                       lambda m:m['defaults']['economy'].update(biomass_factor=[1,0])]:
            model=copy.deepcopy(self.m);mutate(model)
            with self.assertRaises(ValueError):build.validate(model)

    def test_v1_migration_is_explicit_nonmutating_and_valid(self):
        old=copy.deepcopy(self.m);old['schema_version']=1
        old['defaults'].pop('gaia',None);old['routes']=[r for r in old['routes'] if r['target']!='pc_gaia']
        for key in ('ai_policy','economy','supported_deposits'):old['defaults'].pop(key)
        before=copy.deepcopy(old)
        migrated=upgrade_v1(old)
        self.assertEqual(old,before)
        build.validate(migrated)
        with self.assertRaises(ValueError):upgrade_v1(migrated)

    def test_early_v1_defaults_and_stale_prices_can_be_upgraded(self):
        old=copy.deepcopy(self.m);old['schema_version']=1
        old['defaults'].pop('gaia',None);old['routes']=[r for r in old['routes'] if r['target']!='pc_gaia']
        old['defaults']={k:old['defaults'][k] for k in ('min_size_proxy','max_size_proxy','ai_enabled')}
        route=next(r for r in old['routes'] if r['id']=='barren_to_continental');route['energy']=22000
        result=upgrade_v1(old);build.validate(result)
        self.assertEqual(next(r for r in result['routes'] if r['id']=='barren_to_continental')['energy'],19000)

    def test_tooltip_bounds_are_derived_from_model(self):
        self.m['defaults']['min_size_proxy']=11
        text=build.render(self.m)['telluric_horizons/localisation/russian/th_l_russian.yml'].decode('utf-8-sig')
        self.assertIn('11–40',text)
        self.assertNotIn('$TH_MIN_SIZE$',text)
        self.m['localization'].pop('th_deposits')
        with self.assertRaises(ValueError):build.validate(self.m)

    def test_runtime_fixtures_are_opt_in_and_cover_all_routes(self):
        fixtures=fixture_files(self.m)
        text=fixtures['events/th_test_events.txt'].decode()
        self.assertEqual(text.count('spawn_planet = {'),42)
        self.assertEqual(text.count('[TH TEST] PASS '),42*5+11)
        for name in build.render(self.m):self.assertNotIn('th_test',name)
        parse(text)

    def test_ai_monitor_has_no_cheats_and_cleans_sampling_variables(self):
        files=fixture_files(self.m,'ai')
        text=files['events/th_ai_test_events.txt'].decode()
        keys={k for k,_,v in walk(parse(text))}
        self.assertFalse({'give_technology','add_resource','spawn_planet','set_owner'} & keys)
        self.assertIn('on_yearly_pulse_country',files['common/on_actions/th_ai_test_on_actions.txt'].decode())
        self.assertEqual(text.count('clear_variable = th_ai_'),7)

    def test_reviewed_generated_link_snapshots(self):
        text=build.render(self.m)['telluric_horizons/common/terraform/zz_th_engineering.txt'].decode()
        for route in ('barren_to_desert','toxic_to_arctic'):
            block='# '+route+'\n'+text.split('# '+route+'\n',1)[1].split('\n# ',1)[0]
            if not block.endswith('\n'):block+='\n'
            expected=(Path(__file__).parent/'golden'/(route+'.txt')).read_text()
            self.assertEqual(block,expected)

    def test_collector_cannot_turn_missing_or_duplicate_checks_into_pass(self):
        self.assertEqual(collect('',self.m)['eligibility_fixture'],'INCOMPLETE')
        text='[TH TEST] SETUP COMPLETE;\n'
        for r in self.m['routes']:
            for case in ('eligible','protected','small','special_deposit','restored'):
                text+='[TH TEST] PASS '+r['id']+' '+case+'\n'
        self.assertEqual(collect(text,self.m)['eligibility_fixture'],'PASS')
        self.assertEqual(collect(text+text,self.m)['eligibility_fixture'],'INCOMPLETE')
        self.assertEqual(collect(text+'[TH TEST] FAIL example\n',self.m)['eligibility_fixture'],'FAIL')
        self.assertEqual(collect(text,self.m)['gameplay_payment'],'NOT TESTED')


if __name__=='__main__':unittest.main()
