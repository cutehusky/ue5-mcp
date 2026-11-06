"""Run the first or second phase of prepare/restart/verify smoke scripts.

Usage: run phase A against a running editor, restart the editor, then run phase B.
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent

# script -> (phase A argv, phase B argv); a trailing cleanup argv runs after B when present.
POSITIONAL_WRITE = ['animation_attribute_persistence', 'animation_blueprint_persistence', 'animation_bone_track_persistence',
                    'animation_compression_persistence', 'animation_state_machine_persistence',
                    'animation_timing_persistence', 'sound_cue_graph_persistence']
POSITIONAL_PREP = ['behavior_tree_compound', 'behavior_tree_dynamic', 'environment_query', 'environment_query_composite',
                   'state_tree', 'state_tree_assets', 'state_tree_bindings', 'state_tree_blueprint_instances',
                   'state_tree_container_parameters', 'state_tree_expressions', 'state_tree_functions', 'state_tree_linked',
                   'state_tree_node_references', 'state_tree_ordering', 'state_tree_output_bindings',
                   'state_tree_parameter_layout', 'state_tree_references', 'state_tree_required_events',
                   'state_tree_schema_settings', 'state_tree_single_task', 'state_tree_utility']
FLAG_PREP = ['audio_component_inheritance', 'audio_component_instances', 'audio_component_persistence',
             'behavior_tree_compound_subtree', 'behavior_tree_graph', 'behavior_tree_parallel', 'behavior_tree_subtree',
             'blackboard_authoring', 'blackboard_defaults', 'navigation_area', 'navigation_filter', 'navigation_links',
             'navigation_mesh', 'navigation_modifier', 'navigation_smart', 'world_navigation', 'world_settings']
FLAG_CREATE = ['audio_attenuation_live', 'dialogue_live', 'modulation_authoring_live', 'modulation_live',
               'modulation_profiles_live']
SETUP = ['level_instance_break_live', 'level_instance_edit_live', 'level_instance_live']

SPECS = {}
for n in POSITIONAL_WRITE:
    SPECS[n] = (['write'], ['verify'], None)
for n in POSITIONAL_PREP:
    SPECS[n] = (['prepare'], ['verify'], ['cleanup'])
for n in FLAG_PREP:
    has_cleanup = n not in ('audio_component_inheritance', 'audio_component_instances', 'audio_component_persistence', 'world_settings')
    SPECS[n] = (['--phase', 'prepare'], ['--phase', 'verify'], ['--phase', 'cleanup'] if has_cleanup else None)
for n in FLAG_CREATE:
    SPECS[n] = (['--phase', 'create'], ['--phase', 'verify'], None)
for n in SETUP:
    SPECS[n] = (['setup'], ['verify'], None)
SPECS['blend_space_ids_live'] = (['--stage', 'create'], ['--stage', 'verify'], None)


def run(script, argv, timeout):
    start = time.time()
    try:
        p = subprocess.run([sys.executable, str(HERE / f'smoke_{script}.py'), *argv], cwd=HERE,
                           capture_output=True, text=True, timeout=timeout)
        status = 'pass' if p.returncode == 0 else 'fail'
        tail = (p.stdout[-1200:] + p.stderr[-2500:]).strip()
    except subprocess.TimeoutExpired as e:
        status, tail = 'timeout', str(e)[-800:]
    return {'status': status, 'seconds': round(time.time() - start, 1), 'tail': tail}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['A', 'B'])
    parser.add_argument('--out', required=True)
    parser.add_argument('--only', nargs='*')
    parser.add_argument('--timeout', type=int, default=900)
    args = parser.parse_args()
    out = Path(args.out)
    results = json.loads(out.read_text(encoding='utf-8')) if out.exists() else {}
    for name, (a, b, cleanup) in SPECS.items():
        if args.only and name not in args.only:
            continue
        entry = results.setdefault(name, {})
        if args.phase == 'A':
            entry['A'] = run(name, a, args.timeout)
            print(f"A {entry['A']['status']:7} smoke_{name}.py", flush=True)
        elif entry.get('A', {}).get('status') == 'pass':
            entry['B'] = run(name, b, args.timeout)
            print(f"B {entry['B']['status']:7} smoke_{name}.py", flush=True)
            if cleanup and entry['B']['status'] != 'pass':
                entry['cleanup'] = run(name, cleanup, args.timeout)
        out.write_text(json.dumps(results, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
