"""Read-only structural comparison with an external mod; not a runtime guarantee."""
import argparse
import json
import re
from pathlib import Path
from build import load, render
from paradox import read,walk,parse


SENSITIVE={'terraform_link','change_pc','set_planet_size','spawn_planet','clear_deposits',
           'reroll_deposits','remove_deposit','add_deposit','on_terraforming_begun','on_terraforming_complete'}


def inspect(mod, model):
    mod=Path(mod)
    if not (mod/'descriptor.mod').is_file():raise ValueError('External mod descriptor missing')
    files=[p for p in mod.rglob('*') if p.is_file()]
    own=render(model)
    paths={k.removeprefix('telluric_horizons/') for k in own if k.startswith('telluric_horizons/') and not k.endswith('descriptor.mod')}
    collisions=sorted(paths & {p.relative_to(mod).as_posix() for p in files})
    own_triggers={k for name,data in own.items() if '/scripted_triggers/' in name for k,_,v in parse(data.decode())}
    declared=set();sensitive=set();scripts=0
    for path in mod.rglob('*.txt'):
        tree=read(path);scripts+=1
        sensitive.update(k for k,_,v in walk(tree) if k in SENSITIVE)
        if 'scripted_triggers' in path.parts:declared.update(k for k,_,v in tree)
    duplicates=sorted(own_triggers & declared)
    foreign_loc={k for p in mod.rglob('*.yml') for k in re.findall(r'^\s*([a-zA-Z0-9_]+):',p.read_text(encoding='utf-8-sig'),re.M)}
    loc_collisions=sorted(set(model['localization']) & foreign_loc)
    return dict(status='REVIEW_REQUIRED' if collisions or duplicates or sensitive or loc_collisions else 'NO_STATIC_CONFLICT_FOUND',
                script_files=scripts,path_collisions=collisions,trigger_collisions=duplicates,
                localization_collisions=loc_collisions,sensitive_script_keys=sorted(sensitive),gameplay='NOT TESTED')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mod',type=Path);a=p.parse_args()
    result=inspect(a.mod,load());print(json.dumps(result,indent=2))
    return 0 if result['status']=='NO_STATIC_CONFLICT_FOUND' else 2


if __name__=='__main__':raise SystemExit(main())
