"""Base-cost graph checks. Does not simulate modifiers, DLC or an economy."""
import heapq


def shortest(edges, source, metric):
    distance = {source: 0}
    queue = [(0, source)]
    while queue:
        cost, node = heapq.heappop(queue)
        if cost != distance[node]:
            continue
        for edge in edges:
            if edge['source'] != node:
                continue
            value = cost + edge[metric]
            target = edge['target']
            if value < distance.get(target, float('inf')):
                distance[target] = value
                heapq.heappush(queue, (value, target))
    return distance


def climate_edges(defaults):
    groups = defaults['climate_groups']
    return [dict(source=a, target=b, **defaults['climate_costs'][
                'same_group' if groups[a] == groups[b] else 'cross_group'])
            for a in groups for b in groups if a != b]


def engineering_targets(model):
    return set(model['defaults']['climate_groups']) | ({model['defaults']['gaia']['target']} if 'gaia' in model['defaults'] else set())


def downstream_edges(defaults):
    edges=climate_edges(defaults)
    if 'gaia' in defaults:
        g=defaults['gaia']
        edges += [dict(source=c,target=g['target'],energy=g['energy'],biomass=g['biomass'],days=g['days']) for c in defaults['climate_groups']]
    return edges


def check_routes(model, climate=None):
    routes = [r for r in model['routes'] if r.get('variant')!='ready_candidate']
    edges = routes + (downstream_edges(model['defaults']) if climate is None else climate)
    for source in {r['source'] for r in routes}:
        for metric in ('energy', 'days'):
            distances = shortest(edges, source, metric)
            for route in routes:
                if route['source'] == source and distances[route['target']] < route[metric]:
                    raise ValueError(f"Cheaper indirect path: {route['id']} ({metric})")
