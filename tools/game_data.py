"""Read-only audits against an external game installation. Never copies game scripts."""
from collections import Counter
import hashlib
from pathlib import Path
from paradox import read, one, walk, parse
from balance import climate_edges, check_routes
from economy import price_table
from fractions import Fraction


def terraform_links(game):
    links = []
    for path in sorted((Path(game)/'common/terraform').glob('*.txt')):
        nodes = read(path)
        variables = {k:v for k, op, v in nodes if k and k.startswith('@')}
        def number(value):
            value = variables.get(value, value)
            return int(value) if value is not None and str(value).isdigit() else None
        for k, op, v in nodes:
            if k != 'terraform_link':
                continue
            resources = one(v, 'resources', [])
            costs = [number(value) for key, _, value in walk(resources) if key in ('ENERGY_COST','energy')]
            biomass=[number(value) for key,_,value in walk(resources) if key in ('BIOMASS_COST','biomass')]
            links.append(dict(source=one(v,'from'), target=one(v,'to'),
                              energy=costs[0] if len(costs)==1 else None,
                              biomass=biomass[0] if len(biomass)==1 else None,
                              days=number(one(v,'duration')),
                              modifiers={value for key, _, value in walk(one(v,'potential',[])) if key=='has_modifier'},
                              unlock_perks={value for key,_,value in walk(one(v,'condition',[])) if key=='has_ascension_perk'},
                              unlock_flags={value for key,_,value in walk(one(v,'condition',[])) if key=='has_country_flag'},
                              file=path.name))
    if not links:
        raise ValueError('No vanilla terraform definitions')
    return links


def audit(game, model):
    game = Path(game)
    links = terraform_links(game)
    climates = set(model['defaults']['climate_groups'])
    actual = [r for r in links if r['source'] in climates and r['target'] in climates and r['source']!=r['target']]
    expected = {(r['source'],r['target']):(r['energy'],r['days']) for r in climate_edges(model['defaults'])}
    # Extra story-specific alternatives do not replace the standard climate edge.
    for pair, cost in expected.items():
        candidates = [r for r in actual if (r['source'],r['target'])==pair]
        if not any((r['energy'],r['days'])==cost for r in candidates):
            raise ValueError('Vanilla climate baseline changed: ' + str(pair))
    check_routes(model, climate_edges(model['defaults']))
    # Relax all story/DLC gates on the numeric downstream network. A pass in this
    # superset proves no cheaper scalar-energy route in any gated subset.
    from balance import shortest
    sources={r['source'] for r in model['routes']}
    downstream=[r for r in links if r['source'] not in sources and r['energy'] is not None and r['days'] is not None]
    for hydro in (False,True):
        price=price_table(model,hydro)
        discount=Fraction(*model['defaults']['economy']['hydrocentric_ocean_factor']) if hydro else 1
        extended=[dict(r,energy=Fraction(r['energy'])*(discount if r['target']=='pc_ocean' else 1)) for r in downstream]
        extended += [dict(r,energy=price[r['id']]['energy']) for r in model['routes']]
        for source in sources:
            for metric in ('energy','days'):
                distances=shortest(extended,source,metric)
                for route in model['routes']:
                    expected_price=price[route['id']]['energy'] if metric=='energy' else route['days']
                    if route['source']==source and distances[route['target']]<expected_price:
                        raise ValueError('Extended-network shortcut: '+route['id']+' '+metric)
    for route in actual:
        if (route['source'],route['target']) in expected and route['biomass'] is not None:
            if route['biomass'] != route['energy']*Fraction(*model['defaults']['economy']['biomass_factor']):
                raise ValueError('Vanilla biomass ratio changed')
    overlaps = 0
    for route in model['routes']:
        candidates = [r for r in links if r['source']==route['source'] and r['target']==route['target']]
        if candidates:
            handoff = model['defaults']['candidate_handoffs'].get(route['source'])
            if not handoff or (handoff['targets']!='all' and route['target'] not in handoff['targets']):
                raise ValueError('Unhandled vanilla pair overlap: ' + route['id'])
            if any(handoff['modifier'] not in c['modifiers'] for c in candidates):
                raise ValueError('Candidate gate changed: ' + route['id'])
            for c in candidates:
                if handoff['aquatic_only'] != ('ap_hydrocentric' in c['unlock_perks']):
                    raise ValueError('Hydrocentric handoff contract changed')
                detox=('ap_detox' in c['unlock_perks'] or 'knights_detox' in c['unlock_flags'])
                if handoff['detox_only'] != detox:raise ValueError('Detox handoff contract changed')
            overlaps += 1
    hashes = {p.relative_to(game).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted((game/'common/terraform').glob('*.txt'))}
    pairs = Counter((r['source'],r['target']) for r in links)
    return dict(terraform_links=len(links), repeated_vanilla_pairs=sum(n>1 for n in pairs.values()),
                engineering_overlaps_with_candidate_handoff=overlaps,
                standard_climate_pairs=len(expected),extended_numeric_downstream_links=len(downstream),
                source_sha256=hashes)


