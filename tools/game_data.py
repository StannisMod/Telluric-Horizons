"""Read-only audits against an external game installation. Never copies game scripts."""
from collections import Counter
import hashlib
from pathlib import Path
from paradox import read, one, walk
from balance import climate_edges, check_routes


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
            links.append(dict(source=one(v,'from'), target=one(v,'to'),
                              energy=costs[0] if len(costs)==1 else None,
                              days=number(one(v,'duration')),
                              modifiers={value for key, _, value in walk(one(v,'potential',[])) if key=='has_modifier'},
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
    overlaps = 0
    for route in model['routes']:
        candidates = [r for r in links if r['source']==route['source'] and r['target']==route['target']]
        if candidates:
            handoff = model['defaults']['candidate_handoffs'].get(route['source'])
            if not handoff or (handoff['targets']!='all' and route['target'] not in handoff['targets']):
                raise ValueError('Unhandled vanilla pair overlap: ' + route['id'])
            if any(handoff['modifier'] not in c['modifiers'] for c in candidates):
                raise ValueError('Candidate gate changed: ' + route['id'])
            overlaps += 1
    hashes = {p.relative_to(game).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted((game/'common/terraform').glob('*.txt'))}
    pairs = Counter((r['source'],r['target']) for r in links)
    return dict(terraform_links=len(links), repeated_vanilla_pairs=sum(n>1 for n in pairs.values()),
                engineering_overlaps_with_candidate_handoff=overlaps,
                standard_climate_pairs=len(expected), source_sha256=hashes)
