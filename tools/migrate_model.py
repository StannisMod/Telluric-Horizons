"""Explicit v1 -> v2 migration of our model; never reads game data or saves."""
import argparse
import copy
import json
from pathlib import Path

V2_TOOLTIPS={
    'th_surveyed':{'english':'The world must be surveyed.','russian':'Мир должен быть полностью изучен.'},
    'th_borders':{'english':'The world must be inside your borders.','russian':'Мир должен находиться в ваших границах.'},
    'th_uncolonized':{'english':'Engineering requires an uncolonized world.','russian':'Для инженерии требуется незаселённый мир.'},
    'th_size':{'english':'Allowed size: $TH_MIN_SIZE$–$TH_MAX_SIZE$ (gameplay filter, not gravity).','russian':'Допустимый размер: $TH_MIN_SIZE$–$TH_MAX_SIZE$ (игровой фильтр, не гравитация).'},
    'th_investigation':{'english':'Anomalies and archaeological sites must be absent.','russian':'На мире не должно быть аномалий и археологических объектов.'},
    'th_story':{'english':'Protected, sacred and listed story worlds are excluded.','russian':'Защищённые, священные и перечисленные сюжетные миры исключены.'},
    'th_deposits':{'english':'Special or unknown deposits require a dedicated preservation rule.','russian':'Для особых или неизвестных месторождений требуется отдельное правило сохранения.'},
    'th_megastructure':{'english':'No megastructure may be attached to this world; gateways elsewhere in the system are allowed.','russian':'К этому миру не должно быть прикреплено мегасооружение; врата в другой части системы допустимы.'},
}


def upgrade_v1(old):
    if old.get('schema_version') != 1:
        raise ValueError('Expected schema v1')
    m=copy.deepcopy(old)
    m.update(schema_version=2,version='0.3.0-dev')
    d=m['defaults'];d['ai_enabled']=True
    # Early v1 (0.1) did not yet carry audited climate/handoff metadata.
    groups={k:group for group,ks in {
        'dry':['pc_desert','pc_arid','pc_savannah'],
        'cold':['pc_arctic','pc_tundra','pc_alpine'],
        'wet':['pc_continental','pc_ocean','pc_tropical']}.items() for k in ks}
    d.setdefault('climate_groups',groups)
    d.setdefault('climate_costs',{'same_group':{'energy':2000,'days':1800},'cross_group':{'energy':5000,'days':3600}})
    d.setdefault('candidate_handoffs',{s:{'modifier':v,'targets':t,'aquatic_only':a} for s,v,t,a in [
        ('pc_barren','terraforming_candidate','all',False),('pc_barren_cold','terraforming_candidate','all',False),
        ('pc_toxic','toxic_terraforming_candidate','all',False),('pc_frozen','frozen_terraforming_candidate',['pc_ocean'],True)]})
    for source,handoff in d['candidate_handoffs'].items():handoff['detox_only']=source=='pc_toxic'
    d.setdefault('protected_planet_flags',['th_protected','precursor_world','terraform_nucleus_transfixed','planet_earth'])
    d.setdefault('protected_star_flags',['precursor_system','lcluster','lcluster1','lcluster2','lcluster3','lcluster4','lcluster5','lcluster_lgate','guardian_toxic_god_system'])
    d.setdefault('protected_modifiers',['consecrated_world'])
    d['ai_policy']={'cost_multiple':2,'reserve':{'energy':10000,'biomass':5000},
                    'min_income':{'energy':100,'biomass':50},'min_colonies':3}
    d['economy']={'hydrocentric_ocean_factor':[3,4],'biomass_factor':[1,2],
                  'parent_cost_factors':[[1,1],[3,4],[1,2],[3,2],[2,1]],
                  'income_scenarios':[{'label':'early_reference','monthly_energy':50},{'label':'mid_reference','monthly_energy':200},{'label':'late_reference','monthly_energy':500}]}
    d['supported_deposits']=[f'd_{resource}_{n}' for resource in
        ('minerals','energy','society','physics','engineering') for n in range(1,11)]+['d_society_15']
    d['protected_planet_flags']=list(dict.fromkeys(d['protected_planet_flags']+[
        'megastructure','has_megastructure','living_planet','hoard_planet','hatchling_egg',
        'phaseshifting_active','is_time_loop_world','czyrni_planet','ratling_planet',
        'graveyard_gas','graveyard_site','ignore_startup_effect','reinforcement_fleet_spawn_point','salvager_enclave_planet',
        'frozen_in_time_flag','utopian_planet','ancient_history_planet','crisis_vital_planet','destroyed_by_colossus','planet_cracked',
        'pheromonefrenzy_reviving','previously_infested','shroud_storm_changed','stellarite_terraformed',
        'massex_1_planet','massex_2_planet','massex_3_planet','massex_4_planet','massex_5_planet',
        'machine_world_1','machine_world_2','machine_world_3','machine_world_4']))
    d['reviewed_unprotected_flags']=['toxic_terraforming_candidate']
    for r in m['routes']:
        r['ai_weight']=1
        r['features']='native_terraforming_with_preflight'
    from balance import shortest,climate_edges
    edges=copy.deepcopy(m['routes'])+climate_edges(d)
    for source in {r['source'] for r in m['routes']}:
        for metric in ('energy','days'):
            distances=shortest(edges,source,metric)
            for route in m['routes']:
                if route['source']==source:route[metric]=distances[route['target']]
    m['localization']['th_eligible']={
        'english':'Requires a surveyed uncolonized world inside your borders, allowed size, no anomaly, archaeology, protected story status, attached megastructure or special/unknown deposit. Ordinary orbital deposits use native terraforming rules; no extra resource grants.',
        'russian':'Требуется изученный незаселённый мир в ваших границах, допустимого размера, без аномалии, археологии, защищённого сюжета, прикреплённого мегасооружения и особых/неизвестных месторождений. Обычные орбитальные месторождения обрабатываются штатным терраформированием; дополнительных ресурсов мод не выдаёт.'}
    m['localization'].update(copy.deepcopy(V2_TOOLTIPS))
    return m


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('input',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    if a.output.exists():p.error('Output must be a new file; review before replacing the original')
    model=upgrade_v1(json.loads(a.input.read_text()))
    from build import validate
    validate(model)
    a.output.write_text(json.dumps(model,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':main()
