"""Bounded real-engine loading probe in a disposable user profile.

Not a gameplay, terraforming completion, DLC, save or AI test.
Only authored generated mod files are copied; game installation remains external.
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from build import build, ROOT


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-dir',default=os.environ.get('STELLARIS_GAME_DIR'))
    parser.add_argument('--seconds',type=int,default=40)
    args=parser.parse_args()
    if not args.game_dir or not 20 <= args.seconds <= 55:
        parser.error('Set --game-dir / STELLARIS_GAME_DIR and seconds in 20..55')
    game=Path(args.game_dir).resolve()
    if not (game/'stellaris').is_file():
        parser.error('Linux Stellaris executable missing')
    build(check=True)
    work=Path(tempfile.mkdtemp(prefix='th-engine-smoke-'))
    user=work/'user';mods=user/'mod';mods.mkdir(parents=True)
    mod=mods/'telluric_horizons'
    shutil.copytree(ROOT/'generated/telluric_horizons',mod)
    descriptor=(ROOT/'generated/telluric_horizons.mod').read_text().replace(
        'path="mod/telluric_horizons"',f'path="{mod}"')
    (mods/'telluric_horizons.mod').write_text(descriptor)
    # Test-only mounting witness; never included in the distributed mod.
    marker='th_runtime_mount_probe'
    folder=mod/'common/static_modifiers';folder.mkdir(exist_ok=True)
    (folder/'th_runtime_probe.txt').write_text(marker+' = { }\n')
    for language in ('english','russian'):
        (mod/f'localisation/{language}/th_runtime_probe_l_{language}.yml').write_text(
            f'l_{language}:\n {marker}:0 "Runtime mounting probe"\n',encoding='utf-8-sig')
    (user/'dlc_load.json').write_text(json.dumps({'disabled_dlcs':[],'enabled_mods':['mod/telluric_horizons.mod']}))
    env=dict(os.environ,XDG_DATA_HOME=str(work/'data'))
    command=[str(game/'stellaris'),f'-userdir={user}',f'-mod={mods / "telluric_horizons.mod"}','-debug_mode']
    print('Isolated engine profile:',work,flush=True)
    timed_out=False
    with (work/'stdout.log').open('w') as log:
        process=subprocess.Popen(command,cwd=game,env=env,stdout=log,stderr=subprocess.STDOUT)
        try:
            code=process.wait(timeout=args.seconds)
        except subprocess.TimeoutExpired:
            timed_out=True;process.terminate()
            try:code=process.wait(timeout=3)
            except subprocess.TimeoutExpired:process.kill();code=process.wait()
    logs=user/'logs'
    setup=(logs/'setup.log').read_text(errors='replace') if (logs/'setup.log').exists() else ''
    errors=(logs/'error.log').read_text(errors='replace') if (logs/'error.log').exists() else ''
    diagnostics=[line for line in errors.splitlines() if re.search(r'\bth_|zz_th_engineering|telluric_horizons',line,re.I)]
    result=dict(profile=str(work),exit_code=code,bounded_stop=timed_out,
                mod_mounted=marker in setup,mod_diagnostics=diagnostics,
                total_error_lines=len(errors.splitlines()),gameplay='NOT TESTED')
    (work/'result.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
    return 0 if result['mod_mounted'] and not diagnostics and timed_out else 1


if __name__=='__main__':raise SystemExit(main())