def definitions(game, folder):
    return {k:v for p in sorted((Path(game)/'common'/folder).rglob('*.txt'))
            for k,op,v in read(p) if k and isinstance(v,list)}


def check_references(game, model, files):
    """Check only explicitly typed references; does not claim general scope validation."""
    mappings={'has_technology':'technology','has_ascension_perk':'ascension_perks',
              'has_trait':'traits','has_modifier':'static_modifiers','is_deposit_type':'deposits'}
    catalogs={key:set(definitions(game,folder)) for key,folder in mappings.items()}
    own={k for name,data in files.items() if '/scripted_triggers/' in name
         for k,_,v in parse(data.decode()) if k and isinstance(v,list)}
    scripted=set(definitions(game,'scripted_triggers'))|own
    required_helpers={'is_wilderness_empire','has_aquatic_trait','is_holy_world'}
    if required_helpers-scripted:raise ValueError('Missing scripted helpers: '+str(sorted(required_helpers-scripted)))
    checked=0
    for name,data in files.items():
        if not name.endswith('.txt'):continue
        for key,op,value in walk(parse(data.decode('utf-8-sig'))):
            if key in catalogs and isinstance(value,str):
                if value not in catalogs[key]:raise ValueError('Missing '+mappings[key]+' reference: '+value)
                checked+=1
            if key and key.startswith('th_') and key not in own:
                raise ValueError('Unknown authored scripted trigger: '+key)
            if key=='fail_text' and isinstance(value,str) and value.startswith('th_') and value not in model['localization']:
                raise ValueError('Missing authored tooltip: '+value)
            if key=='inline_script' and isinstance(value,list):
                script=one(value,'script')
                if not script or not (Path(game)/'common/inline_scripts'/f'{script}.txt').is_file():
                    raise ValueError('Missing inline script: '+str(script))
            if key=='th_ai_engineering_budget' and isinstance(value,list) and one(value,'TARGET') is not None:
                if one(value,'TARGET') not in model['classes']:raise ValueError('Invalid AI target parameter')
    helper=Path(game)/'common/inline_scripts/terraform/wilderness_biomass.txt'
    if not helper.is_file():raise ValueError('Missing native Wilderness queue helper')
    helper_keys={key for key,_,v in read(helper)}
    if not {'on_queued','on_unqueued'} <= helper_keys:
        raise ValueError('Native Wilderness queue contract changed')
    effects=definitions(game,'scripted_effects')
    if not {'global_biomass_spender','unqueue_biomass_effect'} <= effects.keys():
        raise ValueError('Native biomass queue effects missing')
    # Public metadata expresses this exact category modifier; a drift must not
    # silently result in a manual discount differing from the native perk.
    perks=definitions(game,'ascension_perks')
    actual=one(one(perks['ap_hydrocentric'],'modifier',[]),'terraforming_ocean_cost_mult')
    if actual is None or 1+Fraction(actual)!=Fraction(*model['defaults']['economy']['hydrocentric_ocean_factor']):
        raise ValueError('Hydrocentric discount changed')
    configured=model['defaults']
    marked=set()
    engineering={k for k,v in model['classes'].items() if v['policy']=='engineer'}
    for path in (Path(game)/'common/solar_system_initializers').glob('*.txt'):
        for key,_,body in walk(read(path)):
            if key=='planet' and isinstance(body,list) and one(body,'class') in engineering:
                marked.update(v for k,_,v in walk(body) if k in {'set_planet_flag','set_carrier_flag'} and isinstance(v,str))
    reviewed=set(configured['protected_planet_flags'])|set(configured['reviewed_unprotected_flags'])
    if marked-reviewed:
        raise ValueError('Unreviewed marked initializer bodies: '+str(sorted(marked-reviewed)))
    return checked
