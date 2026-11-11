"""Deterministic offline compiler. Does not emulate the Stellaris engine."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import zipfile
from paradox import read as read_script
from balance import check_routes
from game_data import audit, check_references
from economy import check_scenarios, price_table, render_report
from mechanics import resources, ai_call, ai_weight, auxiliary_triggers
from schema import validate_shape

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "model/terraforming.json"
OUT = ROOT / "generated"
SCHEMA = json.loads((ROOT/'model/schema.json').read_text())


def validate(m):
    validate_shape(m,SCHEMA)
    if m.get("schema_version") != 2:
        raise ValueError("Unsupported schema version; no implicit migration")
    if set(m) != {"schema_version", "version", "target_game", "target_checksum", "days_per_year", "defaults", "classes", "routes", "localization"}:
        raise ValueError("Unknown or missing model fields")
    if m["days_per_year"] != 360:
        raise ValueError("Expected Stellaris 360-day accounting year")
    for k in ("min_size_proxy", "max_size_proxy"):
        if type(m["defaults"][k]) is not int or m["defaults"][k] <= 0:
            raise ValueError("Invalid size proxy")
    if m["defaults"]["min_size_proxy"] > m["defaults"]["max_size_proxy"]:
        raise ValueError("Inverted size range")
    ids, pairs = set(), set()
    for name, c in m["classes"].items():
        if not re.fullmatch(r"pc_[a-z0-9_]+", name) or c["policy"] not in {"engineer", "forbidden", "vanilla"}:
            raise ValueError("Invalid class")
    for t in m["routes"]:
        if set(t) != {"id", "source", "target", "energy", "days", "technologies", "ai_weight", "features", "reason"}:
            raise ValueError("Unknown or missing route field")
        pair = t["source"], t["target"]
        if t["id"] in ids or pair in pairs or not re.fullmatch(r"[a-z0-9_]+", t["id"]):
            raise ValueError("Duplicate or invalid route")
        ids.add(t["id"]); pairs.add(pair)
        if any(k not in m["classes"] for k in pair):
            raise ValueError("Unknown planet class")
        if m["classes"][pair[0]]["policy"] != "engineer" or m["classes"][pair[1]]["biosphere"] != "present":
            raise ValueError("Forbidden route")
        for k in ("energy", "days"):
            if type(t[k]) is not int or t[k] <= 0:
                raise ValueError("Nonpositive cost or duration")
        if not t["technologies"] or any(not re.fullmatch(r"tech_[a-z0-9_]+", x) for x in t["technologies"]):
            raise ValueError("Invalid technology requirement")
        if type(t['ai_weight']) is not int or not 0 <= t['ai_weight'] <= 5:
            raise ValueError('AI weight must be an integer in 0..5')
        if not t["reason"] or t["features"] != "native_terraforming_with_preflight":
            raise ValueError("Missing documented feature policy")
    for c, spec in m["classes"].items():
        if spec["policy"] == "engineer" and not any(x[0] == c for x in pairs):
            raise ValueError("Unreachable engineering class")
    for key, values in m["localization"].items():
        if set(values) != {"english", "russian"} or not all(values.values()):
            raise ValueError("Incomplete localization: " + key)
    if not re.fullmatch(r'\d+\.\d+\.\d+', m['target_game']) or not re.fullmatch(r'[0-9a-f]{4}', m['target_checksum']):
        raise ValueError('Invalid target version/checksum')
    d = m['defaults']
    if type(d['ai_enabled']) is not bool:
        raise ValueError('AI enabled must be boolean')
    for field in ('protected_planet_flags', 'protected_star_flags', 'protected_modifiers','supported_deposits'):
        if not isinstance(d[field], list) or any(not re.fullmatch(r'[a-z0-9_]+', x) for x in d[field]):
            raise ValueError('Invalid protection identifier')
    targets = set(d['climate_groups'])
    if set(d['candidate_handoffs']) != {k for k,v in m['classes'].items() if v['policy']=='engineer'}:
        raise ValueError('Each engineering source needs a candidate policy')
    for source, spec in m['classes'].items():
        if spec['policy'] == 'engineer' and {b for a,b in pairs if a == source} != targets:
            raise ValueError('Incomplete engineering climate coverage')
    for costs in d['climate_costs'].values():
        if set(costs) != {'energy','days'} or any(type(x) is not int or x <= 0 for x in costs.values()):
            raise ValueError('Invalid climate cost baseline')
    for source, handoff in d['candidate_handoffs'].items():
        if source not in m['classes'] or not re.fullmatch(r'[a-z0-9_]+', handoff['modifier']):
            raise ValueError('Invalid candidate handoff')
        if handoff['targets'] != 'all' and (not isinstance(handoff['targets'],list) or not set(handoff['targets']) <= targets):
            raise ValueError('Invalid handoff targets')
        if type(handoff['aquatic_only']) is not bool:
            raise ValueError('Invalid aquatic gate')
    check_routes(m)
    policy=d['ai_policy']
    if type(policy['cost_multiple']) is not int or policy['cost_multiple'] < 2:
        raise ValueError('AI must retain at least two base costs')
    if type(policy['min_colonies']) is not int or policy['min_colonies'] < 1:
        raise ValueError('Invalid AI colony floor')
    for field in ('reserve','min_income'):
        if set(policy[field]) != {'energy','biomass'} or any(type(x) is not int or x <= 0 for x in policy[field].values()):
            raise ValueError('Invalid AI resource thresholds')
    for field in ('hydrocentric_ocean_factor','biomass_factor'):
        factor=d['economy'][field]
        if len(factor)!=2 or any(type(x) is not int or x<=0 for x in factor) or factor[0]>factor[1]:
            raise ValueError('Invalid price conversion factor')
    check_scenarios(m)
    return m


def load():
    return validate(json.loads(MODEL.read_text()))


def render(m):
    header = "# GENERATED by tools/build.py; edit model/terraforming.json instead.\n"
    links = [header]
    tables={h:price_table(m,h) for h in (False,True)}
    for t in sorted(m["routes"], key=lambda x: x["id"]):
        tech = "\n".join("        has_technology = " + x for x in t["technologies"])
        handoff = m['defaults']['candidate_handoffs'].get(t['source'])
        gate = ''
        if handoff and (handoff['targets'] == 'all' or t['target'] in handoff['targets']):
            candidate = f"from = {{ has_modifier = {handoff['modifier']} }}"
            if handoff['aquatic_only']:
                candidate += '\n            OR = { has_aquatic_trait = yes has_trait = trait_robot_aquatic }\n            has_ascension_perk = ap_hydrocentric'
            if handoff['detox_only']:
                candidate += '\n            OR = { has_ascension_perk = ap_detox has_country_flag = knights_detox }'
            gate = f'\n        NOT = {{ AND = {{ {candidate} }} }}'
        ai_visibility='' if m['defaults']['ai_enabled'] else '        is_ai = no\n'
        links.append(f'''# {t['id']}
terraform_link = {{
    from = {t['source']}
    to = {t['target']}
{resources(m,t,tables)}
    duration = {t['days']}
    potential = {{
{ai_visibility}        exists = owner{gate}
    }}
    condition = {{
{tech}
        from = {{ th_eligible_world = yes }}
        OR = {{ is_ai = no {ai_call(m,t)} }}
    }}
{ai_weight(m,t)}
    effect = {{ from = {{
        if = {{ limit = {{ has_modifier = {handoff['modifier']} }} remove_modifier = {handoff['modifier']} }}
    }} }}
}}
''')
    d = m["defaults"]
    protections = '\n'.join('    NOT = { has_planet_flag = ' + f + ' }' for f in d['protected_planet_flags'])
    modifiers = '\n'.join('    NOT = { has_modifier = ' + f + ' }' for f in d['protected_modifiers'])
    stars = '\n'.join('            has_star_flag = ' + f for f in d['protected_star_flags'])
    trigger = header + f'''# Scope: planet. Size is a configurable gameplay proxy, not mass/gravity.
th_eligible_world = {{
    custom_tooltip = {{ fail_text = th_surveyed is_surveyed = {{ who = root status = yes }} }}
    custom_tooltip = {{ fail_text = th_uncolonized is_colony = no }}
    custom_tooltip = {{ fail_text = th_borders is_inside_border = root }}
    custom_tooltip = {{ fail_text = th_size planet_size >= {d['min_size_proxy']} planet_size <= {d['max_size_proxy']} }}
    custom_tooltip = {{ fail_text = th_investigation has_anomaly = no NOT = {{ exists = archaeological_site }} }}
    custom_tooltip = {{ fail_text = th_deposits NOT = {{ any_deposit = {{ NOT = {{ th_supported_engineering_deposit = yes }} }} }} }}
    custom_tooltip = {{
    fail_text = th_story
    is_holy_world = no
{protections}
{modifiers}
    solar_system = {{ NOR = {{
{stars}
    }} }}
    }}
    custom_tooltip = {{
    fail_text = th_megastructure
    solar_system = {{
        NOT = {{
            any_system_megastructure = {{
                built_on_planet = yes
                planet = {{ is_same_value = prevprevprev }}
            }}
        }}
    }}
    }}
}}
'''
    trigger += auxiliary_triggers(m)
    descriptor = f'''version="{m['version']}"
name="Telluric Horizons — Planetary Engineering"
tags={{ "Gameplay" }}
supported_version="{m['target_game']}"
'''
    files = {"telluric_horizons/common/terraform/zz_th_engineering.txt": "".join(links).encode(),
             "telluric_horizons/common/scripted_triggers/th_eligibility.txt": trigger.encode(),
             "telluric_horizons/descriptor.mod": descriptor.encode(),
             "telluric_horizons.mod": (descriptor + 'path="mod/telluric_horizons"\n').encode()}
    for lang in ("english", "russian"):
        def localized(value):
            return value.replace('$TH_MIN_SIZE$',str(d['min_size_proxy'])).replace('$TH_MAX_SIZE$',str(d['max_size_proxy']))
        text = f"l_{lang}:\n" + "".join(f" {k}:0 {json.dumps(localized(v[lang]), ensure_ascii=False)}\n" for k,v in sorted(m["localization"].items()))
        files[f"telluric_horizons/localisation/{lang}/th_l_{lang}.yml"] = text.encode("utf-8-sig")
    matrix = [f"# Generated transition matrix\n\nModel {m['version']}; target {m['target_game']} ({m['target_checksum']}).\n\n"
              "Base costs only, before country/DLC modifiers. Existing vanilla links are preserved.\n"
              "New branches yield to usable vanilla candidate links; missing Detox/Hydrocentric unlocks retain the expensive fallback.\n"
              "All new projects use the common protection/size/deposit filter; Wilderness biomass and conservative AI are implemented.\n\n"
              "| From | To | Energy | Years | Technology |\n|---|---|---:|---:|---|\n"]
    for t in m["routes"]:
        matrix.append(f"| {t['source']} | {t['target']} | {t['energy']} | {t['days']/360:g} | {', '.join(t['technologies'])} |\n")
    matrix.append("\n## Preserved and forbidden classes\n\n| Class | Policy | Reason |\n|---|---|---|\n")
    for k,v in m["classes"].items():
        matrix.append(f"| {k} | {v['policy']} | {v['reason']} |\n")
    files["TERRAFORMING_MATRIX.md"] = "".join(matrix).encode()
    files['BALANCE_REPORT.md']=render_report(m)
    return files


def build(check=False):
    files = render(load())
    if check:
        existing = {p.relative_to(OUT).as_posix(): p.read_bytes() for p in OUT.rglob("*") if p.is_file()}
        if existing != files:
            raise ValueError("Generated output is stale, missing or contains unexpected files")
    else:
        # Only own generated directory; never delete or overwrite manual source fragments.
        existing = {p.relative_to(OUT).as_posix() for p in OUT.rglob("*") if p.is_file()}
        if existing - files.keys():
            raise ValueError("Unexpected generated files; inspect before removing: " + str(existing-files.keys()))
        for name, data in files.items():
            dest = OUT/name; dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(data)
    return files


def package():
    files = build(check=True)
    dest = ROOT / f"dist/telluric-horizons-{load()['version']}.zip"
    dest.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name,data in sorted(files.items()):
            entry = zipfile.ZipInfo(name, (2026,1,1,0,0,0)); entry.compress_type = zipfile.ZIP_DEFLATED; entry.external_attr = 0o100644 << 16
            z.writestr(entry,data)
    print(dest.name, hashlib.sha256(dest.read_bytes()).hexdigest())


def check_game():
    raw = os.environ.get("STELLARIS_GAME_DIR")
    if not raw:
        print("NOT TESTED: STELLARIS_GAME_DIR is unset")
        return 2
    game = Path(raw)
    m = load()
    for folder,prefix,required in [("planet_classes", "pc_", set(m["classes"])), ("technology", "tech_", {x for t in m["routes"] for x in t["technologies"]})]:
        paths = list((game / "common" / folder).rglob("*.txt"))
        if not paths:
            raise ValueError("Missing game data: " + folder)
        names = set()
        for p in paths:
            names.update(k for k, op, v in read_script(p) if k and k.startswith(prefix) and isinstance(v, list))
        missing = required-names
        if missing:
            raise ValueError("Missing game definitions: " + str(sorted(missing)))
        if folder == 'planet_classes' and names != required:
            raise ValueError('Unclassified game classes: ' + str(sorted(names-required)))
    settings = json.loads((game/'launcher-settings.json').read_text())
    if settings.get('rawVersion', '').lstrip('v') != m['target_game'] or m['target_checksum'] not in settings.get('version', ''):
        raise ValueError('Installed version/checksum differs from model target')
    result = audit(game, m)
    result['typed_references_checked']=check_references(game,m,render(m))
    print(json.dumps(result, indent=2))
    print("PASS: complete class inventory, version, references, vanilla climate baseline and candidate handoffs; execution/UI remain NOT TESTED")
    return 0


def main():
    p=argparse.ArgumentParser();p.add_argument("command",choices=["lint","build","check-generated","package","check-game"]);a=p.parse_args()
    if a.command == "lint": load(); print("PASS: model invariants")
    elif a.command == "build": build()
    elif a.command == "check-generated": build(check=True)
    elif a.command == "package": package()
    else: return check_game()
    return 0

if __name__ == "__main__":
    try: sys.exit(main())
    except (ValueError, KeyError, OSError) as e:
        print("FAIL:",e,file=sys.stderr);sys.exit(1)
