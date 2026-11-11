"""Authored, opt-in fixtures for disposable NEW games. Never part of release ZIP.

These scripts do not test UI payment/cancellation automatically. Setup is a cheat
fixture and must never be enabled on a valued save. No original game files needed.
"""
import argparse
from pathlib import Path
from build import load
from balance import engineering_targets


def assertion(condition, label, should_pass=True):
    yes,no=('PASS','FAIL') if should_pass else ('FAIL','PASS')
    return f'''if = {{
    limit = {{ {condition} }}
    log = "[TH TEST] {yes} {label}"
}}
else = {{ log = "[TH TEST] {no} {label}" }}'''


def ai_fixture_files(model):
    variables=['day','energy','energy_income','biomass','biomass_income','projects','colonies']
    clear='\n'.join('clear_variable = th_ai_'+v for v in variables)
    events=f'''# AUTHORED TEST MONITOR. No technology/resource/planet grants.
namespace = th_ai_test
country_event = {{
    id = th_ai_test.1
    hide_window = yes
    is_triggered_only = yes
    trigger = {{ is_ai = yes is_country_type = default }}
    immediate = {{
        export_trigger_value_to_variable = {{ trigger = days_passed variable = th_ai_day }}
        export_trigger_value_to_variable = {{ trigger = num_owned_planets variable = th_ai_colonies }}
        export_resource_stockpile_to_variable = {{ resource = energy variable = th_ai_energy }}
        export_resource_income_to_variable = {{ resource = energy variable = th_ai_energy_income }}
        export_resource_stockpile_to_variable = {{ resource = biomass variable = th_ai_biomass }}
        export_resource_income_to_variable = {{ resource = biomass variable = th_ai_biomass_income }}
        set_variable = {{ which = th_ai_projects value = 0 }}
        every_planet_within_border = {{
            limit = {{ is_terraforming = yes }}
            root = {{ change_variable = {{ which = th_ai_projects value = 1 }} }}
        }}
        log = "[TH AI] SAMPLE day=[This.th_ai_day];country=[This.GetName];colonies=[This.th_ai_colonies];energy=[This.th_ai_energy];net_energy=[This.th_ai_energy_income];biomass=[This.th_ai_biomass];net_biomass=[This.th_ai_biomass_income];projects=[This.th_ai_projects]"
        {clear}
    }}
}}
'''
    return {'events/th_ai_test_events.txt':events.encode(),
            'common/on_actions/th_ai_test_on_actions.txt':b'on_yearly_pulse_country = { events = { th_ai_test.1 } }\n'}


def fixture_files(model, mode='eligibility'):
    if mode=='ai':return ai_fixture_files(model)
    if mode!='eligibility':raise ValueError('Unknown runtime fixture mode')
    fixtures=[]
    for i,route in enumerate(model['routes']):
        tests=assertion('th_eligible_world = yes',route['id']+' eligible')
        tests+='\nset_planet_flag = th_protected\n'+assertion('th_eligible_world = yes',route['id']+' protected',False)
        tests+='\nremove_planet_flag = th_protected\nset_planet_size = 9\n'+assertion('th_eligible_world = yes',route['id']+' small',False)
        tests+='\nset_planet_size = 15\nadd_deposit = d_living_metal_deposit\n'+assertion('th_eligible_world = yes',route['id']+' special_deposit',False)
        tests+='\nremove_deposit = d_living_metal_deposit\n'+assertion('th_eligible_world = yes',route['id']+' restored')
        fixtures.append(f'''spawn_planet = {{
    class = {route['source']}
    location = this
    orbit_distance_offset = {100+i*10}
    orbit_angle_offset = {i*10}
    size = 15
    init_effect = {{
        set_name = "TH_TEST_{route['id']}"
        set_planet_flag = th_test_fixture
        set_planet_flag = th_test_target_{route['target']}
        clear_deposits = yes
        clear_planet_modifiers = yes
        set_surveyed = {{ surveyed = yes surveyor = root }}
        {tests}
    }}
}}''')
    bodies='\n'.join(fixtures)
    completion=[]
    for target in sorted(engineering_targets(model)):
        completion.append(f'''if = {{ limit = {{ has_planet_flag = th_test_target_{target} }}
{assertion(f'is_planet_class = {target}', 'completed '+target)}
}}''')
    gaia_perk='add_ascension_perk = '+model['defaults']['gaia']['required_perk'] if 'gaia' in model['defaults'] else ''
    events=f'''# AUTHORED TEST FIXTURE. DISPOSABLE NEW GAME ONLY. NOT RELEASE CONTENT.
namespace = th_test
country_event = {{
    id = th_test.0
    hide_window = yes
    is_triggered_only = yes
    trigger = {{ is_ai = no }}
    immediate = {{ country_event = {{ id = th_test.1 days = 3 }} }}
}}
country_event = {{
    id = th_test.1
    hide_window = yes
    is_triggered_only = yes
    trigger = {{ is_ai = no NOT = {{ has_country_flag = th_test_setup }} }}
    immediate = {{
        set_country_flag = th_test_setup
        give_technology = {{ tech = tech_terrestrial_sculpting message = no }}
        give_technology = {{ tech = tech_climate_restoration message = no }}
        {gaia_perk}
        capital_scope = {{ solar_system = {{
{bodies}
        }} }}
        log = "[TH TEST] SETUP COMPLETE; manual native projects, resources, saves and AI still NOT TESTED"
    }}
}}
planet_event = {{
    id = th_test.2
    hide_window = yes
    is_triggered_only = yes
    trigger = {{ has_planet_flag = th_test_fixture }}
    immediate = {{
        {assertion('is_terraforming = no','project no longer active')}
        {''.join(completion)}
        log = "[TH TEST] Completion class check only; resource/property correctness requires before/after comparison"
    }}
}}
'''
    return {'events/th_test_events.txt':events.encode(),
            'common/on_actions/th_test_on_actions.txt':b'on_game_start_country = { events = { th_test.0 } }\n'}


def install_fixture(destination, model, mode='eligibility'):
    for name,data in fixture_files(model,mode).items():
        path=Path(destination)/name
        if path.exists():raise ValueError('Test fixture already exists: '+str(path))
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path)
    p.add_argument('--mode',choices=['eligibility','ai'],default='eligibility');a=p.parse_args()
    if a.output.exists():p.error('Use a NEW empty destination outside the release tree')
    from build import ROOT
    if a.output.resolve().is_relative_to(ROOT):p.error('Keep runtime artifacts outside the repository')
    install_fixture(a.output,load(),a.mode)
    print(a.output)


if __name__=='__main__':main()
