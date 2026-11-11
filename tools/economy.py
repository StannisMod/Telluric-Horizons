"""Exact, deterministic price scenarios; these are calculations, not engine tests."""
from fractions import Fraction
from balance import climate_edges, downstream_edges, shortest


def price_table(model, hydrocentric=False):
    d = model['defaults']
    discount = Fraction(*d['economy']['hydrocentric_ocean_factor']) if hydrocentric else Fraction(1)
    edges = []
    normal=[r for r in model['routes'] if r['target'] in d['climate_groups']]
    for route in normal + climate_edges(d):
        cost = Fraction(route['energy']) * (discount if route['target']=='pc_ocean' else 1)
        edges.append(dict(source=route['source'],target=route['target'],energy=cost))
    distances = {s:shortest(edges,s,'energy') for s in {r['source'] for r in model['routes']}}
    # Integrality is required: never silently round a price up and reintroduce a shortcut.
    result = {}
    for route in normal:
        price = distances[route['source']][route['target']]
        biomass = price * Fraction(*d['economy']['biomass_factor'])
        if price.denominator != 1 or biomass.denominator != 1:
            raise ValueError('Nonintegral scenario price: ' + route['id'])
        result[route['id']] = dict(energy=int(price),biomass=int(biomass))
    if 'gaia' in d:
        g=d['gaia']
        for route in model['routes']:
            if route['target']!=g['target']:continue
            if route.get('variant')=='ready_candidate':
                profile=g['candidate_sources'][route['source']]
                factor=discount if hydrocentric else 1
                energy=Fraction(profile['energy'])*factor+g['energy']
                biomass=Fraction(profile['biomass'])*factor+g['biomass']
            else:
                prices=[result[r['id']] for r in normal if r['source']==route['source']]
                energy=min(p['energy'] for p in prices)+g['energy']
                biomass=min(p['biomass'] for p in prices)+g['biomass']
            if Fraction(energy).denominator!=1 or Fraction(biomass).denominator!=1:
                raise ValueError('Nonintegral Gaia scenario price')
            result[route['id']]={'energy':int(energy),'biomass':int(biomass)}
    return result


def ai_reserves(model, route):
    d = model['defaults']
    price = price_table(model)[route['id']]
    policy = d['ai_policy']
    return {resource:price[resource]*policy['cost_multiple']+policy['reserve'][resource]
            for resource in ('energy','biomass')}


def ai_decision(policy, *, ideal, peaceful, colonies, active_projects, available_colony,
                stockpile, income, required_stockpile, deficits, resource='energy'):
    """Pure reference policy for boundary tests; not a simulation of native AI."""
    return (ideal and peaceful and colonies >= policy['min_colonies'] and
            active_projects == 0 and not available_colony and not deficits and
            stockpile >= required_stockpile and income >= policy['min_income'][resource])


def check_scenarios(model):
    for hydro in (False,True):
        prices = price_table(model,hydro)
        climate = downstream_edges(model['defaults'])
        for resource in ('energy','biomass'):
            factor = Fraction(*model['defaults']['economy']['biomass_factor']) if resource=='biomass' else Fraction(1)
            discount = Fraction(*model['defaults']['economy']['hydrocentric_ocean_factor']) if hydro else Fraction(1)
            edges=[dict(source=r['source'],target=r['target'],energy=(r['biomass'] if resource=='biomass' and 'biomass' in r else Fraction(r['energy'])*factor)*(discount if r['target']=='pc_ocean' else 1)) for r in climate]
            regular=[r for r in model['routes'] if r.get('variant')!='ready_candidate']
            edges += [dict(source=r['source'],target=r['target'],energy=prices[r['id']][resource]) for r in regular]
            for source in {r['source'] for r in model['routes']}:
                dist=shortest(edges,source,'energy')
                for route in regular:
                    if route['source']==source and dist[route['target']] < prices[route['id']][resource]:
                        raise ValueError('Scenario shortcut: '+route['id'])
    # Uniform parent-category modifiers scale all paths equally; positive floor only.
    for factor in model['defaults']['economy']['parent_cost_factors']:
        if Fraction(*factor) <= 0:
            raise ValueError('Nonpositive scenario multiplier')


def render_report(model):
    tables={h:price_table(model,h) for h in (False,True)}
    lines=['# Calculated economy scenarios\n\nNot a game simulation. Prices precede uniform country modifiers.\n\n',
           '| Route | Energy | Biomass | Hydro energy | Hydro biomass | Years | AI energy reserve | AI biomass reserve |\n',
           '|---|---:|---:|---:|---:|---:|---:|---:|\n']
    for r in model['routes']:
        a,b=tables[False][r['id']],tables[True][r['id']];reserve=ai_reserves(model,r)
        lines.append(f"| {r['id']} | {a['energy']} | {a['biomass']} | {b['energy']} | {b['biomass']} | {r['days']/360:g} | {reserve['energy']} | {reserve['biomass']} |\n")
    lines.append('\n## Affordability reference\n\nSavings time at constant net energy income; no growth, upkeep shocks, opportunity cost or actual game year is simulated. All routes still require tier-4 Climate Restoration.\n\n| Scenario | Net energy/month | Cheapest project savings years | Most expensive project savings years |\n|---|---:|---:|---:|\n')
    prices=[v['energy'] for v in tables[False].values()]
    for s in model['defaults']['economy']['income_scenarios']:
        income=s['monthly_energy']
        lines.append(f"| {s['label']} | {income} | {min(prices)/(income*12):.2f} | {max(prices)/(income*12):.2f} |\n")
    lines.append('\nBoth resources, both Hydrocentric states, and positive parent-category multipliers are checked. Uniform multipliers preserve shortest-path ordering. New costs use terraforming, with the Ocean discount explicitly applied once and propagated through the engineering price closure. Native climate/DLC links remain unchanged. Gaia includes the native 7,500 energy / 3,500 biomass / 10-year step; ready-candidate variants are separate applicability states, not unconditional shortcuts. Compound parent/Ocean modifier stacking and rounding still require runtime verification. AI thresholds deliberately use undiscounted costs plus a reserve.\n')
    return ''.join(lines).encode()
