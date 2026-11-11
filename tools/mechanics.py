"""Authored script templates. Vanilla helpers are referenced, never copied."""
from economy import price_table, ai_reserves


def candidate_condition(handoff):
    text=f"from = {{ has_modifier = {handoff['modifier']} }}"
    if handoff['aquatic_only']:
        text+='\n            OR = { has_aquatic_trait = yes has_trait = trait_robot_aquatic }\n            has_ascension_perk = ap_hydrocentric'
    if handoff['detox_only']:
        text+='\n            OR = { has_ascension_perk = ap_detox has_country_flag = knights_detox }'
    return text


def resources(model, route, tables):
    lines=['    resources = { category = terraforming']
    for wilderness,resource in ((False,'energy'),(True,'biomass')):
        for hydro in (False,True):
            condition='has_ascension_perk = ap_hydrocentric'
            if not hydro:condition='NOT = { '+condition+' }'
            price=tables[hydro][route['id']][resource]
            lines.append(f'''        cost = {{
            trigger = {{ is_wilderness_empire = {'yes' if wilderness else 'no'} {condition} }}
            {resource} = {price}
        }}''')
    lines.append('    }\n    inline_script = { script = terraform/wilderness_biomass }')
    return '\n'.join(lines)


def ai_call(model, route):
    reserves=ai_reserves(model,route)
    gaia='yes' if route['target']==model['defaults'].get('gaia',{}).get('target') else 'no'
    return f"th_ai_engineering_budget = {{ TARGET = {route['target']} GAIA = {gaia} ENERGY = {reserves['energy']} BIOMASS = {reserves['biomass']} }}"


def ai_weight(model, route):
    if not model['defaults']['ai_enabled'] or route['ai_weight']==0:
        return '    ai_weight = { weight = 0 }'
    return f'''    ai_weight = {{
        weight = 0
        modifier = {{ weight = {route['ai_weight']} is_ai = yes {ai_call(model,route)} }}
    }}'''


def auxiliary_triggers(model):
    d=model['defaults'];p=d['ai_policy']
    allowed='\n'.join('        is_deposit_type = '+x for x in d['supported_deposits'])
    return f'''
# Scope: deposit. Unknown/event/strategic deposits block engineering, rather than being copied.
th_supported_engineering_deposit = {{
    OR = {{
{allowed}
    }}
}}

# Scope: country. Native weights and hard conditions share the same budget policy.
th_ai_engineering_budget = {{
    OR = {{ ideal_planet_class = $TARGET$ AND = {{ always = $GAIA$ has_ascension_perk = ap_world_shaper }} }}
    is_at_war = no
    num_owned_planets >= {p['min_colonies']}
    NOR = {{ has_deficit = energy has_deficit = minerals has_deficit = food has_deficit = consumer_goods }}
    OR = {{
        AND = {{
            is_wilderness_empire = no
            resource_stockpile_compare = {{ resource = energy value >= $ENERGY$ }}
            resource_income_compare = {{ resource = energy value >= {p['min_income']['energy']} }}
        }}
        AND = {{
            is_wilderness_empire = yes
            NOT = {{ has_deficit = biomass }}
            resource_stockpile_compare = {{ resource = biomass value >= $BIOMASS$ }}
            resource_income_compare = {{ resource = biomass value >= {p['min_income']['biomass']} }}
        }}
    }}
    NOT = {{ any_planet_within_border = {{ is_terraforming = yes }} }}
    NOT = {{ any_planet_within_border = {{ is_colony = no can_colonize = {{ who = root status = yes }} }} }}
}}
'''
